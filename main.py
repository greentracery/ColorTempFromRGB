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
        
        self.w = self.window.winfo_screenwidth() - 30 # screen width
        self.h = self.window.winfo_screenheight() - 30 #screen height
        
        self.video_source = video_source
        self.video2screen = False

        self.pause = pause
        self.t0 = int(datetime.datetime.now().timestamp())
        
        self.ct = ColorTemp()
        self.img2rgb = IMG2RGB()
        
        # open video source (by default this will try to open the computer webcam)
        self.vid = VideoCapture(self.video_source)
        # show video source info in console:
        print(f'Source:{video_source},  width:{self.vid.width}, height:{self.vid.height}')
        
        zoom_x = self.vid.width / self.w if self.vid.width > self.w else 1
        zoom_y = self.vid.height / self.h if self.vid.height > self.h else 1
        
        self.zoom = max(zoom_x, zoom_y)
        
        # Create a canvas that can fit the above video source size
        self.canvas = tkinter.Canvas(window, width = int(self.vid.width / self.zoom), height = int(self.vid.height / self.zoom))
        self.canvas.pack()
        
        # Popup menu available by mouse right button click
        self.canvas.bind("<Button-3>", self.popup_handler)
        self.popup_menu = tkinter.Menu(tearoff=0)
        self.popup_menu.add_command(label="Snapshot", command=self.snapshot_handler)
        self.popup_menu.add_command(label="Close", command=self.popup_close_handler)
        self.popup_menu.add_separator()
        self.popup_menu.add_command(label="Exit", command=self.exit_handler)
        
        # Button that lets the user take a snapshot
        self.btn_snapshot=tkinter.Button(window, text="Snapshot", width=40, command=self.snapshot_handler)
        self.btn_snapshot.pack(anchor=tkinter.E, expand=True)
        
        # Exit button
        self.btn_exit=tkinter.Button(window, text="Exit", width=40, command=self.exit_handler)
        self.btn_exit.pack(anchor=tkinter.E, expand=True)

        # After it is called once, the update method will be automatically called every delay milliseconds
        self.delay = 50
        self.update()

        self.window.mainloop()
    
    def popup_handler(self, event):
        global x, y
        x = event.x
        y = event.y
        self.popup_menu.post(event.x_root, event.y_root)
    
    def popup_close_handler(self):
        self.popup_menu.unpost()
    
    def exit_handler(self):
        self.window.destroy()  # close window & app
        print("Bye!")
    
    def update(self):
        # Get a frame from the video source
        status, frame = self.vid.get_frame()
        
        if status:
            
            r,g,b = self.img2rgb.getRBGmatrix(frame)
            
            self.RGB = (self.img2rgb.getAverageValue(r), self.img2rgb.getAverageValue(g), self.img2rgb.getAverageValue(b))
            
            self.rgbN = self.ct.normalize(self.RGB[0], self.RGB[1], self.RGB[2]) # normalized in [0..1]
            
            self.color_temp, self.distance = self.ct.getColorTempFromRGBN(self.rgbN[0],self.rgbN[1], self.rgbN[2])
            
            dt = datetime.datetime.now()
            
            frame = self.add_frame_info(frame, dt)
            
            t2 = int(dt.timestamp())
            if t2 >= self.t0 + self.pause:
                # show frame info in console:
                print(f'{dt.strftime("%d.%m.%Y %H:%M:%S")} Average R,G,B = {self.RGB[0]}, {self.RGB[1]}, {self.RGB[2]} ({self.rgbN[0]}, {self.rgbN[1]}, {self.rgbN[2]})')
                print(f'{dt.strftime("%d.%m.%Y %H:%M:%S")} Average color temperature {self.color_temp} K ({self.distance})')
                self.t0 = t2
            
            image = Image.fromarray(frame)
            # resize frame to canvas size:
            if self.zoom > 1:
                image = image.resize((int(self.vid.width / self.zoom), int(self.vid.height / self.zoom)))
            
            self.photo = ImageTk.PhotoImage(image)
            self.canvas.create_image(0, 0, image = self.photo, anchor = tkinter.NW)
        
        self.window.after(self.delay, self.update)

    def add_frame_info(self, frame, dt):
        
        cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        # restore R,G,B from normalized values
        RGBN = self.ct.rgb_from_normal(self.rgbN[0], self.rgbN[1], self.rgbN[2]) 
        # add info about frame
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
            f"Average R,G,B = {self.RGB[0]}, {self.RGB[1]}, {self.RGB[2]} ({self.rgbN[0]}, {self.rgbN[1]}, {self.rgbN[2]})", 
            (10, 75), 
            self.vid.font, 
            self.vid.fontsize, 
            self.vid.default_fontcolor, 
            1
        )
        cv2.putText(
            frame, 
            f"Average color temperature {self.color_temp} K ({self.distance})", 
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
            (self.RGB[2], self.RGB[1], self.RGB[0]), # src. average color (BGR)
            -1
        )
        cv2.rectangle(
            frame, 
            (50, 120),
            (90, 160),
            (RGBN[2], RGBN[1], RGBN[0]), # color from normalized values (BGR)
            -1
        )
        cv2.rectangle(
            frame, 
            (10, 120),
            (90, 160),
            (0, 250, 0),
            1
        )
        cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return frame
        
    def snapshot_handler(self):
        # Check filepath
        imgdir = 'snapshots'
        target_path = os.path.join(os.getcwd(), imgdir)
        if not os.path.exists(target_path):
            os.makedirs(target_path)
        
        # Get a frame from the video source
        status, frame = self.vid.get_frame()

        if status:
            dt = datetime.datetime.now()
            
            frame = self.add_frame_info(frame, dt)
            cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            # set encode param
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
            # compress image into buffer
            result, imgencode = cv2.imencode(".jpg", frame, encode_param)
            # read from buffer & save into file
            filename = os.path.join(target_path, f'frame-{dt.strftime("%d-%m-%Y-%H-%M-%S")}.jpg')
            
            cv2.imdecode(imgencode, cv2.IMREAD_COLOR)
            cv2.imwrite(filename, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            
            print(f"{filename} saved!")

if __name__ == "__main__":
        # Create a window and pass it to the Application object
        App(tkinter.Tk(), "Color Temperature From RGB", video_source)
