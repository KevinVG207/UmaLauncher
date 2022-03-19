from PIL import Image, ImageFilter
import os
import ocr

for file in os.listdir("_ocr/_raw/"):
    img = Image.open("_ocr/_raw/" + file)
    img = img.convert("L")
    img = img.point(lambda x: 0 if x < 200 else 255)
    img.save("_ocr/" + file)

count = 0
total = 0
for group in ocr.numbers_left:
    total += group[1] - group[0]
    total += group[2] - group[1]
    count += 2
average = total / count
spacing = average - ocr.number_width_height[0]
fraction_spacing = spacing / ocr.screen_width_height[0]
num_width_height_fraction = (ocr.number_width_height[0] / ocr.screen_width_height[0], ocr.number_width_height[1] / ocr.screen_width_height[1])
print(f"Average distance between numbers: {average}")
print(f"Spacing: {spacing}")
print(f"Spacing in fraction: {fraction_spacing}")
print(f"Number in fraction {num_width_height_fraction}")

