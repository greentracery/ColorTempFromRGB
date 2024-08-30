##
## ColorTempFromRGB CV2 Frame Capture module. 
## - Capture frame from selected video source & save snapshots
##
## https://github.com/greentracery/ColorTempFromRGB
##

import cv2
import os
import sys
import io
import time

class VideoCapture():
    
    def __init__(self, video_source = 0):
        # Open the video source
        self.vid = cv2.VideoCapture(video_source)
        if not self.vid.isOpened():
            raise ValueError("Unable to open video source", video_source)
        # Get video source width and height
        self.width = int(self.vid.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.font = cv2.FONT_HERSHEY_COMPLEX
        self.fontsize = 0.6
        self.default_fontcolor = (0, 250, 0)
    
    def get_frame(self):
        if self.vid.isOpened():
            status, frame = self.vid.read()
            if status:
                # Return a boolean success flag and the current frame converted to BGR
                return (status, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            else:
                return (status, None)
        else:
            return (False, None)
    
    # Release the video source when the object is destroyed
    def __del__(self):
        if self.vid.isOpened():
            self.vid.release()
