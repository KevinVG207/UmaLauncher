import util
from loguru import logger
from PIL import Image
import math
import cv2
import numpy as np

default_window_size = (564, 1008)
failchance = Image.open("_ocr/_ref/_training/failchance.png")
failpercent = Image.open("_ocr/_ref/_training/failpercent.png")
failchance_blue = Image.open("_ocr/_ref/_training/failchance_blue.png")
failpercent_blue = Image.open("_ocr/_ref/_training/failpercent_blue.png")


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


def pil_image_to_cv2_image(pil_image, size_multiplier=1) -> cv2.Mat:
    return cv2.cvtColor(np.array(pil_image.resize((round(pil_image.width * size_multiplier), round(pil_image.height * size_multiplier)))), cv2.COLOR_RGB2BGR)


def get_template_match_bbox(big_cv_image, small_cv_image, method=cv2.TM_CCOEFF_NORMED) -> tuple[int,int,int,int]:
    template_matches = cv2.matchTemplate(big_cv_image, small_cv_image, method)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(template_matches)
    top_left = max_loc
    logger.info(top_left)
    logger.info(small_cv_image.shape[0])
    logger.info(small_cv_image.shape[1])
    bottom_right = (top_left[0] + small_cv_image.shape[1], top_left[1] + small_cv_image.shape[0])

    cv2.rectangle(big_cv_image, top_left, bottom_right, (0, 0, 255), 2)
    cv2.imshow("big_cv_image", big_cv_image)
    cv2.waitKey(0)

    return top_left + bottom_right


def get_fail_chance_bbox(cv_image: cv2.Mat, size_multiplier: float) -> tuple[int,int,int,int]:
    failchance_cv2 = pil_image_to_cv2_image(failchance_blue, size_multiplier)
    failpercent_cv2 = pil_image_to_cv2_image(failpercent, size_multiplier)
    failchance_bbox = get_template_match_bbox(cv_image, failchance_cv2)
    failpercent_bbox = get_template_match_bbox(cv_image, failpercent_cv2)
    logger.info(f"Failchance bbox: {failchance_bbox}")
    logger.info(f"Failpercent bbox: {failpercent_bbox}")
    fail_chance_numbers_bbox = (failchance_bbox[2], failchance_bbox[1], failpercent_bbox[0], failpercent_bbox[3])
    
    return fail_chance_numbers_bbox

def get_fail_chance(img: Image.Image, cv_image: cv2.Mat, size_multiplier: float) -> int:
    bbox = get_fail_chance_bbox(cv_image, size_multiplier)
    fail_chance_crop = img.crop(bbox)
    fail_chance_crop.save("fail_chance_crop.png")
    return 0


def main():
    game_handle = util.get_window_handle("umamusume", util.EXACT)
    img = util.take_screenshot(game_handle)
    cv_image = pil_image_to_cv2_image(img)
    img.save("screenshot.png")
    size_multiplier = img.height / default_window_size[1]
    training_selection_crop = img.crop((round(32 * size_multiplier), round(717 * size_multiplier), round(32+100 * size_multiplier), round(717+210 * size_multiplier)))
    training_selection_crop_cv2 = pil_image_to_cv2_image(training_selection_crop)
    training_selection_crop.save("training_selection_crop.png")
    fail_chance = get_fail_chance(training_selection_crop, training_selection_crop_cv2, size_multiplier)
    # estimate_energy(img)



if __name__ == "__main__":
    main()