import cv2
import numpy as np
from scipy.signal import find_peaks_cwt

# Finds the appropriate upper and lower pixel value bounds that excludes the threshold percentage
# of pixels on both sides of the histogram
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

# Automatic brightness and contrast optimization with optional histogram clipping
# param clipHistPercent cut wings of histogram at given percent tipical=>1, 0=>Disabled
#      note In case of BGRA image, we won't touch the transparency
def BrightnessAndContrastAuto(src, clipHistPercent):
	#to calculate grayscale histogram
	histSize = 256
	gray = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
	
	#the grayscale histogram
	hist = cv2.calcHist([gray], [0], None, [histSize], [0, histSize])
	total_pixels = np.sum(hist)
    
	# calculate cumulative distribution from the histogram
	clipHistPercent *= (total_pixels / 100.0); #make percent as absolute
	clipHistPercent /= 2.0  #left and right wings
							#locate left cut
	lower_threshold = clipHistPercent
	upper_threshold = total_pixels - clipHistPercent
	minGray,maxGray = findRange(hist, lower_threshold, upper_threshold)
	inputRange = maxGray - minGray

	# alpha expands current range to histsize range
	alpha = (histSize - 1) / inputRange;   #alpha expands current range to histsize range
	
	# beta shifts current range so that minGray will go to 0
	beta = -minGray * alpha;   
	
	# Apply brightness and contrast normalization
    # convertTo operates with saurate_cast
	dst = cv2.addWeighted(src, alpha, src, 0, beta)
	
	return dst
