import urllib.request
import subprocess
import time
import os
import shutil
import threading
import sys
from urllib.parse import urlparse
from loguru import logger
import util
import gui
import glob

VERSION = "1.15.1"

def parse_version(version_string: str):
    """Convert version string to tuple."""
    if not version_string:
        return (0,0,0)
    return tuple(int(num) for num in version_string.split("."))

def vstr(version_tuple: tuple):
    """Convert version tuple to string."""
    return ".".join([str(num) for num in version_tuple])


def upgrade(umasettings, raw_settings):
    """Upgrades old versions."""
    script_version = parse_version(VERSION)
    settings_version = parse_version(umasettings["version"])
    logger.info(f"Script version: {vstr(script_version)}, Settings version: {vstr(settings_version)}")

    # Update settings file
    if script_version < settings_version:
        logger.warning("Umasettings are for a newer version.")

    # PERFORM UPGRADE FROM PRE-1.5.0
    if "_version" in raw_settings:
        logger.info("Attempting to upgrade settings from pre-1.5.0...")

        # Create a backup of the old settings file, just in case
        if not os.path.exists("umasettings.json.bak"):
            shutil.copy("umasettings.json", "umasettings.json.bak")

        pre_1_5_0_update_dict = {
            "_unique_id": "unique_id",
            "save_packet": "save_packets",
            "beta_optin": "beta_optin",
            "debug_mode": "debug_mode",
            "autoclose_dmm": "autoclose_dmm",
            "browser_position": "browser_position",
            "selected_browser": "selected_browser",
            "game_install_path": "game_install_path",
            "training_helper_table_preset": "training_helper_table_preset",
            "training_helper_table_preset_list": "training_helper_table_preset_list",
        }

        pre_1_5_0_update_dict_2 = {
            ("tray_items", "Lock game window"): "lock_game_window",
            ("tray_items", "Discord rich presence"): "discord_rich_presence",
            ("tray_items", "Enable CarrotJuicer"): "enable_carrotjuicer",
            ("tray_items", "Track trainings"): "track_trainings",
            ("game_position", "portrait"): "game_position_portrait",
            ("game_position", "landscape"): "game_position_landscape",
        }

        for key, value in pre_1_5_0_update_dict.items():
            if key in raw_settings:
                umasettings[value] = raw_settings[key]
        
        for key, value in pre_1_5_0_update_dict_2.items():
            if key[0] in raw_settings and key[1] in raw_settings[key[0]]:
                umasettings[value] = raw_settings[key[0]][key[1]]
    
    if settings_version <= (1, 12, 1):
        logger.info("Upgrading settings from <=1.12.1. Moving files to appdata folder.")
        # Transfer relative files to appdata folder.
        to_move = [
            "umasettings.json",
            "lock.pid",
            "update.tmp",
            "log.log",
            "training_logs",
            "ovpn.log",
            "chr_profile",
            "edg_profile"
        ]
        logzips = glob.glob("*.log.zip")
        to_move += logzips

        if not util.is_script:
            # Add the old exe
            to_move.append(sys.argv[0][:-3]+"old")

        for path in to_move:
            rel_path = util.get_relative(path)
            if not os.path.exists(rel_path):
                continue

            if path == 'log.log':
                path = 'pre-appdata.log'

            shutil.move(rel_path, util.get_appdata(path))
        
        logger.info("Moving complete.")
    
    if settings_version <= (1, 14, 3):
        patcher_exe = util.get_appdata("CarotenePatcher.exe")
        if os.path.exists(patcher_exe):
            os.remove(patcher_exe)

    # If upgraded at all
    if script_version > settings_version:
        umasettings['skip_update'] = None

    # Upgrade settings version no.
    umasettings["version"] = vstr(script_version)

def force_update(umasettings):
    result = auto_update(umasettings, force=True)
    if result:
        util.show_info_box("No updates found", "You are already using the latest version.")

def auto_update(umasettings, force=False):
    logger.info("Checking for updates...")

    script_version = parse_version(VERSION)
    skip_version = parse_version(umasettings["skip_update"])

    # Don't update if we're running from script.
    if util.is_script:
        logger.info("Skipping auto-update because you are running the script version.")
        return True

    # Check if we're coming from an update
    if os.path.exists("update.tmp"):
        os.remove("update.tmp")
        util.show_info_box("Update complete!", f"Uma Launcher updated successfully to v{vstr(script_version)}.<br>To see what's new, <a href=\"https://github.com/KevinVG207/UmaLauncher/releases/tag/v{vstr(script_version)}\">click here</a>.")

    response = util.do_get_request("https://umapyoi.net/api/v1/github/KevinVG207/UmaLauncher/releases", error_message="Could not check for updates. Please check your internet connection.", ignore_timeout=True)
    if not response:
        return True
    response_json = response.json()

    allow_prerelease = umasettings["beta_optin"]
    latest_release = None
    for release in response_json:
        if release.get('draft', False):
            continue
        if release.get('prerelease', False) and not allow_prerelease:
            continue
        latest_release = release
        break
    if not latest_release:
        logger.error("Could not find a release in the API response?")
        util.show_error_box("Update Error", "Could not update. Please contact the developer if this reoccurs.")
        return True

    release_version = parse_version(latest_release['tag_name'][1:])
    logger.info(f"Latest release: {vstr(release_version)}")

    # Check if update is needed
    if release_version <= script_version:
        # No need to update
        return True

    # Newer version found
    # Return if skipped
    if not force and release_version <= skip_version:
        return True

    logger.info("Newer version found. Asking user to update.")

    choice = [1]  # Default to no
    gui.show_widget(gui.UmaUpdateConfirm, latest_release, vstr(release_version), choice)
    choice = choice[-1]

    logger.debug(f"User choice: {choice}")

    # No
    if choice == 1:
        return True

    # Skip
    elif choice == 2:
        umasettings['skip_update'] = vstr(release_version)
        return True

    # Yes
    # Remove the lock file.
    lock_path = util.get_appdata("lock.pid")
    if os.path.exists(lock_path):
        os.remove(lock_path)

    # Create updater thread
    update_object = Updater(latest_release['assets'])
    update_thread = threading.Thread(target=update_object.run)
    update_thread.start()

    # Show updater window
    gui.show_widget(gui.UmaUpdatePopup, update_object)

    logger.debug("Update window closed: Update failed.")
    if os.path.exists(util.get_appdata("update.tmp")):
        os.remove(util.get_appdata("update.tmp"))
    util.show_warning_box("Update failed.", "Could not update. Please check your internet connection.<br>Uma Launcher will now close.")
    return False


class Updater():
    assets = None
    close_me = False
    def __init__(self, assets):
        self.assets = assets

    def run(self):
        logger.debug("Updater thread started.")
        for asset in self.assets:
            if asset['name'] == "UmaLauncher.exe":
                # Found the correct file, download and overwrite
                download_url = asset['browser_download_url']
                parsed = urlparse(download_url)
                if parsed.scheme != "https":
                    logger.error(f"Download URL is not HTTPS! {download_url}")
                    util.show_error_box("Update failed.", "Please contact the developer if this error reoccurs.")
                    self.close_me = True
                    return
                try:
                    path_to_exe = sys.argv[0]
                    exe_file = os.path.basename(path_to_exe)
                    without_ext = os.path.splitext(exe_file)[0]
                    old_file = without_ext + ".old"
                    old_path = util.get_appdata(old_file)
                    tmp_file = without_ext + ".tmp"
                    tmp_path = util.get_appdata(tmp_file)

                    logger.info(f"Attempting to download from {download_url}")
                    urllib.request.urlretrieve(download_url, tmp_path)
                    # Start a process that starts the new exe.
                    logger.info("Download complete, now trying to open the new launcher.")
                    open(util.get_appdata("update.tmp"), "wb").close()
                    sub = subprocess.Popen(f"taskkill /F /IM \"{exe_file}\" && move /y \".\\{exe_file}\" \"{old_path}\" && move /y \"{tmp_path}\" \".\\{exe_file}\" && \".\\{exe_file}\"", shell=True)
                    while True:
                        # Check if subprocess is still running
                        if sub.poll() is not None:
                            # Subprocess is done, but we should never reach this point.
                            self.close_me = True
                            return
                        time.sleep(1)
                except Exception as e:
                    logger.error(e)
                    self.close_me = True
                    return
