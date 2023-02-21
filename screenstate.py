import time
import asyncio
from enum import Enum
from io import BytesIO
import requests
import win32gui
import win32con
import pyautogui
import pypresence
from PIL import Image
from loguru import logger
import win32clipboard
import presence_screens as scr
import util
import dmm
import mdb

START_TIME = time.time()


class Location(Enum):
    MAIN_MENU = 0
    CIRCLE = 1
    THEATER = 2
    TRAINING = 3



def get_available_icons():
    # Prepare the character icon names
    chara_icons = []
    music_icons = []
    logger.info("Requesting Rich Presence assets.")
    response = requests.get("https://discord.com/api/v9/oauth2/applications/954453106765225995/assets")
    if not response.ok:
        logger.error("Could not fetch Rich Presence assets.")
        return chara_icons, music_icons

    assets = response.json()
    for asset in assets:
        name = asset['name']
        if name.startswith("chara_"):
            chara_icons.append(name)
        elif name.startswith("music_"):
            music_icons.append(name)
    return chara_icons, music_icons

def get_character_name_dict():
    chara_dict = {}
    logger.info("Requesting character names.")
    response = requests.get("https://umapyoi.net/api/v1/character/names")
    if not response.ok:
        logger.error("Could not fetch character names")
        return chara_dict

    for character in response.json():
        chara_dict[character['game_id']] = character['name']

    return chara_dict

class ScreenState:
    location = Location.MAIN_MENU
    main = "Launching game..."
    sub = "Ready your umapyois!"
    large_image = "umaicon"
    large_text = "It's Special Week!"
    small_image = None
    small_text = None

    available_chara_icons, available_music_icons = get_available_icons()
    fallback_chara_icon = "chara_0000"
    fallback_music_icon = "music_0000"

    chara_names_dict = get_character_name_dict()

    def to_dict(self) -> dict:
        return {
            "state": self.sub,
            "details": self.main,
            "start": START_TIME,
            "large_text": self.large_text,
            "large_image": self.large_image,
            "small_text": self.small_text,
            "small_image": self.small_image,
        }

    def set_chara(self, chara_id):
        chara_icon = f"chara_{chara_id}"
        if chara_icon not in self.available_chara_icons:
            chara_icon = self.fallback_chara_icon
        self.small_image = self.large_image
        self.small_text = self.large_text
        self.large_image = chara_icon
        if chara_id in self.chara_names_dict:
            self.large_text = self.chara_names_dict[chara_id]
        else:
            self.large_text = None

    def set_music(self, music_id):
        music_id = str(music_id)
        music_icon = f"music_{music_id}"
        if music_icon not in self.available_music_icons:
            music_icon = self.fallback_music_icon
        song_title = mdb.get_song_title(music_id)
        self.small_image = self.large_image
        self.small_text = self.large_text
        self.large_image = music_icon
        self.large_text = song_title
        self.main = "Watching a concert:"
        self.sub = song_title

    def __eq__(self, other):
        if isinstance(other, ScreenState):
            return self.to_dict() == other.to_dict()
        return False


class ScreenStateHandler():
    threader = None

    screen_state = None
    carrotjuicer_state = None

    dmm_seen = False
    dmm_handle = None
    dmm_closed = False

    game_seen = False
    game_handle = None

    carrotjuicer_closed = False

    should_stop = False

    rpc_client_id = 954453106765225995
    rpc = None
    event_loop = None
    rpc_last_update = 0
    rpc_latest_state = None

    sleep_time = 0.25

    def __init__(self, threader):
        self.threader = threader

        self.screen_state = ScreenState()

        dmm_handle = util.get_window_handle("DMM GAME PLAYER", type=util.LAZY)
        if dmm_handle:
            self.dmm_handle = dmm_handle
            self.dmm_seen = True

        self.check_game()
        return

    def get_screenshot(self, debug=False):
        if util.is_minimized(self.game_handle):
            logger.warning("Game is minimized, cannot get screenshot.")
            return None
        try:
            x, y, x1, y1 = win32gui.GetClientRect(self.game_handle)
            x, y = win32gui.ClientToScreen(self.game_handle, (x, y))
            x1, y1 = win32gui.ClientToScreen(self.game_handle, (x1 - x, y1 - y))
            image = pyautogui.screenshot(region=(x, y, x1, y1)).convert("RGB")
            if debug:
                image.save("screenshot.png", "PNG")
            return image
        except Exception:
            logger.error("Couldn't get screenshot.")
            return None

    def screenshot_to_clipboard(self):
        try:
            img = self.get_screenshot()
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

    def check_game(self):
        game_handle = util.get_window_handle("umamusume", type=util.EXACT)
        if game_handle:
            self.game_handle = game_handle
            self.game_seen = True

    def stop(self):
        self.should_stop = True

    def run(self):
        # If DMM is not seen AND Game is not seen: Start DMM
        if not self.game_seen:
            if self.threader.settings.unpatch_dmm:
                dmm.unpatch_dmm(self.threader.settings.unpatch_dmm)
            dmm.start()

        while not self.should_stop:
            time.sleep(self.sleep_time)

            # Check if game exists
            if self.game_handle and not win32gui.IsWindow(self.game_handle):
                self.game_handle = None

            # Game was never seen before
            if not self.game_seen:
                self.check_game()
                continue
            # After this, the game was open at some point.

            # Game closed
            if not self.game_handle:
                self.threader.stop()

            # Close DMM
            if not self.dmm_closed:
                # Attempt to close DMM, even if it doesn't exist
                new_dmm_handle = util.get_window_handle("DMM GAME PLAYER", type=util.LAZY)
                if new_dmm_handle:
                    logger.info("Closing DMM.")
                    win32gui.PostMessage(new_dmm_handle, win32con.WM_CLOSE, 0, 0)
                self.dmm_closed = True

            if not self.carrotjuicer_closed:
                self.carrotjuicer_closed = True
                carrotjuicer_handle = util.get_window_handle("Umapyoi", type=util.EXACT)
                if carrotjuicer_handle:
                    logger.info("Attempting to minimize CarrotJuicer.")
                    success = util.show_window(carrotjuicer_handle, win32con.SW_MINIMIZE)
                    if not success:
                        logger.error("Failed to minimize CarrotJuicer")
                    time.sleep(0.25)

            self.sleep_time = 1.

            # Game is open, DMM is closed. Do screen state stuff

            self.update()
            cur_update = time.time()

            if self.threader.settings.get_tray_setting("Discord rich presence"):
                if not self.rpc:
                    try:
                        self.event_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(self.event_loop)
                        self.rpc = pypresence.Presence(self.rpc_client_id)
                        self.rpc.connect()
                    except pypresence.exceptions.DiscordNotFound:
                        continue

                # Get the latest screen state.
                if cur_update - self.rpc_last_update > 15 and self.screen_state != self.rpc_latest_state:
                    logger.info(f"Updating Rich Presence state: {self.screen_state.main}, {self.screen_state.sub}")
                    self.rpc_last_update = cur_update
                    self.rpc_latest_state = self.screen_state
                    self.rpc.update(**self.screen_state.to_dict())
            elif self.rpc:
                self.close_rpc()
        if self.rpc:
            self.close_rpc()
        return

    def close_rpc(self):
        self.rpc.clear()
        self.rpc.close()
        self.rpc = None
        self.event_loop.stop()
        self.event_loop.close()
        self.event_loop = None
        return

    def update(self):
        new_state = self.determine_state()
        if new_state != self.screen_state:
            # New state is different
            self.screen_state = new_state
            logger.info(f"Determined state: {self.screen_state.main}, {self.screen_state.sub}")

    def determine_state(self):
        # Carrotjuicer takes priority
        if self.carrotjuicer_state:
            tmp = self.carrotjuicer_state
            self.carrotjuicer_state = None
            return tmp
        else:
            new_state = ScreenState()
            image = self.get_screenshot()

            if image:
                # DETERMINE / ADJUST STATE
                for main_screen, check_targets in scr.screens.items():
                    if main_screen == "Main Menu":
                        # Main Menu:
                        count = 0
                        tmp_subscr = str()

                        for subscreen, subscr_data in scr.screens["Main Menu"].items():
                            pos = subscr_data["pos"]
                            col = subscr_data["col"]
                            pixel_color = util.get_position_rgb(image, pos)

                            tab_enabled = util.similar_color(pixel_color, col)
                            tab_visible = util.similar_color(pixel_color, (226, 223, 231))

                            if tab_enabled or tab_visible :
                                # Current pixel should be part of the menu
                                count += 1
                                if tab_enabled:
                                    tmp_subscr = subscreen
                            else:
                                break
                        if count == 5 and tmp_subscr:
                            # All menu items found and one is enabled. This must be the home menu.
                            new_state.main = "Main Menu"
                            new_state.sub = tmp_subscr
                            return new_state

        return self.screen_state
