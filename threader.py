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
    screenstate = None
    threads = []

    def __init__(self):
        self.settings = settings.Settings()

        self.screenstate = screenstate.ScreenStateHandler(self)
        self.threads.append(threading.Thread(target=self.screenstate.run))

        self.carrotjuicer = carrotjuicer.CarrotJuicer(self)
        self.threads.append(threading.Thread(target=self.carrotjuicer.run))

        self.windowmover = windowmover.WindowMover(self)
        self.threads.append(threading.Thread(target=self.windowmover.run))

        self.tray = umatray.UmaTray(self)
        self.threads.append(threading.Thread(target=self.tray.run))

        for thread in self.threads:
            thread.start()

        win32api.SetConsoleCtrlHandler(self.stop_signal, True)

    def stop_signal(self, *_):
        self.stop()

    def stop(self):
        logger.info("=== Closing launcher ===")
        self.tray.stop()
        self.carrotjuicer.stop()
        self.screenstate.stop()
        self.windowmover.stop()

@logger.catch
def main():
    logger.add("log.log", rotation="1 week", compression="zip", retention="1 month", encoding='utf-8')
    logger.info("==== Starting Launcher ====")
    Threader()

if __name__ == "__main__":
    main()
