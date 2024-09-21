## Handles English patch

import util
import os
from loguru import logger
import win32gui
import subprocess
import gui
import time

def get_patcher_path(settings):
    # Check if exe already exists
    exe_path = util.get_appdata("CarotenePatcher.exe")

    logger.debug(f"Exe path: {exe_path}")
    if not os.path.exists(exe_path):
        logger.debug("Downloading patcher")

        latest_release = util.fetch_latest_github_release("KevinVG207", "Uma-Carotene-English-Patch", prerelease=settings['beta_optin'])

        # Find the asset
        dl_asset = None
        for asset in latest_release['assets']:
            if asset['name'] == "CarotenePatcher.exe":
                dl_asset = asset
                break
        
        if not dl_asset:
            util.show_error_box("Patch Error", "Could not find the patcher asset in GitHub release. Please contact the developer.")
            return

        url = dl_asset['browser_download_url']

        logger.debug(f"Downloading patcher from {url}")

        util.download_file(url, exe_path)
    
    logger.debug("Patcher exe exists.")
    return exe_path

def run_patcher_and_wait(command, umaserver, message="", no_popup=False):
    umaserver.reset_en_patch()
    logger.debug(f"Running patcher with command: {command}")
    logger.info(message)
    subprocess.Popen(command, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
    if not no_popup:
        gui.show_widget(gui.UmaBorderlessPopup, "Carotene Patcher", f"{message}<br>Please wait...", None, umaserver.en_patch_success)
    while len(umaserver.en_patch_success) == 0:
        time.sleep(0.2)

def unpatch(threader):
    if threader.screenstate.game_seen and threader.screenstate.game_handle and win32gui.IsWindow(threader.screenstate.game_handle):
        util.show_warning_box("Unpatch Error", "Please close the game before unpatching.")
        return

    exe_path = get_patcher_path(threader.settings)
    command = f"\"{exe_path}\" -u -U"
    
    run_patcher_and_wait(command, threader.umaserver, "Removing English Patch.")
