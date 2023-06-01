import shutil
import os
import util
from loguru import logger


def unpatch_dmm(dmm_path):
    logger.info("Attempting to unpatch DMM.")
    resources_path = os.path.join(dmm_path, "resources")
    if os.path.isdir(resources_path):
        cwd_before = os.getcwd()
        os.chdir(resources_path)
        if os.path.isfile("app.asar.org"):
            logger.debug("Reverting app.asar.")
            if os.path.isfile("app.asar"):
                os.remove("app.asar")
            shutil.copy("app.asar.org", "app.asar")
            os.remove("app.asar.org")
        if os.path.isdir("tmp"):
            logger.debug("Removing tmp folder.")
            shutil.rmtree("tmp")
        if os.path.isfile("app.hash"):
            logger.debug("Removing hash file.")
            os.remove("app.hash")
        os.chdir(cwd_before)
    else:
        logger.warning("Could not find DMM folder to unpatch DMM.")


def start():
    logger.info("Launching Uma Musume via DMM.")
    os.system("Start dmmgameplayer://play/GCL/umamusume/cl/win")

def get_dmm_handle():
    for window_title in ['DMM GAME PLAYER', 'マイゲーム']:
        dmm_handle = util.get_window_handle(window_title, type=util.LAZY)
        if dmm_handle:
            return dmm_handle
    return None