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

def is_point_in_body_area(pixscale, bodyShape, bodySize, centerX, centerY, X, Y):
    deltaX=X-centerX
    deltaY=Y-centerY
    cxhalf = bodySize[0]*0.5*pixscale[1]
    cyhalf = bodySize[1]*0.5*pixscale[1]
    if bodyShape == "Rectangular":
        if -cxhalf >= deltaX and deltaX <= cxhalf and -cyhalf >=deltaY and deltaY <= cyhalf:
            return True
    elif bodyShape == "Circular":
        if np.square(deltaX)/np.square(cxhalf)+ np.square(deltaY)/np.square(cyhalf) <= 1:
            return True
    return False

def find_marker(image_gray, pixscale, bodyShape, bodySize, maskShape, maskSize, template_gray, template_threshold, hintPos):
    # adjust brightness and contrast

    # first match template
    template_loc=image_processing.helper_find_template(image_gray, template_gray, template_threshold)

    # fixme load from data
    threshold=[128, 255]
    area=[0.9, 1.1]
    inertia=[0.9, 1.1]
    circularity=[]
    convexity=[0.9, 1.1]

    #minVal, maxVal, minLoc, maxLoc=cv2.minMaxLoc(res)
    #print(minVal, maxVal, minLoc, maxLoc)

    keypoints=image_processing.helper_find_blob(image_gray, pixscale, bodyShape, bodySize, maskShape, maskSize, threshold, area, inertia, circularity, convexity)

    heightt, widtht = template_gray.shape

    markers_unsorted=[]
    # take all keypoints within template_loc
    for k in keypoints:
        for pt in zip(*template_loc[::-1]):
            if is_point_in_body_area(pixscale, bodyShape, bodySize, k.pt[0], k.pt[1], pt[0]+widtht*0.5, pt[1]+heightt*0.5):
                marker={ "RefX": k.pt[0], "RefY":k.pt[1], "Diameter":k.size, "Distance": np.sqrt(np.square(k.pt[0]-hintPos[0])+np.square(k.pt[1]-hintPos[1])) }
                markers_unsorted.append(marker)
                #print("marker",marker)
                break
    markers=sorted(markers_unsorted, key=lambda k: k['Distance'] )
    return markers, template_loc, keypoints
