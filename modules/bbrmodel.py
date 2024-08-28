##
## ColorTempFromRGB blackbody radiation model
## - Convert RGB color values to color temperature (K)
##
## https://github.com/greentracery/ColorTempFromRGB
##
## Based on Mitchell Charity's blackbody data model
## See also http://www.vendian.org/mncharity/dir3/blackbody/UnstableURLs/bbr_color.html
## Fields:
##  K     temperature (K)
##  CMF   {" 2deg","10deg"}
##          either CIE 1931  2 degree CMFs with Judd Vos corrections
##              or CIE 1964 10 degree CMFs
##  x y   chromaticity coordinates
##  P     power in semi-arbitrary units
##  R G B {0-1}, normalized, mapped to gamut, logrithmic
##        (sRGB primaries and gamma correction)
##  r g b {0-255}
##  #rgb  {00-ff}
##

from contextlib import closing
import os
import numpy as np

class ColorTemp():
    
    data_model_file = r'bbr_color.txt'
    
    def __init__(self):
        i = 0
        cmfx = {}
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', self.data_model_file), "r") as file:
            for line in file:
                if i > 18 and i < 801:
                    temp_K = int(line[:6].strip())
                    cmf = line[9:15].strip()
                    r = int(line[66:70].strip())
                    g = int(line[70:74].strip())
                    b = int(line[74:78].strip())
                    
                    rn = float(line[44:51].strip())
                    gn = float(line[52:58].strip())
                    bn = float(line[59:65].strip())
                    
                    if cmf not in cmfx:
                        cmfx[cmf] = {}
                    cmfx[cmf][temp_K] = ((r, g, b), (rn, gn, bn))
                i += 1
        self.cmfx = cmfx

    def getColorTempFromRGBN(self, rn: float, gn: float, bn: float, cmf: str = '10deg'):
        """ Return nearest color temperature for RGB (normalized) using blackbody data model """
        rgb_npa = np.array([rn, gn, bn], dtype=float)
        temp_distance = {}
        
        for key, item in self.cmfx[cmf].items():
            temp_rgb_npa = np.array([item[1][0], item[1][1],item[1][2]], dtype=float)
            temp_distance[key] = np.linalg.norm(rgb_npa - temp_rgb_npa)
        
        min_distance = min(temp_distance.values())
        min_distance_temp_K = list(filter(lambda k: temp_distance[k] == min_distance, temp_distance))
        
        return min_distance_temp_K[0], round(1 - temp_distance[min_distance_temp_K[0]], 2)
    
    def getColorTempFromRGB(self, r: int, g: int, b: int, cmf: str = '10deg'):
        """ Return nearest color temperature for RGB using blackbody data model """
        rn , bn, gn = self.normalize(r, g, b)
        
        return self.getColorTempFromRGBN(rn, gn, bn, cmf)
    
    def closest_number(self, numbers, target):
        return min(numbers, key=lambda x: abs(x - target)) if numbers is not None else None
    
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
