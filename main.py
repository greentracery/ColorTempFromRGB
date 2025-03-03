##
## ColorTempFromRGB main module
##  - Open video source, get snapshots, calculate average color temperature
##
## https://github.com/greentracery/ColorTempFromRGB
##

import sys
import os

version = (sys.version_info.major, sys.version_info.minor)
if (sys.version_info.major < 3 or sys.version_info.minor < 6):
    e = f'Python version 3.6 or higher required! (Current version {sys.version_info.major}.{sys.version_info.minor})'
    print(e)
    sys.exit(1)

import argparse
import cv2
import numpy as np
import datetime
import time
import tkinter

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageTk

from modules.bbrmodel import ColorTempModel
from modules.img2layers import IMG2Layers
from modules.capture import VideoCapture
from modules.logger import LogWriter

class App():
    """ Main GUI App based on TkInter 
    
        method: popup_handler: Show popup menu
        method: popup_close_handler: Close popup menu
        method: init_capture: Open video source & set init. params
        method: exit_handler: Exit & close app
        method: update: Update frame on GUI form
        method: get_frame_info: Return extended info about frame, include color temperature, brightnes etc
        method: add_frame_info: Draw extended info on frame, include color temperature, brightnes etc
        method: snapshot_handler: Make a snapshot of frame
    """
    
    def __init__(self, window, window_title, video_source = 0, pause: int = 3, quality: int = 90, mode: str = 'mean', logfile = None):
        """
            :param window:
            :param window_title:
            :param video_source: default, rtsp or filename
            :param pause: pause between frames, sec.
            :param quality: jpeg quality for snapshots
            :param mode: mean or median mode for average Tk & brightness
        """
        self.window = window
        self.window.title(window_title)
        self.window.protocol("WM_DELETE_WINDOW", self.exit_handler)
        
        self.w = self.window.winfo_screenwidth() - 30 # screen width
        self.h = self.window.winfo_screenheight() - 30 #screen height
        
        self.video_source = video_source
        self.video2screen = False

        self.pause = pause
        self.quality = quality
        self.mode = mode
        self.t0 = int(datetime.datetime.now().timestamp())
        
        self.ct = ColorTempModel()
        self.img2rgb = IMG2Layers()
        
        if logfile is not None:
            self.lw = LogWriter(logfile)
        else:
            self.lw = None
        
        _msg = f"OpenCV version: {cv2.__version__}"
        print(_msg)
        if self.lw:
            self.lw.log_info(_msg)
        
        self.init_capture()
        
        # Create a canvas that can fit the above video source size
        self.canvas = tkinter.Canvas(window, width = int(self.vid.width / self.zoom), height = int(self.vid.height / self.zoom))
        self.canvas.pack()
        
        # Popup menu available by mouse right button click
        self.canvas.bind("<Button-3>", self.popup_handler)
        self.popup_menu = tkinter.Menu(tearoff=0)
        self.popup_menu.add_command(label="Settings", command=self.settings_handler)
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
        """ Show popup menu
            
            :param event:
        """
        global x, y
        x = event.x
        y = event.y
        self.popup_menu.post(event.x_root, event.y_root)
    
    def popup_close_handler(self):
        """ Close popup menu """
        self.popup_menu.unpost()
    
    def settings_handler(self):
        self.settings_window = tkinter.Toplevel()
        self.settings_window.title("Settings")
        self.settings_window.geometry("250x200")
        self.settings_window.protocol("WM_DELETE_WINDOW", lambda: self.dismiss_settings(self.settings_window))
        self.settings_window.label = tkinter.Label(self.settings_window, text="Set new videosource (0 to default)")
        self.settings_window.label.pack(anchor=tkinter.CENTER,  padx=8, pady=8)
        # Text field fo new video source (rtsp stream or filename, "0" to default)
        self.settings_window.vsource = tkinter.Entry(self.settings_window)
        self.settings_window.vsource.pack(anchor=tkinter.N, expand=True, padx=8, pady=8)
        # Button "save settings"
        self.settings_window.btn = tkinter.Button(self.settings_window, text="Save Settings", width=40, command=self.save_settings_handler)
        self.settings_window.btn.pack(anchor=tkinter.E, expand=True, padx=8, pady=8)
        self.settings_window.grab_set()
        self.settings_window.focus_set()
        self.settings_window.wait_window()
    
    def dismiss_settings(self, window):
        window.grab_release() 
        window.destroy()
    
    def save_settings_handler(self):
        vsource = self.settings_window.vsource.get()
        self.dismiss_settings(self.settings_window)
        
        vsource = vsource.strip()
        if len(vsource) == 0:
            _msg = f"New video source is empty!"
            print(_msg)
            if self.lw:
                self.lw.log_warnint(_msg)
            return
        
        _msg = f"Try to open new video source: {vsource}"
        print(_msg)
        if self.lw:
            self.lw.log_info(_msg)
        
        if vsource.isdigit():
            vsource = int(vsource)
        
        if vsource == self.video_source:
            _msg = f"Video source was not changed!"
            print(_msg)
            if self.lw:
                self.lw.log_warnint(_msg)
            return
        
        try:
            self.video_source = vsource
            self.init_capture()
        except Exception as e:
            print(e)
            if self.lw:
                self.lw.log_error(repr(e))
    
    def init_capture(self):
        """ Open video source & set init. params """
        try:
            # open video source (by default this will try to open the computer webcam)
            self.vid = VideoCapture(self.video_source)
            
            zoom_x = self.vid.width / self.w if self.vid.width > self.w else 1
            zoom_y = self.vid.height / self.h if self.vid.height > self.h else 1
            
            self.zoom = max(zoom_x, zoom_y)
            
            # show video source info in console:
            info_msg = f'Source:{video_source},  width:{self.vid.width}, height:{self.vid.height}, every {self.pause} sec.'
            print(info_msg)
            if self.lw:
                self.lw.log_info(info_msg)
            
        except Exception as e:
            print(e)
            if self.lw:
                self.lw.log_error(e)
            self.exit_handler()
    
    def exit_handler(self):
        """ Exit & close app """
        self.window.destroy()  # close window & app
        print("Bye!")
    
    def update(self):
        """ Update frame on GUI form """
        
        dt = datetime.datetime.now()
        
        status = self.vid.grab()
        
        if not status:
            warn_msg = 'Can not capture image from camera'
            print(f'{dt.strftime("%d.%m.%Y %H:%M:%S")} {warn_msg}')
            if self.lw:
                self.lw.log_warning(warn_msg)
            self.vid.release()
            time.sleep(10)
            self.init_capture()
        
        t2 = int(dt.timestamp())
        if t2 >= self.t0 + self.pause: # update frame every {pause} sec.
            
            try:
                # Get a frame from the video source
                status, frame = self.vid.retrieve()
            except:
                warn_msg = 'No frame'
                print(f'{dt.strftime("%d.%m.%Y %H:%M:%S")} {warn_msg}')
                if self.lw:
                    self.lw.log_warning(warn_msg)
            
            if status:
                
                self.RGB, self.rgbN, self.color_temp, self.distance, self.brightness = self.get_frame_info(frame)
                
                frame = self.add_frame_info(frame, dt)
                
                # show frame info in console:
                info_msg = f'Average R,G,B = {self.RGB[0]}, {self.RGB[1]}, {self.RGB[2]} ({self.rgbN[0]}, {self.rgbN[1]}, {self.rgbN[2]})'
                print(f'{dt.strftime("%d.%m.%Y %H:%M:%S")} {info_msg}')
                if self.lw:
                    self.lw.log_info(info_msg)
                info_msg = f'Average color temperature {self.color_temp} K ({self.distance}), brightness {self.brightness}% {self.imgmode}'
                print(f'{dt.strftime("%d.%m.%Y %H:%M:%S")} {info_msg}')
                if self.lw:
                    self.lw.log_info(info_msg)
                self.t0 = t2
            
                image = Image.fromarray(frame)
                # resize frame to canvas size:
                if self.zoom > 1:
                    image = image.resize((int(self.vid.width / self.zoom), int(self.vid.height / self.zoom)))
                
                self.photo = ImageTk.PhotoImage(image)
                self.canvas.create_image(0, 0, image = self.photo, anchor = tkinter.NW)
        
        self.window.after(self.delay, self.update)
    
    def get_frame_info(self, frame):
        """ Return extended info about frame, include color temperature, brightnes etc
            
            :param frame: frame from video source (numpy array)
            
            return: tuple(
                RGB: list[R,G,B]: R,G,B values 
                rgbN: list[R,G,B]: R,G,B values (normalized)
                color_temp: int: average color temperature
                distance: float: accuracy (0..1)
                brightness: int: average brightness (0..100%)
            )
        """
        r,g,b = self.img2rgb.get_rgb_matrix(frame) 
        
        RGB = self.img2rgb.get_average_colorvalues([r, g, b], self.mode)
        
        brightness = self.img2rgb.get_average_brightness(RGB)
        
        rgbN = self.ct.rgb_normalize(RGB[0], RGB[1], RGB[2]) # normalized in [0..1]
        
        color_temp, distance = self.ct.getColorTempFromRGBN(rgbN[0], rgbN[1], rgbN[2])
        
        if np.array_equal(r, g) and np.array_equal(g, b):
            self.imgmode = '(Night/grayscale mode)'
        else:
            self.imgmode = '(RGB mode)'
        
        return RGB, rgbN, color_temp, distance, brightness
    
    def add_frame_info(self, frame, dt):
        """ Draw extended info on frame, include color temperature, brightnes etc
            
            :param frame: frame from video source (numpy array)
            :param dt: datetime
            
            return frame: frame (numpy array) with extended info 
        """
        
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
            f"width:{self.vid.width}, height:{self.vid.height} {self.imgmode}", 
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
            f"Average color temperature {self.color_temp} K ({self.distance}), brightness {self.brightness}%", 
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
            (self.RGB[0], self.RGB[1], self.RGB[2]), # src. average color
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
        cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return frame
        
    def snapshot_handler(self):
        """ Make a snapshot of frame """
        
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
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.quality]
            # compress image into buffer
            result, imgencode = cv2.imencode(".jpg", frame, encode_param)
            # read from buffer & save into file
            filename = os.path.join(target_path, f'frame-{dt.strftime("%d-%m-%Y-%H-%M-%S")}.jpg')
            
            cv2.imdecode(imgencode, cv2.IMREAD_COLOR)
            cv2.imwrite(filename, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            
            print(f"{filename} saved!")
            if self.lw:
                    self.lw.log_info(f"{filename} saved!")


parser = argparse.ArgumentParser(description="Calculate average color temperature for frame")
parser.add_argument("-url", "--urlsource", type=str, help="Open IP video stream for video capturing")
parser.add_argument("-file", "--filesource", type=str, help="Open video file or image file sequence")
parser.add_argument("-ci", "--camindex", type=int, help="Camera index")
parser.add_argument("-p", "--pause", type=int, help="Pause between log messages (sec., defult 3)")
parser.add_argument("-m", "--mode", type=str, help="Mean or median mode for average values")
parser.add_argument("-q", "--quality", type=int, help="JPEG quality (default 90)")
parser.add_argument("-log", "--logfile", type=str, help="Log to file")

args = parser.parse_args()

video_source = 0 # open the default camera using default API

if args.urlsource:
    video_source = str(args.urlsource)
if args.filesource:
    video_source = str(args.filesource)
if args.camindex:
    video_source = int(args.camindex)

if args.mode and args.mode.lower() in ('mean', 'median'):
    mode = args.mode.lower()
else:
    mode = 'mean'

if args.pause:
    pause = int(args.pause) # do smth. every {pause} sec.
else:
    pause = 3

if args.quality:
    quality = int(args.quality) if args.quality <= 100 and args.quality > 0 else 90
else:
    quality = 90

if args.logfile:
    logfile = args.logfile
else:
    logfile = None

if __name__ == "__main__":
    try:
        # Create a window and pass it to the Application object
        App(tkinter.Tk(), "Color Temperature From RGB", video_source, pause, quality, mode, logfile)
    except Exception as e:
        print(repr(e))
        sys.exit(2)
