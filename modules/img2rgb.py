##
## ColorTempFromRGB IMG2RGB module
## - Get RBG matrix & average RGB values for frame/image
##
## https://github.com/greentracery/ColorTempFromRGB
##

from PIL import Image, ImageDraw, ImageFont
import io
import os
import numpy as np

class IMG2RGB():
    
    def img_from_array(self, img):
        """ Return Pilow Image """
        return Image.fromarray(img)
        
    def img_to_array(self, img_filename):
        """ Return numpy.array """
        buf = io.BytesIO()
        img = Image.open(img_filename)
        imgFormat = img.format
        imgMode = img.mode
        if (imgMode == 'RGBA'):
            rgb_image = img.convert('RGB')
            rgb_image.save(buf, format='JPEG')
        else:
            img.save(buf, format='JPEG')
        byte_img = buf.getvalue()
        orgimg = np.array(Image.open(io.BytesIO(byte_img)))
        return orgimg
    
    def getRBGmatrix(self, image) -> tuple:
        """ Return tuple of numpy.arrays """
        img = self.img_from_array(image)
        width, height = img.size
        frm = img.format
        mode = img.mode # 'RGB', 'RGBA', 'CMYK', 'L'
        bands = img.getbands() # ('R','G','B'), ('C','M','Y','K'), ('L')
        
        if mode == 'L':
            raise Exception ("Grayscale mode")
            
        if mode == 'RGBA' or mode == 'CMYK':
            img = img.convert('RGB')
        
        red, green, blue = img.split()
        
        R = np.array(red)
        G = np.array(green)
        B = np.array(blue)
        
        return R, G, B
        
    def getAverageValue(self, pix_array) -> int:
        """ Return average value for all image pixels in R,G or B -layer """
        pix_cnt = len(pix_array) * len(pix_array[0])
        color = 0
        for row in pix_array:
            for pix in row:
                color += pix
        color = int(color / pix_cnt)
        
        return color if color < 255 else 255
    
    def normalize(self, r, g, b) -> tuple:
        """ Return normalized values for R,G,B """
        max_value = max(r, g, b)
        if max_value != 0:
            k = 1 / max_value 
            r, g, b = round(r * k, 4), round(g * k, 4), round(b * k, 4)
        
        return r, g, b
    
    def rgb_from_normal(self, rn, gn, bn) -> tuple:
        """ Return R,G,B values from normalized """
        max_val = 255
        R, G, B = int(max_val * rn), int(max_val * gn), int(max_val * bn)
        
        R = R if R <= max_val else max_val
        G = G if G <= max_val else max_val
        B = B if B <= max_val else max_val
        
        return R, G, B
