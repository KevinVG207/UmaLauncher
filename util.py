import win32api
import win32gui
import threading
from loguru import logger
from PIL import Image
import pyautogui
import time

window_handle = None


def _show_alert_box(error, message):
    win32api.MessageBox(
        None,
        message,
        error,
        48
    )


def show_alert_box(error, message):
    logger.error(f"{error}")
    threading.Thread(target=_show_alert_box, args=(error, message), daemon=False).start()


def _get_window_exact(hwnd: int, query: str):
    global window_handle
    if win32gui.IsWindowVisible(hwnd):
        if win32gui.GetWindowText(hwnd) == query:
            logger.info(f"Found window {query}!")
            window_handle = hwnd


def _get_window_lazy(hwnd: int, query: str):
    global window_handle
    if win32gui.IsWindowVisible(hwnd):
        if query.lower() in win32gui.GetWindowText(hwnd).lower():
            logger.info(f"Found window {query}!")
            window_handle = hwnd


def _get_window_startswith(hwnd: int, query: str):
    global window_handle
    if win32gui.IsWindowVisible(hwnd):
        if win32gui.GetWindowText(hwnd).startswith(query):
            logger.info(f"Found window {query}!")
            window_handle = hwnd


LAZY = _get_window_lazy
EXACT = _get_window_exact
STARTSWITH = _get_window_startswith

def get_window_handle(query: str, type: int=LAZY) -> str:
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

def take_screenshot(window_handle) -> Image.Image:
    x, y, x1, y1 = win32gui.GetClientRect(window_handle)
    x, y = win32gui.ClientToScreen(window_handle, (x, y))
    x1, y1 = win32gui.ClientToScreen(window_handle, (x1 - x, y1 - y))
    return pyautogui.screenshot(region=(x, y, x1, y1)).convert("RGB")

def convert_fractions_to_window_coords(window_handle, fractions: tuple[float,float]) -> tuple[float,float]:
    x, y, x1, y1 = win32gui.GetClientRect(window_handle)
    width = x1 - x
    height = y1 - y
    return (round(fractions[0] * width), round(fractions[1] * height))

def move_mouse_to_window_coords(window_handle, coords: tuple[float,float], click: bool = False):
    x, y = win32gui.ClientToScreen(window_handle, (coords[0], coords[1]))
    pyautogui.moveTo(x, y)
    if click:
        time.sleep(0.1)
        pyautogui.click()
    return None

def map(value, leftMin, leftMax, rightMin, rightMax):
    # Figure out how 'wide' each range is
    leftSpan = leftMax - leftMin
    rightSpan = rightMax - rightMin

    # Convert the left range into a 0-1 range (float)
    valueScaled = float(value - leftMin) / float(leftSpan)

    # Convert the 0-1 range into a value in the right range.
    return rightMin + (valueScaled * rightSpan)