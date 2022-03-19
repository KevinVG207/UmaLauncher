import time
from PIL import Image

numbers_top = 675
numbers_top_fraction = 0.66964

numbers_left = (
    (
        60,
        75,
        89
    ),
    (
        151,
        165,
        180
    ),
    (
        237,
        252,
        266
    ),
    (
        326,
        340,
        355
    ),
    (
        414,
        428,
        443
    )
)

number_width_height = (13, 18)
screen_width_height = (564, 1008)

right_sides = (
    102,
    193,
    279,
    368,
    456
)

right_sides_fractions = (
    0.18085,
    0.34220,
    0.49468,
    0.65248,
    0.80851
)

big_number_wh = (0.02305, 0.01786)
spacing_between_big_numbers = 0.00266


def preprocess_image(img: Image.Image) -> Image:
    preprocessed = img.convert("L")
    preprocessed = preprocessed.point(lambda x: 0 if x < 200 else 255)
    return preprocessed


def get_big_stat_number_bounding_boxes(right, top, img: Image.Image):
    # Assumes there are three numbers.
    top_pxl = top * img.height
    right_pxl = right * img.width
    number_width_pxl = big_number_wh[0] * img.width
    number_height_pxl = big_number_wh[1] * img.height
    spacing_pxl = spacing_between_big_numbers * img.width

    bounding_boxes = list()
    
    for i in range(3):
        cur_right_pxl = right_pxl - (number_width_pxl + spacing_pxl) * i
        cur_bb = (
            round(cur_right_pxl - number_width_pxl),
            round(top_pxl),
            round(cur_right_pxl),
            round(top_pxl + number_height_pxl)
        )
        bounding_boxes.append(cur_bb)
    return reversed(bounding_boxes)


def get_all_big_number_bounding_boxes_(img: Image.Image, export: bool = False):
    if export:
        now = time.time()
        num = 0
    for right_side in right_sides_fractions:
        bounding_boxes = get_big_stat_number_bounding_boxes(right_side, numbers_top_fraction, img)
        for bb in bounding_boxes:
            print(img.width, img.height)
            print(bb)
            num_img = img.crop(bb)
            num_img = num_img.resize((8, 10))
            num_img = preprocess_image(num_img)
            if export:
                num_img.save(f"_ocr/_ref/_big_num/{str(now)}_{str(num)}.png", "PNG")
                num += 1