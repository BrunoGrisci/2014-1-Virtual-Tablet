#-------------------------------------------------------------------------------
# Name:        hsvsliders
# Purpose:
#
# Author:      Bruno Iochins Grisci
#
# Created:     20/05/2014
# Copyright:   (c) Bruno Grisci 2014
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import cv2
import numpy as np
import time

minHSV = {'H': 0, 'S': 0, 'V': 0}
maxHSV = {'H': 0, 'S': 0, 'V': 0}

def nothing(*arg):
    pass

def main():
    c = cv2.VideoCapture(666)
    c = cv2.VideoCapture(0)
    time.sleep(1) # delays for 1 seconds
    cv2.namedWindow("Mask")
    cv2.createTrackbar("Min H","Mask", 0, 360, nothing)
    cv2.createTrackbar("Min S","Mask", 0, 255, nothing)
    cv2.createTrackbar("Min V","Mask", 0, 255, nothing)
    cv2.createTrackbar("Max H","Mask", 0, 360, nothing)
    cv2.createTrackbar("Max S","Mask", 0, 255, nothing)
    cv2.createTrackbar("Max V","Mask", 0, 255, nothing)

    while(True):
        _,f = c.read()
        blur = cv2.medianBlur(f,5)
        hsv = cv2.cvtColor(blur,cv2.COLOR_BGR2HSV)
        minHSV['H'] = cv2.getTrackbarPos("Min H","Mask")
        minHSV['S'] = cv2.getTrackbarPos("Min S","Mask")
        minHSV['V'] = cv2.getTrackbarPos("Min V","Mask")
        maxHSV['H'] = cv2.getTrackbarPos("Max H","Mask")
        maxHSV['S'] = cv2.getTrackbarPos("Max S","Mask")
        maxHSV['V'] = cv2.getTrackbarPos("Max V","Mask")
        mask = cv2.inRange(hsv,np.array((minHSV['H'],minHSV['S'],minHSV['V'])),
                               np.array((maxHSV['H'],maxHSV['S'],maxHSV['V'])))
        cv2.imshow('Original',f)
        cv2.imshow('Mask',mask)

        if cv2.waitKey(25) == 27:
            break

    cv2.destroyAllWindows()
    c.release()

if __name__ == '__main__':
    main()
