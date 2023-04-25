import os
import time
import glob
import traceback
import math
import json
from subprocess import CREATE_NO_WINDOW
import msgpack
from loguru import logger
from selenium.common.exceptions import WebDriverException
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.common.exceptions import NoSuchWindowException
from screenstate import ScreenState, Location
import util
import constants
import mdb
import helper_table
import training_tracker

class CarrotJuicer():
    start_time = None
    browser = None
    previous_element = None
    threader = None
    screen_state_handler = None
    helper_table = None
    should_stop = False
    last_browser_rect = None
    reset_browser = False
    helper_url = None
    last_training_id = None
    training_tracker = None
    previous_request = None
    last_helper_data = None
    previous_race_program_id = None

    _browser_list = None

    def __init__(self, threader):
        self.threader = threader

        self._browser_list = {
            'Chrome': self.chrome_setup,
            'Firefox': self.firefox_setup,
            'Edge': self.edge_setup,
        }

        self.screen_state_handler = threader.screenstate
        self.restart_time()

        self.helper_table = helper_table.HelperTable(self)

        # Remove existing geckodriver.log
        if os.path.exists("geckodriver.log"):
            try:
                os.remove("geckodriver.log")
            except PermissionError:
                logger.warning("Could not delete geckodriver.log because it is already in use!")
                return


    def restart_time(self):
        self.start_time = math.floor(time.time() * 1000)


    def load_request(self, msg_path):
        try:
            with open(msg_path, "rb") as in_file:
                unpacked = msgpack.unpackb(in_file.read()[170:], strict_map_key=False)
                # Remove keys that are not needed
                for key in constants.REQUEST_KEYS_TO_BE_REMOVED:
                    if key in unpacked:
                        del unpacked[key]
                return unpacked
        except PermissionError:
            logger.warning("Could not load request because it is already in use!")
            time.sleep(0.1)
            return self.load_request(msg_path)


    def load_response(self, msg_path):
        try:
            with open(msg_path, "rb") as in_file:
                return msgpack.unpackb(in_file.read(), strict_map_key=False)
        except PermissionError:
            logger.warning("Could not load response because it is already in use!")
            time.sleep(0.1)
            return self.load_response(msg_path)


    def create_gametora_helper_url_from_start(self, packet_data):
        if 'start_chara' not in packet_data:
            return None
        d = packet_data['start_chara']
        supports = d['support_card_ids'] + [d['friend_support_card_info']['support_card_id']]

        return util.create_gametora_helper_url(d['card_id'], d['scenario_id'], supports)


    def to_json(self, packet, out_name="packet.json"):
        with open(out_name, 'w', encoding='utf-8') as f:
            f.write(json.dumps(packet, indent=4, ensure_ascii=False))

    # def to_python_dict_file(self, packet, out_name="packet.py"):
    #     with open(out_name, 'w', encoding='utf-8') as f:
    #         f.write("packet = " + str(packet))

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
        options.add_argument("--remote-debugging-port=9222")
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

    def init_browser(self):
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
                driver = browser_setup(self.helper_url)
                break
            except Exception:
                logger.error("Failed to start browser")
                logger.error(traceback.format_exc())
        if not driver:
            util.show_warning_box("Uma Launcher: Unable to start browser.", "Selected webbrowser cannot be started. Use the tray icon to select a browser that is installed on your system.")
        return driver
    
    def setup_helper_page(self):
        self.browser.execute_script("""
        if (window.UL_OVERLAY) {
            window.UL_OVERLAY.remove();
        }
        window.UL_OVERLAY = document.createElement("div");
        window.GT_PAGE = document.getElementById("__next");
        window.OVERLAY_HEIGHT = "15rem";
        window.UL_OVERLAY.style.height = "max_content";
        window.UL_OVERLAY.style.width = "100%";
        window.UL_OVERLAY.style.padding = "0.5rem 0";
        window.UL_OVERLAY.style.position = "fixed";
        window.UL_OVERLAY.style.bottom = "100%";
        window.UL_OVERLAY.style.zIndex = 100;
        window.UL_OVERLAY.style.backgroundColor = "var(--c-bg-main)";
        window.UL_OVERLAY.style.borderBottom = "2px solid var(--c-topnav)";

        var ul_data = document.createElement("div");
        ul_data.id = "ul-data";
        window.UL_OVERLAY.appendChild(ul_data);

        window.UL_OVERLAY.ul_data = ul_data;

        ul_data.style.display = "flex";
        ul_data.style.alignItems = "center";
        ul_data.style.justifyContent = "center";
        ul_data.style.flexDirection = "column";
        ul_data.style.gap = "0.5rem";
        ul_data.style.fontSize = "0.9rem";

        var ul_dropdown = document.createElement("div");
        ul_dropdown.id = "ul-dropdown";
        ul_dropdown.style = "position: fixed;right: 0;top: 0;width: 3rem;height: 1.6rem;background-color: var(--c-bg-main);text-align: center;z-index: 101;line-height: 1.5rem;border-left: 2px solid var(--c-topnav);border-bottom: 2px solid var(--c-topnav);border-bottom-left-radius: 0.5rem;cursor: pointer;";
        ul_dropdown.textContent = "⯅";
        window.UL_OVERLAY.appendChild(ul_dropdown);

        window.hide_overlay = function() {
            window.UL_DATA.expanded = false;
            document.getElementById("ul-dropdown").textContent = "⯆";
            document.getElementById("ul-dropdown").style.top = "-2px";
            window.GT_PAGE.style.paddingTop = "0";
            window.UL_OVERLAY.style.bottom = "100%";
        }

        window.expand_overlay = function() {
            window.UL_DATA.expanded = true;

            var height = window.UL_OVERLAY.offsetHeight;
            console.log(height)
            window.OVERLAY_HEIGHT = height + "px";

            document.getElementById("ul-dropdown").textContent = "⯅";
            document.getElementById("ul-dropdown").style.top = "calc(" + window.OVERLAY_HEIGHT + " - 2px)";
            window.GT_PAGE.style.paddingTop = window.OVERLAY_HEIGHT;
            window.UL_OVERLAY.style.bottom = "calc(100% - " + window.OVERLAY_HEIGHT + ")";
        }

        ul_dropdown.addEventListener("click", function() {
            if (window.UL_DATA.expanded) {
                window.hide_overlay();
            } else {
                window.expand_overlay();
            }
        });

        window.UL_DATA = {
            energy: 100,
            max_energy: 100,
            table: "",
            expanded: true
        };

        document.body.prepend(window.UL_OVERLAY);

        window.UL_OVERLAY.querySelector("#ul-dropdown").style.transition = "top 0.5s";
        window.UL_OVERLAY.style.transition = "bottom 0.5s";
        window.GT_PAGE.style.transition = "padding-top 0.5s";

        window.update_overlay = function() {
            window.UL_OVERLAY.ul_data.replaceChildren();
            window.UL_OVERLAY.ul_data.insertAdjacentHTML("afterbegin", window.UL_DATA.overlay_html)
            //window.UL_OVERLAY.ul_data.innerHTML = window.UL_DATA.overlay_html;

            if (window.UL_DATA.expanded) {
                window.expand_overlay();
                //setTimeout(window.expand_overlay, 100);
            }
        };
        """)

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

        while not self.browser.execute_script("""return document.getElementById("adnote");"""):
            time.sleep(0.25)

        # Hide the cookies banner
        self.browser.execute_script("""document.getElementById("adnote").style.display = 'none';""")
        return

    def open_helper(self):
        self.previous_element = None

        if self.browser:
            self.close_browser()

        self.browser = self.init_browser()

        saved_pos = self.threader.settings.get("browser_position")
        if not saved_pos:
            self.reset_browser_position()
        else:
            logger.debug(saved_pos)
            self.browser.set_window_rect(*saved_pos)

        # TODO: Find a way to know if the page is actually finished loading

        self.setup_helper_page()


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

    def end_training(self):
        if self.training_tracker:
            self.training_tracker = None
        self.close_browser()
        return
    
    def add_response_to_tracker(self, data):
        should_track = self.threader.settings.get_tray_setting("Track trainings")
        if self.previous_request:
            if should_track:
                self.training_tracker.add_request(self.previous_request)
            self.previous_request = None
        if should_track:
            self.training_tracker.add_response(data)


    EVENT_ID_TO_POS_STRING = {
        7005: '(1st)',
        7006: '(2nd-5th)',
        7007: '(6th or worse)'
    }

    def get_after_race_event_title(self, event_id):
        if not self.previous_race_program_id:
            return "PREVIOUS RACE UNKNOWN"

        race_grade = mdb.get_program_id_grade(self.previous_race_program_id)

        if not race_grade:
            logger.error(f"Race grade not found for program id {self.previous_race_program_id}")
            return "RACE GRADE NOT FOUND"

        grade_text = ""
        if race_grade > 300:
            grade_text = "OP/Pre-OP"
        elif race_grade > 100:
            grade_text = "G2/G3"
        else:
            grade_text = "G1"

        return f"{grade_text} {self.EVENT_ID_TO_POS_STRING[event_id]}"

    def handle_response(self, message):
        data = self.load_response(message)

        if self.threader.settings.loaded_settings.get("save_packet", False):
            logger.debug("Response:")
            logger.debug(json.dumps(data))
            self.to_json(data, "packet_in.json")

        try:
            if 'data' not in data:
                # logger.info("This packet doesn't have data :)")
                return

            data = data['data']

            # Close whatever popup is open
            if self.browser:
                self.browser.execute_script(
                    """
                    document.querySelectorAll("[class^='compatibility_viewer_item_'][aria-expanded=true]").forEach(e => e.click());
                    """
                )

            # Run ended
            if 'single_mode_factor_select_common' in data:
                self.end_training()
                return

            # Concert Theater
            if "live_theater_save_info_array" in data:
                if self.screen_state_handler:
                    new_state = ScreenState(self.threader.screenstate)
                    new_state.location = Location.THEATER
                    new_state.main = "Concert Theater"
                    new_state.sub = "Vibing"

                    self.screen_state_handler.carrotjuicer_state = new_state
                return
            
            # Race starts.
            if 'race_scenario' in data and 'race_start_info' in data and data['race_scenario']:
                self.previous_race_program_id = data['race_start_info']['program_id']
                # Currently starting a race. Add packet to training tracker.
                logger.debug("Race packet received.")
                self.add_response_to_tracker(data)
                return


            # Update history
            if 'race_history' in data and data['race_history']:
                self.previous_race_program_id = data['race_history'][-1]['program_id']


            # Gametora
            if 'chara_info' in data:
                # Inside training run.

                training_id = data['chara_info']['start_time']
                if not self.training_tracker or not self.training_tracker.training_id_matches(training_id):
                    self.training_tracker = training_tracker.TrainingTracker(training_id, data['chara_info']['card_id'])

                # Add request to tracker
                self.add_response_to_tracker(data)

                # Training info
                outfit_id = data['chara_info']['card_id']
                chara_id = int(str(outfit_id)[:-2])
                supports = [card_data['support_card_id'] for card_data in data['chara_info']['support_card_array']]
                scenario_id = data['chara_info']['scenario_id']

                # Training stats
                if self.screen_state_handler:
                    new_state = ScreenState(self.threader.screenstate)

                    new_state.location = Location.TRAINING

                    new_state.main = f"Training - {util.turn_to_string(data['chara_info']['turn'])}"
                    new_state.sub = f"{data['chara_info']['speed']} {data['chara_info']['stamina']} {data['chara_info']['power']} {data['chara_info']['guts']} {data['chara_info']['wiz']} | {data['chara_info']['skill_point']}"

                    scenario_id = data['chara_info']['scenario_id']
                    scenario_name = constants.SCENARIO_DICT.get(scenario_id, None)
                    if not scenario_name:
                        logger.error(f"Scenario ID not found in scenario dict: {scenario_id}")
                        scenario_name = "You are now breathing manually."
                    new_state.set_chara(chara_id, outfit_id=outfit_id, small_text=scenario_name)

                    self.screen_state_handler.carrotjuicer_state = new_state

                if not self.browser or not self.browser.current_url.startswith("https://gametora.com/umamusume/training-event-helper"):
                    logger.info("GT tab not open, opening tab")
                    self.helper_url = util.create_gametora_helper_url(outfit_id, scenario_id, supports)
                    logger.debug(f"Helper URL: {self.helper_url}")
                    self.open_helper()
                
                self.last_helper_data = data
                self.update_helper_table(data)

            if 'unchecked_event_array' in data and data['unchecked_event_array']:
                # Training event.
                logger.debug("Training event detected")
                event_data = data['unchecked_event_array'][0]
                event_title = mdb.get_event_title(event_data['story_id'])
                logger.debug(f"Event title: {event_title}")
                # TODO: Check if there can be multiple events??
                if len(data['unchecked_event_array']) > 1:
                    logger.warning(f"Packet has more than 1 unchecked event! {message}")

                if len(event_data['event_contents_info']['choice_array']) > 1:

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

                    # Check for after-race event.
                    if event_data['event_id'] in (7005, 7006, 7007):
                        logger.debug("After-race event detected.")
                        event_title = self.get_after_race_event_title(event_data['event_id'])

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
                        logger.debug(f"Could not find event on GT page: {event_title} {event_data['story_id']}")
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
            util.show_warning_box("Uma Launcher: Error in response msgpack.", "This should not happen. You may contact the developer about this issue.")
            # self.close_browser()

    def check_browser(self):
        if self.browser:
            try:
                if self.browser.current_url.startswith("https://gametora.com/umamusume/training-event-helper"):
                    if not self.browser.execute_script("return window.UL_OVERLAY;"):
                        self.browser.get(self.helper_url)
                        self.setup_helper_page()
            except WebDriverException:
                self.browser.quit()
                self.browser = None
                self.previous_element = None
        return

    def start_concert(self, music_id):
        logger.debug("Starting concert")
        new_state = ScreenState(self.threader.screenstate)
        new_state.location = Location.THEATER
        new_state.set_music(music_id)
        self.screen_state_handler.carrotjuicer_state = new_state
        return

    def handle_request(self, message):
        data = self.load_request(message)

        if self.threader.settings.loaded_settings.get("save_packet", False):
            logger.debug("Request:")
            logger.debug(json.dumps(data))
            self.to_json(data, "packet_out.json")

        self.previous_request = data

        try:
            if 'is_force_delete' in data:
                # Packet is a request to delete a training
                self.end_training()
                return

            # Watching a concert
            if "live_theater_save_info" in data:
                self.start_concert(data['live_theater_save_info']['music_id'])
                return

            if "music_id" in data:
                self.start_concert(data['music_id'])
                return

            if 'start_chara' in data:
                # Packet is a request to start a training
                logger.debug("Start of training detected")
                self.helper_url = self.create_gametora_helper_url_from_start(data)
                logger.debug(f"Helper URL: {self.helper_url}")
                self.open_helper()
                return

        except Exception:
            logger.error("ERROR IN HANDLING REQUEST MSGPACK")
            logger.error(data)
            logger.error(traceback.format_exc())
            util.show_warning_box("Uma Launcher: Error in request msgpack.", "This should not happen. You may contact the developer about this issue.")
            # self.close_browser()


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


    def update_helper_table(self, data):
        helper_table = self.helper_table.create_helper_elements(data)
        if helper_table:
            self.browser.execute_script("""
                window.UL_DATA.overlay_html = arguments[0];
                window.update_overlay();
                """,
                helper_table
            )


    def run(self):
        msg_path = self.threader.settings.get("game_install_path")

        if not msg_path:
            logger.error("Packet intercept enabled but no carrotjuicer path found")
            util.show_error_box("Uma Launcher: No game install path found.", "This should not happen. Please add the game install path to umasettings.json")
            return

        msg_path = os.path.join(msg_path, "CarrotJuicer")

        try:
            while not self.should_stop:
                time.sleep(0.25)

                self.check_browser()

                if not self.threader.settings.get_tray_setting("Enable CarrotJuicer"):
                    continue

                if self.reset_browser:
                    self.reset_browser = False
                    self.reset_browser_position()

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
            try:
                self.last_browser_rect = self.browser.get_window_rect()
                self.browser.quit()
            except: pass

        self.save_last_browser_rect()
        return


    def stop(self):
        self.should_stop = True
