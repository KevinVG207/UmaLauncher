import win32gui
from loguru import logger

def _get_nord(hwnd, lParam):
    global nord_window
    if win32gui.IsWindowVisible(hwnd):
        print(win32gui.GetWindowText(hwnd))
        if win32gui.GetWindowText(hwnd) == "NordVPN":
            logger.info("Found NordVPN window!")
            nord_window = hwnd


def get_nord():
    win32gui.EnumWindows(_get_nord, None)

get_nord()