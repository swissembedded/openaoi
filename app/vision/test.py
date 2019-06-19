# Test
# This file is part of the opensoldering project distribution (https://github.com/swissembedded/opensolderingrobot.git).
# Copyright (c) 2019 by Daniel Haensse
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import cv2
import numpy as np

import find_marker
import image_processing
import brightness_correction

import os
import glob

# marker image folder for testing
marker_path = "../../testdata/images"

for marker in range(1,4):
    marker_rgb,marker_gray=image_processing.load_image(marker_path+"/marker"+str(marker)+".jpg")
    heightm, widthm, channelsm = marker_rgb.shape

    for file in glob.glob(marker_path + "/marker"+str(marker)+"_*.jpg"):

        image_rgb,image_gray=image_processing.load_image(file)

        #brightness correction
        image_rgb,image_gray = brightness_correction.BrightnessAndContrastAuto(image_rgb, 2.0)

        heighti, widthi, channelsi = image_rgb.shape

        hintPos=[widthi/2.0, heighti/2.0]

        if marker==1:
            markers, templatelocm,keypointsm=find_marker.find_marker(image_gray, [141.33, 141.33], "Circular", [2.2, 2.2], "Rectangular", [3.0, 3.0], marker_gray, 0.6, hintPos)
        elif marker==2:
            markers, templatelocm,keypointsm=find_marker.find_marker(image_gray, [141.33, 141.33], "Circular", [2.0, 2.0], "Rectangular", [3.0, 3.0], marker_gray, 0.6, hintPos)
        elif marker==3:
            markers, templatelocm,keypointsm=find_marker.find_marker(image_gray, [141.33, 141.33], "Circular", [3.0, 3.0], "Rectangular", [3.0, 3.0], marker_gray, 0.6, hintPos)

        print("image", file, "found markers", markers)

        # Show the final image with the matched area.
        # primary marker is red
        for m, elem in enumerate(markers):
            if m==0:
                color=(0,0,255)
            else:
                color=(0,255,0)
            cv2.circle(image_rgb, ( int(markers[m]['RefX']), int(markers[m]['RefY']) ), int(markers[m]['Diameter']*0.5), color,5 )


        # it shows small image as display resolution is higher than image resolution
        small_image_rgb = image_processing.scale_image(image_rgb, 0.5, 0.5)
        cv2.imshow(file, small_image_rgb)
        cv2.waitKey(0)
