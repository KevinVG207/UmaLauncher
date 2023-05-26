import urllib.request
import subprocess
import time
import os
import sys
import threading
from urllib.parse import urlparse
import requests
from loguru import logger
import dmm
import util
import gui

VERSION = "1.4.6"

def parse_version(version_string: str):
    """Convert version string to tuple."""
    if not version_string:
        return (0,0,0)
    return tuple(int(num) for num in version_string.split("."))

def vstr(version_tuple: tuple):
    """Convert version tuple to string."""
    return ".".join([str(num) for num in version_tuple])


def upgrade(umasettings):
    """Upgrades old versions."""
    script_version = parse_version(VERSION)
    skip_version = parse_version(umasettings.get("_skip_update", None))
    settings_version = parse_version(umasettings.get("_version", None))
    logger.info(f"Script version: {vstr(script_version)}, Settings version: {vstr(settings_version)}")

    # Auto-update
    if not auto_update(umasettings, script_version, skip_version):
        sys.exit()

    # Update settings file
    if script_version < settings_version:
        logger.warning("Umasettings are for a newer version.")
    #     return umasettings

    if settings_version <= (0,9,0):
        # Remove DMM patch
        logger.info("Need to upgrade settings past 0.9.0 - Attempting to unpatch DMM.")
        # Unpatch DMM if needed.
        if "dmm_path" in umasettings:
            dmm.unpatch_dmm(umasettings['dmm_path'])
            del umasettings['dmm_path']
        if 'Patch DMM' in umasettings['tray_items']:
            del umasettings['tray_items']['Patch DMM']
        logger.info("Completed upgrade.")

    if settings_version <= (1,1,4):
        logger.info("Need to upgrade settings past 1.1.4 - Upgrading.")
        if "Automatic training event helper" in umasettings["tray_items"]:
            del umasettings["tray_items"]["Automatic training event helper"]
        logger.info("Completed upgrade.")

    # If upgraded at all
    if script_version > settings_version:
        if '_skip_update' in umasettings:
            del umasettings['_skip_update']
        umasettings = {'_skip_update': None, **umasettings}

    # Upgrade settings version no.
    if '_version' in umasettings:
        del umasettings['_version']
    umasettings = {'_version': vstr(script_version), **umasettings}
    return umasettings


def auto_update(umasettings, script_version, skip_version):
    logger.info("Checking for updates...")

    # Don't update if we're running from script.
    if util.is_script:
        logger.info("Skipping auto-update because you are running the script version.")
        return True

    # Check if we're coming from an update
    if os.path.exists("update.tmp"):
        os.remove("update.tmp")
        util.show_info_box("Update complete!", f"Uma Launcher updated successfully.<br>To see what's new, <a href=\"https://github.com/KevinVG207/UmaLauncher/releases/tag/v{vstr(script_version)}\">click here</a>.")

    response = util.do_get_request("https://api.github.com/repos/KevinVG207/UmaLauncher/releases", error_message="Could not check for updates on Github. Please check your internet connection.", ignore_timeout=True)
    if not response:
        return True
    response_json = response.json()

    allow_prerelease = umasettings.get("beta_optin", False)
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
    if release_version <= skip_version:
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
    if choice == 2:
        umasettings['_skip_update'] = vstr(release_version)
        return True

    # Yes
    # Create updater thread
    update_object = Updater(latest_release['assets'])
    update_thread = threading.Thread(target=update_object.run)
    update_thread.start()

    # Show updater window
    gui.show_widget(gui.UmaUpdatePopup, update_object)

    logger.debug("Update window closed: Update failed.")
    if os.path.exists(util.get_relative("update.tmp")):
        os.remove(util.get_relative("update.tmp"))
    util.show_error_box("Update failed.", "Could not update. Please check your internet connection.<br>Uma Launcher will now close.")
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
                    logger.info(f"Attempting to download from {download_url}")
                    urllib.request.urlretrieve(download_url, "UmaLauncher.exe_")
                    # Start a process that starts the new exe.
                    logger.info("Download complete, now trying to open the new launcher.")
                    open(util.get_relative("update.tmp"), "wb").close()
                    sub = subprocess.Popen("taskkill /F /IM UmaLauncher.exe && move /y .\\UmaLauncher.exe .\\UmaLauncher.old && move /y .\\UmaLauncher.exe_ .\\UmaLauncher.exe && .\\UmaLauncher.exe", shell=True)
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
