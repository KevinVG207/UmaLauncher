import os
import time
import glob
import traceback
import math
import json
import msgpack
from loguru import logger
from selenium.common.exceptions import NoSuchWindowException
import screenstate_utils
import util
import constants
import mdb
import helper_table
import training_tracker
import horsium

class CarrotJuicer():
    start_time = None
    browser: horsium.BrowserWindow = None
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
    skills_list = []
    previous_skills_list = []
    previous_race_program_id = None
    last_data = None
    open_skill_window = False
    skill_browser = None
    last_skills_rect = None
    skipped_msgpacks = []

    def __init__(self, threader):
        self.threader = threader

        self.skill_id_dict = mdb.get_skill_id_dict()

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
        with open(util.get_relative(out_name), 'w', encoding='utf-8') as f:
            f.write(json.dumps(packet, indent=4, ensure_ascii=False))

    def open_helper(self):
        self.close_browser()

        start_pos = self.threader.settings["s_browser_position"]
        if not start_pos:
            start_pos = self.get_browser_reset_position()
        
        self.browser = horsium.BrowserWindow(self.helper_url, self.threader, rect=start_pos, run_at_launch=setup_helper_page)

    def get_browser_reset_position(self):
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
        return [left_x, workspace_rect[1], width, workspace_rect[3] - workspace_rect[1] + 6]


    def close_browser(self):
        if self.browser and self.browser.alive():
            self.browser.close()
            self.save_last_browser_rect()
            self.browser = None
        return

    def save_rect(self, rect_var, setting):
        if rect_var:
            if (rect_var['x'] == -32000 and rect_var['y'] == -32000):
                logger.warning(f"Browser minimized, cannot save position for {setting}: {rect_var}")
                rect_var = None
                return
            rect_list = [rect_var['x'], rect_var['y'], rect_var['width'], rect_var['height']]
            if self.threader.settings[setting] != rect_list:
                self.threader.settings[setting] = rect_list
            rect_var = None

    def save_last_browser_rect(self):
        self.save_rect(self.last_browser_rect, "s_browser_position")
    
    def save_skill_window_rect(self):
        if self.skill_browser:
            self.skill_browser.last_window_rect = self.last_skills_rect
        self.save_rect(self.last_skills_rect, "s_skills_position")

    def end_training(self):
        if self.training_tracker:
            self.training_tracker = None
        if self.skill_browser and self.skill_browser.alive():
            self.skill_browser.close()
        self.close_browser()
        return
    
    def add_response_to_tracker(self, data):
        should_track = self.threader.settings["s_track_trainings"]
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

        return [f"{grade_text} {self.EVENT_ID_TO_POS_STRING[event_id]}"]

    def handle_response(self, message, is_json=False):
        if is_json:
            data = message
        else:
            data = self.load_response(message)

        if self.threader.settings["s_save_packets"]:
            logger.debug("Response:")
            logger.debug(json.dumps(data))
            self.to_json(data, "packet_in.json")

        try:
            if 'data' not in data:
                # logger.info("This packet doesn't have data :)")
                return

            data = data['data']


            # New loading behavior?
            if 'single_mode_load_common' in data:
                for key, value in data['single_mode_load_common'].items():
                    data[key] = value


            # Close whatever popup is open
            if self.browser and self.browser.alive():
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
                    new_state = screenstate_utils.ss.ScreenState(self.screen_state_handler)
                    new_state.location = screenstate_utils.ss.Location.THEATER
                    new_state.main = "Concert Theater"
                    new_state.sub = "Vibing"

                    self.screen_state_handler.carrotjuicer_state = new_state
                return
            
            # Team Building
            if 'scout_ranking_state' in data:
                if data.get("own_team_info") and data['own_team_info'].get('team_score') and self.screen_state_handler:
                    team_score = data['own_team_info'].get('team_score')
                    leader_chara_id = data['own_team_info'].get('entry_chara_array',[{}])[0].get('trained_chara', {}).get('card_id')

                    if team_score and leader_chara_id:
                        logger.debug(f"Team score: {team_score}, leader chara id: {leader_chara_id}")
                        self.screen_state_handler.carrotjuicer_state = screenstate_utils.make_scouting_state(self.screen_state_handler, team_score, leader_chara_id)
            
            # League of Heroes
            if 'heroes_id' in data:
                if data.get("own_team_info") and data['own_team_info']['team_name'] and data['own_team_info']['league_score'] and self.screen_state_handler:
                    self.screen_state_handler.carrotjuicer_state = screenstate_utils.make_league_of_heroes_state(
                        self.screen_state_handler,
                        data['own_team_info']['team_name'],
                        data['own_team_info']['league_score']
                    )
                return
            
            if data.get('stage1_grand_result'):
                if self.screen_state_handler and \
                        self.screen_state_handler.screen_state and \
                        self.screen_state_handler.screen_state.location == screenstate_utils.ss.Location.LEAGUE_OF_HEROES and \
                        data['stage1_grand_result'].get('after_league_score'):
                    tmp = self.screen_state_handler.screen_state
                    tmp2 = screenstate_utils.ss.ScreenState(self.screen_state_handler)
                    tmp2.location = screenstate_utils.ss.Location.LEAGUE_OF_HEROES
                    tmp2.main = tmp.main
                    tmp2.sub = screenstate_utils.get_league_of_heroes_substate(data['stage1_grand_result']['after_league_score'])
                    self.screen_state_handler.carrotjuicer_state = tmp2
                    return
            
            # Claw Machine
            if 'collected_plushies' in data:
                if self.screen_state_handler:
                    self.screen_state_handler.carrotjuicer_state = screenstate_utils.make_claw_machine_state(data, self.threader.screenstate)
            
            # Race starts.
            if self.training_tracker and 'race_scenario' in data and 'race_start_info' in data and data['race_scenario']:
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
                    # Update cached dicts first
                    mdb.update_mdb_cache()

                    self.training_tracker = training_tracker.TrainingTracker(training_id, data['chara_info']['card_id'])

                self.skills_list = []
                for skill_data in data['chara_info']['skill_array']:
                    self.skills_list.append(skill_data['skill_id'])
                
                self.skills_list += mdb.get_card_inherent_skills(data['chara_info']['card_id'], data['chara_info']['talent_level'])

                for skill_tip in data['chara_info']['skill_tips_array']:
                    if skill_tip['rarity'] > 1:
                        self.skills_list.append(self.skill_id_dict[(skill_tip['group_id'], skill_tip['rarity'])])  # TODO: Check if level is correct. Check gold skills and purple skills.
                    else:
                        self.skills_list.append(mdb.determine_skill_id_from_group_id(skill_tip['group_id'], skill_tip['rarity'], self.skills_list))

                # self.skills_list.sort()
                self.skills_list = mdb.sort_skills_by_display_order(self.skills_list)

                # Fix certain skills for GameTora
                for i in range(len(self.skills_list)):
                    cur_skill_id = self.skills_list[i]
                    if 900000 <= cur_skill_id < 1000000:
                        self.skills_list[i] = cur_skill_id - 800000
                
                logger.debug(f"Skills list: {self.skills_list}")

                # Add request to tracker
                self.add_response_to_tracker(data)

                # Training info
                outfit_id = data['chara_info']['card_id']
                supports = [card_data['support_card_id'] for card_data in data['chara_info']['support_card_array']]
                scenario_id = data['chara_info']['scenario_id']

                # Training stats
                if self.screen_state_handler:
                    if data.get('race_start_info', None):
                        self.screen_state_handler.carrotjuicer_state = screenstate_utils.make_training_race_state(data, self.threader.screenstate)
                    else:
                        self.screen_state_handler.carrotjuicer_state = screenstate_utils.make_training_state(data, self.threader.screenstate)

                if not self.browser or not self.browser.current_url().startswith("https://gametora.com/umamusume/training-event-helper"):
                    logger.info("GT tab not open, opening tab")
                    self.helper_url = util.create_gametora_helper_url(outfit_id, scenario_id, supports)
                    logger.debug(f"Helper URL: {self.helper_url}")
                    self.open_helper()
                
                self.update_helper_table(data)

            if 'unchecked_event_array' in data and data['unchecked_event_array']:
                # Training event.
                logger.debug("Training event detected")
                event_data = data['unchecked_event_array'][0]
                event_titles = mdb.get_event_titles(event_data['story_id'], data['chara_info']['card_id'])
                logger.debug(f"Event titles: {event_titles}")

                if len(data['unchecked_event_array']) > 1:
                    logger.warning(f"Packet has more than 1 unchecked event! {message}")

                if len(event_data['event_contents_info']['choice_array']) > 1:
                    # Event has choices

                    # If character is the trained character
                    if event_data['event_contents_info']['support_card_id'] and event_data['event_contents_info']['support_card_id'] not in supports:
                        # Random support card event
                        logger.debug("Random support card detected")

                        self.browser.execute_script("""document.getElementById("boxSupportExtra").click();""")
                        self.browser.execute_script(
                            """
                            var cont = document.getElementById("30021").parentElement.parentElement;

                            var ele = document.getElementById(arguments[0].toString());

                            if (ele) {
                                ele.click();
                                return;
                            }
                            cont.querySelector('img[src="/images/ui/close.png"]').click();
                            """,
                            event_data['event_contents_info']['support_card_id']
                        )
                    else:
                        logger.debug("Trained character or support card detected")

                    # Check for after-race event.
                    if event_data['event_id'] in (7005, 7006, 7007):
                        logger.debug("After-race event detected.")
                        event_titles = self.get_after_race_event_title(event_data['event_id'])

                    # Activate and scroll to the outcome.
                    event_element = self.determine_event_element(event_titles)

                    if not event_element:
                        logger.debug(f"Could not find event on GT page: {event_data['story_id']}")
                    self.browser.execute_script("""
                        if (arguments[0]) {
                            arguments[0].click();
                            window.scrollBy({top: arguments[0].getBoundingClientRect().bottom - window.innerHeight + 32, left: 0, behavior: 'smooth'});
                        }
                        """,
                        event_element
                    )


            if 'reserved_race_array' in data and 'chara_info' not in data and self.last_helper_data:
                # User changed reserved races
                self.last_helper_data['reserved_race_array'] = data['reserved_race_array']
                data = self.last_helper_data
                self.update_helper_table(data)

            self.last_data = data
        except Exception:
            logger.error("ERROR IN HANDLING RESPONSE MSGPACK")
            logger.error(data)
            exception_string = traceback.format_exc()
            logger.error(exception_string)
            util.show_error_box("Uma Launcher: Error in response msgpack.", f"This should not happen. You may contact the developer about this issue.")
            # self.close_browser()

    def start_concert(self, music_id):
        logger.debug("Starting concert")
        self.screen_state_handler.carrotjuicer_state = screenstate_utils.make_concert_state(music_id, self.threader.screenstate)
        return

    def handle_request(self, message):
        data = self.load_request(message)

        if self.threader.settings["s_save_packets"]:
            logger.debug("Request:")
            logger.debug(json.dumps(data))
            self.to_json(data, "packet_out.json")

        self.previous_request = data

        try:
            if 'attestation_type' in data:
                mdb.update_mdb_cache()

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
            exception_string = traceback.format_exc()
            logger.error(exception_string)
            util.show_error_box("Uma Launcher: Error in request msgpack.", f"This should not happen. You may contact the developer about this issue.")
            # self.close_browser()

    def remove_message(self, message_path):
        if message_path in self.skipped_msgpacks:
            return

        tries = 0
        last_exception = None
        while tries < 5:
            try:
                if os.path.exists(message_path):
                    os.remove(message_path)
                    return
                else:
                    logger.warning(f"Attempted to delete non-existent msgpack file: {message_path}. Skipped.")
                    return
            except Exception as e:
                last_exception = e
                tries += 1
                time.sleep(1)
        
        logger.warning(f"Failed to remove msgpack file: {message_path}.")
        logger.warning(''.join(traceback.format_tb(last_exception.__traceback__)))
        self.skipped_msgpacks.append(message_path)


    def process_message(self, message: str):
        if message in self.skipped_msgpacks:
            return

        try:
            message_time = int(str(os.path.basename(message))[:-9])
        except ValueError:
            return
        if message_time < self.start_time:
            # Delete old msgpack files.
            self.remove_message(message)
            return

        # logger.info(f"New Packet: {os.path.basename(message)}")

        if message.endswith("R.msgpack"):
            # Response
            self.handle_response(message)

        else:
            # Request
            self.handle_request(message)

        self.remove_message(message)
        return


    def get_msgpack_batch(self, msg_path):
        return sorted(glob.glob(os.path.join(msg_path, "*.msgpack")), key=os.path.getmtime)


    def update_helper_table(self, data):
        helper_table = self.helper_table.create_helper_elements(data, self.last_helper_data)
        self.last_helper_data = data
        if helper_table:
            self.browser.execute_script("""
                window.UL_DATA.overlay_html = arguments[0];
                window.update_overlay();
                """,
                helper_table)


    def update_skill_window(self):
        if not self.skill_browser:
            self.skill_browser = horsium.BrowserWindow("https://gametora.com/umamusume/skills", self.threader, rect=self.threader.settings['s_skills_position'], run_at_launch=setup_skill_window)
        else:
            self.skill_browser.ensure_tab_open()
        if self.browser and self.browser.alive():
            self.browser.execute_script("""window.skill_window_opened();""")
        
        # Handle showing/hiding skills.
        self.skill_browser.execute_script(
            """
            let skills_list = arguments[0];
            let skill_elements = [];
            let skills_table = document.querySelector("[class^='skills_skill_table_']");
            let skill_rows = document.querySelectorAll("[class^='skills_table_desc_']");
            let color_class = [...document.querySelector("[class*='skills_stripes_']").classList].filter(item => item.startsWith("skills_stripes_"))[0];

            // Set display to none for all elements.
            for (const item of skill_rows) {
                item.parentNode.style.display = "none";
            }

            // Find the elements that match the skills list.
            for (const skill_id of skills_list) {
                let skill_string = "(" + skill_id + ")";
                let ele = null;
                for (const item of skill_rows) {
                    if (item.textContent.includes(skill_string)) {
                        skill_elements.push(item.parentNode);
                        item.parentNode.remove();
                        break;
                    }
                }
            }

            // Reappend the elements in the correct order.
            for (let i = 0; i < skill_elements.length; i++) {
                const item = skill_elements[i];
                item.style.display = "grid";

                if (i % 2 == 0) {
                    item.classList.add(color_class);
                } else {
                    item.classList.remove(color_class);
                }
                skills_table.appendChild(item);
            }
            """, self.skills_list)
    
    def determine_event_element(self, event_titles):
        ranked_elements = []
        for event_title in event_titles:
            possible_elements = self.browser.execute_script(
                """
                let a = document.querySelectorAll("[class^='compatibility_viewer_item_']");
                let ele = [];
                for (let i = 0; i < a.length; i++) {
                    let item = a[i];
                    if (item.textContent.includes(arguments[0])) {
                        let diff = item.textContent.length - arguments[0].length;
                        ele.push([diff, item, item.textContent]);
                    }
                }
                return ele;
                """,
                event_title
            )
            if possible_elements:
                possible_elements.sort(key=lambda x: x[0])
                ranked_elements.append(possible_elements[0])
        
        if not ranked_elements:
            return None

        ranked_elements.sort(key=lambda x: x[0])
        logger.info(f"Event element: {ranked_elements[0][2]}")
        return ranked_elements[0][1]


    def run_with_catch(self):
        try:
            self.run()
        except Exception:
            util.show_error_box("Critical Error", "Uma Launcher has encountered a critical error and will now close.")
            self.threader.stop()


    def run(self):
        try:
            while not self.should_stop:
                time.sleep(0.25)

                msg_path = self.threader.settings["s_game_install_path"]

                if not msg_path:
                    logger.error("Packet intercept enabled but no carrotjuicer path found")
                    util.show_error_box("Uma Launcher: No game install path found.", "This should not happen. Please add the game install path to umasettings.json")
                    return

                msg_path = os.path.join(msg_path, "CarrotJuicer")

                if not self.threader.settings["s_enable_carrotjuicer"] or not self.threader.settings['s_enable_browser']:
                    if self.browser and self.browser.alive():
                        self.browser.quit()
                    if self.skill_browser and self.skill_browser.alive():
                        self.skill_browser.quit()
                    continue

                if self.browser and self.browser.alive():
                    if self.reset_browser:
                        self.browser.set_window_rect(self.get_browser_reset_position())
                elif self.last_browser_rect:
                    self.save_last_browser_rect()
                
                self.reset_browser = False


                # Skill window.
                if self.open_skill_window:
                    self.open_skill_window = False
                    self.update_skill_window()
                elif self.skill_browser and self.skill_browser.alive() and self.previous_skills_list != self.skills_list:
                    self.previous_skills_list = self.skills_list
                    self.update_skill_window()


                if self.skill_browser:
                    if self.skill_browser.alive():
                        # Update skill window.
                        # self.update_skill_window()
                        pass
                    else:
                        self.save_skill_window_rect()

                if os.path.exists(util.get_relative("debug.in")) and util.is_debug:
                    try:
                        with open(util.get_relative("debug.in"), "r", encoding="utf-8") as f:
                            data = json.load(f)
                        self.handle_response(data, is_json=True)
                        os.remove(util.get_relative("debug.in"))
                    except Exception as e:
                        logger.error(traceback.format_exc())
                        pass

                messages = self.get_msgpack_batch(msg_path)
                for message in messages:
                    self.process_message(message)
        except NoSuchWindowException:
            pass

        if self.browser:
            logger.debug("Closing browser.")
            self.browser.quit()

        if self.skill_browser:
            logger.debug("Closing skill browser.")
            self.skill_browser.quit()

        self.save_last_browser_rect()
        self.save_skill_window_rect()

        return


    def stop(self):
        self.should_stop = True




def setup_helper_page(browser: horsium.BrowserWindow):
    browser.execute_script("""
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
    ul_dropdown.classList.add("ul-overlay-button");
    ul_dropdown.style = "position: fixed;right: 0;top: 0;width: 3rem;height: 1.6rem;background-color: var(--c-bg-main);text-align: center;z-index: 101;line-height: 1.5rem;border-left: 2px solid var(--c-topnav);border-bottom: 2px solid var(--c-topnav);border-bottom-left-radius: 0.5rem;cursor: pointer;";
    ul_dropdown.textContent = "⯅";
    window.UL_OVERLAY.appendChild(ul_dropdown);

    var ul_skills = document.createElement("div");
    ul_skills.id = "ul-skills";
    ul_skills.classList.add("ul-overlay-button");
    ul_skills.style = "position: fixed; right: 50px; top: 0; width: 3.5rem; height: 1.6rem; background-color: var(--c-bg-main); text-align: center; z-index: 101; line-height: 1.5rem; border-left: 2px solid var(--c-topnav); border-bottom: 2px solid var(--c-topnav); border-right: 2px solid var(--c-topnav); border-bottom-left-radius: 0.5rem; border-bottom-right-radius: 0.5rem; cursor: pointer; transition: top 0.5s ease 0s;";
    ul_skills.textContent = "Skills";
    window.UL_OVERLAY.appendChild(ul_skills);

    window.hide_overlay = function() {
        window.UL_DATA.expanded = false;
        document.getElementById("ul-dropdown").textContent = "⯆";
        // document.getElementById("ul-dropdown").style.top = "-2px";
        [...document.querySelectorAll(".ul-overlay-button")].forEach(div => {
            div.style.top = "-2px";
        })
        window.GT_PAGE.style.paddingTop = "0";
        window.UL_OVERLAY.style.bottom = "100%";
    }

    window.expand_overlay = function() {
        window.UL_DATA.expanded = true;

        var height = window.UL_OVERLAY.offsetHeight;
        console.log(height)
        window.OVERLAY_HEIGHT = height + "px";

        document.getElementById("ul-dropdown").textContent = "⯅";
        // document.getElementById("ul-dropdown").style.top = "calc(" + window.OVERLAY_HEIGHT + " - 2px)";
        [...document.querySelectorAll(".ul-overlay-button")].forEach(div => {
            div.style.top = "calc(" + window.OVERLAY_HEIGHT + " - 2px)";
        })
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

    // Skill window.
    window.await_skill_window_timeout = null;
    window.await_skill_window = function() {
        window.await_skill_window_timeout = setTimeout(function() {
            ul_skills.style.filter = "";
        }, 15000);

        ul_skills.style.filter = "brightness(0.5)";
        fetch('http://127.0.0.1:3150/open-skill-window', { method: 'POST' });
    }
    window.skill_window_opened = function() {
        if (window.await_skill_window_timeout) {
            clearTimeout(window.await_skill_window_timeout);
        }
        ul_skills.style.filter = "";
    }

    ul_skills.addEventListener("click", window.await_skill_window);

    
    window.send_screen_rect = function() {
        let rect = {
            'x': window.screenX,
            'y': window.screenY,
            'width': window.outerWidth,
            'height': window.outerHeight
        };
        fetch('http://127.0.0.1:3150/helper-window-rect', { method: 'POST', body: JSON.stringify(rect), headers: { 'Content-Type': 'text/plain' } });
        setTimeout(window.send_screen_rect, 2000);
    }
    setTimeout(window.send_screen_rect, 2000);

    """)

    gametora_dark_mode(browser)

    # Enable all cards
    browser.execute_script("""document.querySelector("[class^='filters_settings_button_']").click()""")
    all_cards_enabled = browser.execute_script("""return document.getElementById("allAtOnceCheckbox").checked;""")
    if not all_cards_enabled:
        browser.execute_script("""document.getElementById("allAtOnceCheckbox").click()""")
    browser.execute_script("""document.querySelector("[class^='filters_confirm_button_']").click()""")

    gametora_remove_cookies_banner(browser)

def setup_skill_window(browser: horsium.BrowserWindow):
    # Setup callback for window position
    browser.execute_script("""
    window.send_screen_rect = function() {
        let rect = {
            'x': window.screenX,
            'y': window.screenY,
            'width': window.outerWidth,
            'height': window.outerHeight
        };
        fetch('http://127.0.0.1:3150/skills-window-rect', { method: 'POST', body: JSON.stringify(rect), headers: { 'Content-Type': 'text/plain' } });
        setTimeout(window.send_screen_rect, 2000);
    }
    setTimeout(window.send_screen_rect, 2000);

    """)


    # Hide filters
    browser.execute_script("""document.querySelector("[class^='filters_filter_container_']").style.display = "none";""")

    gametora_dark_mode(browser)

    # Enable settings
    # Expand settings
    browser.execute_script("""document.querySelector("[class^='utils_padbottom_half_']").querySelector("button").click();""")
    while not browser.execute_script("""return document.querySelector("label[for='highlightCheckbox']");"""):
        time.sleep(0.25)

    # Enable highlight
    highlight_checked = browser.execute_script("""return document.querySelector("label[for='highlightCheckbox']").previousSibling.checked;""")
    if not highlight_checked:
        browser.execute_script("""document.querySelector("label[for='highlightCheckbox']").click();""")

    # Enable show id
    show_id_checked = browser.execute_script("""return document.querySelector("label[for='showIdCheckbox']").previousSibling.checked;""")
    if not show_id_checked:
        browser.execute_script("""document.querySelector("label[for='showIdCheckbox']").click();""")

    # Collapse settings
    browser.execute_script("""document.querySelector("[class^='utils_padbottom_half_']").querySelector("button").click();""")

    gametora_remove_cookies_banner(browser)

def gametora_dark_mode(browser: horsium.BrowserWindow):
    # Enable dark mode (the only reasonable color scheme)
    browser.execute_script("""document.querySelector("[class^='styles_header_settings_']").click()""")
    while not browser.execute_script("""return document.querySelector("[class^='filters_toggle_button_']");"""):
        time.sleep(0.25)
    
    dark_enabled = browser.execute_script("""return document.querySelector("[class^='tooltips_tooltip_']").querySelector("[class^='filters_toggle_button_']").childNodes[0].querySelector("input").checked;""")
    if dark_enabled != browser.threader.settings["s_gametora_dark_mode"]:
        browser.execute_script("""document.querySelector("[class^='tooltips_tooltip_']").querySelector("[class^='filters_toggle_button_']").childNodes[0].querySelector("input").click()""")
    browser.execute_script("""document.querySelector("[class^='styles_header_settings_']").click()""")


def gametora_remove_cookies_banner(browser: horsium.BrowserWindow):
    while not browser.execute_script("""return document.getElementById("adnote");"""):
        time.sleep(0.25)

    # Hide the cookies banner
    browser.execute_script("""document.getElementById("adnote").style.display = 'none';""")


def setup_gametora(browser: horsium.BrowserWindow):
    gametora_dark_mode(browser)
    gametora_remove_cookies_banner(browser)