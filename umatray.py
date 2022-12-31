from io import BytesIO
import pystray
import win32clipboard
from loguru import logger
from PIL import Image
import util
from threader import Threader

class UmaTray():
    menu_items = None
    icon_thread = None
    threader = None

    def __init__(self, threader: Threader):
        self.threader = threader
        menu_items = [
            pystray.MenuItem(
                menu_item,
                self.threader.settings.set_tray_setting,
                checked=lambda item: self.threader.settings.get_tray_setting(item.text)
            ) for menu_item in self.threader.settings.default_settings["tray_items"]
        ]
        menu_items.append(pystray.MenuItem("Take screenshot", lambda: tray_take_screenshot(self)))
        menu_items.append(pystray.Menu.SEPARATOR)
        menu_items.append(pystray.MenuItem("Close", lambda: close_clicked(self)))

        self.icon_thread = pystray.Icon(
            'Uma Launcher',
            Image.open("favicon.ico"),
            menu=pystray.Menu(*menu_items)
        )

    def run(self):
        self.icon_thread.run()
    
    def stop(self):
        self.icon_thread.stop()

def close_clicked(tray: UmaTray):
    tray.threader.stop()

def tray_take_screenshot(tray):
    try:
        img = get_screenshot()
    except OSError:
        logger.error("Couldn't get screenshot.")
        util.show_alert_box("Failed to take screenshot.", "Couldn't take screenshot of the game.")
        return
    output = BytesIO()
    img.convert("RGB").save(output, "BMP")
    image_data = output.getvalue()[14:]
    output.close()
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(win32clipboard.CF_DIB, image_data)
    win32clipboard.CloseClipboard()
