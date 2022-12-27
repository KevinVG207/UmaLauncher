import os
import msgpack
import numpy as np
import time
import settings
from loguru import logger
import glob
import webbrowser
import time
import math
import json
import sqlite3
from selenium.common.exceptions import WebDriverException
from selenium import webdriver

START_TIME = math.floor(time.time() * 1000)
browser = None
previous_element = None


def load_request(msg_path):
    with open(msg_path, "rb") as in_file:
        packet = msgpack.unpackb(in_file.read()[170:], strict_map_key=False)
    return packet

def load_response(msg_path):
    with open(msg_path, "rb") as in_file:
        packet = msgpack.unpackb(in_file.read(), strict_map_key=False)
    return packet

def create_gametora_helper_url_from_start(packet_data):
    if 'start_chara' not in packet_data:
        return None
    d = packet_data['start_chara']
    supports = d['support_card_ids'] + [d['friend_support_card_info']['support_card_id']]

    return create_gametora_helper_url(d['card_id'], d['scenario_id'], supports)

def create_gametora_helper_url(card_id, scenario_id, support_ids):
    support_ids = list(map(str, support_ids))
    return f"https://gametora.com/umamusume/training-event-helper?deck={np.base_repr(int(str(card_id) + str(scenario_id)), 36)}-{np.base_repr(int(support_ids[0] + support_ids[1] + support_ids[2]), 36)}-{np.base_repr(int(support_ids[3] + support_ids[4] + support_ids[5]), 36)}".lower()

def to_json(packet):
    with open("packet.json", 'w', encoding='utf-8') as f:
        f.write(json.dumps(packet, indent=4, ensure_ascii=False))

def open_helper(helper_url):
    global browser

    if not browser:
        browser = webdriver.Firefox()

    browser.get(helper_url)
    # TODO: Find a way to know if the page is actually finished loading

    time.sleep(1)

    # Hide the cookies banner
    browser.execute_script("""document.querySelector("[class^='legal_cookie_banner_wrapper_']").style.display = 'none';""")

    # Enable dark mode (the only reasonable color scheme)
    browser.execute_script("""document.querySelector("[class^='styles_header_settings_']").click()""")
    while not browser.execute_script("""return document.querySelector("[class^='filters_toggle_button_']");"""):
        time.sleep(0.2)
    dark_enabled = browser.execute_script("""document.querySelector("[class^='filters_toggle_button_']").childNodes[0].querySelector("input").checked;""")
    if not dark_enabled:
        browser.execute_script("""document.querySelector("[class^='filters_toggle_button_']").childNodes[0].querySelector("input").click()""")
    browser.execute_script("""document.querySelector("[class^='styles_header_settings_']").click()""")

    # Enable all cards
    browser.execute_script("""document.querySelector("[class^='filters_settings_button_']").click()""")
    all_cards_enabled = browser.execute_script("""document.getElementById("allAtOnceCheckbox").checked;""")
    if not all_cards_enabled:
        browser.execute_script("""document.getElementById("allAtOnceCheckbox").click()""")
    browser.execute_script("""document.querySelector("[class^='filters_confirm_button_']").click()""")


def close_browser():
    global browser

    if browser:
        browser.close()
        browser = None
    return

def handle_response(message):
    global browser
    global previous_element

    data = load_response(message)
    logger.info(data)

    if 'data' not in data:
        logger.info("This packet doesn't have data :)")
        return

    data = data['data']

    # Run ended
    if 'single_mode_factor_select_common' in data:
        close_browser()
        return

    # Gametora
    if 'chara_info' in data:
        logger.info("chara_info in data")
        if "mission_list" in data:
            # New run
            close_browser()

        # Training info
        outfit_id = data['chara_info']['card_id']
        chara_id = int(str(outfit_id)[:-2])
        supports = [card_data['support_card_id'] for card_data in data['chara_info']['support_card_array']]
        scenario_id = data['chara_info']['scenario_id']

        if not browser or not browser.current_url.startswith("https://gametora.com/umamusume/training-event-helper"):
            logger.info("GT tab not open, opening tab")
            open_helper(create_gametora_helper_url(outfit_id, scenario_id, supports))
    
    if 'unchecked_event_array' in data and data['unchecked_event_array']:
        # Training event.
        logger.info("Training event detected")
        event_data = data['unchecked_event_array'][0]
        # TODO: Check if there can be multiple events??
        if len(data['unchecked_event_array']) > 1:
            logger.warning(f"Packet has more than 1 unchecked event! {message}")

        if len(event_data['event_contents_info']['choice_array']) > 1:

            if previous_element:
                browser.execute_script(
                    """
                    if (arguments[0].getAttribute("aria-expanded") == "true"){
                        arguments[0].click();
                    }
                    """,
                    previous_element
                )
            
            time.sleep(0.4)

            conn = sqlite3.connect(os.path.expandvars("%userprofile%\\appdata\\locallow\\Cygames\\umamusume\\master\\master.mdb"))
            cursor = conn.cursor()
            cursor.execute(
                """SELECT text FROM text_data WHERE category = 181 AND "index" = ?""",
                (event_data['story_id'],)
            )
            event_title = cursor.fetchone()[0]

            conn.close()
            logger.info(f"Event title determined: {event_title}")

            # Event has choices
            
            # If character is the trained character
            if event_data['event_contents_info']['support_card_id'] and event_data['event_contents_info']['support_card_id'] not in supports:
                # Random support card event
                logger.info("Random support card detected")
                browser.execute_script("""document.getElementById("boxSupportExtra").click();""")
                browser.execute_script(
                    """
                    document.getElementById(arguments[0].toString()).click();
                    """,
                    event_data['event_contents_info']['support_card_id']
                )
            else:
                logger.info("Trained character or support card detected")

            # Activate and scroll to the outcome.
            previous_element = browser.execute_script(
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
            if not previous_element:
                logger.info("Could not find event on GT page.")
            time.sleep(0.25)
            browser.execute_script("""
                if (arguments[0]) {
                    document.querySelector(".tippy-box").scrollIntoView({behavior:"smooth", block:"center"});
                }
                """,
                previous_element
            )

def check_browser():
    global browser

    if browser:
        try:
            browser.current_url
            return
        except WebDriverException:
            browser = None
    return

def process_message(message: str):
    global previous_element
    global browser

    check_browser()

    try:
        message_time = int(str(os.path.basename(message))[:-9])
    except ValueError:
        return
    if message_time < START_TIME:
        return

    logger.info(f"New Packet: {os.path.basename(message)}")

    if message.endswith("R.msgpack"):
        # Response
        handle_response(message)


    else:
        # Request
        data = load_request(message)
        logger.info(data)

        if 'start_chara' in data:
            # Packet is a request to start a training
            logger.info("Start of training detected")
            open_helper(create_gametora_helper_url_from_start(data))


    os.remove(message)
    return


def get_msgpack_batch(msg_path):
    return sorted(glob.glob(os.path.join(msg_path, "*.msgpack")), key=os.path.getmtime)

def run():
    global browser

    if not settings.get_tray_setting("Intercept packets"):
        return

    msg_path = settings.get("game_install_path")

    if not msg_path:
        logger.error("Packet intercept enabled but no carrotjuicer path found")
        return
    
    msg_path = os.path.join(msg_path, "CarrotJuicer")

    while True:
        if not settings.check_alive():
            if browser:
                browser.close()
            return
        time.sleep(0.25)
        
        messages = get_msgpack_batch(msg_path)
        for message in messages:
            process_message(message)
