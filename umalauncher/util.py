import os
import sys
import base64
import io
import ctypes
import win32event
from win32com.shell.shell import ShellExecuteEx
from win32com.shell import shellcon
import win32con
import win32process
from PIL import Image
from loguru import logger
import constants

ignore_errors = False

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
    """Gets the absolute path of a file relative to the executable's directory.
    """
    return os.path.join(relative_dir, relative_path)

def get_asset(asset_path):
    """Gets the absolute path of an asset relative to the unpack directory.
    """
    return os.path.join(unpack_dir, asset_path)

def elevate():
    """Elevate the script if it's not already running as admin.
    Based on PyUAC https://github.com/Preston-Landers/pyuac
    """

    if ctypes.windll.shell32.IsUserAnAdmin():
        return True
    
    # Elevate the script.
    proc_info = None
    executable = sys.executable
    params = " ".join(sys.argv if is_script else sys.argv[1:])  # Add the script path if it's a script.
    try:
        proc_info = ShellExecuteEx(
            nShow=win32con.SW_SHOWNORMAL,
            fMask=shellcon.SEE_MASK_NOCLOSEPROCESS | shellcon.SEE_MASK_NO_CONSOLE,
            lpVerb="runas",
            lpFile=executable,
            lpParameters=params,
        )
    except Exception as e:
        return False

    if not proc_info:
        return False
    
    handle = proc_info["hProcess"]
    _ = win32event.WaitForSingleObject(handle, win32event.INFINITE)
    sys.exit(1)


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


# Import the rest of the modules after logging is set up.
import win32api
import win32gui
import win32con
import traceback
import math
import time
import requests
from pywintypes import error as pywinerror  # pylint: disable=no-name-in-module
from PIL import Image
import numpy as np
import mdb
import gui

last_failed_request = None
has_failed_once = False
def do_get_request(url, error_title=None, error_message=None, ignore_timeout=False):
    global last_failed_request
    global has_failed_once

    try:
        if not ignore_timeout and last_failed_request is not None:
            # Ignore everything from umapyoi.net for 5 minutes to avoid spamming requests.
            if time.perf_counter() - last_failed_request > 60 * 5:
                last_failed_request = None
            else:
                return None
        logger.debug(f"GET request to {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response
    except:
        logger.warning(f"Failed to connect to {url}")
        logger.warning(traceback.format_exc())
        if ignore_timeout or not has_failed_once:
            has_failed_once = True
            logger.warning(traceback.format_exc())
            show_warning_box(
                "Failed to connect to server" if error_title is None else error_title,
                "Uma Launcher failed to connect to umapyoi.net to load English translations.<br>You can still use Uma Launcher, but some text (rich presence, CSV) may be in Japanese." if error_message is None else error_message
            )
        if not ignore_timeout:
            last_failed_request = time.perf_counter()
        return None



window_handle = None


def get_width_from_height(height, portrait):
    if portrait:
        return math.ceil((height * 0.5626065430) - 6.2123937177)
    return math.ceil((height * 1.7770777107) - 52.7501897551)


def _show_alert_box(error, message, icon):
    gui.show_widget(gui.UmaInfoPopup, error, message, icon)


def show_error_box(error, message, custom_traceback=None):
    logger.error(error)
    logger.error(message)
    traceback_str = traceback.format_exc() if custom_traceback is None else custom_traceback
    logger.error(traceback_str)

    global ignore_errors
    if ignore_errors:
        return
    
    gui.show_widget(
        gui.UmaErrorPopup,
        error,
        message,
        traceback_str,
        gui.THREADER.settings["s_unique_id"] if gui.THREADER is not None and gui.THREADER.settings is not None else None,
        gui.ICONS.Critical
    )

def show_error_box_no_report(error, message):
    logger.error(error)
    logger.error(message)

    global ignore_errors
    if ignore_errors:
        return

    _show_alert_box(error, message, gui.ICONS.Critical)


def show_warning_box(error, message):
    logger.warning(f"{error}")
    logger.warning(f"{message}")

    global ignore_errors
    if ignore_errors:
        return
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

def _get_window_by_executable(hwnd: int, query: str):
    global window_handle
    if win32gui.IsWindowVisible(hwnd):
        # Get the process ID of the window
        pid = win32process.GetWindowThreadProcessId(hwnd)[1]
        # Open the process, and get the executable path
        proc_path = win32process.GetModuleFileNameEx(win32api.OpenProcess(win32con.PROCESS_QUERY_LIMITED_INFORMATION, False, pid), 0)
        executable = os.path.basename(proc_path)
        if executable == query:
            logger.debug(f"Found window {query}!")
            window_handle = hwnd


LAZY = _get_window_lazy
EXACT = _get_window_exact
STARTSWITH = _get_window_startswith
EXEC_MATCH = _get_window_by_executable

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

    if turn < 12:
        turn /= 2
        turn += 6
        turn = math.floor(turn)

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

def hide_window_from_taskbar(window_handle):
    try:
        style = win32gui.GetWindowLong(window_handle, win32con.GWL_EXSTYLE)
        style |= win32con.WS_EX_TOOLWINDOW
        win32gui.ShowWindow(window_handle, win32con.SW_HIDE)
        win32gui.SetWindowLong(window_handle, win32con.GWL_EXSTYLE, style)
        return True
    except pywinerror:
        return False


def is_minimized(handle):
    try:
        tup = win32gui.GetWindowPlacement(handle)
        if tup[1] == win32con.SW_SHOWMINIMIZED:
            return True
        return False
    except pywinerror as e:
        logger.warning("Failed to get window placement.")
        logger.warning(e)
        logger.warning(traceback.format_exc())
        # Default to it being minimized as to not save the game window.
        return True

downloaded_chara_dict = {}
def get_character_name_dict(force=False):
    global downloaded_chara_dict

    if force or not downloaded_chara_dict:
        chara_dict = mdb.get_chara_name_dict()
        response = do_get_request("https://umapyoi.net/api/v1/character/names")
        if not response:
            return chara_dict

        for character in response.json():
            chara_dict[character['game_id']] = character['name']

        downloaded_chara_dict.update(chara_dict)
    return downloaded_chara_dict

downloaded_outfit_dict = {}
def get_outfit_name_dict(force=False):
    global downloaded_outfit_dict

    if force or not downloaded_outfit_dict:
        outfit_dict = mdb.get_outfit_name_dict()
        response = do_get_request("https://umapyoi.net/api/v1/outfit")
        if not response:
            return outfit_dict

        for outfit in response.json():
            outfit_dict[outfit['id']] = outfit['title']

        downloaded_outfit_dict.update(outfit_dict)
    return downloaded_outfit_dict

downloaded_race_name_dict = {}
def get_race_name_dict(force=False):
    global downloaded_race_name_dict

    if force or not downloaded_race_name_dict:
        race_name_dict = mdb.get_race_program_name_dict()
        logger.info("Requesting race names from umapyoi.net")
        response = do_get_request("https://umapyoi.net/api/v1/race_program")
        if not response:
            return race_name_dict
        
        for race_program in response.json():
            race_name_dict[race_program['id']] = race_program['name']
        
        downloaded_race_name_dict.update(race_name_dict)
    return downloaded_race_name_dict

def create_gametora_helper_url(card_id, scenario_id, support_ids):
    support_ids = list(map(str, support_ids))
    return f"https://gametora.com/umamusume/training-event-helper?deck={np.base_repr(int(str(card_id) + str(scenario_id)), 36)}-{np.base_repr(int(support_ids[0] + support_ids[1] + support_ids[2]), 36)}-{np.base_repr(int(support_ids[3] + support_ids[4] + support_ids[5]), 36)}".lower()

gm_fragment_dict = {}
def get_gm_fragment_dict(force=False):
    global gm_fragment_dict

    if force or not gm_fragment_dict:
        logger.debug("Loading Grand Master fragment images...")
        tmp_gm_fragment_dict = {}
        for i in range(0, 23):
            fragment_img_path = f"_assets/gm/frag_{i:02}.png"
            asset_path = get_asset(fragment_img_path)

            if not os.path.exists(asset_path):
                continue

            img = Image.open(asset_path)
            img.thumbnail((36, 36))

            # Save the image in memory in PNG format
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            img.close()

            # Encode PNG image to base64 string
            b64 = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("utf-8")
            tmp_gm_fragment_dict[i] = b64

            buffer.close()
        
        gm_fragment_dict.update(tmp_gm_fragment_dict)
    return gm_fragment_dict


gl_token_dict = {}
def get_gl_token_dict(force=False):
    global gl_token_dict

    if force or not gl_token_dict:
        logger.debug("Loading Grand Live token images...")
        tmp_gl_token_dict = {}

        token_folder = get_asset("_assets/gl/tokens")
        for token_file in os.listdir(token_folder):
            if not token_file.endswith(".png"):
                continue

            token_name = token_file[:-4]

            img = Image.open(os.path.join(token_folder, token_file))
            img.thumbnail((36, 36))

            # Save the image in memory in PNG format
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            img.close()

            # Encode PNG image to base64 string
            b64 = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("utf-8")
            tmp_gl_token_dict[token_name] = b64

            buffer.close()
        
        gl_token_dict.update(tmp_gl_token_dict)

    return gl_token_dict

GROUP_SUPPORT_ID_TO_PASSION_ZONE_EFFECT_ID_DICT = {}
def get_group_support_id_to_passion_zone_effect_id_dict(force=False):
    global GROUP_SUPPORT_ID_TO_PASSION_ZONE_EFFECT_ID_DICT

    if force or not GROUP_SUPPORT_ID_TO_PASSION_ZONE_EFFECT_ID_DICT:
        cards = mdb.get_group_card_effect_ids()
        GROUP_SUPPORT_ID_TO_PASSION_ZONE_EFFECT_ID_DICT.update({card[0]: card[1] for card in cards})

    return GROUP_SUPPORT_ID_TO_PASSION_ZONE_EFFECT_ID_DICT

def heroes_score_to_league_string(score):
    current_league = list(constants.HEROES_SCORE_TO_LEAGUE_DICT.keys())[0]
    for score_threshold, league in constants.HEROES_SCORE_TO_LEAGUE_DICT.items():
        if score >= score_threshold:
            current_league = league
        else:
            break
    return current_league

def scouting_score_to_rank_string(score):
    current_rank = list(constants.SCOUTING_SCORE_TO_RANK_DICT.keys())[0]
    for score_threshold, rank in constants.SCOUTING_SCORE_TO_RANK_DICT.items():
        if score >= score_threshold:
            current_rank = rank
        else:
            break
    return current_rank

UPDATE_FUNCS = [
    get_character_name_dict,
    get_outfit_name_dict,
    get_race_name_dict,
    get_gm_fragment_dict,
    get_gl_token_dict,
    get_group_support_id_to_passion_zone_effect_id_dict,
]