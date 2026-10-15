from glob import glob

import cv2 as cv
import pytesseract
import regex as re

def main():
    files = sorted(glob('./examples/*.png') + glob('./examples/*.jpg'))
    for fn in files:
        img = cv.imread(fn)
        if img is None:
            continue
        print(img_to_apuesta(img))

regex = re.compile("(?<=(apuesta|jug(a|r)da).*)\\d+(\\.|,)*\\d*", re.IGNORECASE)
def img_to_apuesta(img):
    extracted_text = pytesseract.image_to_string(img)
    match = regex.search(extracted_text)
    if match == None:
        return None
    str = match.group().replace(',', '.')
    return float(str)


if __name__ == '__main__':
    main()
