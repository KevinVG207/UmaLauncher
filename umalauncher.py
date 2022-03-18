import pystray
import asyncio
import os
import threading
from PIL import Image
import time
import win32api
import win32gui
import win32ui
import win32con
import pywintypes
from pypresence import Presence
from elevate import elevate
from PIL import Image
import pyautogui
import presence_locations

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


client_id = 954453106765225995
rpc_next = {"details": "Launching game..."}
last_screen = time.time()
last_rpc_update = time.time()
rpc = Presence(client_id)
rpc.connect()


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
    quit(0)


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


def similar_color(col1, col2) -> bool:
    total_diff = 0
    for i in range(3):
        total_diff += abs(col1[i] - col2[i])
    return total_diff < 32


def do_presence(save: bool = False):
    global gaem
    global rpc
    global rpc_next
    
    # Get screenshot
    img = get_screenshot()
    if save:
        img.save("screenshot.png", "PNG")

    presence_state = None
    presence_details = None
    
    for location in presence_locations.locations:
        sublocations = presence_locations.locations[location]
        
        for sublocation, subloc_data in sublocations.items():
            pos = subloc_data["pos"]
            col = subloc_data["col"]
            pixel_pos = (round(img.width * pos[0]), round(img.height * pos[1]))
            pixel_color = img.getpixel(pixel_pos)
            if similar_color(pixel_color, col):
                presence_state = sublocation
                presence_details = location

    if presence_state:
        rpc_next = {
            "state": presence_state,
            "details": presence_details
        }


def main():
    global gaem
    global gaem_got
    global portrait_topleft
    global landscape_topleft
    global stop_threads
    global icon
    global last_screen
    global rpc
    global rpc_next
    global last_rpc_update

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
            try:
                if win32gui.IsWindow(gaem):
                    # Do stuff
                    scale_height()
                    if time.time() - last_screen >= 1:
                        # Take a screenshot every second
                        last_screen = time.time()
                        do_presence()
                    if time.time() - last_rpc_update >= 15:
                        # Update rich presence every 15 seconds
                        last_rpc_update = time.time()
                        rpc_next["large_image"] = "umaicon"
                        rpc_next["large_text"] = "It's Special Week!"
                        rpc.update(**rpc_next)
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

rpc.clear()
rpc.close()