import cv2

import os
import glob

import brightness_correction
import image_processing

# marker image folder for testing
home_path = os.path.expanduser('~')
marker_path = home_path + "/Pictures/marker"

for file in glob.glob(marker_path + "/*_Raw.jpg"):
    src_rgb,src_gray=image_processing.load_image(file)

    dst = brightness_correction.BrightnessAndContrastAuto(src_rgb, 2.0)

    #it shows small image as display resolution is higher than image resolution
    small_src = image_processing.scale_image(src_rgb, 0.5, 0.5)
    small_dst = image_processing.scale_image(dst, 0.5, 0.5)
    cv2.imshow("src", small_src)
    cv2.imshow("src_collection", small_dst)

    cv2.waitKey(0)
