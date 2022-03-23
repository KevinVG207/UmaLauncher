from loguru import logger
import requests
import time
import settings
import util
import os
import subprocess


def _get_nord_path() -> str:
    nord_path = settings.get("nordvpn_path")
    if "NordVPN.exe" in os.listdir(nord_path):
        return nord_path
    util.show_alert_box("NordVPN not found.", "NordVPN could not be found in the folder specified by umasettings.json.\nEither change that path to the installation folder of NordVPN or disable NordVPN autoconnect in the tray icon.")
    return None

def _get_ip() -> str:
    return requests.get("https://api.myip.com/").json()["ip"]


def connect(group):
    logger.info(f"Attempting to connect to {group} with NordVPN.")
    before_ip = _get_ip()

    error = False

    logger.info("Waiting until IP changes.")
    while True:
        time.sleep(5)
        after_ip = _get_ip()
        if before_ip != after_ip:
            break
        nord_path = _get_nord_path()
        if not nord_path:
            error = True
            break
        subprocess.run("nordvpn -c -g \"Japan\"", shell=True, cwd=nord_path)
    
    if error:
        logger.error("Connecting to Nord failed.")
    else:
        logger.info("IP changed, so connected to VPN.")


def disconnect():
    logger.info("Attempting to disconnect NordVPN.")
    nord_path = _get_nord_path()
    if not nord_path:
        return
    subprocess.run("nordvpn -d", shell=True, cwd=nord_path)
    return