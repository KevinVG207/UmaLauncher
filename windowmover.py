import time
from loguru import logger
import util


class GameWindow():
    # Object to be shared with Threader and holds functions to manipulate the game window.
    carrotjuicer_maximized_trigger = False

    def __init__(self, handle):
        self.handle = handle
        return

    def get_rect(self):
        rect = util.get_window_rect(self.handle)
        if not rect:
            return None, None
        return rect, rect_is_portrait(rect)

    def set_pos(self, pos):
        if pos[2] < 1 or pos[3] < 1:
            logger.error(f"Trying to set window to invalid size: {pos}")
            logger.error("Skipping")
            return False
        success = util.move_window(self.handle, pos[0], pos[1], pos[2], pos[3], True)
        if not success:
            logger.error(f"Could not move window. {self.handle}")
        return success

    def get_workspace_rect(self):
        monitor = util.monitor_from_window(self.handle)
        if not monitor:
            return None
        monitor_info = util.get_monitor_info(monitor)
        if not monitor_info:
            return None
        return monitor_info.get("Work")

    def calc_max_and_center_pos(self):
        workspace_rect = self.get_workspace_rect()
        if not workspace_rect:
            logger.error("Cannot find workspace of game window")
            return

        # Get the current game rect, dejankify it and turn it into pos.
        game_rect, is_portrait = self.get_rect()
        game_rect = dejankify(list(game_rect))
        game_pos = rect_to_pos(game_rect)

        # Get workspace w/h
        workspace_height = float(workspace_rect[3] - workspace_rect[1])
        workspace_width = float(workspace_rect[2] - workspace_rect[0])

        # Scale game based on height.
        multiplier = workspace_height / game_pos[3]
        new_game_height = round(game_pos[3] * multiplier)
        new_game_width = util.get_width_from_height(new_game_height, is_portrait)

        # Check if game is too wide, scale based on width.
        if new_game_width > workspace_width:
            multiplier = workspace_width / new_game_width
            new_game_height = round(new_game_height * multiplier)
            new_game_width = util.get_width_from_height(new_game_height, is_portrait)
        else:
            new_game_width = round(new_game_width)

        # Calcualte the new top-left x and y position
        new_x = workspace_rect[0] + round((workspace_width * 0.5) - (new_game_width * 0.5))
        new_y = workspace_rect[1] + round((workspace_height * 0.5) - (new_game_height * 0.5))

        # Create the new game rect
        new_game_rect = [
            new_x,
            new_y,
            new_x + util.get_width_from_height(new_game_height, is_portrait),
            new_y + new_game_height
        ]

        # Re-add jank before resizing window
        new_game_rect = jankify(new_game_rect)
        new_game_pos = rect_to_pos(new_game_rect)
        new_game_pos[2] = util.get_width_from_height(new_game_pos[3], is_portrait)
        return new_game_pos, is_portrait

    def maximize_and_center(self):
        self.set_pos(self.calc_max_and_center_pos()[0])
        return


JANK_OFFSET = 8

def dejankify(rect):
    rect[0] = rect[0] + JANK_OFFSET
    rect[2] = rect[2] - JANK_OFFSET
    rect[3] = rect[3] - JANK_OFFSET
    return rect

def jankify(rect):
    rect[0] = rect[0] - JANK_OFFSET
    rect[2] = rect[2] + JANK_OFFSET
    rect[3] = rect[3] + JANK_OFFSET
    return rect

def rect_is_portrait(rect):
    return rect[3] - rect[1] > rect[2] - rect[0]

def rect_to_pos(rect):
    return [rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1]]

def pos_to_rect(pos):
    return [pos[0], pos[1], pos[0] + pos[2], pos[1] + pos[3]]


class WindowMover():
    should_stop = False

    last_portrait = None
    last_rect = None
    window = None
    prev_auto_resize = None

    def __init__(self, threader):
        self.threader = threader
        self.screenstate = threader.screenstate
        self.window = None
        self.prev_auto_resize = self.threader.settings.get_tray_setting("Lock game window")
    
    def try_maximize(self):
        if self.window:
            new_pos, is_portrait = self.window.calc_max_and_center_pos()
            self.threader.settings.save_game_position(new_pos, is_portrait)
            self.window.set_pos(new_pos)
            self.threader.carrotjuicer.reset_browser = True

    def stop(self):
        self.should_stop = True

    def run(self):
        while not self.should_stop and not self.screenstate.game_handle:
            time.sleep(0.25)

        self.window = GameWindow(self.screenstate.game_handle)

        while not self.should_stop and self.screenstate.game_handle:
            time.sleep(0.25)
            game_rect, is_portrait = self.window.get_rect()

            if not game_rect:
                continue

            # Keep maximize option in the tray.
            # Toggle to auto-resize

            auto_resize = self.threader.settings.get_tray_setting("Lock game window")

            if auto_resize:

                # Just enabled auto-resize. Save current window position so it can be re-used.
                if not self.prev_auto_resize:
                    self.threader.settings.save_game_position(rect_to_pos(game_rect), portrait=is_portrait)

                # Already in auto-resize but orientation changed. Save the previous orientation's position.
                if self.last_portrait != is_portrait:
                    if self.last_rect:
                        self.threader.settings.save_game_position(rect_to_pos(self.last_rect), portrait=self.last_portrait)

                # Load current orientation's position and apply.
                # If None: maximize.
                new_pos = self.threader.settings.load_game_position(portrait=is_portrait)
                if new_pos:
                    self.window.set_pos(new_pos)
                else:
                    new_pos, is_portrait = self.window.calc_max_and_center_pos()
                    self.threader.settings.save_game_position(new_pos, is_portrait)
                    self.window.set_pos(new_pos)

                # Position may have changed: update variables.
                game_rect, is_portrait = self.window.get_rect()
                if not game_rect:
                    continue

            self.prev_auto_resize = auto_resize
            self.last_portrait = is_portrait
            self.last_rect = game_rect

        return
