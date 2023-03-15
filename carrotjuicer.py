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

# TODO: Track amount of trainings on every facility to know when it upgrades next.

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
    helper_url = None

    _browser_list = None

    def __init__(self, threader):
        self.threader = threader

        self._browser_list = {
            'Firefox': self.firefox_setup,
            'Chrome': self.chrome_setup,
            'Edge': self.edge_setup,
        }

        self.screen_state_handler = threader.screenstate
        self.restart_time()

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


    def to_json(self, packet, out_name="packet.json"):
        with open(out_name, 'w', encoding='utf-8') as f:
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
                pass
        if not driver:
            util.show_alert_box("UmaLauncher: Unable to start browser.", "Selected webbrowser cannot be started. Use the tray icon to select a browser that is installed on your system.")
        return driver
    
    def setup_helper_page(self):
        self.browser.execute_script("""
        window.UL_OVERLAY = document.createElement("div");
        window.GT_PAGE = document.getElementById("__next");
        window.OVERLAY_HEIGHT = "15rem";
        window.UL_OVERLAY.style.height = OVERLAY_HEIGHT;
        window.UL_OVERLAY.style.width = "100%";
        window.UL_OVERLAY.style.position = "fixed";
        window.UL_OVERLAY.style.top = "0";
        window.UL_OVERLAY.style.zIndex = 100;
        window.UL_OVERLAY.style.backgroundColor = "var(--c-bg-main)";
        window.UL_OVERLAY.style.borderBottom = "2px solid var(--c-topnav)";
        window.UL_OVERLAY.style.display = "flex";
        window.UL_OVERLAY.style.alignItems = "center";
        window.UL_OVERLAY.style.justifyContent = "center";
        window.UL_OVERLAY.style.flexDirection = "column";

        window.UL_OVERLAY.innerHTML = `
            <div>Energy: <span id="energy"></span></div>
            <table id="training-table">
                <thead>
                    <tr>
                        <th>Facility</th>
                        <th>Speed</th>
                        <th>Stamina</th>
                        <th>Power</th>
                        <th>Guts</th>
                        <th>Wisdom</th>
                    </tr>
                </thead>
                <tbody></tbody>
            </table>
        `;

        window.UL_DATA = {
            energy: 100,
            max_energy: 100,
            training: {}
        };

        document.body.prepend(window.UL_OVERLAY);
        window.GT_PAGE.style.paddingTop = OVERLAY_HEIGHT;

        window.update_overlay = function() {
            var training_metadata_array = [
                {name: "Speed", command_id: 101},
                {name: "Stamina", command_id: 105},
                {name: "Power", command_id: 102},
                {name: "Guts", command_id: 103},
                {name: "Wisdom", command_id: 106}
            ];

            var row_meatdata_array = [
                {name: "Stat Gain", key: "stats"},
                {name: "Energy", key: "energy"},
                {name: "Useful Bond", key: "bond"},
                {name: "Skillpt Gain", key: "skillpt"},
                {name: "Fail %", key: "failure_rate"},
                {name: "Level", key: "level"}
            ];

            document.getElementById("energy").innerText = window.UL_DATA.energy + "/" + window.UL_DATA.max_energy;
            var tbody = document.getElementById("training-table").querySelector("tbody");
            tbody.innerHTML = "";
            for (var i = 0; i < row_meatdata_array.length; i++) {
                var tr = document.createElement("tr");
                var row_metadata = row_meatdata_array[i];
                for (var j = 0; j < training_metadata_array.length + 1; j++) {
                    var td = document.createElement("td");
                    if (j == 0){
                        td.innerText = row_metadata.name;
                    } else {
                        var training_metadata = training_metadata_array[j - 1];
                        td.innerText = window.UL_DATA.training[training_metadata.command_id][row_metadata.key];
                    }
                    tr.appendChild(td);
                }
                tbody.appendChild(tr);
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


    def handle_response(self, message):
        data = self.load_response(message)
        # logger.info(json.dumps(data))
        if self.threader.settings.get("save_packet"):
            self.to_json(data, "packet_in.json")

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
                    new_state = ScreenState(self.threader.screenstate)
                    new_state.location = Location.THEATER
                    new_state.main = "Concert Theater"
                    new_state.sub = "Vibing"

                    self.screen_state_handler.carrotjuicer_state = new_state
                return

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
                    new_state = ScreenState(self.threader.screenstate)

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
                    self.helper_url = self.create_gametora_helper_url(outfit_id, scenario_id, supports)
                    self.open_helper()
                
                # Update browser variables
                # First generate the evaluation dict
                if 'home_info' in data:
                    eval_dict = {eval_data['training_partner_id']: eval_data['evaluation'] for eval_data in data['chara_info']['evaluation_info_array']}

                    cur_training = {}

                    all_commands = {}
                    
                    # Default commands
                    for command in data['home_info']['command_info_array']:
                        all_commands[command['command_id']] = command
                    
                    # Grand Masters specific commands
                    if 'venus_data_set' in data:
                        for command in data['venus_data_set']['command_info_array']:
                            all_commands[command['command_id']]['params_inc_dec_info_array'] += command['params_inc_dec_info_array']

                    for command in all_commands.values():
                        level = command['level']
                        failure_rate = command['failure_rate']
                        stats = 0
                        skillpt = 0
                        bond = 0
                        energy = 0

                        for param in command['params_inc_dec_info_array']:
                            if param['target_type'] < 6:
                                stats += param['value']
                            elif param['target_type'] == 30:
                                skillpt += param['value']
                            elif param['target_type'] == 10:
                                energy += param['value']
                            

                        for training_partner_id in command['training_partner_array']:
                            # Akikawa is 102
                            if training_partner_id <= 6 or training_partner_id == 102:
                                if not training_partner_id in eval_dict:
                                    logger.error(f"Training partner ID not found in eval dict: {training_partner_id}")
                                    continue
                                cur_bond = eval_dict[training_partner_id]
                                if cur_bond < 80:
                                    new_bond = cur_bond + 7
                                    new_bond = min(new_bond, 80)
                                    effective_bond = new_bond - cur_bond
                                    bond += effective_bond

                        for tips_partner_id in command['tips_event_partner_array']:
                            if tips_partner_id <= 6:
                                if not tips_partner_id in eval_dict:
                                    logger.error(f"Training partner ID not found in eval dict: {tips_partner_id}")
                                    continue
                                cur_bond = eval_dict[tips_partner_id]
                                if cur_bond < 80:
                                    new_bond = cur_bond + 5
                                    new_bond = min(new_bond, 80)
                                    effective_bond = new_bond - cur_bond
                                    bond += effective_bond

                        cur_training[command['command_id']] = {
                            'level': level,
                            'failure_rate': failure_rate,
                            'stats': stats,
                            'skillpt': skillpt,
                            'bond': bond,
                            'energy': energy
                        }
                    
                    self.browser.execute_script("""
                        var energy_data = arguments[0];
                        window.UL_DATA.energy = energy_data[0];
                        window.UL_DATA.max_energy = energy_data[1];
                        var cur_training = arguments[1];
                        window.UL_DATA.training = cur_training;
                        window.update_overlay();
                        """, [data['chara_info']['vital'], data['chara_info']['max_vital']], cur_training)

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
        # logger.info(json.dumps(data))

        if self.threader.settings.get("save_packet"):
            self.to_json(data, "packet_out.json")

        try:
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
                self.open_helper()
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
        msg_path = self.threader.settings.get("game_install_path")

        if not msg_path:
            logger.error("Packet intercept enabled but no carrotjuicer path found")
            util.show_alert_box("UmaLauncher: No game install path found.", "This should not happen. Please add the game install path to umasettings.json")
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
            self.last_browser_rect = self.browser.get_window_rect()
            self.browser.quit()
        self.save_last_browser_rect()
        return


    def stop(self):
        self.should_stop = True
