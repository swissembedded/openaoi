import math
import numpy as np
import cv2

#dictionary of all contours
contours = {}
#array of edges of polygon
approx = []
#scale of the text
scale = 1

#camera
cap = cv2.VideoCapture(0)
print("press q to exit")

#calculate angle
def angle(pt1,pt2,pt0):
    dx1 = pt1[0][0] - pt0[0][0]
    dy1 = pt1[0][1] - pt0[0][1]
    dx2 = pt2[0][0] - pt0[0][0]
    dy2 = pt2[0][1] - pt0[0][1]
    return float((dx1*dx2 + dy1*dy2))/math.sqrt(float((dx1*dx1 + dy1*dy1))*(dx2*dx2 + dy2*dy2) + 1e-10)

while(cap.isOpened()):
    ret, frame = cap.read()
    if ret==True:
        #grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        #Canny
        canny = cv2.Canny(frame,100,200)

        #contours
        contours, hierarchy = cv2.findContours(canny,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        for i in range(0,len(contours)):
            #approximate the contour with accuracy proportional to
            #the contour perimeter
            approx = cv2.approxPolyDP(contours[i],cv2.arcLength(contours[i],True)*0.02,True)

            #Skip small or non-convex objects
            if(abs(cv2.contourArea(contours[i]))<100 or not(cv2.isContourConvex(approx))):
                continue

            #triangle
            if(len(approx) > 6):
                area = cv2.contourArea(contours[i])
                x,y,w,h = cv2.boundingRect(contours[i])
                radius = w/2
                if(abs(1 - (float(w)/h))<=2 and abs(1-(area/(math.pi*radius*radius)))<=0.2):
                    cv2.putText(frame,'Marker',(x,y-10),cv2.FONT_HERSHEY_SIMPLEX,scale,(0,255,0),2,cv2.LINE_AA)
                    cv2.rectangle(frame, (x,y),(x+w,y+h), (0,255,0), 3)

        #Display the resulting frame
        cv2.imshow('frame',frame)
        cv2.imshow('canny',canny)
        if cv2.waitKey(1) == 1048689: #if q is pressed
            break

#When everything done, release the capture
cap.release()
cv2.destroyAllWindows()
