import threading
from loguru import logger
import settings
import carrotjuicer
import umatray
import screenstate

logger.add("log.log", rotation="1 week", compression="zip", retention="1 month")

class Threader():
    settings = None
    tray = None
    carrotjuicer = None
    windowmover = None
    screenstate = None  # Screen states for rich presence (+ get screenshot?)

    def __init__(self):
        self.settings = settings.Settings()

        self.tray = umatray.UmaTray(self)
        threading.Thread(target=self.tray.run).start()

        self.screenstate = screenstate.ScreenStateHandler(self)
        threading.Thread(target=self.screenstate.run).start()

        self.carrotjuicer = carrotjuicer.CarrotJuicer(self, self.screenstate)
        threading.Thread(target=self.carrotjuicer.run).start()

    def stop(self):
        self.tray.stop()
        self.carrotjuicer.stop()
        self.screenstate.stop()
        # self.windowmover.stop()

def main():
    logger.info("==== Starting Launcher ====")
    Threader()

if __name__ == "__main__":
    main()
