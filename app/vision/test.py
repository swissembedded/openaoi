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

image_rgb,image_gray=image_processing.load_image('part.jpg')
marker_rgb,marker_gray=image_processing.load_image('marker.jpg')
heighti, widthi, channelsi = image_rgb.shape
heightm, widthm, channelsm = marker_rgb.shape

hintPos=[widthi/2.0, heighti/2.0]

templateloc,keypoints=find_marker.find_marker(image_gray, [141.33, 141.33], "Circular", [2.2, 2.2], "Rectangular", [3.0, 3.0], marker_gray, 0.6, hintPos)

# Draw a rectangle around the matched region.
for pt in zip(*templateloc[::-1]):
    cv2.rectangle(image_rgb, pt, (pt[0] + widthm-1, pt[1] + heightm-1), (0,0,255), 1)

# Show the final image with the matched area.
cv2.imshow('Marker by template',image_rgb)
cv2.waitKey(0)

# Draw detected blobs as red circles.
# cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS ensures the size of the circle corresponds to the size of blob
im_with_keypoints = cv2.drawKeypoints(image_rgb, keypoints, np.array([]), (0,0,255), cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)

# Show keypoints
cv2.imshow("Keypoints", im_with_keypoints)
cv2.waitKey(0)
