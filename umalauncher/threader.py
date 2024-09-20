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
    util.show_warning_box("Launch Error", "Uma Launcher needs administrator privileges to start.")
    sys.exit()

import threading
import time
import psutil
import os
import win32api
from loguru import logger
import requests
import settings
import carrotjuicer
import umatray
import screenstate
import windowmover
import training_tracker
import gui
import umaserver
import horsium

THREAD_OBJECTS = []
THREADS = []
THREADER_OBJECT = None

class Threader():
    unpack_dir = None
    settings = None
    tray = None
    carrotjuicer = None
    windowmover = None
    screenstate = None
    umaserver = None
    should_stop = False
    show_preferences = False
    show_helper_table_dialog = False
    show_training_csv_dialog = False
    widget_queue = []

    def __init__(self):
        gui.THREADER = self

        self.settings = settings.SettingsHandler(self)
        
        # Ensure only a single instance is running.
        self.check_single_instance()

        if self.should_stop:
            return

        # Ping the server to track usage
        self.settings.notify_server()

        self.umaserver = umaserver.UmaServer(self)
        THREAD_OBJECTS.append(self.umaserver)
        THREADS.append(threading.Thread(target=self.umaserver.run_with_catch, name="UmaServer"))
        THREADS[-1].start()

        timeout = time.time() + 10
        while time.time() < timeout:
            try:
                r = requests.get(f"http://{umaserver.domain}:{umaserver.port}", timeout=1)
                if r.status_code == 200:
                    break
            except:
                pass

        self.screenstate = screenstate.ScreenStateHandler(self)
        THREAD_OBJECTS.append(self.screenstate)
        THREADS.append(threading.Thread(target=self.screenstate.run_with_catch, name="ScreenStateHandler"))

        self.carrotjuicer = carrotjuicer.CarrotJuicer(self)
        THREAD_OBJECTS.append(self.carrotjuicer)
        THREADS.append(threading.Thread(target=self.carrotjuicer.run_with_catch, name="CarrotJuicer"))

        self.windowmover = windowmover.WindowMover(self)
        THREAD_OBJECTS.append(self.windowmover)
        THREADS.append(threading.Thread(target=self.windowmover.run_with_catch, name="WindowMover"))

        self.tray = umatray.UmaTray(self)
        THREAD_OBJECTS.append(self.tray)
        THREADS.append(threading.Thread(target=self.tray.run_with_catch, name="UmaTray"))

        for thread in THREADS:
            if not thread.is_alive() and not thread.ident:
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
        util.ignore_errors = True
        self.should_stop = True


    def check_single_instance(self):
        # Get the process id of the current process
        current_pid = os.getpid()

        # Check if a pid file exists.
        pid_file = util.get_appdata("lock.pid")
        if os.path.exists(pid_file):
            try:
                with open(pid_file, "r", encoding='utf-8') as f:
                    pid = f.read()
                pid = int(pid)
                if psutil.pid_exists(pid):
                    util.show_warning_box("Launch Error", "<b>Uma Launcher is already running.</b><br>If you just closed Uma Launcher,<br>wait a few moments and try again.")
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
    
    # Wait for all threads to stop
    for thread in THREADS:
        logger.info(f"Waiting for thread {thread.name} to stop")
        thread.join()
        logger.info(f"Thread {thread.name} stopped")


@logger.catch
def main():
    global THREADER_OBJECT

    logger.info("==== Starting Launcher ====")
    try:
        THREADER_OBJECT = Threader()
    except Exception:
        util.show_error_box("Critical Error", "Uma Launcher has encountered a critical error and will now close.")
    
    # Kill all threads that may be running
    logger.debug("Killing threads")
    kill_threads()
    logger.debug("Threads killed")

    # Stop the application
    logger.debug("Stopping Qt")
    gui.stop_application()
    logger.debug("Qt stopped")

    logger.debug("Closing browsers")
    horsium.quit_all_drivers()
    logger.debug("Browsers closed")

    # Remove the pid file
    lock_path = util.get_appdata("lock.pid")
    if os.path.exists(lock_path):
        os.remove(lock_path)

    logger.info("=== Launcher closed ===")

if __name__ == "__main__":
    main()
