import os
import json
from loguru import logger

SETTINGS_FILE = "umasettings.json"
DEFAULT_SETTINGS = {
    "nordvpn_path": "c:\\Program Files\\NordVPN\\",
    "tray_items": {
        "Auto-resize": True,
        "Discord rich presence": True,
        "NordVPN autolaunch": False
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
                if default_setting not in loaded_settings:
                    loaded_settings[default_setting] = DEFAULT_SETTINGS[default_setting]
        
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
        logger.info(f"Saving setting. Key: {key}\tValue: {value}")
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


# Load settings on import.
if not os.path.exists(SETTINGS_FILE):
    logger.info("Settings file not found. Starting with default settings.")
    loaded_settings = DEFAULT_SETTINGS
    save_settings()
else:
    load_settings()

print(loaded_settings)