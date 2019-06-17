import cv2
import numpy as np
from scipy.signal import find_peaks_cwt

def createHistogram(image, mask):
	histogram = []
	for channel in range(image.shape[2]):
		hist = cv2.calcHist([image.astype(np.uint8)], [channel], mask[:,:,channel], [256], [0, 256])
		histogram.append(hist)
		
	return histogram

def findRange(histogram, lower_threshold, upper_threshold):
	# Calculate total number of pixels in the histogram (if used 
	# with joinHistLayers, will count total for each channel)
	total_pixels = np.sum(histogram)

	# Starting from the bottom of the range, 0, find the intensity 
	# value for which a threshold percent of pixels are excluded
	total = 0
	i = 0
	while np.sum(histogram[:i]) <= lower_threshold:
		i += 1
	start = i - 1

	# Also find upper bound
	total = 0
	i = histogram.shape[0]
	while np.sum(histogram[i:]) > upper_threshold:
		i -= 1
	end = i + 1

	return start, end

def BrightnessAndContrastAuto(src, clipHistPercent):
    histSize = 256
    gray = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
    hist = cv2.calcHist([gray], [0], None, [histSize], [0, histSize])
    total_pixels = np.sum(hist)
    
    print("total", total_pixels)

    clipHistPercent *= (total_pixels / 100.0); #make percent as absolute
    clipHistPercent /= 2.0  #left and right wings
							#locate left cut
    lower_threshold = clipHistPercent
    upper_threshold = total_pixels - clipHistPercent

    minGray,maxGray = findRange(hist, lower_threshold, upper_threshold)
    
    inputRange = maxGray - minGray
    alpha = (histSize - 1) / inputRange;   #alpha expands current range to histsize range
    beta = -minGray * alpha;   

    dst = cv2.addWeighted(src, alpha, src, 0, beta)

    #dst = np.zeros(src.shape, src.dtype)
    #for y in range(src.shape[0]):
    #    for x in range(src.shape[1]):
    #        for c in range(src.shape[2]):
    #            dst[y,x,c] = np.clip(alpha*src[y,x,c] + beta, 0, 255)

    return dst
