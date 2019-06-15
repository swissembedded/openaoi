import numpy as np
import cv2
import imutils

# load the image image, convert it to grayscale, and detect edges
template = cv2.imread("template.jpg")

template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
template = cv2.Canny(template, 50, 200)
(tH, tW) = template.shape[:2]
cv2.imshow("Template", template)

image = cv2.imread("part.jpg")
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
found = None

# loop over the scales of the image
for scale in np.linspace(0.2, 1.0, 20)[::-1]:

    resized = imutils.resize(gray, width = int(gray.shape[1] * scale))
    r = gray.shape[1] / float(resized.shape[1])

    if resized.shape[0] < tH or resized.shape[1] < tW:
        break

    # detect edges in the resized, grayscale image and apply template
    # matching to find the template in the image
    edged = cv2.Canny(resized, 50, 200)
    result = cv2.matchTemplate(edged, template, cv2.TM_CCOEFF)
    (_, maxVal, _, maxLoc) = cv2.minMaxLoc(result)
   
    if found is None or maxVal > found[0]:
        found = (maxVal, maxLoc, r)


(_, maxLoc, r) = found
(startX, startY) = (int(maxLoc[0] * r), int(maxLoc[1] * r))
(endX, endY) = (int((maxLoc[0] + tW) * r), int((maxLoc[1] + tH) * r))

# draw a bounding box around the detected result and display the image
cv2.rectangle(image, (startX, startY), (endX, endY), (0, 0, 255), 2)
image = cv2.resize(image, (0,0), fx=0.5, fy=0.5)
cv2.imshow("Image", image)
cv2.waitKey(0)