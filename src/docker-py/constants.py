import os


RUN_DIR = os.path.abspath(os.path.dirname(__file__))

def RUN_PATH(*file_parts: str):
    return os.path.join(RUN_DIR, *file_parts)


IMG_DIR = os.path.join(RUN_DIR, "img")

def IMG_PATH(img_filename: str):
    return os.path.join(IMG_DIR, img_filename)