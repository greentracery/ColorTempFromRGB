##
## ColorTempFromRGB main module
##  - Open video source, get snapshots, calculate average color temperature
##
## https://github.com/greentracery/ColorTempFromRGB
##

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageTk
import cv2
import sys
import os
import io
import numpy as np
import datetime
import time
import argparse
import tkinter

from modules.bbrmodel import ColorTemp
from modules.img2rgb import IMG2RGB
from modules.capture import VideoCapture

parser = argparse.ArgumentParser(description="Calculate average color temperature for frame")
parser.add_argument("-url", "--urlsource", type=str, help="Open IP video stream for video capturing")
parser.add_argument("-file", "--filesource", type=str, help="Open video file or image file sequence")
parser.add_argument("-ci", "--camindex", type=int, help="Camera index")
parser.add_argument("-p", "--pause", type=int, help="Pause between log messages (sec.)")

args = parser.parse_args()

video_source = 0 # open the default camera using default API

if args.urlsource:
    video_source = str(args.urlsource)
if args.filesource:
    video_source = str(args.filesource)
if args.camindex:
    video_source = int(args.camindex)

if args.pause:
    pause = int(args.pause) # do smth. every {pause} sec.
else:
    pause = 5

class App():
    
    def __init__(self, window, window_title, video_source = 0, pause = 5):
        
        self.window = window
        self.window.title(window_title)
        self.window.protocol("WM_DELETE_WINDOW", self.exit_handler)
        
        self.video_source = video_source
        self.video2screen = False

        self.pause = pause
        self.t0 = int(datetime.datetime.now().timestamp())
        
        self.ct = ColorTemp()
        self.img2rgb = IMG2RGB()
    
        # open video source (by default this will try to open the computer webcam)
        self.vid = VideoCapture(self.video_source)

        # Create a canvas that can fit the above video source size
        self.canvas = tkinter.Canvas(window, width = self.vid.width, height = self.vid.height)
        self.canvas.pack()

        # Button that lets the user take a snapshot
        self.btn_snapshot=tkinter.Button(window, text="Snapshot", width=40, command=self.snapshot_handler)
        self.btn_snapshot.pack(anchor=tkinter.E, expand=True)
        
        # Exit button
        self.btn_exit=tkinter.Button(window, text="Exit", width=40, command=self.exit_handler)
        self.btn_exit.pack(anchor=tkinter.E, expand=True)

        # After it is called once, the update method will be automatically called every delay milliseconds
        self.delay = 15
        self.update()

        self.window.mainloop()
    
    def exit_handler(self):
        self.window.destroy()  # close window & app
        print("Bye!")
    
    def snapshot_handler(self):
        # Get a frame from the video source
        status, frame = self.vid.get_frame()

        if status:
            f = self.vid.snapshot('snapshots')
            print(f"{f} saved!")
    
    def update(self):
        # Get a frame from the video source
        status, frame = self.vid.get_frame()
        
        if status:
            r,g,b = self.img2rgb.getRBGmatrix(frame)
            
            RGB = (self.img2rgb.getAverageValue(r), self.img2rgb.getAverageValue(g), self.img2rgb.getAverageValue(b))
            
            rgbN = self.ct.normalize(RGB[0], RGB[1], RGB[2]) # normalized in [0..1]
            
            color_temp, distance = self.ct.getColorTempFromRGBN(rgbN[0],rgbN[1], rgbN[2])
            
            frame, dt = self.add_frame_info(frame, RGB, rgbN, color_temp, distance)
            
            t2 = int(dt.timestamp())
            if t2 >= self.t0 + self.pause:
                print(f'{dt.strftime("%d.%m.%Y %H:%M:%S")} Average R,G,B = {RGB[0]}, {RGB[1]}, {RGB[2]} ({rgbN[0]}, {rgbN[1]}, {rgbN[2]})')
                print(f'{dt.strftime("%d.%m.%Y %H:%M:%S")} Average color temperature {color_temp} K ({distance})')
                self.t0 = t2
            
            self.photo = ImageTk.PhotoImage(image = Image.fromarray(frame))
            self.canvas.create_image(0, 0, image = self.photo, anchor = tkinter.NW)
        
        self.window.after(self.delay, self.update)

    def add_frame_info(self, frame, RGB, rgbN, color_temp, distance):
        # restore RGB from normalized values
        RGBN = self.ct.rgb_from_normal(rgbN[0],rgbN[1], rgbN[2]) 
        # add info about frame
        dt = datetime.datetime.now()
        cv2.putText(frame, 
            f'{dt.strftime("%d.%m.%Y %H:%M:%S")}', 
            (10, 25), 
            self.vid.font, 
            self.vid.fontsize, 
            self.vid.default_fontcolor, 
            1
        )
        cv2.putText(frame, 
            f"width:{self.vid.width}, height:{self.vid.height} ", 
            (10, 50), 
            self.vid.font, 
            self.vid.fontsize, 
            self.vid.default_fontcolor, 
            1
        )

        cv2.putText(
            frame, 
            f"Average R,G,B = {RGB[0]}, {RGB[1]}, {RGB[2]} ({rgbN[0]}, {rgbN[1]}, {rgbN[2]})", 
            (10, 75), 
            self.vid.font, 
            self.vid.fontsize, 
            self.vid.default_fontcolor, 
            1
        )
        cv2.putText(
            frame, 
            f"Average color temperature {color_temp} K ({distance})", 
            (10, 100), 
            self.vid.font, 
            self.vid.fontsize, 
            self.vid.default_fontcolor, 
            1
        )
        cv2.rectangle(
            frame, 
            (10, 120),
            (50, 160),
            (RGB[0], RGB[1], RGB[1]), # src. average color
            -1
        )
        cv2.rectangle(
            frame, 
            (50, 120),
            (90, 160),
            (RGBN[0], RGBN[1], RGBN[2]), # color from normalized values
            -1
        )
        cv2.rectangle(
            frame, 
            (10, 120),
            (90, 160),
            (0, 250, 0),
            1
        )
        #return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) #BGR2RGB
        return frame, dt

if __name__ == "__main__":
        # Create a window and pass it to the Application object
        App(tkinter.Tk(), "Color Temperature From RGB", video_source)
