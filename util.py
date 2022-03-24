import win32api
import win32gui
import threading
from loguru import logger

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


def get_window_handle(query: str, exact: bool=False) -> str:
    global window_handle
    window_handle = None

    if exact:
        win32gui.EnumWindows(_get_window_exact, query)
    else:
        win32gui.EnumWindows(_get_window_lazy, query)

    return window_handle

