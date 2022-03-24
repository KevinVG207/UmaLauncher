from elevate import elevate
elevate()

from loguru import logger
logger.add("log.log", retention="1 week")
logger.info("==== Starting Launcher ====")

import psutil
import pystray
import asyncio
import os
import threading
from PIL import Image
import time
import win32api
import win32gui
import win32con
import pywintypes
from pypresence import Presence
from PIL import Image
import pyautogui
from screenstate import ScreenState
import settings
import nord

gaem = None
gaem_got = False

dmm = None
dmm_got = False

scaling_thread = None
stop_threads = False

icon = None

first_orientation = True
was_portrait = True

prev_height = 0


def _get_dmm(hwnd, lParam):
    global dmm
    if win32gui.IsWindowVisible(hwnd):
        if "DMM GAME PLAYER" in win32gui.GetWindowText(hwnd):
            logger.info("Found DMMGamePlayer!")
            dmm = hwnd


def get_dmm():
    global dmm_got
    win32gui.EnumWindows(_get_dmm, None)
    if dmm:
        dmm_got = True


def _get_game(hwnd, lParam):
    global gaem
    if win32gui.IsWindowVisible(hwnd):
        if win32gui.GetWindowText(hwnd) == "umamusume":
            logger.info("Found uma game!")
            gaem = hwnd


def get_game():
    global gaem
    global gaem_got
    global prev_height
    win32gui.EnumWindows(_get_game, None)
    if gaem:
        gaem_got = True
        cur_gaem_rect = win32gui.GetWindowRect(gaem)
        prev_height = cur_gaem_rect[3] - cur_gaem_rect[1]


def get_workspace():
    global gaem
    if gaem:
        monitor = win32api.MonitorFromWindow(gaem)
        return win32api.GetMonitorInfo(monitor).get("Work") if monitor else None
    else:
        return None


def is_portrait() -> bool:
    global gaem
    cur_gaem_rect = win32gui.GetWindowRect(gaem)
    cur_height = cur_gaem_rect[3] - cur_gaem_rect[1]
    cur_width = cur_gaem_rect[2] - cur_gaem_rect[0]
    return cur_height > cur_width


def scale_height():
    global gaem
    global was_portrait
    global first_orientation
    global prev_height

    workspace = get_workspace()
    if workspace:
        jank_resize = False
        cur_gaem_rect = win32gui.GetWindowRect(gaem)
        cur_height = cur_gaem_rect[3] - cur_gaem_rect[1]
        cur_width = cur_gaem_rect[2] - cur_gaem_rect[0]
        if prev_height - cur_height > 250:
            jank_resize = True

        jank_offset = 7
        workspace_height = workspace[3] - workspace[1]
        workspace_width = workspace[2] - workspace[0]
        scaled_height = workspace_height + jank_offset
        scale_factor = scaled_height / cur_height
        scaled_width = cur_width * scale_factor

        if scaled_width > workspace_width:
            scale_factor = workspace_width / scaled_width
            scaled_height = scaled_height * scale_factor
            scaled_width = workspace_width

        scaled_size = (round(scaled_width), round(scaled_height))
        win32gui.MoveWindow(gaem, cur_gaem_rect[0], workspace[1], scaled_size[0], scaled_size[1], True)

        # Determine if orientation changed.
        prev_portrait = is_portrait()
        if first_orientation or jank_resize or prev_portrait != was_portrait:
            new_left = round((workspace_width / 2) - (scaled_width / 2))
            win32gui.MoveWindow(gaem, new_left, workspace[1], scaled_size[0], scaled_size[1], True)
            first_orientation = False
        was_portrait = prev_portrait
        new_gaem_rect = win32gui.GetWindowRect(gaem)
        cur_height = new_gaem_rect[3] - new_gaem_rect[1]
        prev_height = cur_height
    

def get_screenshot():
    global gaem
    # win32gui.SetForegroundWindow(gaem)
    x, y, x1, y1 = win32gui.GetClientRect(gaem)
    x, y = win32gui.ClientToScreen(gaem, (x, y))
    x1, y1 = win32gui.ClientToScreen(gaem, (x1 - x, y1 - y))
    return pyautogui.screenshot(region=(x, y, x1, y1)).convert("RGB")


def do_presence(debug: bool = False):
    global gaem
    global rpc
    global screen_state
    
    # Get screenshot
    try:
        img = get_screenshot()
    except OSError:
        logger.error("Couldn't get screenshot.")
        return
    if not img:
        return
    if debug:
        img.save("screenshot.png", "PNG")

    screen_state.update(img, debug)

nord_auto = False
def main():
    global dmm
    global dmm_got
    global gaem
    global gaem_got
    global portrait_topleft
    global landscape_topleft
    global stop_threads
    global icon
    global last_screen
    global rpc
    global last_rpc_update
    global vpn_settings
    global screen_state
    global nord_auto
    dmm_closed = False
    dmm_ignored = False
    rpc_on = False
    nord_auto = settings.get_tray_setting("NordVPN autolaunch")  # We only check this once, to ensure consistency with closing VPN later.

    # Rich Presence
    # First, we need to create an async event loop in the thread.
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    client_id = 954453106765225995
    last_screen = time.time()
    last_rpc_update = time.time()
    rpc = Presence(client_id)
    screen_state = ScreenState()

    get_game()
    if not gaem:
        # VPN
        if nord_auto:
            last_attempt_time = nord.connect("Japan")
            now = time.time()
            time_difference = now - last_attempt_time
            if time_difference < 10:
                # Connection jank, so wait until at least 10 seconds pass to hopefully avoid a "Network Changed" error in DMM.
                time.sleep(time_difference) 
    else:
        dmm_ignored = True
        do_presence(True)

    if not dmm_ignored:
        logger.info("Sending DMMGamePlayer to umamusume.")
        os.system("Start dmmgameplayer://umamusume/cl/general/umamusume")


    while True:
        time.sleep(0.1)

        if stop_threads:
            break

        new_rpc_state = settings.get_tray_setting("Discord rich presence")
        if rpc_on != new_rpc_state:
            # RPC state changed
            rpc_on = new_rpc_state
            # Determine what to do now
            if rpc_on:
                logger.info("Enabling Rich Presence.")
                rpc.connect()
            else:
                logger.info("Disabling Rich Presence.")
                try:
                    rpc.clear()
                    rpc.close()
                except AssertionError:
                    # Happens when not connected before.
                    pass
        
        if not dmm and not dmm_got:
            get_dmm()

        if dmm_got and not dmm_ignored and not dmm_closed:
            # Check if it changed window.
            if not win32gui.IsWindow(dmm):
                dmm = None
                if not dmm and "DMMGamePlayer.exe" not in (p.name() for p in psutil.process_iter()):
                    # DMM Player was open and is now closed.
                    logger.info("Disconnect VPN because DMM was closed.")
                    dmm_closed = True
                    if nord_auto:
                        nord.disconnect()
                    if not gaem:
                        break
                else:
                    time.sleep(0.5)
                    get_dmm()

        if not gaem:
            if gaem_got:
                # Game was found before, but no more.
                get_game()
                if not gaem:
                    break
            else:
                get_game()
            
        if gaem:
            if not dmm_ignored and dmm_got and not dmm_closed:
                # Game was launched via DMM.
                logger.info("Automatically shutting down VPN.")
                if settings.get("autoclose_dmm"):
                    # Automatically close the DMM window.
                    logger.info("Closing DMM window.")
                    win32gui.PostMessage(dmm, win32con.WM_CLOSE, 0, 0)
                dmm_closed = True
                if nord_auto:
                    nord.disconnect()
            try:
                if win32gui.IsWindow(gaem):
                    # Do stuff
                    if settings.get_tray_setting("Auto-resize"):
                        scale_height()
                    if rpc_on:
                        if time.time() - last_screen >= 1:
                            # Take a screenshot every second
                            last_screen = time.time()
                            do_presence(False)
                        if time.time() - last_rpc_update >= 15:
                            # Update rich presence every 15 seconds
                            last_rpc_update = time.time()
                            rpc_next = screen_state.get_state()
                            rpc_next["large_image"] = "umaicon"
                            rpc_next["large_text"] = "It's Special Week!"
                            rpc.update(**rpc_next)
                else:
                    # Game window closed
                    gaem = None
            except pywintypes.error as e:
                # Game window probaby closed
                logger.warning("Game probably closed. Error details:")
                logger.info(e)
                gaem = None
    if icon:
        icon.stop()
    if nord_auto:
        nord.disconnect()
    rpc.clear()
    rpc.close()
    return None



# Set up tray icon.
def close_clicked(icon, item):
    global stop_threads
    stop_threads = True
    icon.stop()

def setting_clicked(icon, item):
    settings.set_tray_setting(item.text, not item.checked)

menu_items = [pystray.MenuItem(menu_item, setting_clicked, checked=lambda item: settings.get_tray_setting(item.text)) for menu_item in settings.DEFAULT_SETTINGS["tray_items"]]
menu_items.append(pystray.Menu.SEPARATOR)
menu_items.append(pystray.MenuItem("Close", close_clicked))


icon = pystray.Icon(
    'Uma Launcher',
    Image.open("favicon.ico"),
    menu=pystray.Menu(*menu_items)
    )


logger.info("Starting threads.")
scaling_thread = threading.Thread(target=main, daemon=True)
scaling_thread.start()

icon.run()

if nord_auto:
    nord.disconnect()
