import util
import sys
gzips = list([path for path in sys.argv if path.endswith(".gz")])
if gzips:
    # User dropped file(s) on the launcher.
    # Use them for CSV generation.
    import training_tracker
    training_tracker.training_csv_dialog(gzips)
    sys.exit()

from elevate import elevate
try:
    elevate()
except OSError:
    import util
    util.show_error_box("Launch Error", "Uma Launcher needs administrator privileges to start.")
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
    logger.info("==== Starting Launcher ====")
    Threader()

if __name__ == "__main__":
    main()
