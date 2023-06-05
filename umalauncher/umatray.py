import pystray
import util
from loguru import logger
from PIL import Image

class UmaTray():
    menu_items = None
    icon_thread = None
    threader = None

    def __init__(self, threader):
        self.threader = threader
        menu_items = []
        menu_items.append(pystray.MenuItem("Lock game window", lambda: self.flip_setting("s_lock_game_window"), checked=lambda _: self.check_setting("s_lock_game_window")))
        menu_items.append(pystray.Menu.SEPARATOR)
        menu_items.append(pystray.MenuItem("Preferences", lambda: self.show_preferences()))
        menu_items.append(pystray.MenuItem("Maximize + center game", self.threader.windowmover.try_maximize))
        menu_items.append(pystray.MenuItem("Take screenshot", self.threader.screenstate.screenshot_to_clipboard))
        menu_items.append(pystray.MenuItem("Export Training CSV", lambda: self.show_training_csv_dialog()))
        menu_items.append(pystray.Menu.SEPARATOR)
        menu_items.append(pystray.MenuItem("Close", lambda: close_clicked(self)))
        # if util.is_debug:
        #     menu_items.append(pystray.Menu.SEPARATOR)
            # menu_items.append(pystray.MenuItem("Debug", lambda: self.threader.carrotjuicer.helper_table.debug_change_settings()))

        self.icon_thread = pystray.Icon(
            'Uma Launcher',
            Image.open(util.get_asset("favicon.ico")),
            menu=pystray.Menu(*menu_items)
        )

    def run(self):
        self.icon_thread.run()
    
    def run_with_catch(self):
        try:
            self.run()
        except Exception:
            util.show_error_box("Critical Error", "Uma Launcher has encountered a critical error and will now close.")
            self.threader.stop()

    def stop(self):
        self.icon_thread.stop()

    def flip_setting(self, setting_name):
        self.threader.settings[setting_name] = not self.threader.settings[setting_name]

    def check_setting(self, setting_name):
        return self.threader.settings[setting_name]

    def show_preferences(self):
        self.threader.show_preferences = True

    def show_helper_table_dialog(self):
        self.threader.show_helper_table_dialog = True

    def show_training_csv_dialog(self):
        self.threader.show_training_csv_dialog = True

def close_clicked(tray: UmaTray):
    tray.threader.stop()
