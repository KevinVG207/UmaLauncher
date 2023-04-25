import os
import sys
import base64
import io
from PIL import Image
from loguru import logger
import constants

relative_dir = os.path.abspath(os.getcwd())
unpack_dir = relative_dir
is_script = True
if hasattr(sys, "_MEIPASS"):
    unpack_dir = sys._MEIPASS
    is_script = False
    relative_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    os.chdir(relative_dir)
is_debug = is_script

def get_relative(relative_path):
    return os.path.join(relative_dir, relative_path)

def get_asset(asset_path):
    return os.path.join(unpack_dir, asset_path)

def log_reset():
    logger.remove()
    if is_script:
        logger.add(sys.stderr, level="TRACE")
    return

def log_set_info():
    log_reset()
    logger.add(get_relative("log.log"), rotation="1 week", compression="zip", retention="1 month", encoding='utf-8', level="INFO")
    return

def log_set_trace():
    log_reset()
    logger.add(get_relative("log.log"), rotation="1 week", compression="zip", retention="1 month", encoding='utf-8', level="TRACE")
    return

if is_script:
    log_set_trace()
    logger.debug("Running from script, enabling debug logging.")
else:
    log_set_info()

import win32api
import win32gui
import win32con
import math
import requests
from pywintypes import error as pywinerror  # pylint: disable=no-name-in-module
from PIL import Image
import numpy as np
import mdb
import gui

window_handle = None

def get_width_from_height(height, portrait):
    if portrait:
        return math.ceil((height * 0.5626065430) - 6.2123937177)
    return math.ceil((height * 1.7770777107) - 52.7501897551)

def _show_alert_box(error, message, icon):
    app = gui.UmaApp()
    app.run(gui.UmaInfoPopup(error, message, icon))
    app.close()


def show_error_box(error, message):
    logger.error(f"{error}")
    logger.error(f"{message}")
    _show_alert_box(error, message, gui.ICONS.Critical)


def show_warning_box(error, message):
    logger.warning(f"{error}")
    logger.warning(f"{message}")
    _show_alert_box(error, message, gui.ICONS.Warning)


def show_info_box(error, message):
    logger.info(f"{error}")
    logger.info(f"{message}")
    _show_alert_box(error, message, gui.ICONS.Information)


def _get_window_exact(hwnd: int, query: str):
    global window_handle
    if win32gui.IsWindowVisible(hwnd):
        if win32gui.GetWindowText(hwnd) == query:
            logger.debug(f"Found window {query}!")
            window_handle = hwnd


def _get_window_lazy(hwnd: int, query: str):
    global window_handle
    if win32gui.IsWindowVisible(hwnd):
        if query.lower() in win32gui.GetWindowText(hwnd).lower():
            logger.debug(f"Found window {query}!")
            window_handle = hwnd


def _get_window_startswith(hwnd: int, query: str):
    global window_handle
    if win32gui.IsWindowVisible(hwnd):
        if win32gui.GetWindowText(hwnd).startswith(query):
            logger.debug(f"Found window {query}!")
            window_handle = hwnd


LAZY = _get_window_lazy
EXACT = _get_window_exact
STARTSWITH = _get_window_startswith

def get_window_handle(query: str, type=LAZY) -> str:
    global window_handle

    window_handle = None
    win32gui.EnumWindows(type, query)
    return window_handle


def get_position_rgb(image: Image.Image, position: tuple[float,float]) -> tuple[int,int,int]:
    pixel_color = None
    pixel_pos = (round(image.width * position[0]), round(image.height * position[1]))
    try:
        pixel_color = image.getpixel(pixel_pos)
    except IndexError:
        pass
    return pixel_color


def similar_color(col1: tuple[int,int,int], col2: tuple[int,int,int], threshold: int = 32) -> bool:
    total_diff = 0
    for i in range(3):
        total_diff += abs(col1[i] - col2[i])
    return total_diff < threshold

def turn_to_string(turn):
    turn = turn - 1

    second_half = turn % 2 != 0
    if second_half:
        turn -= 1
    turn /= 2
    month = int(turn) % 12 + 1
    year = math.floor(turn / 12) + 1

    return f"Y{year}, {'Late' if second_half else 'Early'} {constants.MONTH_DICT[month]}"

def get_window_rect(*args, **kwargs):
    try:
        return win32gui.GetWindowRect(*args, **kwargs)
    except pywinerror:
        return None

def move_window(*args, **kwargs):
    try:
        win32gui.MoveWindow(*args, **kwargs)
        return True
    except pywinerror:
        return False

def monitor_from_window(*args, **kwargs):
    try:
        return win32api.MonitorFromWindow(*args, **kwargs)
    except pywinerror:
        return None

def get_monitor_info(*args, **kwargs):
    try:
        return win32api.GetMonitorInfo(*args, **kwargs)
    except pywinerror:
        return None

def show_window(*args, **kwargs):
    try:
        win32gui.ShowWindow(*args, **kwargs)
        return True
    except pywinerror:
        return False

def is_minimized(handle):
    try:
        tup = win32gui.GetWindowPlacement(handle)
        if tup[1] == win32con.SW_SHOWMINIMIZED:
            return True
        return False
    except pywinerror:
        # Default to it being minimized as to not save the game window.
        return True

downloaded_chara_dict = None

def get_character_name_dict():
    global downloaded_chara_dict

    if not downloaded_chara_dict:
        chara_dict = mdb.get_chara_name_dict()
        logger.info("Requesting character names from umapyoi.net")
        response = requests.get("https://umapyoi.net/api/v1/character/names")
        if not response.ok:
            show_warning_box("Uma Launcher: Internet error.", "Cannot download the character names from umapyoi.net for the Discord Rich Presence. Please check your internet connection.")
            return chara_dict

        for character in response.json():
            chara_dict[character['game_id']] = character['name']

        downloaded_chara_dict = chara_dict
    return downloaded_chara_dict

downloaded_outfit_dict = None
def get_outfit_name_dict():
    global downloaded_outfit_dict

    if not downloaded_outfit_dict:
        outfit_dict = mdb.get_outfit_name_dict()
        logger.info("Requesting outfit names from umapyoi.net")
        response = requests.get("https://umapyoi.net/api/v1/outfit")
        if not response.ok:
            show_warning_box("Uma Launcher: Internet error.", "Cannot download the outfit names from umapyoi.net for the Discord Rich Presence. Please check your internet connection.")
            return outfit_dict

        for outfit in response.json():
            outfit_dict[outfit['id']] = outfit['title']

        downloaded_outfit_dict = outfit_dict
    return downloaded_outfit_dict

def create_gametora_helper_url(card_id, scenario_id, support_ids):
    support_ids = list(map(str, support_ids))
    return f"https://gametora.com/umamusume/training-event-helper?deck={np.base_repr(int(str(card_id) + str(scenario_id)), 36)}-{np.base_repr(int(support_ids[0] + support_ids[1] + support_ids[2]), 36)}-{np.base_repr(int(support_ids[3] + support_ids[4] + support_ids[5]), 36)}".lower()

gm_fragment_dict = None
def get_gm_fragment_dict():
    global gm_fragment_dict

    if not gm_fragment_dict:
        logger.debug("Loading Grand Master fragment images...")
        gm_fragment_dict = {}
        for i in range(0, 23):
            fragment_img_path = f"_assets/gm/frag_{i:02}.png"
            asset_path = get_asset(fragment_img_path)

            if not os.path.exists(asset_path):
                continue

            img = Image.open(asset_path)
            img.thumbnail((36, 36), Image.ANTIALIAS)

            # Save the image in memory in PNG format
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            img.close()

            # Encode PNG image to base64 string
            b64 = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("utf-8")
            gm_fragment_dict[i] = b64

            buffer.close()
    return gm_fragment_dict


gl_token_dict = None
def get_gl_token_dict():
    global gl_token_dict

    if not gl_token_dict:
        logger.debug("Loading Grand Live token images...")
        gl_token_dict = {}

        token_folder = get_asset("_assets/gl/tokens")
        for token_file in os.listdir(token_folder):
            if not token_file.endswith(".png"):
                continue

            token_name = token_file[:-4]

            img = Image.open(os.path.join(token_folder, token_file))
            img.thumbnail((36, 36), Image.ANTIALIAS)

            # Save the image in memory in PNG format
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            img.close()

            # Encode PNG image to base64 string
            b64 = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("utf-8")
            gl_token_dict[token_name] = b64

            buffer.close()

    return gl_token_dict

GROUP_SUPPORT_ID_TO_PASSION_ZONE_EFFECT_ID_DICT = None
def get_group_support_id_to_passion_zone_effect_id_dict():
    global GROUP_SUPPORT_ID_TO_PASSION_ZONE_EFFECT_ID_DICT

    if not GROUP_SUPPORT_ID_TO_PASSION_ZONE_EFFECT_ID_DICT:
        cards = mdb.get_group_card_effect_ids()
        GROUP_SUPPORT_ID_TO_PASSION_ZONE_EFFECT_ID_DICT = {card[0]: card[1] for card in cards}

    return GROUP_SUPPORT_ID_TO_PASSION_ZONE_EFFECT_ID_DICT