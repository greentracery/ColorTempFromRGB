##
## ColorTempFromRGB main module
##  - Open video source, get snapshots, calculate average color temperature
##
## https://github.com/greentracery/ColorTempFromRGB
##
## P(rint) - save snapshot
## Q(uit) - close & exit
##

from PIL import Image, ImageDraw, ImageFont
import cv2
import sys
import os
import numpy as np
import datetime
import time
import argparse

from modules.bbrmodel import ColorTemp
from modules.img2rgb import IMG2RGB
from modules.capture import VideoCapture

ct = ColorTemp()
img2rgb = IMG2RGB()

print("P(rint) - save snapshot, Q(uit) - close & exit")

parser = argparse.ArgumentParser(description="Calculate average color temperature for frame")
parser.add_argument("-url", "--urlsource", type=str, help="Open IP video stream for video capturing")
parser.add_argument("-file", "--filesource", type=str, help="Open video file or image file sequence")

args = parser.parse_args()

if args.urlsource or args.filesource:
    src = args.source
else:
    src = 0 # open the default camera using default API

vc = VideoCapture(src)

t0 = int(datetime.datetime.utcnow().timestamp())

delay = 5 # do smth. every {delay} sec.

while True:
    status, frame = vc.get_frame()
    
    if status:
        r,g,b = img2rgb.getRBGmatrix(frame)
        
        RGB = (img2rgb.getAverageValue(r), img2rgb.getAverageValue(g), img2rgb.getAverageValue(b))
        
        rgbN = ct.normalize(RGB[0], RGB[1], RGB[2]) # normalized in [0..1]
        
        RGBN = ct.rgb_from_normal(rgbN[0],rgbN[1], rgbN[2]) # RGB from normalized values
        
        color_temp, distance = ct.getColorTempFromRGBN(rgbN[0],rgbN[1], rgbN[2])
        
        # info about frame
        cv2.putText(
            frame, 
            f"Average R,G,B = {RGB[0]}, {RGB[1]}, {RGB[2]} ({rgbN[0]}, {rgbN[1]}, {rgbN[2]})", 
            (10, vc.height - 100), 
            vc.font, 
            0.6, 
            (0, 0, 250), 
            1
        )
        cv2.putText(
            frame, 
            f"Average color temperature {color_temp} K ({distance})", 
            (10, vc.height - 75), 
            vc.font, 
            0.6, 
            (0, 0, 250), 
            1
        )
        cv2.rectangle(
            frame, 
            (vc.width - 100, vc.height - 60),
            (vc.width - 60, vc.height - 20),
            (RGB[2], RGB[1], RGB[0]), #BGR
            -1
        )
        cv2.rectangle(
            frame, 
            (vc.width - 60, vc.height - 60),
            (vc.width - 20, vc.height - 20),
            (RGBN[2], RGBN[1], RGBN[0]), # from normalized values
            -1
        )
        cv2.rectangle(
            frame, 
            (vc.width - 100, vc.height - 60),
            (vc.width - 20, vc.height - 20),
            (0, 250, 0), #BGR
            1
        )
        cv2.putText(frame, f"width:{vc.width}", (10, vc.height - 50), vc.font, 0.6, (0, 250, 0), 1)
        cv2.putText(frame, f"height:{vc.height}", (10, vc.height - 25), vc.font, 0.6, (0, 250, 0), 1)
        
        t2 = int(datetime.datetime.utcnow().timestamp())
        if t2 >= t0 + delay:
            print(f"Average R,G,B = {RGB[0]}, {RGB[1]}, {RGB[2]} ({rgbN[0]}, {rgbN[1]}, {rgbN[2]}), average color temp. {color_temp} K ({distance})")
            t0 = t2
        
        # Display the resulting image
        cv2.imshow('Video', frame)
    
    # Hotkeys
    key = cv2.waitKey(1) & 0xFF
    # Hit 'p' on keyboard to make screenshot
    if key == ord('p'):
        f = vc.snapshot('snapshots')
        print(f"{f} saved!")
    # Hit 'q' on the keyboard to quit!
    if key == ord('q'):
        break
        
# Release handle to the webcam
cv2.destroyAllWindows()

