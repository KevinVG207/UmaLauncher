import os
import util
from loguru import logger

def start():
    logger.info("Launching Uma Musume via DMM.")
    os.system("Start dmmgameplayer://play/GCL/umamusume/cl/win")

def get_dmm_handle():
    for window_title in ['ストアトップ | 一般', 'DMM GAME PLAYER', 'マイゲーム']:
        dmm_handle = util.get_window_handle(window_title, type=util.LAZY)
        if dmm_handle:
            return dmm_handle
    return None