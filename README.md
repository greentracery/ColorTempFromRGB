# ColorTempFromRGB - Calculate average color temperature.

Homepage: https://github.com/greentracery/ColorTempFromRGB
    
## Requirements:
    
    - Python >= 3.6

    - Pillow
    
    - Numpy
    
    - OpenCV

## Usage:
    
```shell
    [python3] main.py [-url="rtsp://url_of_stream_source"] [-file="file_source"] [-ci=0] [-p=10] [-q=90] [-m=median|mean] [-log="logfile"]
```

Screenshots:

- Normal lightning, ~5000 К:

![Normal lightning, ~5000 К](img/normal_lightning.jpg)

- UV-lamp, ~ 8000-40000 K (camera w/o UV-filter):

![UV-lamp, ~ 8000-40000 K (camera w/o UV-filter)](img/uv_lightning.jpg)

- Red lamp , ~ 3700 K:

![Red lamp, ~ 3700 K](img/red_lamp.jpg)
