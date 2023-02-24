import urllib.request
import subprocess
import time
import sys
import os
import threading
from urllib.parse import urlparse
import requests
import easygui
from loguru import logger
import dmm
import util

VERSION = "1.1.0"

def parse_version(version_string: str):
    """Convert version string to tuple."""
    if not version_string:
        return (0,0,0)
    return tuple(int(num) for num in version_string.split("."))

def vstr(version_tuple: tuple):
    """Convert version tuple to string."""
    return ".".join([str(num) for num in version_tuple])


def upgrade(umasettings: dict):
    """Upgrades old versions."""
    script_version = parse_version(VERSION)
    skip_version = parse_version(umasettings.get("_skip_update", None))
    settings_version = parse_version(umasettings.get("_version", None))
    logger.info(f"Script version: {vstr(script_version)}, Settings version: {vstr(settings_version)}")

    # Auto-update
    auto_update(umasettings, script_version, skip_version)

    # Update settings file
    if script_version < settings_version:
        logger.warning("Umasettings are for a newer version. Skipping upgrade.")
        return umasettings

    if settings_version < (0,9,1):
        # Remove DMM patch
        logger.info("Found settings before 0.9.1 - Attempting to unpatch DMM.")
        # Unpatch DMM if needed.
        if "dmm_path" in umasettings:
            dmm.unpatch_dmm(umasettings['dmm_path'])
            del umasettings['dmm_path']
        if 'Patch DMM' in umasettings['tray_items']:
            del umasettings['tray_items']['Patch DMM']
        logger.info("Completed upgrade to version 0.9.1")

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
    # Don't update if we're running from script.
    if not hasattr(sys, "_MEIPASS"):
        logger.info("Skipping auto-update because you are running the script version.")
        return
    
    # Check if we're coming from an update
    if os.path.exists("update.tmp"):
        os.remove("update.tmp")
        easygui.msgbox(
            title="Update complete!",
            msg="Uma Launcher updated successfully."
        )

    response = requests.get("https://api.github.com/repos/KevinVG207/UmaLauncher/releases")
    if not response.ok:
        logger.error("Could not fetch latest release.")
        return
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
        util.show_alert_box("Update Error", "Could not update. Please contact the developer if this reoccurs.")
        return

    release_version = parse_version(latest_release['tag_name'][1:])

    # Check if update is needed
    if release_version <= script_version:
        # No need to update
        return

    # Newer version found
    # Return if skipped
    if release_version <= skip_version:
        return

    # Ask user to update
    choice = easygui.indexbox(
        title=f"New version: {vstr(release_version)}",
        msg="A new version of Uma Launcher was found. Update now?",
        choices=("Yes", "No", "Skip this version"),
        default_choice="Yes",
        cancel_choice="No"
    )

    # No
    if choice == 1:
        return

    # Skip
    if choice == 2:
        umasettings['_skip_update'] = vstr(release_version)
        return

    # Yes
    process = threading.Thread(target=show_update_box)
    process.start()
    for asset in latest_release['assets']:
        if asset['name'] == "UmaLauncher.exe":
            # Found the correct file, download and overwrite
            download_url = asset['browser_download_url']
            parsed = urlparse(download_url)
            if parsed.scheme != "https":
                logger.error(f"Download URL is not HTTPS! {download_url}")
                util.show_alert_box("Update failed.", "Please contact the developer if this error reoccurs.")
                return
            try:
                logger.info(f"Attempting to download from {download_url}")
                urllib.request.urlretrieve(download_url, "UmaLauncher.exe_")
                # Start a process that starts the new exe.
                logger.info("Download complete, now trying to open the new launcher.")
                open("update.tmp", "wb").close()
                subprocess.Popen("taskkill /F /IM UmaLauncher.exe && mv ./UmaLauncher.exe_ ./UmaLauncher.exe && .\\UmaLauncher.exe", shell=True)
                while True:
                    time.sleep(1)
            except Exception as e:
                if os.path.exists("update.tmp"):
                    os.remove("update.tmp")
                logger.error(e)
                util.show_alert_box("Error downloading update.", "Could not download the latest version. Check your internet connection.")
                return


def show_update_box():
    easygui.msgbox(
        title="Now updating",
        msg="Please wait while Uma Launcher updates..."
    )
    while True:
        time.sleep(1)
