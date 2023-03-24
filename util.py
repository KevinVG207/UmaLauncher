import win32api
import win32gui
import win32con
import threading
import math
import os
import sys
import requests
from pywintypes import error as pywinerror  # pylint: disable=no-name-in-module
from loguru import logger
from PIL import Image
import numpy as np
import mdb

window_handle = None

SCENARIO_DICT = {
    1: "URA Finals",
    2: "Aoharu Cup",
    3: "Grand Live",
    4: "Make a New Track",
    5: "Grand Masters",
}

MOTIVATION_DICT = {
    5: "Very High",
    4: "High",
    3: "Normal",
    2: "Low",
    1: "Very Low"
}

SUPPORT_CARD_RARITY_DICT = {
    1: "R",
    2: "SR",
    3: "SSR"
}

SUPPORT_CARD_TYPE_DICT = {
    (101, 1): "Speed",
    (105, 1): "Stamina",
    (102, 1): "Power",
    (103, 1): "Guts",
    (106, 1): "Wisdom",
    (0, 2): "Friend",
    (0, 3): "Group"
}

unpack_dir = os.getcwd()
is_script = True
if hasattr(sys, "_MEIPASS"):
    unpack_dir = sys._MEIPASS
    is_script = False
is_debug = is_script

def get_asset(asset_path):
    return os.path.join(unpack_dir, asset_path)

def get_width_from_height(height, portrait):
    if portrait:
        return math.ceil((height * 0.5626065430) - 6.2123937177)
    return math.ceil((height * 1.7770777107) - 52.7501897551)

def _show_alert_box(error, message):
    win32api.MessageBox(
        None,
        message,
        error,
        48
    )


def show_alert_box(error, message):
    logger.error(f"{error}")
    logger.error(f"{message}")
    threading.Thread(target=_show_alert_box, args=(error, message), daemon=False).start()


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

MONTH_DICT = {
    1: 'January',
    2: 'February',
    3: 'March',
    4: 'April',
    5: 'May',
    6: 'June',
    7: 'July',
    8: 'August',
    9: 'September',
    10: 'October',
    11: 'November',
    12: 'December'
}

def turn_to_string(turn):
    turn = turn - 1

    second_half = turn % 2 != 0
    if second_half:
        turn -= 1
    turn /= 2
    month = int(turn) % 12 + 1
    year = math.floor(turn / 12) + 1

    return f"Y{year}, {'Late' if second_half else 'Early'} {MONTH_DICT[month]}"

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

def log_reset():
    logger.remove()
    if is_script:
        logger.add(sys.stderr, level="TRACE")
    return

def log_set_info():
    log_reset()
    logger.add("log.log", rotation="1 week", compression="zip", retention="1 month", encoding='utf-8', level="INFO")
    return

def log_set_trace():
    log_reset()
    logger.add("log.log", rotation="1 week", compression="zip", retention="1 month", encoding='utf-8', level="TRACE")
    return

downloaded_chara_dict = None

def get_character_name_dict():
    global downloaded_chara_dict

    if not downloaded_chara_dict:
        chara_dict = mdb.get_chara_name_dict()
        logger.info("Requesting character names from umapyoi.net")
        response = requests.get("https://umapyoi.net/api/v1/character/names")
        if not response.ok:
            show_alert_box("UmaLauncher: Internet error.", "Cannot download the character names from umapyoi.net for the Discord Rich Presence. Please check your internet connection.")
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
            show_alert_box("UmaLauncher: Internet error.", "Cannot download the outfit names from umapyoi.net for the Discord Rich Presence. Please check your internet connection.")
            return outfit_dict

        for outfit in response.json():
            outfit_dict[outfit['id']] = outfit['title']

        downloaded_outfit_dict = outfit_dict
    return downloaded_outfit_dict

def create_gametora_helper_url(card_id, scenario_id, support_ids):
    support_ids = list(map(str, support_ids))
    return f"https://gametora.com/umamusume/training-event-helper?deck={np.base_repr(int(str(card_id) + str(scenario_id)), 36)}-{np.base_repr(int(support_ids[0] + support_ids[1] + support_ids[2]), 36)}-{np.base_repr(int(support_ids[3] + support_ids[4] + support_ids[5]), 36)}".lower()
