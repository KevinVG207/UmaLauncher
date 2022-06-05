import time
import util
from PIL import Image
import random


def get_pixel_values(img: Image.Image) -> tuple:
    num_values = list()
    for x in range(img.width):
        for y in range(img.height):
            pixel_value = img.getpixel((x, y))
            if pixel_value > 125:
                num_values.append(1)
            else:
                num_values.append(0)
    return tuple(num_values)


big_num_ref_path = "_ocr/_ref/_big_num/"

big_number_references = dict()
for i in range(11):
    key = i
    if i == 10:
        key = ""
        cur_image = Image.open(f"{big_num_ref_path}None.png").convert("L")
    else:
        cur_image = Image.open(f"{big_num_ref_path}{str(i)}.png").convert("L")
    big_number_references[key] = get_pixel_values(cur_image)
    cur_image.close()


numbers_top_fraction = 0.66964

right_sides_fractions = (
    0.18085,
    0.34220,
    0.49468,
    0.65248,
    0.80851
)


three_number_wh = (0.02305, 0.01786)
spacing_between_three_numbers = 0.00266
four_number_wh = (0.02028, 0.01786)
spacing_between_four_numbers = 0.00220


def preprocess_image(img: Image.Image) -> Image:
    preprocessed = img.convert("L")
    preprocessed = preprocessed.point(lambda x: 0 if x < 200 else 255)
    return preprocessed


def has_four_numbers(right, top, img: Image.Image) -> bool:
    check_coords = (right - 0.079365, top + three_number_wh[1] / 2)
    check_pxl = util.get_position_rgb(img, check_coords)
    return not util.similar_color(check_pxl, (255, 255, 255))


def get_big_stat_number_bounding_boxes(right, top, img: Image.Image):
    if has_four_numbers(right, top, img):
        return get_four_numbers_bounding_boxes(right, top, img)
    else:
        return get_three_numbers_bounding_boxes(right, top, img)


def get_four_numbers_bounding_boxes(right, top, img: Image.Image):
    # Assumes there are four numbers.
    top_pxl = top * img.height
    right_pxl = right * img.width
    number_width_pxl = four_number_wh[0] * img.width
    number_height_pxl = four_number_wh[1] * img.height
    spacing_pxl = spacing_between_four_numbers * img.width

    bounding_boxes = list()
    
    for i in range(4):
        cur_right_pxl = right_pxl - (number_width_pxl + spacing_pxl) * i
        cur_bb = (
            round(cur_right_pxl - number_width_pxl),
            round(top_pxl),
            round(cur_right_pxl),
            round(top_pxl + number_height_pxl)
        )
        bounding_boxes.append(cur_bb)
    return reversed(bounding_boxes)


def get_three_numbers_bounding_boxes(right, top, img: Image.Image):
    # Assumes there are three numbers.
    top_pxl = top * img.height
    right_pxl = right * img.width
    number_width_pxl = three_number_wh[0] * img.width
    number_height_pxl = three_number_wh[1] * img.height
    spacing_pxl = spacing_between_three_numbers * img.width

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


def get_skill_points_bounding_boxes(img: Image.Image) -> list:
    # Assumes there are three numbers.
    top_pxl = 0.6765 * img.height
    right_pxl = 0.936 * img.width
    number_width_pxl = three_number_wh[0] * img.width * 1
    number_height_pxl = three_number_wh[1] * img.height * 1.05
    spacing_pxl = spacing_between_three_numbers * img.width * 1.25

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


def most_likely_big_number(img: Image.Image) -> int:
    pixel_values = get_pixel_values(img)
    scores = list()
    for number, ref_values in big_number_references.items():
        correct = 0
        for i in range(len(pixel_values)):
            if pixel_values[i] == ref_values[i]:
                correct += 1
        scores.append((number, correct))
    scores.sort(key= lambda x: x[1], reverse=True)
    return scores[0][0]


def bounding_boxes_to_stats(bounding_boxes: list, img: Image.Image, export: bool = False) -> list:
    cur_stat = list()
    for bb in bounding_boxes:
        num_img = img.crop(bb)
        num_img = num_img.resize((12, 18))
        num_img = preprocess_image(num_img)
        if export:
            now = time.time()
            num = 0
            num_img.save(f"_ocr/_tmp/{str(now)}_{str(num + random.randint(0,10000))}.png", "PNG")
            num += 1
        cur_stat.append(most_likely_big_number(num_img))
    return cur_stat


def get_all_big_numbers(img: Image.Image, export: bool = False) -> list:
    stats = list()
    # Training stats
    for right_side in right_sides_fractions:
        bounding_boxes = get_big_stat_number_bounding_boxes(right_side, numbers_top_fraction, img)
        stats.append(bounding_boxes_to_stats(bounding_boxes, img, export))
    
    # Skill points
    bounding_boxes = get_skill_points_bounding_boxes(img)
    stats.append(bounding_boxes_to_stats(bounding_boxes, img, export))

    return stats


def get_training_stats(image: Image.Image, export: bool = False) -> dict:
    stat_types = (
        "Speed",
        "Stamina",
        "Power",
        "Guts",
        "Intelligence",
        "Skill Pt"
    )

    out = dict()

    raw_stats = get_all_big_numbers(image, export)
    for i in range(len(raw_stats)):
        cur_type_stats = raw_stats[i]
        number_str = str()
        for number in cur_type_stats:
            number_str += str(number)
        out[stat_types[i]] = number_str
    
    return out