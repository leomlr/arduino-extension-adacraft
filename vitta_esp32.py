from machine import *
import network
import math
import utime
from esp32_lcd_i2c import LCD1602

class CMD:
    def __init__(self):
        try:
            self.lcd = LCD1602(i2c=I2C(scl=Pin(22), sda=Pin(21)))
        except ValueError:
            print("LCD 1602 not detected.")
        
    def init(self, ready):
        print(ready)
        
    def pinADC(self, pinNumber, db=ADC.ATTN_11DB, bit=ADC.WIDTH_10BIT):
        pin = ADC(Pin(pinNumber))
        pin.atten(db)
        pin.width(bit)
        return pin

    def getGroveTemperature(self, pin, unit='celsius'):
        R = 1023.0/(pin.read()+1e-3) - 1
        t = 1/(math.log(R)/4250+1/298.15) - 273.15 # celsius
        if unit == 'fahrenheit':
            t = t * 9/5 + 32
        elif unit == 'kelvin':
            t += 273.15
        return t
