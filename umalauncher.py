import pystray
import asyncio
import os
import pygetwindow as gw
import threading
from PIL import Image
import time
from win32api import GetMonitorInfo, MonitorFromPoint
from elevate import elevate

elevate()

global gaem
gaem = None
gaem_got = False

scaling_thread = None
stop_threads = False

icon = None

first_orientation = True
was_portrait = True

prev_height = 0

def get_game():
    global gaem_got
    global prev_height
    windows = gw.getWindowsWithTitle("umamusume")
    for window in windows:
        if window.title == "umamusume":
            gaem_got = True
            cur_gaem = windows[0]
            prev_height = cur_gaem.height
            return cur_gaem
    return None


def get_workspace():
    if gaem:
        monitor = MonitorFromPoint(gaem.topleft)
        if not monitor:
            monitor = MonitorFromPoint(gaem.bottomright)
        return GetMonitorInfo(monitor).get("Work") if monitor else None
    else:
        return None

def start_async(icon):
    asyncio.run(main())


def on_clicked(icon, item):
    global stop_threads
    stop_threads = True
    icon.stop()
    quit()


def is_portrait() -> bool:
    global gaem
    return gaem.height > gaem.width


def scale_height():
    global gaem
    global was_portrait
    global first_orientation
    global prev_height

    workspace = get_workspace()
    if workspace:
        jank_resize = False
        cur_height = gaem.height
        if prev_height - cur_height > 250:
            jank_resize = True

        jank_offset = 7
        workspace_height = workspace[3] - workspace[1]
        workspace_width = workspace[2] - workspace[0]
        scaled_height = workspace_height + jank_offset
        scale_factor = scaled_height / gaem.height
        scaled_width = gaem.width * scale_factor

        if scaled_width > workspace_width:
            scale_factor = workspace_width / scaled_width
            scaled_height = scaled_height * scale_factor
            scaled_width = workspace_width

        scaled_size = (round(scaled_width), round(scaled_height))
        gaem.top = workspace[1]
        gaem.size = scaled_size

        # Determine if orientation changed.
        prev_portrait = is_portrait()
        if first_orientation or jank_resize or prev_portrait != was_portrait:
            gaem.left = round((workspace_width / 2) - (scaled_width / 2))
            first_orientation = False
        was_portrait = prev_portrait
        prev_height = gaem.height
    

def main():
    global gaem
    global gaem_got
    global portrait_topleft
    global landscape_topleft
    global stop_threads
    global icon

    while True:
        time.sleep(0.1)
        
        if stop_threads:
            break

        if not gaem:
            if gaem_got:
                # Game was found before, but no more.
                break
            gaem = get_game()
            
        if gaem:
            # Do stuff
            try:
                scale_height()
            except gw.PyGetWindowException:
                # Game window probably closed
                gaem = None
    if icon:
        icon.stop()
    return None


gaem = get_game()

if not gaem:
    os.startfile("dmmgameplayer://umamusume/cl/general/umamusume")

icon = pystray.Icon(
    'Uma Launcher',
    Image.open("favicon.ico"),
    menu=pystray.Menu(
        pystray.MenuItem(
            "Close",
            on_clicked
        ))
    )

scaling_thread = threading.Thread(target=main, daemon=True)
scaling_thread.start()

icon.run()