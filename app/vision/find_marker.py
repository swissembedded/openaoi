# Find marker
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
import imutils

import numpy as np

import find_marker
import image_processing

def find_marker(image_gray, pixscale, bodyShape, bodySize, maskShape, maskSize, template_gray, template_threshold, hintPos):
    # adjust brightness and contrast

    # first match template
    template_loc=image_processing.helper_find_template(image_gray, template_gray, template_threshold)
    threshold=[128, 255]
    area=[0.9, 1.1]
    inertia=[0.9, 1.1]
    circularity=[0.9, 1.1]
    convexity=[0.9, 1.1]
    keypoints=image_processing.helper_find_blob(image_gray, pixscale, bodyShape, bodySize, maskShape, maskSize, threshold, area, inertia, circularity, convexity)
    return template_loc, keypoints
