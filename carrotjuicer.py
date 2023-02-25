import os
import time
import glob
import traceback
import math
import json
from subprocess import CREATE_NO_WINDOW
import msgpack
import numpy as np
from loguru import logger
from selenium.common.exceptions import WebDriverException
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.common.exceptions import NoSuchWindowException
from screenstate import ScreenState, Location
import util
import mdb

SCENARIO_DICT = {
    1: "URA Finals",
    2: "Aoharu Cup",
    3: "Grand Live",
    4: "Make a New Track",
    5: "Grand Masters",
}

class CarrotJuicer():
    start_time = None
    browser = None
    previous_element = None
    threader = None
    screen_state_handler = None
    should_stop = False
    last_browser_rect = None
    reset_browser = False

    _browser_list = None

    def __init__(self, threader):
        self.threader = threader

        self._browser_list = {
            'Firefox': self.firefox_setup,
            'Chrome': self.chrome_setup,
            'Edge': self.edge_setup,
        }

        self.screen_state_handler = threader.screenstate
        self.start_time = math.floor(time.time() * 1000)

        # Remove existing geckodriver.log
        if os.path.exists("geckodriver.log"):
            os.remove("geckodriver.log")


    def load_request(self, msg_path):
        with open(msg_path, "rb") as in_file:
            packet = msgpack.unpackb(in_file.read()[170:], strict_map_key=False)
        return packet


    def load_response(self, msg_path):
        with open(msg_path, "rb") as in_file:
            packet = msgpack.unpackb(in_file.read(), strict_map_key=False)
        return packet


    def create_gametora_helper_url_from_start(self, packet_data):
        if 'start_chara' not in packet_data:
            return None
        d = packet_data['start_chara']
        supports = d['support_card_ids'] + [d['friend_support_card_info']['support_card_id']]

        return self.create_gametora_helper_url(d['card_id'], d['scenario_id'], supports)


    def create_gametora_helper_url(self, card_id, scenario_id, support_ids):
        support_ids = list(map(str, support_ids))
        return f"https://gametora.com/umamusume/training-event-helper?deck={np.base_repr(int(str(card_id) + str(scenario_id)), 36)}-{np.base_repr(int(support_ids[0] + support_ids[1] + support_ids[2]), 36)}-{np.base_repr(int(support_ids[3] + support_ids[4] + support_ids[5]), 36)}".lower()


    def to_json(self, packet):
        with open("packet.json", 'w', encoding='utf-8') as f:
            f.write(json.dumps(packet, indent=4, ensure_ascii=False))

    def firefox_setup(self, helper_url):
        firefox_service = FirefoxService()
        firefox_service.creation_flags = CREATE_NO_WINDOW
        profile = webdriver.FirefoxProfile(util.get_asset("ff_profile"))
        options = webdriver.FirefoxOptions()
        browser = webdriver.Firefox(service=firefox_service, firefox_profile=profile, options=options)
        browser.get(helper_url)
        return browser

    def chromium_setup(self, service, options_class, driver_class, profile, helper_url):
        service.creation_flags = CREATE_NO_WINDOW
        options = options_class()
        options.add_argument("--user-data-dir=" + str(util.get_asset(profile)))
        options.add_argument("--app=" + helper_url)
        browser = driver_class(service=service, options=options)
        return browser

    def chrome_setup(self, helper_url):
        return self.chromium_setup(
            service=ChromeService(),
            options_class=webdriver.ChromeOptions,
            driver_class=webdriver.Chrome,
            profile="chr_profile",
            helper_url=helper_url
        )

    def edge_setup(self, helper_url):
        return self.chromium_setup(
            service=EdgeService(),
            options_class=webdriver.EdgeOptions,
            driver_class=webdriver.Edge,
            profile="edg_profile",
            helper_url=helper_url
        )

    def init_browser(self, helper_url):
        driver = None

        browser_list = []
        if self.threader.settings.loaded_settings['selected_browser']['Auto']:
            browser_list = self._browser_list.values()
        else:
            browser_list = [
                self._browser_list[browser]
                for browser, selected in self.threader.settings.loaded_settings['selected_browser'].items()
                if selected
            ]

        for browser_setup in browser_list:
            try:
                logger.info("Attempting " + str(browser_setup.__name__))
                driver = browser_setup(helper_url)
                break
            except Exception:
                pass
        if not driver:
            util.show_alert_box("UmaLauncher: Unable to start browser.", "Selected webbrowser cannot be started. Use the tray icon to select a browser that is installed on your system.")
        return driver

    def open_helper(self, helper_url):
        self.previous_element = None

        if self.browser:
            self.close_browser()

        self.browser = self.init_browser(helper_url)

        saved_pos = self.threader.settings.get("browser_position")
        if not saved_pos:
            self.reset_browser_position()
        else:
            logger.debug(saved_pos)
            self.browser.set_window_rect(*saved_pos)

        # TODO: Find a way to know if the page is actually finished loading

        while not self.browser.execute_script("""return document.querySelector("[class^='legal_cookie_banner_wrapper_']")"""):
            time.sleep(0.25)

        # Hide the cookies banner
        self.browser.execute_script("""document.querySelectorAll("[class^='legal_cookie_banner_wrapper_']").forEach(e => e.style.display = 'none');""")

        # Enable dark mode (the only reasonable color scheme)
        self.browser.execute_script("""document.querySelector("[class^='styles_header_settings_']").click()""")
        while not self.browser.execute_script("""return document.querySelector("[class^='filters_toggle_button_']");"""):
            time.sleep(0.25)
        
        dark_enabled = self.browser.execute_script("""return document.querySelector("[class^='filters_toggle_button_']").childNodes[0].querySelector("input").checked;""")
        if not dark_enabled:
            self.browser.execute_script("""document.querySelector("[class^='filters_toggle_button_']").childNodes[0].querySelector("input").click()""")
        self.browser.execute_script("""document.querySelector("[class^='styles_header_settings_']").click()""")

        # Enable all cards
        self.browser.execute_script("""document.querySelector("[class^='filters_settings_button_']").click()""")
        all_cards_enabled = self.browser.execute_script("""return document.getElementById("allAtOnceCheckbox").checked;""")
        if not all_cards_enabled:
            self.browser.execute_script("""document.getElementById("allAtOnceCheckbox").click()""")
        self.browser.execute_script("""document.querySelector("[class^='filters_confirm_button_']").click()""")


    def reset_browser_position(self):
        self.check_browser()
        if self.browser:
            game_rect, _ = self.threader.windowmover.window.get_rect()
            workspace_rect = self.threader.windowmover.window.get_workspace_rect()
            left_side = abs(workspace_rect[0] - game_rect[0])
            right_side = abs(game_rect[2] - workspace_rect[2])
            if left_side > right_side:
                left_x = workspace_rect[0] - 5
                width = left_side
            else:
                left_x = game_rect[2] + 5
                width = right_side
            self.browser.set_window_rect(left_x, workspace_rect[1], width, workspace_rect[3] - workspace_rect[1] + 6)


    def close_browser(self):
        if self.browser:
            self.last_browser_rect = self.browser.get_window_rect()
            self.save_last_browser_rect()
            self.browser.close()
            self.browser = None
            self.previous_element = None
        return


    def save_last_browser_rect(self):
        if self.last_browser_rect:
            if (self.last_browser_rect['x'] == -32000 and self.last_browser_rect['y'] == -32000):
                logger.warning(f"Browser minimized, cannot save position: {self.last_browser_rect}")
                self.last_browser_rect = None
                return
            self.threader.settings.set("browser_position", [self.last_browser_rect['x'], self.last_browser_rect['y'], self.last_browser_rect['width'], self.last_browser_rect['height']])
            self.last_browser_rect = None


    def handle_response(self, message):
        data = self.load_response(message)
        # logger.info(json.dumps(data))
        # self.to_json(data)

        try:
            if 'data' not in data:
                # logger.info("This packet doesn't have data :)")
                return

            data = data['data']

            # Run ended
            if 'single_mode_factor_select_common' in data:
                self.close_browser()
                return

            # Concert Theater
            if "live_theater_save_info_array" in data:
                if self.screen_state_handler:
                    new_state = ScreenState()
                    new_state.location = Location.THEATER
                    new_state.main = "Concert Theater"
                    new_state.sub = "Vibing"

                    self.screen_state_handler.carrotjuicer_state = new_state

            # Gametora
            if 'chara_info' in data:
                logger.debug("chara_info in data")

                # Training info
                outfit_id = data['chara_info']['card_id']
                chara_id = int(str(outfit_id)[:-2])
                supports = [card_data['support_card_id'] for card_data in data['chara_info']['support_card_array']]
                scenario_id = data['chara_info']['scenario_id']

                # Training stats
                if self.screen_state_handler:
                    new_state = ScreenState()

                    new_state.location = Location.TRAINING

                    new_state.main = f"Training - {util.turn_to_string(data['chara_info']['turn'])}"
                    new_state.sub = f"{data['chara_info']['speed']} {data['chara_info']['stamina']} {data['chara_info']['power']} {data['chara_info']['guts']} {data['chara_info']['wiz']} | {data['chara_info']['skill_point']}"

                    scenario_id = data['chara_info']['scenario_id']
                    scenario_name = SCENARIO_DICT.get(scenario_id, None)
                    if not scenario_name:
                        logger.error(f"Scenario ID not found in scenario dict: {scenario_id}")
                        scenario_name = "You are now breathing manually."
                    new_state.set_chara(chara_id, scenario_name)

                    self.screen_state_handler.carrotjuicer_state = new_state

                if not self.browser or not self.browser.current_url.startswith("https://gametora.com/umamusume/training-event-helper"):
                    logger.info("GT tab not open, opening tab")
                    self.open_helper(self.create_gametora_helper_url(outfit_id, scenario_id, supports))

            if 'unchecked_event_array' in data and data['unchecked_event_array']:
                # Training event.
                logger.debug("Training event detected")
                event_data = data['unchecked_event_array'][0]
                # TODO: Check if there can be multiple events??
                if len(data['unchecked_event_array']) > 1:
                    logger.warning(f"Packet has more than 1 unchecked event! {message}")

                self.browser.execute_script(
                    """
                    document.querySelectorAll("[class^='compatibility_viewer_item_'][aria-expanded=true]").forEach(e => e.click());
                    """
                )

                if len(event_data['event_contents_info']['choice_array']) > 1:

                    event_title = mdb.get_event_title(event_data['story_id'])

                    logger.debug(f"Event title determined: {event_title}")

                    # Event has choices

                    # If character is the trained character
                    if event_data['event_contents_info']['support_card_id'] and event_data['event_contents_info']['support_card_id'] not in supports:
                        # Random support card event
                        logger.debug("Random support card detected")
                        self.browser.execute_script("""document.getElementById("boxSupportExtra").click();""")
                        self.browser.execute_script(
                            """
                            document.getElementById(arguments[0].toString()).click();
                            """,
                            event_data['event_contents_info']['support_card_id']
                        )
                    else:
                        logger.debug("Trained character or support card detected")

                    # Activate and scroll to the outcome.
                    self.previous_element = self.browser.execute_script(
                        """a = document.querySelectorAll("[class^='compatibility_viewer_item_']");
                        var ele = null;
                        for (var i = 0; i < a.length; i++) {
                        console.log(i)
                        item = a[i];
                        if (item.textContent.includes(arguments[0])) {
                            item.click();
                            ele = item;
                            break;
                        }
                        }
                        return ele;
                        """,
                        event_title
                    )
                    if not self.previous_element:
                        logger.debug("Could not find event on GT page.")
                    self.browser.execute_script("""
                        if (arguments[0]) {
                            // document.querySelector(".tippy-box").scrollIntoView({behavior:"smooth", block:"center"});
                            // arguments[0].scrollIntoView({behavior:"smooth", block:"end"});
                            window.scrollBy({top: arguments[0].getBoundingClientRect().bottom - window.innerHeight + 32, left: 0, behavior: 'smooth'});
                        }
                        """,
                        self.previous_element
                    )
        except Exception:
            logger.error("ERROR IN HANDLING RESPONSE MSGPACK")
            logger.error(data)
            logger.error(traceback.format_exc())
            util.show_alert_box("UmaLauncher: Error in response msgpack.", "This should not happen. You may contact the developer about this issue.")
            self.close_browser()

    def check_browser(self):
        if self.browser:
            try:
                self.browser.current_url
                return
            except WebDriverException:
                self.browser = None
                self.previous_element = None
        return


    def handle_request(self, message):
        data = self.load_request(message)
        # logger.info(json.dumps(data))
        try:
            # Watching a concert
            if "live_theater_save_info" in data:
                logger.debug("Starting concert")
                new_state = ScreenState()
                new_state.location = Location.THEATER
                new_state.set_music(data['live_theater_save_info']['music_id'])
                self.screen_state_handler.carrotjuicer_state = new_state

            if 'start_chara' in data:
                # Packet is a request to start a training
                logger.debug("Start of training detected")
                self.open_helper(self.create_gametora_helper_url_from_start(data))
        except Exception:
            logger.error("ERROR IN HANDLING REQUEST MSGPACK")
            logger.error(data)
            logger.error(traceback.format_exc())
            util.show_alert_box("UmaLauncher: Error in request msgpack.", "This should not happen. You may contact the developer about this issue.")
            self.close_browser()


    def process_message(self, message: str):
        self.check_browser()

        try:
            message_time = int(str(os.path.basename(message))[:-9])
        except ValueError:
            return
        if message_time < self.start_time:
            # Delete old msgpack files.
            os.remove(message)
            return

        # logger.info(f"New Packet: {os.path.basename(message)}")

        if message.endswith("R.msgpack"):
            # Response
            self.handle_response(message)

        else:
            # Request
            self.handle_request(message)

        os.remove(message)
        return


    def get_msgpack_batch(self, msg_path):
        return sorted(glob.glob(os.path.join(msg_path, "*.msgpack")), key=os.path.getmtime)


    def run(self):
        if not self.threader.settings.get_tray_setting("Automatic training event helper"):
            return

        msg_path = self.threader.settings.get("game_install_path")

        if not msg_path:
            logger.error("Packet intercept enabled but no carrotjuicer path found")
            util.show_alert_box("UmaLauncher: No game install path found.", "This should not happen. Please add the game install path to umasettings.json")
            return

        msg_path = os.path.join(msg_path, "CarrotJuicer")

        try:
            while not self.should_stop:
                time.sleep(0.25)

                if self.reset_browser:
                    self.reset_browser = False
                    self.reset_browser_position()

                self.check_browser()
                if self.browser:
                    self.last_browser_rect = self.browser.get_window_rect()
                elif self.last_browser_rect:
                    self.save_last_browser_rect()

                messages = self.get_msgpack_batch(msg_path)
                for message in messages:
                    self.process_message(message)
        except NoSuchWindowException:
            pass

        if self.browser:
            self.last_browser_rect = self.browser.get_window_rect()
            self.browser.quit()
        self.save_last_browser_rect()
        return


    def stop(self):
        self.should_stop = True
