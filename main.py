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
import io
import numpy as np
import datetime
import time
import argparse

from modules.bbrmodel import ColorTemp
from modules.img2rgb import IMG2RGB
from modules.capture import VideoCapture

print("P(rint) - save snapshot, Q(uit) - close & exit")

parser = argparse.ArgumentParser(description="Calculate average color temperature for frame")
parser.add_argument("-url", "--urlsource", type=str, help="Open IP video stream for video capturing")
parser.add_argument("-file", "--filesource", type=str, help="Open video file or image file sequence")
parser.add_argument("-ci", "--camindex", type=int, help="Camera index")
parser.add_argument("-d", "--delay", type=int, help="Pause between frame info messages (sec.)")

args = parser.parse_args()

video_source = 0 # open the default camera using default API

if args.camindex:
    video_source = int(args.camindex)
if args.urlsource:
    video_source = str(args.urlsource)
if args.filesource:
    video_source = str(args.filesource)

if args.delay:
    delay = int(args.delay) # do smth. every {delay} sec.
else:
    delay = 5

class App():
    
    def __init__(self, video_source = 0, delay = 5):
        
        self.video_source = video_source
        self.vid = VideoCapture(self.video_source)
        self.delay = delay
        self.t0 = int(datetime.datetime.utcnow().timestamp())
        
        self.ct = ColorTemp()
        self.img2rgb = IMG2RGB()
    
    def run(self):
        while True:
            status, frame = self.vid.get_frame()
            
            if status:
                r,g,b = self.img2rgb.getRBGmatrix(frame)
                
                RGB = (self.img2rgb.getAverageValue(r), self.img2rgb.getAverageValue(g), self.img2rgb.getAverageValue(b))
                
                rgbN = self.ct.normalize(RGB[0], RGB[1], RGB[2]) # normalized in [0..1]
                
                color_temp, distance = self.ct.getColorTempFromRGBN(rgbN[0],rgbN[1], rgbN[2])
                
                self.add_frame_info(frame, RGB, rgbN, color_temp, distance)
                
                t2 = int(datetime.datetime.utcnow().timestamp())
                if t2 >= self.t0 + self.delay:
                    print(f"Average R,G,B = {RGB[0]}, {RGB[1]}, {RGB[2]} ({rgbN[0]}, {rgbN[1]}, {rgbN[2]}), average color temp. {color_temp} K ({distance})")
                    self.t0 = t2
            
                # Display the resulting image
                cv2.imshow('Video', frame)
                
            # Hotkeys
            key = cv2.waitKey(1) & 0xFF
            # Hit 'p' on keyboard to make screenshot
            if key == ord('p'):
                f = self.vid.snapshot('snapshots')
                print(f"{f} saved!")
            # Hit 'q' on the keyboard to quit!
            if key == ord('q'):
                break
        
        cv2.destroyAllWindows()
        sys.exit()

    def add_frame_info(self, frame, RGB, rgbN, color_temp, distance):
        # restore RGB from normalized values
        RGBN = self.ct.rgb_from_normal(rgbN[0],rgbN[1], rgbN[2]) 
        # add info about frame
        cv2.putText(
            frame, 
            f"Average R,G,B = {RGB[0]}, {RGB[1]}, {RGB[2]} ({rgbN[0]}, {rgbN[1]}, {rgbN[2]})", 
            (10, self.vid.height - 100), 
            self.vid.font, 
            0.6, 
            (0, 0, 250), 
            1
        )
        cv2.putText(
            frame, 
            f"Average color temperature {color_temp} K ({distance})", 
            (10, self.vid.height - 75), 
            self.vid.font, 
            0.6, 
            (0, 0, 250), 
            1
        )
        cv2.rectangle(
            frame, 
            (self.vid.width - 100, self.vid.height - 60),
            (self.vid.width - 60, self.vid.height - 20),
            (RGB[2], RGB[1], RGB[0]), #BGR
            -1
        )
        cv2.rectangle(
            frame, 
            (self.vid.width - 60, self.vid.height - 60),
            (self.vid.width - 20, self.vid.height - 20),
            (RGBN[2], RGBN[1], RGBN[0]), # from normalized values
            -1
        )
        cv2.rectangle(
            frame, 
            (self.vid.width - 100, self.vid.height - 60),
            (self.vid.width - 20, self.vid.height - 20),
            (0, 250, 0), #BGR
            1
        )
        cv2.putText(frame, f"width:{self.vid.width}", (10, self.vid.height - 50), self.vid.font, 0.6, (0, 250, 0), 1)
        cv2.putText(frame, f"height:{self.vid.height}", (10, self.vid.height - 25), self.vid.font, 0.6, (0, 250, 0), 1)
        

if __name__ == "__main__":
    app = App(video_source, delay)
    app.run()
