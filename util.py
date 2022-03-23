import win32api
import threading
from loguru import logger

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