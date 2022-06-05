import os
import json
import copy
from loguru import logger

SETTINGS_FILE = "umasettings.json"
DEFAULT_SETTINGS = {
    "dmm_path": "c:\\Program Files\\DMMGamePlayer\\",
    "autoclose_dmm": True,
    "tray_items": {
        "Auto-resize": True,
        "Discord rich presence": True
    }
}

loaded_settings = dict()


def save_settings():
    global loaded_settings
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(loaded_settings, f, ensure_ascii=False, indent=2)


def load_settings():
    global loaded_settings
    logger.info("Loading settings file.")
    with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
        try:
            loaded_settings = json.load(f)

            # Ensure that the default settings keys actually exist.
            for default_setting in DEFAULT_SETTINGS:
                if isinstance(DEFAULT_SETTINGS[default_setting], dict):
                    if default_setting not in loaded_settings:
                        logger.warning(f"Adding missing setting: {default_setting}")
                        loaded_settings[default_setting] = DEFAULT_SETTINGS[default_setting]
                    else:
                        for default_subsetting in DEFAULT_SETTINGS[default_setting]:
                            if default_subsetting not in loaded_settings[default_setting]:
                                logger.warning(f"Adding missing subsetting: {default_setting}[{default_subsetting}]")
                                loaded_settings[default_setting][default_subsetting] = DEFAULT_SETTINGS[default_setting][default_subsetting]
                elif default_setting not in loaded_settings:
                    logger.warning(f"Adding missing setting: {default_setting}")
                    loaded_settings[default_setting] = DEFAULT_SETTINGS[default_setting]
            tmp_loaded_settings = copy.deepcopy(loaded_settings)
            for setting in loaded_settings:
                if isinstance(loaded_settings[setting], dict):
                    for sub_setting in loaded_settings[setting]:
                        if sub_setting not in DEFAULT_SETTINGS[setting]:
                            logger.warning(f"Removing unknown setting: {setting}[{sub_setting}]")
                            del tmp_loaded_settings[setting][sub_setting]
                elif setting not in DEFAULT_SETTINGS:
                    logger.warning(f"Removing unknown setting: {setting}")
                    del tmp_loaded_settings[setting]
            loaded_settings = tmp_loaded_settings
            save_settings()
        
        except (json.JSONDecodeError, TypeError):
            logger.info("Failed to load settings file. Loading default settings instead.")
            loaded_settings = DEFAULT_SETTINGS


def get_tray_setting(key: str) -> bool:
    global loaded_settings
    if key in loaded_settings["tray_items"]:
        return loaded_settings["tray_items"][key]
    else:
        logger.error(f"Unknown key wanted from tray items: {key}")
        return None


def set_tray_setting(key: str, value: bool):
    global loaded_settings
    if key in loaded_settings["tray_items"]:
        logger.info(f"Saving tray setting. Key: {key}\tValue: {value}")
        loaded_settings["tray_items"][key] = value
        save_settings()
    else:
        logger.error(f"Unknown key passed to tray items. Key: {key}\tValue: {value}")


def get(key: str):
    global loaded_settings
    if key in loaded_settings:
        return loaded_settings[key]
    else:
        logger.error(f"Unknown key wanted from settings: {key}")
        return None


def set(key: str, value):
    global loaded_settings
    if key in loaded_settings:
        logger.info(f"Saving setting. Key: {key}\tValue: {value}")
        loaded_settings[key] = value
        save_settings()
    else:
        logger.error(f"Unknown key passed to settings. Key: {key}\tValue: {value}")


# Load settings on import.
if not os.path.exists(SETTINGS_FILE):
    logger.info("Settings file not found. Starting with default settings.")
    loaded_settings = DEFAULT_SETTINGS
    save_settings()
else:
    load_settings()

logger.info(loaded_settings)