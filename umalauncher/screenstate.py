import time
import asyncio
from enum import Enum
from io import BytesIO
import os
import win32gui
import win32con
import pypresence
from PIL import ImageGrab
from loguru import logger
import win32clipboard
from requests import JSONDecodeError, HTTPError
import presence_screens as scr
import util
import dmm
import mdb
import vpn
import umapatcher

START_TIME = time.time()

class Location(Enum):
    MAIN_MENU = 0
    CIRCLE = 1
    THEATER = 2
    TRAINING = 3
    EVENT = 4
    LEAGUE_OF_HEROES = 5
    SCOUTING_EVENT = 6
    CLAW_MACHINE = 7

class ScreenState:
    location = None
    main = None
    sub = None
    large_image = None
    large_text = None
    small_image = None
    small_text = None

    def __init__(self, handler):
        self.handler = handler
        self.location = Location.MAIN_MENU
        self.main = "Launching game..."
        self.sub = "Ready your umapyois!"
        self.large_image = "umaicon"
        self.large_text = "It's Special Week!"
        self.small_image = None
        self.small_text = None
    
    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, ScreenState):
            return False
        return self.to_dict() == __value.to_dict()

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

    def set_chara(self, chara_id, outfit_id=None, small_text=None):
        chara_icon = f"chara_{chara_id}"
        if chara_icon not in self.handler.available_chara_icons:
            chara_icon = self.handler.fallback_chara_icon
        self.small_image = self.large_image
        if small_text:
            self.small_text = small_text
        else:
            self.small_text = self.large_text
        self.large_image = chara_icon
        if chara_id in self.handler.chara_names_dict:
            self.large_text = self.handler.chara_names_dict[chara_id]
            if outfit_id:
                if outfit_id in self.handler.outfit_names_dict:
                    self.large_text += f"\n{self.handler.outfit_names_dict[outfit_id]}"
        else:
            self.large_text = None

    def set_music(self, music_id):
        music_id = str(music_id)
        music_icon = f"music_{music_id}"
        if music_icon not in self.handler.available_music_icons:
            music_icon = self.handler.fallback_music_icon
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
    last_seen = 0.0
    game_closed = False

    carrotjuicer_closed = False
    carrotjuicer_handle = None

    should_stop = False

    rpc_client_id = 954453106765225995
    rpc = None
    event_loop = None
    rpc_last_update = 0
    rpc_latest_state = None

    sleep_time = 0.25

    available_chara_icons = None
    available_music_icons = None
    fallback_chara_icon = "chara_0000"
    fallback_music_icon = "music_0000"

    chara_names_dict = None
    outfit_names_dict = None

    vpn = None

    def __init__(self, threader):
        self.threader = threader

        self.get_available_icons()
        self.chara_names_dict = util.get_character_name_dict()
        self.outfit_names_dict = util.get_outfit_name_dict()
        self.screen_state = ScreenState(self)

        self.last_seen = time.perf_counter()
        
        self.vpn = None

        dmm_handle = dmm.get_dmm_handle()
        if dmm_handle:
            self.dmm_handle = dmm_handle
            self.dmm_seen = True

        self.check_game()
        return


    def get_available_icons(self):
        # Prepare the character icon names
        chara_icons = []
        music_icons = []
        logger.info("Requesting Rich Presence assets.")
        response = util.do_get_request("https://umapyoi.net/uma-launcher/discord-assets")
        if response:
            try:
                assets = response.json()
                for asset in assets:
                    name = asset['name']
                    if name.startswith("chara_"):
                        chara_icons.append(name)
                    elif name.startswith("music_"):
                        music_icons.append(name)
            except (KeyError, JSONDecodeError, HTTPError) as ex:
                logger.warning(f"Rich Presence assets response was invalid. Response: {response.status_code} {response.content}, Exception: {ex}")

        self.available_chara_icons = chara_icons
        self.available_music_icons = music_icons


    def get_screenshot(self):
        if util.is_minimized(self.game_handle):
            # logger.warning("Game is minimized, cannot get screenshot.")
            return None
        try:
            x, y, x1, y1 = win32gui.GetClientRect(self.game_handle)
            x, y = win32gui.ClientToScreen(self.game_handle, (x, y))
            x1, y1 = win32gui.ClientToScreen(self.game_handle, (x1 - x, y1 - y))
            
            image = ImageGrab.grab(bbox=(x, y, x+x1, y+y1), all_screens=True)

            if util.is_debug:
                image.save(util.get_relative("screenshot.png"), "PNG")
            return image
        except Exception:
            logger.error("Couldn't get screenshot.")
            return None

    def screenshot_to_clipboard(self):
        try:
            img = self.get_screenshot()
        except OSError:
            logger.error("Couldn't get screenshot.")
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
        game_handle = util.get_game_handle()
        if game_handle:
            self.game_handle = game_handle
            self.game_seen = True

    def stop(self):
        self.should_stop = True
    
    def run_with_catch(self):
        try:
            self.run()
        except Exception:
            util.show_error_box("Critical Error", "Uma Launcher has encountered a critical error and will now close.")
            self.threader.stop()

    def run(self):
        # If Carotene was enabled in the past, run the deprecation procedure.
        if "enable_english_patch" in self.threader.settings and self.threader.settings["enable_english_patch"]:
            logger.info("Disabling Carotene as it has been deprecated.")
            util.show_warning_box("Carotene end of life", """<h2>Support for Carotene English Patch has ended</h2><p>Carotene English Patch will no longer receive updates. Thank you for using my mod!</p><p>Carotene has merged with <b><a href="https://hachimi.leadrdrk.com/">Hachimi</a></b> and translation updates will continue there.<br>Because Hachimi updates itself while the game is running, patching using Uma Launcher is no longer needed and Carotene is automatically being uninstalled.</p><p><b>Installation instructions</b> for Hachimi together with CarrotJuicer can be found <a href="https://umapyoi.net/uma-launcher">on the Uma Launcher website</a>.<p>""")
            self.threader.settings["enable_english_patch"] = False
            umapatcher.unpatch(self.threader)

        # Enable VPN if needed
        if self.threader.settings["vpn_enabled"] and not self.threader.settings["vpn_dmm_only"]:
            self.vpn = vpn.create_client(self.threader, cygames=True)
            self.vpn.connect()

        onetime = True

        while not self.should_stop:
            time.sleep(self.sleep_time)

            # Check if game exists
            if self.game_handle and not win32gui.IsWindow(self.game_handle):
                self.game_handle = None
            if self.game_handle:
                onetime = False
                self.last_seen = time.perf_counter()

            # Game was never seen before
            if not self.game_seen:
                self.check_game()

                if onetime:
                    onetime = False
                    # If DMM is not seen AND Game is not seen: Start DMM
                    if not self.game_seen:
                        # Enable DMM-only VPN
                        if self.threader.settings["vpn_enabled"] and self.threader.settings["vpn_dmm_only"]:
                            self.vpn = vpn.create_client(self.threader)
                            self.vpn.connect()

                        dmm.start()
                
                if not self.game_closed:
                    continue
            # After this, the game was open at some point.

            # Game closed
            if not self.game_handle:
                time_since_seen = time.perf_counter() - self.last_seen
                if time_since_seen < 15.0:
                    self.game_seen = False
                    self.game_closed = True
                    continue

                self.threader.stop()
                self.stop()
                continue

            # Close DMM
            if not self.dmm_closed and self.threader.settings["autoclose_dmm"]:
                # Attempt to close DMM, even if it doesn't exist
                new_dmm_handle = dmm.get_dmm_handle()
                if new_dmm_handle:
                    logger.info("Closing DMM.")
                    win32gui.PostMessage(new_dmm_handle, win32con.WM_CLOSE, 0, 0)
                self.dmm_closed = True

                # Disconnect VPN
                if self.vpn and self.threader.settings["vpn_dmm_only"]:
                    self.vpn.disconnect()
                    self.vpn = None

            if not self.carrotjuicer_closed and self.threader.settings["hide_carrotjuicer"]:
                self.carrotjuicer_handle = util.get_window_handle("Umapyoi", type=util.EXACT)
                if self.carrotjuicer_handle:
                    logger.info("Attempting to minimize CarrotJuicer.")
                    success1 = util.show_window(self.carrotjuicer_handle, win32con.SW_MINIMIZE)
                    success2 = util.hide_window_from_taskbar(self.carrotjuicer_handle)
                    success = success1 and success2
                    if not success:
                        logger.error("Failed to minimize CarrotJuicer")
                    else:
                        self.carrotjuicer_closed = True
                        time.sleep(0.25)
            
            if self.carrotjuicer_closed and not self.threader.settings["hide_carrotjuicer"]:
                logger.debug(f"CarrotJuicer handle: {self.carrotjuicer_handle}")
                if self.carrotjuicer_handle:
                    logger.info("Attempting to restore CarrotJuicer.")
                    success1 = util.show_window(self.carrotjuicer_handle, win32con.SW_RESTORE)
                    success2 = util.unhide_window_from_taskbar(self.carrotjuicer_handle)
                    success = success1 and success2
                    if not success:
                        logger.error("Failed to restore CarrotJuicer")
                    else:
                        self.carrotjuicer_closed = False
                        time.sleep(0.25)

            self.sleep_time = 1.0  # TODO: Maybe 2.0?

            # Game is open, DMM is closed. Do screen state stuff

            self.update()
            cur_update = time.time()

            if self.threader.settings["discord_rich_presence"]:
                if not self.rpc:
                    try:
                        self.rpc_latest_state = None
                        self.event_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(self.event_loop)
                        self.rpc = pypresence.Presence(self.rpc_client_id)
                        self.rpc.connect()
                    except Exception:
                        continue

                # Get the latest screen state.
                if self.rpc and cur_update - self.rpc_last_update > 15:
                    if self.rpc_latest_state != self.screen_state:
                        logger.debug(f"Updating Rich Presence state: {self.screen_state.main}, {self.screen_state.sub}")
                    self.rpc_last_update = cur_update
                    self.rpc_latest_state = self.screen_state
                    try:
                        self.rpc.update(**self.screen_state.to_dict())
                    except Exception:
                        # RPC not connected. Continue
                        self.close_rpc()
                        pass
            elif self.rpc:
                self.close_rpc()

        if self.rpc:
            self.close_rpc()

        if self.vpn:
            self.vpn.disconnect()
            self.vpn = None
        return

    def close_rpc(self):
        try:
            self.rpc.clear()
            self.rpc.close()
        except Exception:
            pass
        self.rpc = None

        asyncio.set_event_loop(None)
        self.event_loop.stop()
        self.event_loop.close()
        self.event_loop = None
        self.rpc_latest_state = None
        return

    def update(self):
        new_state = self.determine_state()

        if new_state == self.screen_state:
            return

        # New state is different
        self.screen_state = new_state
        logger.debug(f"Determined state: {self.screen_state.main}, {self.screen_state.sub}")

    def determine_state(self):
        # Carrotjuicer takes priority
        if self.carrotjuicer_state:
            tmp = self.carrotjuicer_state
            self.carrotjuicer_state = None
            return tmp
        else:
            new_state = ScreenState(self)
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

                            if pixel_color is None:
                                logger.warning(f"Couldn't get pixel color at {pos}.")
                                break

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
