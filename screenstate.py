import time
from PIL import Image
import presence_screens as scr
import ocr

class ScreenState:
    def __init__(self):
        self.main = "Launching game..."
        self.sub = str()
        self.start_time = time.time()
        self.training_horse = str()


    def has_state(self) -> bool:
        if self.main and self.sub:
            return True
        return False


    def get_state(self) -> dict:
        print(self.main, self.sub)
        return {
            "state": self.sub,
            "details": self.main,
            "start": self.start_time
        }


    def update(self, image: Image.Image, debug = False):
        self.determine_location(image, debug)
    
    def determine_location(self, image: Image.Image, debug = False) -> str:
        try:
            # Main Menu:
            count = 0
            tmp_subscr = str()
            for subscreen, subscr_data in scr.screens["Main Menu"].items():
                pos = subscr_data["pos"]
                col = subscr_data["col"]
                pixel_color = get_position_rgb(image, pos)

                tab_enabled = similar_color(pixel_color, col)
                tab_visible = similar_color(pixel_color, (226, 223, 231))

                if tab_enabled or tab_visible :
                    # Current pixel should be part of the menu
                    count += 1
                    if tab_enabled:
                        tmp_subscr = subscreen
                else:
                    break
            if count == 5 and tmp_subscr:
                # All menu items found and one is enabled. This must be the home menu.
                self.training_horse = str()
                self.main = "Main Menu"
                self.sub = tmp_subscr
            
            for check_target in scr.screens["Training"].values():
                # Check if we're in training.
                pos = check_target["pos"]
                col = check_target["col"]
                pixel_color = get_position_rgb(image, pos)

                if similar_color(pixel_color, col):
                    # We are in training (probably)
                    stats_dict = ocr.get_training_stats(image, debug)

                    if len(stats_dict) < 6:
                        self.sub = " ".join(stats_dict.values())
                    else:
                        self.sub = " ".join(stats_dict.values()[:-1]) + " | " + stats_dict.values()[-1]
                    self.main = "Training"
        except IOError:
            # This may occur if the screen is not visible?
            pass


def get_position_rgb(image: Image.Image, position: tuple[float,float]) -> tuple[int,int,int]:
    pixel_color = None
    pixel_pos = (round(image.width * position[0]), round(image.height * position[1]))
    try:
        pixel_color = image.getpixel(pixel_pos)
    except IndexError:
        pass
    return pixel_color


def similar_color(col1: tuple[int,int,int], col2: tuple[int,int,int], threshold: int = 32) -> bool:
    total_diff = 0
    for i in range(3):
        total_diff += abs(col1[i] - col2[i])
    return total_diff < threshold