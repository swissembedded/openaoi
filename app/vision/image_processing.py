# Open CV Image processing
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
import imutils

def helper_find_template(img_gray, template_gray, threshold):
    # Perform match operations.
    res = cv2.matchTemplate(img_gray,template_gray, cv2.TM_CCOEFF_NORMED)

    # Store the coordinates of matched area in a numpy array
    minVal, maxVal, minLoc, maxLoc=cv2.minMaxLoc(res)
    print(minVal, maxVal, minLoc, maxLoc)
    loc = np.where( res >= threshold)
    return loc

# good examples can be found here https://www.learnopencv.com/blob-detection-using-opencv-python-c/
def helper_find_blob(img_gray, pixscale, bodyShape, bodySize, maskShape, maskSize, threshold, area, inertia, circularity, convexity):
    params = cv2.SimpleBlobDetector_Params()
    params.minThreshold = threshold[0]
    params.maxThreshold = threshold[1]

    # pixscale on x and y axis
    if bodyShape=="Rectangular":
        expected_area=bodySize[0]*pixscale[0]*bodySize[1]*pixscale[1]
        expected_perimeter=2.0*bodySize[0]*pixscale[0]+2.0*bodySize[1]*pixscale[1]
    elif bodyShape=="Circular":
        expected_area=bodySize[0]*pixscale[0]*0.5*bodySize[1]*pixscale[1]*0.5*np.pi
        expected_perimeter=np.pi * np.sqrt(2.0*(np.square(bodySize[0]*0.5*pixscale[0])+np.square(bodySize[1]*0.5*pixscale[1])))

    expected_circularity = 4.0 * np.pi * expected_area / np.square(expected_perimeter)

    if bodySize[0] <= bodySize[1]:
        expected_inertia=bodySize[0]/bodySize[1]
    else:
        expected_inertia=bodySize[1]/bodySize[0]

    expected_convexity=1.0

    # filter by Area
    params.filterByArea = True
    params.minArea = expected_area*area[0]
    params.maxArea = expected_area*area[1]

    # Filter by Inertia
    params.filterByInertia = True
    params.minInertiaRatio = min(1.0,expected_inertia*inertia[0])
    params.maxInertiaRatio = min(1.0,expected_inertia*inertia[1])

    # Filter for circles
    params.filterByCircularity = False
    params.minCircularity = min(1.0,expected_circularity*circularity[0])
    params.maxCircularity = min(1.0,expected_circularity*circularity[1])
    print("Circularity",params.minCircularity,params.maxCircularity)

    # Filter by convecity
    params.filterByConvexity = True
    params.minConvexity=min(1.0,expected_convexity*convexity[0])
    params.maxConvexity=min(1.0,expected_convexity*convexity[1])

    params.filterByColor = False
    params.blobColor = 255

    # Set up the detector with default parameters.
    detector = cv2.SimpleBlobDetector_create(params)

    # Detect blobs.
    keypoints = detector.detect(img_gray)
    return keypoints

def scale_image(img, scalex, scaley):
    img_size = img.shape
    img_scaled = cv2.resize(img, (img_size[1]*scalex, img_size[0]*scaley) )
    return img_scaled

def load_image(filename):
    img_rgb = cv2.imread(filename, cv2.IMREAD_COLOR)
    img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
    return img_rgb, img_gray
