import datetime
import pystray
import asyncio
import os
import threading
from PIL import Image
import time
import win32api
import win32gui
import pywintypes
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

def enumHandler(hwnd, lParam):
    global gaem
    if win32gui.IsWindowVisible(hwnd):
        if win32gui.GetWindowText(hwnd) == "umamusume":
            gaem = hwnd


def get_game():
    global gaem
    global gaem_got
    global prev_height
    win32gui.EnumWindows(enumHandler, None)
    if gaem != None:
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

def start_async(icon):
    asyncio.run(main())


def on_clicked(icon, item):
    global stop_threads
    stop_threads = True
    icon.stop()
    quit()


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
                get_game()
                if not gaem:
                    break
            else:
                get_game()
            
        if gaem:
            # Do stuff
            # TODO: Catch an error if game is closed within scale_height()
            try:
                if win32gui.IsWindow(gaem):
                    scale_height()
                else:
                    # Game window closed
                    print("considered closed")
                    gaem = None
            except pywintypes.error as e:
                # Game window probaby closed
                print(e)
                gaem = None
    if icon:
        icon.stop()
    return None


get_game()

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