import win32gui
from loguru import logger
import ocr
from PIL import Image

print(ocr.get_training_stats(Image.open("_ocr/_raw/1000stat/cropped1.png"), True))