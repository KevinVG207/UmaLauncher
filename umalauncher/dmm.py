import os
import util
from loguru import logger

def start():
    logger.info("Launching Uma Musume via DMM.")
    os.system("Start dmmgameplayer://play/GCL/umamusume/cl/win")

def get_dmm_handle():
    dmm_handle = util.get_window_handle("DMMGamePlayer.exe", type=util.EXEC_MATCH)
    if dmm_handle:
        return dmm_handle
    return None