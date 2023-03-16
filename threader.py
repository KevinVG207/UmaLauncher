from elevate import elevate
try:
    elevate()
except OSError:
    import util
    import sys
    util.show_alert_box("Launch Error", "Uma Launcher needs administrator privileges to start.")
    sys.exit()

import threading
from loguru import logger
import settings
import carrotjuicer
import umatray
import screenstate
import windowmover
import win32api
import util

class Threader():
    unpack_dir = None
    settings = None
    tray = None
    carrotjuicer = None
    windowmover = None
    screenstate = None
    threads = []

    def __init__(self):
        # Set directory to find assets
        self.settings = settings.Settings(self)

        self.screenstate = screenstate.ScreenStateHandler(self)
        self.threads.append(threading.Thread(target=self.screenstate.run, name="ScreenStateHandler"))

        self.carrotjuicer = carrotjuicer.CarrotJuicer(self)
        self.threads.append(threading.Thread(target=self.carrotjuicer.run, name="CarrotJuicer"))

        self.windowmover = windowmover.WindowMover(self)
        self.threads.append(threading.Thread(target=self.windowmover.run, name="WindowMover"))

        self.tray = umatray.UmaTray(self)
        self.threads.append(threading.Thread(target=self.tray.run, name="UmaTray"))

        for thread in self.threads:
            thread.start()

        win32api.SetConsoleCtrlHandler(self.stop_signal, True)

    def stop_signal(self, *_):
        self.stop()

    def stop(self):
        logger.info("=== Closing launcher ===")
        if self.tray:
            self.tray.stop()
        if self.carrotjuicer:
            self.carrotjuicer.stop()
        if self.screenstate:
            self.screenstate.stop()
        if self.windowmover:
            self.windowmover.stop()

        logger.info("=== Launcher closed ===")

@logger.catch
def main():
    if util.is_script:
        util.log_set_trace()
        logger.debug("Running from script, enabling debug logging.")
    else:
        util.log_set_info()
    logger.info("==== Starting Launcher ====")
    Threader()

if __name__ == "__main__":
    main()
