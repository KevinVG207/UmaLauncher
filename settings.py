import os
import json
import copy
from enum import Enum
from loguru import logger

ORIENTATION_DICT = {
    True: 'portrait',
    False: 'landscape',
    'portrait': True,
    'landscape': False,
}

class Settings():

    settings_file = "umasettings.json"
    default_settings = {
        "dmm_path": "c:\\Program Files\\DMMGamePlayer",
        "autoclose_dmm": True,
        "tray_items": {
            "Discord rich presence": True,
            "Patch DMM": True,
            "Intercept packets": False,
        },
        "game_install_path": "%userprofile%\\Umamusume",
        "game_position": {
            "portrait": None,
            "landscape": None
        },
        "browser_position": None
    }

    loaded_settings = {}

    def __init__(self):
        # Load settings on import.
        if not os.path.exists(self.settings_file):
            logger.info("Settings file not found. Starting with default settings.")
            self.loaded_settings = self.default_settings
            self.save_settings()
        else:
            self.load_settings()

        logger.info(self.loaded_settings)

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
                                logger.warning(f"Removing unknown setting: {setting}[{sub_setting}]")
                                del tmp_loaded_settings[setting][sub_setting]
                    elif setting not in self.default_settings:
                        logger.warning(f"Removing unknown setting: {setting}")
                        del tmp_loaded_settings[setting]
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
        orientation_key = ORIENTATION_DICT[portrait]
        self.loaded_settings['game_position'][orientation_key] = pos
        logger.info(f"Saving {orientation_key} position: {pos}")
        self.save_settings()

    def load_game_position(self, portrait):
        orientation_key = ORIENTATION_DICT[portrait]
        return self.loaded_settings['game_position'][orientation_key]
