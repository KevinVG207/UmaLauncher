import util
from loguru import logger
from PIL import Image
import math
import ocr
import time
import elevate
elevate.elevate()


default_window_size = (564, 1008)
training_button_diameter = 0.176366843
training_button_left_offset = 0.0590828924

def estimate_energy(image: Image.Image, max_energy: int = 100) -> int:
    energy_bar_start = math.ceil(image.width * 0.3156)
    energy_bar_end = math.ceil(image.width * 0.7039)
    energy_bar_height = round(image.height * 0.125496)
    energy_bar_length = energy_bar_end - energy_bar_start
    energy_bg_color = (118, 117, 118)
    energy_pixels = 0
    for i in range(energy_bar_start, energy_bar_end):
        cur_pixel = image.getpixel((i, energy_bar_height))
        if util.similar_color(cur_pixel, energy_bg_color):
            break
        energy_pixels += 1
    energy = round(energy_pixels / energy_bar_length * max_energy, 2)
    logger.info(f"Estimated energy: {energy}")
    return energy


def get_training_button_x_fraction(button_number: int) -> int:
    return training_button_left_offset + (training_button_diameter / 2) + (button_number * training_button_diameter)


def get_training_fail_chance(button_number: int, img: Image.Image) -> float:
    button_x_fraction = get_training_button_x_fraction(button_number)
    button_x_pixel = math.ceil(img.width * button_x_fraction)
    start_height = 0.71031746
    stop_height = 0.736111111
    start_pixel_height = math.floor(img.height * start_height)
    stop_pixel_height = math.ceil(img.height * stop_height)
    gottem = None
    for i in range(start_pixel_height, stop_pixel_height):
        pixel_color = img.getpixel((button_x_pixel, i))
        if util.similar_color(pixel_color, (255, 150, 0)) or util.similar_color(pixel_color, (13, 150, 255)) or util.similar_color(pixel_color, (255, 69, 0)):
            gottem = i
            break
    if gottem is None:
        logger.error("Could not find training fail chance box!")
        return None

    text_top_offset = 0.007936
    text_top_pixels = round(img.height * text_top_offset)
    text_bottom_offset = 0.0233
    text_bottom_pixels = round(img.height * text_bottom_offset)
    searching_distance = 0.026455
    searching_pixels = round(img.width * searching_distance)

    pixels_until_number_found = None

    # TODO: Search from the right (percent sign) instead so the starting point can be consistent.

    for i in range(searching_pixels):
        for j in range(text_top_pixels, text_bottom_pixels):
            pixel_color = img.getpixel((button_x_pixel + i, gottem + j))
            if util.similar_color(pixel_color, (255, 255, 255)) or util.similar_color(pixel_color, (255, 218, 18)):
                pixels_until_number_found = i
                logger.info(f"Found number at {button_x_pixel} + {i}, {gottem} + {j}")
                break
        if pixels_until_number_found is not None:
            break
    
    if pixels_until_number_found is None:
        logger.error("Could not find training fail chance number!")
        return None
    
    distance_to_number = pixels_until_number_found / img.width

    number_width = 0.022046

    if distance_to_number < 0.0194:
        logger.info("Found a two-digit fail chance number.")
        bbox1 = (button_x_pixel + pixels_until_number_found - 1, gottem + text_top_pixels, round(button_x_pixel + pixels_until_number_found - 1 + (number_width * img.width)), gottem + text_bottom_pixels)
        bbox2 = (round(button_x_pixel + pixels_until_number_found - 1 + (number_width * img.width)), gottem + text_top_pixels, round(button_x_pixel + pixels_until_number_found - 1 + 2 * (number_width * img.width)), gottem + text_bottom_pixels)

        num1 = img.crop(bbox1)
        num2 = img.crop(bbox2)

        num1 = ocr.preprocess_image(num1, True)
        num1.save("num1.png")
        num2 = ocr.preprocess_image(num2, True)
        num2.save("num2.png")

        logger.info(ocr.most_likely_big_number(num1))
        logger.info(ocr.most_likely_big_number(num2))
        return (10 * int(ocr.most_likely_big_number(num1)) + int(ocr.most_likely_big_number(num2))) / 100
    logger.info("Found a one-digit fail chance number.")
    bbox = (button_x_pixel + pixels_until_number_found - 1, gottem + text_top_pixels, round(button_x_pixel + pixels_until_number_found - 1 + (number_width * img.width)), gottem + text_bottom_pixels)
    num1 = img.crop(bbox)
    num1 = ocr.preprocess_image(num1, True)
    logger.info(ocr.most_likely_big_number(num1))
    return int(ocr.most_likely_big_number(num1)) / 100


def click_training_button(button_number: int):
    global game_handle
    x_fraction = get_training_button_x_fraction(button_number)
    y_fraction = 0.845238
    util.move_mouse_to_window_coords(game_handle, util.convert_fractions_to_window_coords(game_handle, (x_fraction, y_fraction)), click=True if button_number != 0 else False)


def get_all_fail_chances():
    global game_handle
    fail_chances = []
    for i in range(5):
        click_training_button(i)
        time.sleep(0.2)
        while True:
            cur_fail_chance = get_training_fail_chance(i, util.take_screenshot(game_handle))
            if cur_fail_chance is not None:
                fail_chances.append(cur_fail_chance)
                break
            logger.info("Could not get fail chance for training button #" + str(i))
            time.sleep(0.01)
    return fail_chances


def main():
    global game_handle
    game_handle = util.get_window_handle("umamusume", util.EXACT)
    img = util.take_screenshot(game_handle)
    img.save("screenshot.png")
    print(get_all_fail_chances())

    # estimate_energy(img)



if __name__ == "__main__":
    main()