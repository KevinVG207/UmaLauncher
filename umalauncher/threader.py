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
import psutil
import os
import win32api
from loguru import logger
import settings
import carrotjuicer
import umatray
import screenstate
import windowmover
import training_tracker
import gui

THREAD_OBJECTS = []

class Threader():
    unpack_dir = None
    settings = None
    tray = None
    carrotjuicer = None
    windowmover = None
    screenstate = None
    threads = []
    should_stop = False
    show_preferences = False
    show_helper_table_dialog = False
    show_training_csv_dialog = False
    widget_queue = []

    def __init__(self):
        gui.THREADER = self

        # Set directory to find assets
        self.settings = settings.SettingsHandler(self)
        
        # Ensure only a single instance is running.
        self.check_single_instance()

        if self.should_stop:
            return

        # Ping the server to track usage
        self.settings.notify_server()

        self.screenstate = screenstate.ScreenStateHandler(self)
        THREAD_OBJECTS.append(self.screenstate)
        self.threads.append(threading.Thread(target=self.screenstate.run_with_catch, name="ScreenStateHandler"))

        self.carrotjuicer = carrotjuicer.CarrotJuicer(self)
        THREAD_OBJECTS.append(self.carrotjuicer)
        self.threads.append(threading.Thread(target=self.carrotjuicer.run_with_catch, name="CarrotJuicer"))

        self.windowmover = windowmover.WindowMover(self)
        THREAD_OBJECTS.append(self.windowmover)
        self.threads.append(threading.Thread(target=self.windowmover.run_with_catch, name="WindowMover"))

        self.tray = umatray.UmaTray(self)
        THREAD_OBJECTS.append(self.tray)
        self.threads.append(threading.Thread(target=self.tray.run_with_catch, name="UmaTray"))

        for thread in self.threads:
            thread.start()

        win32api.SetConsoleCtrlHandler(self.stop_signal, True)

        while not self.should_stop:
            time.sleep(0.2)

            if self.show_preferences:
                self.settings.display_preferences()
                self.show_preferences = False

            if self.show_helper_table_dialog:
                self.settings.update_helper_table()
                self.show_helper_table_dialog = False
            
            if self.show_training_csv_dialog:
                training_tracker.training_csv_dialog()
                self.show_training_csv_dialog = False
            
            while len(self.widget_queue) > 0:
                widget_tuple = self.widget_queue.pop(0)
                gui.show_widget(widget_tuple[0], *widget_tuple[1], **widget_tuple[2])

    def stop_signal(self, *_):
        self.stop()

    def stop(self):
        logger.info("=== Closing launcher ===")
        self.should_stop = True
        gui.stop_application()


    def check_single_instance(self):
        # Get the process id of the current process
        current_pid = os.getpid()

        # Check if a pid file exists.
        pid_file = util.get_relative("lock.pid")
        if os.path.exists(pid_file):
            try:
                with open(pid_file, "r", encoding='utf-8') as f:
                    pid = f.read()
                pid = int(pid)
                if psutil.pid_exists(pid):
                    util.show_warning_box("Launch Error", "Uma Launcher is already running.")
                    self.should_stop = True
                    return
                else:
                    os.remove(pid_file)
            except:
                util.show_warning_box("Launch Error", "Could not determine if a previous instance is running. Try deleting the lock.pid file and try again.")
                self.should_stop = True
                return

        # Write the current pid to the file
        with open(pid_file, "w", encoding='utf-8') as f:
            f.write(str(current_pid))


def kill_threads():
    for thread_object in THREAD_OBJECTS:
        logger.info(f"Stopping thread {thread_object.__class__.__name__}")
        if thread_object:
            thread_object.stop()


@logger.catch
def main():
    logger.info("==== Starting Launcher ====")
    try:
        Threader()
    except Exception:
        util.show_error_box("Critical Error", "Uma Launcher has encountered a critical error and will now close.")
    
    # Kill all threads that may be running
    kill_threads()

    logger.info("=== Launcher closed ===")

if __name__ == "__main__":
    main()
