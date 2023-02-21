import os
import json
import copy
import tkinter
from tkinter import filedialog
from loguru import logger
import util

ORIENTATION_DICT = {
    True: 'portrait',
    False: 'landscape',
    'portrait': True,
    'landscape': False,
}

class Settings():

    settings_file = "umasettings.json"
    default_settings = {
        "autoclose_dmm": True,
        "tray_items": {
            "Lock game window": True,
            "Discord rich presence": True,
            "Automatic training event helper": True,
        },
        "game_install_path": "%userprofile%/Umamusume",
        "game_position": {
            "portrait": None,
            "landscape": None
        },
        "browser_position": None
    }

    loaded_settings = {}
    unpatch_dmm = False

    def __init__(self, threader):
        self.threader = threader
        # Load settings on import.
        if not os.path.exists(self.settings_file):
            logger.info("Settings file not found. Starting with default settings.")
            self.loaded_settings = self.default_settings
            self.save_settings()
        else:
            self.load_settings()
        
        # Check if the game install path is correct.
        for folder_tuple in [
            ('game_install_path', "umamusume.exe", "Please choose the game's installation folder. (Where umamusume.exe is located.)")
        ]:
            self.make_user_choose_folder(*folder_tuple)

        logger.info(self.loaded_settings)

    def make_user_choose_folder(self, setting, file_to_verify, title):
        while not os.path.exists(os.path.join(self.get(setting), file_to_verify)):
            root = tkinter.Tk()
            root.withdraw()
            file_path = filedialog.askdirectory(title=title)
            if file_path:
                self.set(setting, file_path)
            root.destroy()

    def save_settings(self):
        with open(self.settings_file, 'w', encoding='utf-8') as f:
            json.dump(self.loaded_settings, f, ensure_ascii=False, indent=2)


    def load_settings(self):
        logger.info("Loading settings file.")
        with open(self.settings_file, 'r', encoding='utf-8') as f:
            try:
                self.loaded_settings = json.load(f)

                # Ensure that the default settings keys actually exist.
                for default_setting, setting_value in self.default_settings.items():
                    if isinstance(setting_value, dict):
                        if default_setting not in self.loaded_settings:
                            logger.warning(f"Adding missing setting: {default_setting}")
                            self.loaded_settings[default_setting] = setting_value
                        else:
                            for default_subsetting in self.default_settings[default_setting]:
                                if default_subsetting not in self.loaded_settings[default_setting]:
                                    logger.warning(f"Adding missing subsetting: {default_setting}[{default_subsetting}]")
                                    self.loaded_settings[default_setting][default_subsetting] = self.default_settings[default_setting][default_subsetting]
                    elif default_setting not in self.loaded_settings:
                        logger.warning(f"Adding missing setting: {default_setting}")
                        self.loaded_settings[default_setting] = self.default_settings[default_setting]
                tmp_loaded_settings = copy.deepcopy(self.loaded_settings)
                for setting in self.loaded_settings:
                    if isinstance(self.loaded_settings[setting], dict):
                        for sub_setting in self.loaded_settings[setting]:
                            if sub_setting not in self.default_settings[setting]:
                                logger.warning(f"Unknown setting found: {setting}[{sub_setting}]")
                                # del tmp_loaded_settings[setting][sub_setting]

                    elif setting not in self.default_settings:
                        logger.warning(f"Unknown setting found: {setting}")
                        # del tmp_loaded_settings[setting]

                        # Unpatch DMM if needed.
                        if setting == 'dmm_path':
                            logger.info("Found remnants of DMM patcher. Unpatching DMM.")
                            self.unpatch_dmm = tmp_loaded_settings[setting]
                            del tmp_loaded_settings[setting]
                            if 'Patch DMM' in tmp_loaded_settings['tray_items']:
                                del tmp_loaded_settings['tray_items']['Patch DMM']

                self.loaded_settings = tmp_loaded_settings
                self.save_settings()
            
            except (json.JSONDecodeError, TypeError):
                logger.info("Failed to load settings file. Loading default settings instead.")
                self.loaded_settings = self.default_settings


    def get_tray_setting(self, key: str) -> bool:
        if key in self.loaded_settings["tray_items"]:
            return self.loaded_settings["tray_items"][key]
        else:
            logger.error(f"Unknown key wanted from tray items: {key}")
            return None


    def set_tray_setting(self, _, item):
        key = item.text
        value = not item.checked
        if key in self.loaded_settings["tray_items"]:
            logger.info(f"Saving tray setting. Key: {key}\tValue: {value}")
            self.loaded_settings["tray_items"][key] = value
            self.save_settings()
        else:
            logger.error(f"Unknown key passed to tray items. Key: {key}\tValue: {value}")


    def get(self, key: str):
        if key in self.loaded_settings:
            value = self.loaded_settings[key]
            if isinstance(value, str):
                return os.path.expandvars(value)
            return value
        else:
            logger.error(f"Unknown key wanted from settings: {key}")
            return None


    def set(self, key: str, value):
        if key in self.loaded_settings:
            logger.info(f"Saving setting. Key: {key}\tValue: {value}")
            self.loaded_settings[key] = value
            self.save_settings()
        else:
            logger.error(f"Unknown key passed to settings. Key: {key}\tValue: {value}")

    def save_game_position(self, pos, portrait):
        if util.is_minimized(self.threader.screenstate.game_handle):
            logger.warning(f"Game minimized, cannot save {ORIENTATION_DICT[portrait]} position: {pos}")
            return

        if (pos[0] == -32000 and pos[1] == -32000):
            logger.warning(f"Game minimized, cannot save {ORIENTATION_DICT[portrait]} position: {pos}")
            return

        orientation_key = ORIENTATION_DICT[portrait]
        self.loaded_settings['game_position'][orientation_key] = pos
        logger.info(f"Saving {orientation_key} position: {pos}")
        self.save_settings()

    def load_game_position(self, portrait):
        orientation_key = ORIENTATION_DICT[portrait]
        return self.loaded_settings['game_position'][orientation_key]
