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
    """ Get R,G,B (C,M,Y,K) layers from image, calculate average color values & brightness
    
        property: MODES: 'mean' or 'median'
        
        method: img_from_array: Return Pilow Image from numpy array
        method: img_to_array: Return numpy.array from image file
        method: get_rgb_matrix: Return tuple of numpy.arrays for each color layer (R,G,B)
        method: get_cmyk_matrix: Return tuple of numpy.arrays for each color layer (C,M,Y,K)
        method: get_average_colorvalues: Return average (mean or median) value for all pixels for each color layer
        method: get_mean_colorvalues: Return mean value for all pixels for each color layer
        method: get_median_colorvalues: Return median value for all pixels for each color layer
        method: get_average_brightness: Return average image brightness in [0..100] range
    """
    MODES = ('mean', 'median')
    
    def img_from_array(self, img):
        """ Return Pilow Image from numpy array 
        
            :param img: numpy.array
            
            return Pilow Image
        """
        return Image.fromarray(img)
        
    def img_to_array(self, img_filename):
        """ Return numpy.array from image file 
        
            :param img_filename: path to image file
            
            return numpy.array
        """
        buf = io.BytesIO()
        with Image.open(img_filename) as img:
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
        """ Return tuple of numpy.arrays for each color layer (R,G,B) 
        
            :param image: numpy.array
            
            return tuple(
                R: numpy.array
                G: numpy.array
                B: numpy.array
            )
        """
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
        """ Return tuple of numpy.arrays for each color layer (C,M,Y,K) 
        
            :param image: numpy.array
            
            return tuple(
                C: numpy.array
                M: numpy.array
                Y: numpy.array
                K: numpy.array
            )
        """
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
        """ Return average value for all pixels for each color layer 
        
            :param color_layers: list of color layer's numpy.arrays
            :param mode: 'mean' or 'median'
            
            return list of color layer's average values
        """
        if mode not in self.MODES:
            mode = self.MODES[0] # default == 'mean'
            
        if mode == self.MODES[1]:
            return self.get_median_colorvalues(color_layers)
            
        return self.get_mean_colorvalues(color_layers)
    
    def get_mean_colorvalues(self, color_layers: list) -> list:
        """ Return mean value for all pixels for each color layer 
        
            :param color_layers: list of color layer's numpy.arrays
            
            return list of color layer's average values
        """
        out_layers = []
        for layer in color_layers:
            if len(layer.shape) != 2:
                 raise Exception (f"Invalid shape {layer.shape}")
            layer_mean_value = round(np.array(layer).flatten().mean())
            out_layers.append(layer_mean_value) if layer_mean_value < 255 else out_layers.append(255)
        
        return out_layers
    
    def get_median_colorvalues(self, color_layers: list) -> list:
        """ Return median value for all pixels for each color layer 
        
            :param color_layers: list of color layer's numpy.arrays
            
            return list of color layer's average values
        """
        out_layers = []
        for layer in color_layers:
            if len(layer.shape) != 2:
                 raise Exception (f"Invalid shape {layer.shape}")
            layer_median_value = round(np.median(np.array(layer).flatten()))
            out_layers.append(layer_median_value) if layer_median_value < 255 else out_layers.append(255)
        
        return out_layers
    
    def get_average_brightness(self, average_layer_values: list) -> int:
        """ Return average image brightness in [0..100] range 
        
            :param average_layer_values: list of color layer's average values
            
            return int: brightness in [0..100] range
        """
        return int(max(average_layer_values) * 100 / 255)
