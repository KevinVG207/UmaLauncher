from elevate import elevate
elevate()

import threading
from loguru import logger
import settings
import carrotjuicer
import umatray
import screenstate
import windowmover
import win32api

class Threader():
    settings = None
    tray = None
    carrotjuicer = None
    windowmover = None
    screenstate = None  # Screen states for rich presence (+ get screenshot?)

    def __init__(self):
        self.settings = settings.Settings()

        self.screenstate = screenstate.ScreenStateHandler(self)
        threading.Thread(target=self.screenstate.run).start()

        self.carrotjuicer = carrotjuicer.CarrotJuicer(self)
        threading.Thread(target=self.carrotjuicer.run).start()

        self.windowmover = windowmover.WindowMover(self)
        threading.Thread(target=self.windowmover.run).start()

        self.tray = umatray.UmaTray(self)
        threading.Thread(target=self.tray.run).start()

        win32api.SetConsoleCtrlHandler(self.stop_signal, True)

    def stop_signal(self, *_):
        self.stop()

    def stop(self):
        self.tray.stop()
        self.carrotjuicer.stop()
        self.screenstate.stop()
        self.windowmover.stop()
        logger.info("==== Launcher Closed ===")

def main():
    logger.add("log.log", rotation="1 week", compression="zip", retention="1 month", encoding='utf-8')
    logger.info("==== Starting Launcher ====")
    Threader()

if __name__ == "__main__":
    main()
