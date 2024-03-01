## Handles English patch

import util
import os
from loguru import logger

def get_patcher_path(settings):
    # Check if exe already exists
    exe_path = util.get_appdata("CarotenePatcher.exe")

    logger.debug(f"Exe path: {exe_path}")
    if not os.path.exists(exe_path):
        logger.debug("Downloading patcher")

        latest_release = util.fetch_latest_github_release("KevinVG207", "Uma-Carotene-English-Patch", prerelease=settings['s_beta_optin'])

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

def patch(threader):
    settings = threader.settings
    umaserver = threader.umaserver

    logger.debug("In English Patch code")
    if not settings["s_enable_english_patch"]:
        return
    
    exe_path = get_patcher_path(settings)
    
    # Run the patcher
    dll_name = "version.dll"
    for dll, selected in settings['s_english_patch_dll'].items():
        if selected:
            dll_name = dll
            break
    command = f"\"{exe_path}\" -U -p {dll_name}"

    logger.debug(f"Running patcher with command: {command}")
    logger.info("Starting English patcher")

    umaserver.reset_en_patch()
    os.system(command)

    if umaserver.en_patch_success:
        logger.info("English patcher succeeded")
    else:
        logger.error("English patcher failed")
        util.show_error_box("Patch Error", "English patcher failed.", custom_traceback=umaserver.en_patch_error)

def customize(threader):
    exe_path = get_patcher_path(threader.settings)
    command = f"\"{exe_path}\" -c"
    logger.debug(f"Running patcher with command: {command}")
    logger.info("Opening patcher customization")
    os.system(command)
