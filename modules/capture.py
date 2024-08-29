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
    
    def snapshot(self, imgdir = None):
        # Get a frame from the video source
        status, frame = self.get_frame()
        
        target_path = os.getcwd()
        if imgdir is not None:
            target_path = os.path.join(target_path, imgdir)
            if not os.path.exists(target_path):
                os.makedirs(target_path)
        if status:
            datetime = time.strftime("%d-%m-%Y-%H-%M-%S")
            # set encode param
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
            # compress image into buffer
            result, imgencode = cv2.imencode(".jpg", frame, encode_param)
            # read from buffer & save into file
            filename = os.path.join(target_path, "frame-" + datetime + ".jpg")
            #cv2.imwrite(filename, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
            cv2.imwrite(filename, cv2.imdecode(imgencode, cv2.IMREAD_COLOR))
            return filename
        return None
    
    # Release the video source when the object is destroyed
    def __del__(self):
        if self.vid.isOpened():
            self.vid.release()
