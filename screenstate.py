import time
from PIL import Image
import presence_screens as scr
import ocr
from loguru import logger
import util

class ScreenState:
    def __init__(self):
        self.main = "Launching game..."
        self.sub = "Ready your umapyois!"
        self.start_time = time.time()


    def get_state(self) -> dict:
        logger.info(f"Updating Rich Presence state: {self.main}, {self.sub}")
        return {
            "state": self.sub,
            "details": self.main,
            "start": self.start_time
        }


    def update(self, image: Image.Image, debug = False):
        self.determine_location(image, debug)
        logger.info(f"Determined state: {self.main}, {self.sub}")
    
    def determine_location(self, image: Image.Image, debug = False) -> str:
        try:
            for main_screen in scr.screens:
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
                        self.main = "Main Menu"
                        self.sub = tmp_subscr
                        if tmp_subscr == "Home":
                            for home_sub_name, home_sub_pixels in scr.screens["Main Menu"]["Home"]["home_sub"].items():
                                failed = False
                                for home_sub_pixel in home_sub_pixels.values():
                                    pixel_color = util.get_position_rgb(image, home_sub_pixel["pos"])
                                    if not util.similar_color(pixel_color, home_sub_pixel["col"]):
                                        failed = True
                                        break
                                if not failed:
                                    self.sub = home_sub_name
                else:
                    failed = False
                    for check_target in scr.screens[main_screen].values():
                        pos = check_target["pos"]
                        col = check_target["col"]
                        pixel_color = util.get_position_rgb(image, pos)

                        if not util.similar_color(pixel_color, col):
                            failed = True
                    
                    if not failed:
                        if main_screen == "Training":
                            # We are in training (probably)
                            stats_dict = ocr.get_training_stats(image, debug)

                            if len(stats_dict) < 6:
                                self.sub = " ".join(stats_dict.values())
                            else:
                                self.sub = " ".join(list(stats_dict.values())[:-1]) + " | " + list(stats_dict.values())[-1]
                            self.main = "Training"
                        if main_screen == "Concert Theater":
                            self.sub = "Vibing"
                            self.main = "Concert Theater"
            
        except IOError:
            # This may occur if the screen is not visible?
            pass
