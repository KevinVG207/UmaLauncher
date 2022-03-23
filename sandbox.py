from PIL import Image, ImageFilter
import os
import ocr
import re

path = "_ocr/_raw/_char_icons/"

for file in os.listdir(path):
    try:
        if file.split("_", 3)[3].startswith("1"):
            print(file)
            img = Image.open(path + file)
            img = img.crop((25, 48, 25+206, 48+94))
            img = img.resize((32, 16))
            img = ocr.preprocess_image(img)
            img.save(path + "processed/" + file)

    except IndexError:
        pass

        # img = Image.open("_ocr/_raw/" + file)
        # img = img.convert("L")
        # img = img.point(lambda x: 0 if x < 200 else 255)
        # img.save("_ocr/" + file)
