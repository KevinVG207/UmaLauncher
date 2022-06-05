from loguru import logger
import requests
import time
import settings
import util
import os
import subprocess
import psutil
import win32gui
import win32con


def _get_nord_path() -> str:
    nord_path = settings.get("nordvpn_path")
    if "NordVPN.exe" in os.listdir(nord_path):
        return nord_path
    util.show_alert_box("NordVPN not found.", "NordVPN could not be found in the folder specified by umasettings.json.\nEither change that path to the installation folder of NordVPN or disable NordVPN autoconnect in the tray icon.")
    return None

def _get_ip() -> str:
    ip = None
    i = 0
    while i < 5:
        try:
            # ip = requests.get("https://api.myip.com/").json()["ip"]
            ip = requests.get("https://api.ipify.org/?format=json").json()["ip"]
            break
        except requests.exceptions.ConnectionError:
            time.sleep(0.1)
            i += 1
    return ip


def connect(group):
    logger.info(f"Attempting to connect to {group} with NordVPN.")

    nord_path = _get_nord_path()
    if not nord_path:
        return

    before_ip = _get_ip()
    if not before_ip:
        logger.error("Connection Error! Unable to fetch IP address.")
        return

    logger.info("Waiting until IP changes.")
    last_attempt_time = 0
    while True:
        logger.info("Trying to start NordVPN.")
        subprocess.Popen([os.path.join(nord_path + "NordVPN.exe"), "-c", "-g", "Japan"])
        last_attempt_time = time.time()
        # subprocess.run("NordVPN.exe -c -g \"Japan\"", cwd=nord_path)
        time.sleep(5)
        after_ip = _get_ip()
        if before_ip != after_ip:
            break

    logger.info("IP changed, so connected to VPN.")

    # Automatically close NordVPN window.
    if settings.get("autoclose_nord"):
        nord_window = util.get_window_handle("NordVPN", type=util.STARTSWITH)
        if nord_window:
            logger.info("Closing NordVPN window.")
            win32gui.PostMessage(nord_window, win32con.WM_CLOSE, 0, 0)

    return last_attempt_time


def disconnect():
    logger.info("Attempting to disconnect NordVPN.")
    nord_path = _get_nord_path()
    if not nord_path:
        return
    
    if "NordVPN.exe" in (p.name() for p in psutil.process_iter()):
        # subprocess.run("nordvpn -d", shell=True, cwd=nord_path)
        subprocess.Popen("nordvpn -d", shell=True, cwd=nord_path)
    return
