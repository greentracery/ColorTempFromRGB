##
## ColorTempFromRGB IMG2Layers module
## - Get RBG (CMYK) matrix & average RGB (CMYK) values for frame/image
##
## https://github.com/greentracery/ColorTempFromRGB
##

from PIL import Image, ImageDraw, ImageFont
import io
import os
import numpy as np

class IMG2Layers():
    
    MODES = ('mean', 'median')
    
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
            rgb_image = img.convert('RGB') # delete aplha-channel from image
            rgb_image.save(buf, format='JPEG')
        else:
            img.save(buf, format='JPEG')
        byte_img = buf.getvalue()
        orgimg = np.array(Image.open(io.BytesIO(byte_img)))
        return orgimg
    
    def get_rgb_matrix(self, image) -> tuple:
        """ Return tuple of numpy.arrays """
        img = self.img_from_array(image)
        self.width, self.height = img.size
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
        
    def get_cmyk_matrix(self, image) -> tuple:
        """ Return tuple of numpy.arrays """
        img = self.img_from_array(image)
        width, height = img.size
        frm = img.format
        mode = img.mode # 'RGB', 'RGBA', 'CMYK', 'L'
        bands = img.getbands() # ('R','G','B'), ('C','M','Y','K'), ('L')
        
        if mode == 'L':
            raise Exception ("Grayscale mode")
            
        if mode == 'RGBA' or mode == 'RGB':
            img = img.convert('CMYK')
        
        cyan, magnetta, yellow, black = img.split()
        
        C = np.array(cyan)
        M = np.array(magnetta)
        Y = np.array(yellow)
        K = np.array(black)
        
        return C,M,Y,K
        
    def get_average_colorvalues(self, color_layers: list, mode: str) -> list:
        """ Return average value(s) for all pixels in image color layer(s) """
        if mode not in self.MODES:
            mode = self.MODES[0] # default == 'mean'
            
        if mode == self.MODES[1]:
            return self.get_median_colorvalues(color_layers)
            
        return self.get_mean_colorvalues(color_layers)
    
    def get_mean_colorvalues(self, color_layers: list) -> list:
        """ Return mean value(s) for all pixels in image color layer(s) """
        out_layers = []
        for layer in color_layers:
            if len(layer.shape) != 2:
                 raise Exception (f"Invalid shape {layer.shape}")
            layer_mean_value = round(np.array(layer).flatten().mean())
            out_layers.append(layer_mean_value) if layer_mean_value < 255 else out_layers.append(255)
        
        return out_layers
    
    def get_median_colorvalues(self, color_layers: list) -> list:
        """ Return median value(s) for all pixels in image color layer(s) """
        out_layers = []
        for layer in color_layers:
            if len(layer.shape) != 2:
                 raise Exception (f"Invalid shape {layer.shape}")
            layer_median_value = round(np.median(np.array(layer).flatten()))
            out_layers.append(layer_median_value) if layer_median_value < 255 else out_layers.append(255)
        
        return out_layers
    
    def get_average_brightness(self, average_layer_values: list) -> int:
        """ Return average brightness in [0..100] range """
        return int(max(average_layer_values) * 100 / 255)
