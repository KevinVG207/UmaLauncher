from PIL import Image
import presence_screens as scr

class ScreenState:
    def __init__(self, image: Image.Image):
        self.screen = str()
        self.subscreen = str()
        self.determine_location(image)


    def has_state(self) -> bool:
        if self.screen and self.subscreen:
            return True
        return False


    def get_state(self) -> dict:
        print(self.screen, self.subscreen)
        return {
            "state": self.subscreen,
            "details": self.screen
        }

    
    def determine_location(self, image: Image.Image) -> str:
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
            self.screen = "Main Menu"
            self.subscreen = tmp_subscr


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