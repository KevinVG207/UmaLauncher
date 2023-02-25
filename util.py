import win32api
import win32gui
import win32con
import threading
import math
import os
import sys
from pywintypes import error as pywinerror  # pylint: disable=no-name-in-module
from loguru import logger
from PIL import Image

window_handle = None

unpack_dir = os.getcwd()
is_script = True
if hasattr(sys, "_MEIPASS"):
    unpack_dir = sys._MEIPASS
    is_script = False

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
