import pystray
import util
from loguru import logger
from PIL import Image
import training_tracker

class UmaTray():
    menu_items = None
    icon_thread = None
    threader = None

    def __init__(self, threader):
        self.threader = threader
        menu_items = [
            pystray.MenuItem(
                menu_item,
                self.threader.settings.set_tray_setting,
                checked=lambda item: self.threader.settings.get_tray_setting(item.text)
            ) for menu_item in self.threader.settings.default_settings["tray_items"]
        ]
        menu_items.append(
            pystray.MenuItem(
                "Set Browser Type",
                pystray.Menu(
                    lambda: (
                        pystray.MenuItem(
                            browser,
                            self.threader.settings.set_browser,
                            checked=self.threader.settings.get_browser,
                            radio=True)
                        for browser in self.threader.settings.get_browsers()
                    )
                )
            )
        )
        menu_items.append(pystray.MenuItem("Maximize + center game", self.threader.windowmover.try_maximize))
        menu_items.append(pystray.MenuItem("Take screenshot", self.threader.screenstate.screenshot_to_clipboard))
        menu_items.append(pystray.MenuItem("Export Training CSV", lambda: training_tracker.training_csv_dialog()))
        menu_items.append(pystray.Menu.SEPARATOR)
        menu_items.append(pystray.MenuItem("Close", lambda: close_clicked(self)))

        self.icon_thread = pystray.Icon(
            'Uma Launcher',
            Image.open(util.get_asset("favicon.ico")),
            menu=pystray.Menu(*menu_items)
        )

    def run(self):
        self.icon_thread.run()

    def stop(self):
        self.icon_thread.stop()

def close_clicked(tray: UmaTray):
    tray.threader.stop()
