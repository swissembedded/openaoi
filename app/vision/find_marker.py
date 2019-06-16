# Python program to illustrate
# multiscaling in template matching
import cv2
import numpy as np
import imutils
# Read the main image
img_rgb = cv2.imread('/home/dani/reporting/0_1560485540107_[R1]_[RES_0603]_[0.0]_Rectangular[0.85_1.55]_Rectangular[1.25_2.55]_Raw.jpg')
#img_rgb = cv2.imread('part.jpg')

# Convert to grayscale
img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)

# Read the template
template = cv2.imread('marker.jpg',0)

# Store width and heigth of template in w and h
w, h = template.shape[::-1]
found = None

# Perform match operations.
res = cv2.matchTemplate(img_gray,template,cv2.TM_CCOEFF_NORMED)

# Specify a threshold
threshold = 0.6 # 0.8

# Store the coordinates of matched area in a numpy array
loc = np.where( res >= threshold)

# Draw a rectangle around the matched region.
for pt in zip(*loc[::-1]):
    cv2.rectangle(img_rgb, pt, (pt[0] + w, pt[1] + h), (0,255,255), 2)

# Show the final image with the matched area.
cv2.imshow('Detected',img_rgb)
cv2.waitKey(0)

params = cv2.SimpleBlobDetector_Params()
#params.minThreshold = threshold
params.minThreshold = 128
params.maxThreshold = 255

params.filterByArea = True
d=(w+h)/2.0
A=np.square(d/2.0)*np.pi
params.minArea = A * np.square(0.2)
params.maxArea = A

# Filter for circles
params.filterByCircularity = False
params.minCircularity = 0.2
params.maxCircularity = 1.0

params.filterByInertia = True
params.minInertiaRatio = 0.4
params.maxInertiaRatio = 1.0

params.filterByConvexity = False
params.filterByColor = False
params.blobColor = 255

# Set up the detector with default parameters.
detector = cv2.SimpleBlobDetector_create(params)

img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)

# Detect blobs.
keypoints = detector.detect(img_gray)

# Draw detected blobs as red circles.
# cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS ensures the size of the circle corresponds to the size of blob
im_with_keypoints = cv2.drawKeypoints(img_rgb, keypoints, np.array([]), (0,0,255), cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)

# Show keypoints
cv2.imshow("Keypoints", im_with_keypoints)
cv2.waitKey(0)
