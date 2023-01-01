import time
import win32gui
import win32api
from loguru import logger

# TODO: Fix resize during concert
# Catch the first resize during concert?
# Trigger an event when user interacts with resize?
# On resize, check how big the change is?

class GameWindow():
    # Object to be shared with Threader and holds functions to manipulate the game window.
    def __init__(self, handle):
        self.handle = handle
        return

    def get_rect(self):
        rect = win32gui.GetWindowRect(self.handle)
        return rect, rect_is_portrait(rect)

    def set_pos(self, pos):
        if pos[2] < 1 or pos[3] < 1:
            logger.error(f"Trying to set window to invalid size: {pos}")
            logger.error("Skipping")
            return
        win32gui.MoveWindow(self.handle, pos[0], pos[1], pos[2], pos[3], True)

    def get_workspace_rect(self):
        monitor = win32api.MonitorFromWindow(self.handle)
        return win32api.GetMonitorInfo(monitor).get("Work") if monitor else None

    def maximize(self):
        workspace_rect = self.get_workspace_rect()
        if not workspace_rect:
            logger.error("Cannot find workspace of game window")
            return

        # Get the current game rect, dejankify it and turn it into pos.
        game_rect, _ = self.get_rect()
        game_rect = dejankify(list(game_rect))
        game_pos = rect_to_pos(game_rect)

        # Get workspace w/h
        workspace_height = workspace_rect[3] - workspace_rect[1]
        workspace_width = workspace_rect[2] - workspace_rect[0]

        # Scale game based on height.
        multiplier = workspace_height / game_pos[3]
        new_game_width = round(game_pos[2] * multiplier)
        new_game_height = round(game_pos[3] * multiplier)

        # Check if game is too wide, scale based on width.
        if new_game_width > workspace_width:
            multiplier = workspace_width / new_game_width
            new_game_height = round(new_game_height * multiplier)
            new_game_width = round(new_game_width * multiplier)
            logger.info(f"{new_game_width} {new_game_height}")

        # Calcualte the new top-left x and y position
        new_x = workspace_rect[0] + round((workspace_width * 0.5) - (new_game_width * 0.5))
        new_y = workspace_rect[1] + round((workspace_height * 0.5) - (new_game_height * 0.5))

        # Create the new game rect
        new_game_rect = [
            new_x,
            new_y,
            new_x + new_game_width,
            new_y + new_game_height
        ]

        # Re-add jank before resizing window
        new_game_rect = jankify(new_game_rect)
        self.set_pos(rect_to_pos(new_game_rect))
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
    return (rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1])

def pos_to_rect(pos):
    return (pos[0], pos[1], pos[0] + pos[2], pos[1] + pos[3])


class WindowMover():
    should_stop = False

    last_portrait = None
    last_rect = None
    window = None

    def __init__(self, threader):
        self.threader = threader
        self.screenstate = threader.screenstate
        self.window = None
    
    def try_maximize(self):
        if self.window:
            self.window.maximize()

    def stop(self):
        self.should_stop = True

    def run(self):
        while not self.should_stop and not self.screenstate.game_handle:
            time.sleep(0.2)
        
        self.window = GameWindow(self.screenstate.game_handle)
        
        while not self.should_stop and self.screenstate.game_handle:
            time.sleep(0.25)
            game_rect, is_portrait = self.window.get_rect()

            if self.last_portrait != is_portrait:
                # Orientation change; Save previous position.
                if self.last_rect:
                    self.threader.settings.save_game_position(rect_to_pos(self.last_rect), portrait=self.last_portrait)

                # Try to load saved position
                saved_pos = self.threader.settings.load_game_position(portrait=is_portrait)
                if saved_pos:
                    # Set to saved position
                    self.window.set_pos(saved_pos)
                else:
                    # Move to center/fullscreen
                    self.window.maximize()

                game_rect, is_portrait = self.window.get_rect()

            self.last_portrait = is_portrait
            self.last_rect = game_rect

        self.threader.settings.save_game_position(rect_to_pos(self.last_rect), portrait=self.last_portrait)
        return
