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
import win32clipboard
import pywintypes
import pypresence
from PIL import Image
import pyautogui
from screenstate import ScreenState
import settings
import util
import dmm
from io import BytesIO

# Globals
gaem_handle = None
gaem_was_open = False

dmm_handle = None
dmm_was_open = False
dmm_patched = False

stop_threads = False

tray_icon = None

first_orientation = True
was_portrait = True

prev_height = 0

screen_state = ScreenState()


def get_dmm():
    global dmm_handle
    global dmm_was_open
    dmm_handle = util.get_window_handle("DMM GAME PLAYER", type=util.LAZY)
    if dmm_handle:
        dmm_was_open = True


def close_dmm():
    if win32gui.IsWindow(dmm_handle):
        win32gui.PostMessage(dmm_handle, win32con.WM_CLOSE, 0, 0)


def get_game():
    global gaem_handle
    global gaem_was_open
    global prev_height
    gaem_handle = util.get_window_handle("umamusume", type=util.EXACT)
    if gaem_handle:
        gaem_was_open = True
        cur_gaem_rect = win32gui.GetWindowRect(gaem_handle)
        prev_height = cur_gaem_rect[3] - cur_gaem_rect[1]


def get_workspace():
    global gaem_handle
    if gaem_handle:
        monitor = win32api.MonitorFromWindow(gaem_handle)
        return win32api.GetMonitorInfo(monitor).get("Work") if monitor else None
    else:
        return None


def is_portrait() -> bool:
    global gaem_handle
    cur_gaem_rect = win32gui.GetWindowRect(gaem_handle)
    return rectangle_is_portrait(cur_gaem_rect)


def rectangle_is_portrait(rect):
    return rect[3] - rect[1] > rect[2] - rect[0]


def scale_height():
    global gaem_handle
    global was_portrait
    global first_orientation
    global prev_height

    workspace = get_workspace()
    if workspace:
        jank_resize = False
        cur_gaem_rect = win32gui.GetWindowRect(gaem_handle)
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
        win32gui.MoveWindow(gaem_handle, cur_gaem_rect[0], workspace[1], scaled_size[0], scaled_size[1], True)

        # Determine if orientation changed.
        prev_portrait = is_portrait()
        if first_orientation or jank_resize or prev_portrait != was_portrait:
            new_left = round((workspace_width / 2) - (scaled_width / 2))
            win32gui.MoveWindow(gaem_handle, new_left, workspace[1], scaled_size[0], scaled_size[1], True)
            first_orientation = False
        was_portrait = prev_portrait
        new_gaem_rect = win32gui.GetWindowRect(gaem_handle)
        cur_height = new_gaem_rect[3] - new_gaem_rect[1]
        prev_height = cur_height
    

def get_screenshot():
    global gaem_handle
    x, y, x1, y1 = win32gui.GetClientRect(gaem_handle)
    x, y = win32gui.ClientToScreen(gaem_handle, (x, y))
    x1, y1 = win32gui.ClientToScreen(gaem_handle, (x1 - x, y1 - y))
    return pyautogui.screenshot(region=(x, y, x1, y1)).convert("RGB")


def do_presence(debug: bool = False):
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


@logger.catch
def main():
    global dmm_handle
    global dmm_was_open
    global gaem_handle
    global gaem_was_open
    global portrait_topleft
    global landscape_topleft
    global stop_threads
    global tray_icon
    global last_screen
    global rpc
    global last_rpc_update
    global screen_state
    global dmm_patched
    dmm_closed = False
    dmm_ignored = False
    rpc_on = False

    get_game()
    if gaem_handle:
        dmm_ignored = True
        do_presence()

    if not dmm_ignored:
        logger.info("Sending DMMGamePlayer to umamusume.")
        if settings.get_tray_setting("Auto-launch game"):
            dmm.patch_dmm()
        elif settings.get("unpatch_dmm"):
            dmm.unpatch_dmm()
        os.system("Start dmmgameplayer://umamusume/cl/general/umamusume")


    # Rich Presence
    # First, we need to create an async event loop in the thread.
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    client_id = 954453106765225995
    last_screen = time.time()
    last_rpc_update = time.time()
    rpc = None


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
                if not rpc:
                    try:
                        rpc = pypresence.Presence(client_id)
                    except pypresence.exceptions.DiscordNotFound:
                        logger.error("Couldn't connect to Discord.")
                if rpc:
                    logger.info("Enabling Rich Presence.")
                    rpc.connect()
            else:
                logger.info("Disabling Rich Presence.")
                if rpc:
                    try:
                        rpc.clear()
                        rpc.close()
                    except AssertionError:
                        # Happens when not connected before.
                        pass
        
        if not dmm_handle and not dmm_was_open:
            get_dmm()

        if dmm_was_open and not dmm_ignored and not dmm_closed:
            # Check if it changed window.
            if not win32gui.IsWindow(dmm_handle):
                dmm_handle = None
                if not dmm_handle and "DMMGamePlayer.exe" not in (p.name() for p in psutil.process_iter()):
                    # DMM Player was open and is now closed.
                    logger.info("Disconnect VPN because DMM was closed.")
                    dmm_closed = True
                    if not gaem_handle:
                        break
                else:
                    dmm_was_open = False

        if not gaem_handle:
            if gaem_was_open:
                # Game was found before, but no more.
                get_game()
                if not gaem_handle:
                    break
            else:
                get_game()
            
        if gaem_handle:
            if not dmm_ignored and dmm_was_open and not dmm_closed:
                # Game was launched via DMM.
                if settings.get("autoclose_dmm"):
                    # Automatically close the DMM window.
                    logger.info("Closing DMM window.")
                    close_dmm()
                dmm_closed = True
            try:
                if win32gui.IsWindow(gaem_handle):
                    # Do stuff
                    if settings.get_tray_setting("Auto-resize"):
                        scale_height()
                    if rpc_on and rpc:
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
                    gaem_handle = None
            except pywintypes.error as e:
                # Game window probaby closed
                logger.warning("Game probably closed. Error details:")
                logger.info(e)
                gaem_handle = None
                
    if tray_icon:
        tray_icon.stop()
    if rpc:
        rpc.clear()
        rpc.close()
    return None


# Set up tray icon.
def close_clicked(icon, item):
    global stop_threads
    stop_threads = True
    icon.stop()

def tray_take_screenshot(icon, item):
    try:
        img = get_screenshot()
    except OSError:
        logger.error("Couldn't get screenshot.")
        util.show_alert_box("Failed to take screenshot.", "Couldn't take screenshot of the game.")
        return
    output = BytesIO()
    img.convert("RGB").save(output, "BMP")
    image_data = output.getvalue()[14:]
    output.close()
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(win32clipboard.CF_DIB, image_data)
    win32clipboard.CloseClipboard()

def setting_clicked(icon, item):
    settings.set_tray_setting(item.text, not item.checked)

menu_items = [
    pystray.MenuItem(
        menu_item,
        setting_clicked,
        checked=lambda item: settings.get_tray_setting(item.text)
    ) for menu_item in settings.DEFAULT_SETTINGS["tray_items"]
]
menu_items.append(pystray.MenuItem("Take screenshot", tray_take_screenshot))
menu_items.append(pystray.Menu.SEPARATOR)
menu_items.append(pystray.MenuItem("Close", close_clicked))

tray_icon = pystray.Icon(
    'Uma Launcher',
    Image.open("favicon.ico"),
    menu=pystray.Menu(*menu_items)
    )

# Start the main and tray icon threads.
logger.info("Starting threads.")
threading.Thread(target=main).start()

tray_icon.run()


# After all threads closed.



logger.info("===== Launcher Closed =====")
