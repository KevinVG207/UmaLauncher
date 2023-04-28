import util
import sys
gzips = list([path for path in sys.argv if path.endswith(".gz")])
if gzips:
    # User dropped file(s) on the launcher.
    # Use them for CSV generation.
    import training_tracker
    training_tracker.training_csv_dialog(gzips)
    sys.exit()

if not util.elevate():
    util.show_error_box("Launch Error", "Uma Launcher needs administrator privileges to start.")
    sys.exit()

import threading
import time
from loguru import logger
import settings
import carrotjuicer
import umatray
import screenstate
import windowmover
import win32api

class Threader():
    unpack_dir = None
    settings = None
    tray = None
    carrotjuicer = None
    windowmover = None
    screenstate = None
    threads = []
    should_stop = False
    show_helper_table_dialog = False

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

        while not self.should_stop:
            time.sleep(0.2)

            if self.show_helper_table_dialog:
                self.settings.update_helper_table()
                self.show_helper_table_dialog = False

        logger.info("=== Launcher closed ===")

    def stop_signal(self, *_):
        self.stop()

    def stop(self):
        logger.info("=== Closing launcher ===")
        self.should_stop = True
        if self.tray:
            self.tray.stop()
        if self.carrotjuicer:
            self.carrotjuicer.stop()
        if self.screenstate:
            self.screenstate.stop()
        if self.windowmover:
            self.windowmover.stop()

@logger.catch
def main():
    logger.info("==== Starting Launcher ====")
    Threader()

if __name__ == "__main__":
    main()
