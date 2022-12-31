import os
import msgpack
import numpy as np
import time
from loguru import logger
import glob
import traceback
import time
import math
import json
import sqlite3
from selenium.common.exceptions import WebDriverException
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from subprocess import CREATE_NO_WINDOW
from screenstate import ScreenState, Location

class CarrotJuicer():
    start_time = None
    browser = None
    previous_element = None
    threader = None
    screen_state_handler = None
    should_stop = False

    def __init__(self, threader, screen_state_handler):
        self.threader = threader
        self.screen_state_handler = screen_state_handler
        self.start_time = math.floor(time.time() * 1000)

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


    def open_helper(self, helper_url):
        self.previous_element = None

        if self.browser:
            self.close_browser()

        firefox_service = FirefoxService()
        firefox_service.creation_flags = CREATE_NO_WINDOW
        profile = webdriver.FirefoxProfile("./ff_profile")
        options = webdriver.FirefoxOptions()
        self.browser = webdriver.Firefox(service=firefox_service, firefox_profile=profile, options=options)

        self.browser.get(helper_url)
        # TODO: Find a way to know if the page is actually finished loading

        while not self.browser.execute_script("""return document.querySelector("[class^='legal_cookie_banner_wrapper_']")"""):
            time.sleep(0.1)

        # Hide the cookies banner
        self.browser.execute_script("""document.querySelector("[class^='legal_cookie_banner_wrapper_']").style.display = 'none';""")

        # Enable dark mode (the only reasonable color scheme)
        self.browser.execute_script("""document.querySelector("[class^='styles_header_settings_']").click()""")
        while not self.browser.execute_script("""return document.querySelector("[class^='filters_toggle_button_']");"""):
            time.sleep(0.2)
        dark_enabled = self.browser.execute_script("""document.querySelector("[class^='filters_toggle_button_']").childNodes[0].querySelector("input").checked;""")
        if not dark_enabled:
            self.browser.execute_script("""document.querySelector("[class^='filters_toggle_button_']").childNodes[0].querySelector("input").click()""")
        self.browser.execute_script("""document.querySelector("[class^='styles_header_settings_']").click()""")

        # Enable all cards
        self.browser.execute_script("""document.querySelector("[class^='filters_settings_button_']").click()""")
        all_cards_enabled = self.browser.execute_script("""document.getElementById("allAtOnceCheckbox").checked;""")
        if not all_cards_enabled:
            self.browser.execute_script("""document.getElementById("allAtOnceCheckbox").click()""")
        self.browser.execute_script("""document.querySelector("[class^='filters_confirm_button_']").click()""")


    def close_browser(self):
        if self.browser:
            self.browser.close()
            self.browser = None
            self.previous_element = None
        return


    def handle_response(self, message):
        data = self.load_response(message)
        # logger.info(json.dumps(data))

        try:
            if 'data' not in data:
                logger.info("This packet doesn't have data :)")
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
                logger.info("chara_info in data")

                # Training info
                outfit_id = data['chara_info']['card_id']
                chara_id = int(str(outfit_id)[:-2])
                supports = [card_data['support_card_id'] for card_data in data['chara_info']['support_card_array']]
                scenario_id = data['chara_info']['scenario_id']

                # Training stats
                if self.screen_state_handler:
                    new_state = ScreenState()

                    new_state.location = Location.TRAINING

                    new_state.main = "Training"
                    new_state.sub = f"{data['chara_info']['speed']} {data['chara_info']['stamina']} {data['chara_info']['power']} {data['chara_info']['guts']} {data['chara_info']['wiz']} | {data['chara_info']['skill_point']}"

                    new_state.set_chara(chara_id)

                    self.screen_state_handler.carrotjuicer_state = new_state

                if not self.browser or not self.browser.current_url.startswith("https://gametora.com/umamusume/training-event-helper"):
                    logger.info("GT tab not open, opening tab")
                    self.open_helper(self.create_gametora_helper_url(outfit_id, scenario_id, supports))
            
            if 'unchecked_event_array' in data and data['unchecked_event_array']:
                # Training event.
                logger.info("Training event detected")
                event_data = data['unchecked_event_array'][0]
                # TODO: Check if there can be multiple events??
                if len(data['unchecked_event_array']) > 1:
                    logger.warning(f"Packet has more than 1 unchecked event! {message}")

                if len(event_data['event_contents_info']['choice_array']) > 1:

                    self.browser.execute_script(
                        """
                        document.querySelectorAll("[class^='compatibility_viewer_item_'][aria-expanded=true]").forEach(e => e.click());
                        """
                    )

                    conn = sqlite3.connect(os.path.expandvars("%userprofile%\\appdata\\locallow\\Cygames\\umamusume\\master\\master.mdb"))
                    cursor = conn.cursor()
                    cursor.execute(
                        """SELECT text FROM text_data t JOIN single_mode_story_data s ON t."index" = s.story_id WHERE category = 181 AND t."index" = ? OR s.short_story_id = ? LIMIT 1""",
                        (event_data['story_id'], event_data['story_id'])
                    )
                    event_title = cursor.fetchone()[0]

                    conn.close()
                    logger.info(f"Event title determined: {event_title}")

                    # Event has choices
                    
                    # If character is the trained character
                    if event_data['event_contents_info']['support_card_id'] and event_data['event_contents_info']['support_card_id'] not in supports:
                        # Random support card event
                        logger.info("Random support card detected")
                        self.browser.execute_script("""document.getElementById("boxSupportExtra").click();""")
                        self.browser.execute_script(
                            """
                            document.getElementById(arguments[0].toString()).click();
                            """,
                            event_data['event_contents_info']['support_card_id']
                        )
                    else:
                        logger.info("Trained character or support card detected")

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
                        logger.info("Could not find event on GT page.")
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
                logger.info("Starting concert")
                new_state = ScreenState()
                new_state.location = Location.THEATER
                new_state.set_music(data['live_theater_save_info']['music_id'])
                new_state.main = "Watching a concert"
                new_state.sub = "Vibing"
                self.screen_state_handler.carrotjuicer_state = new_state

            if 'start_chara' in data:
                # Packet is a request to start a training
                logger.info("Start of training detected")
                self.open_helper(self.create_gametora_helper_url_from_start(data))
        except Exception:
            logger.error("ERROR IN HANDLING REQUEST MSGPACK")
            logger.error(data)
            logger.error(traceback.format_exc())
            self.close_browser()


    def process_message(self, message: str):
        self.check_browser()

        try:
            message_time = int(str(os.path.basename(message))[:-9])
        except ValueError:
            return
        if message_time < self.start_time:
            return

        logger.info(f"New Packet: {os.path.basename(message)}")

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
        if not self.threader.settings.get_tray_setting("Intercept packets"):
            return

        msg_path = self.threader.settings.get("game_install_path")

        if not msg_path:
            logger.error("Packet intercept enabled but no carrotjuicer path found")
            return

        msg_path = os.path.join(msg_path, "CarrotJuicer")

        while not self.should_stop:
            time.sleep(0.25)

            messages = self.get_msgpack_batch(msg_path)
            for message in messages:
                self.process_message(message)

        if self.browser:
            self.browser.close()
        return


    def stop(self):
        self.should_stop = True
