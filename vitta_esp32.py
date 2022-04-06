from machine import *
import network
import math
import utime
try:
    from esp32_lcd_i2c import LCD1602
    from vitta_server import SERVER
    from vitta_client import CLIENT
except ImportError:
    print("Cannot import libraries")

class AdacraftExtension:
    def __init__(self):
        try:
            self.lcd = LCD1602(i2c=I2C(scl=Pin(22), sda=Pin(21)))
        except (ValueError, NameError):
            print("LCD 1602 not detected.")
        
    def init(self, ready):
        self.station = None
        self.ap = None
        self.server = None
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
    
    def respond(self, cmd, status=1, value=None):
        return "{\"cmd\":\"" + str(cmd).replace('"', '\\"')+ "\", \"status\":" + str(status) + ", \"value\":" + ("null" if value is None else str(value)) + "}\n"
    
    def connect_station(self, ssid='', password='', ip='', mask='', gateway=''):
        self.station = network.WLAN(network.STA_IF)
        if self.station.isconnected():
            if self.station.config('essid') is ssid:
                print("Already connected on ssid: '%s'" % self.station.config('essid'))
                return
            else:
                disconnect_station()
        print("\nTrying to connect to '%s' ..." % ssid)
        if len(ip) is not 0:
            if len(gateway) == 0:
                gateway = ip.split('.')[0] + '.' + ip.split('.')[1] + '.' + ip.split('.')[2] + '.1'
            if len(mask) == 0:
                mask = '255.255.255.0'
            self.station.ifconfig([ip, mask, gateway, gateway])
        if not self.station.active():
            self.station.active(True)
        self.station.connect(ssid, password)
        while not self.station.isconnected():
            pass
        print("Station connected !")

    def disconnect_station(self):
        if self.station is not None and self.station.isconnected():
            ssid = self.station.config('essid')
            self.station.disconnect()
            for retry in range(100):
                connected = self.station.isconnected()
                if not connected:
                    break
                utime.sleep(0.1)
            if not connected:
                self.station.active(False)
                utime.sleep(0.2)
                print("Disconnected from '%s'\n" %ssid)
            else:
                print("Disconnection from '%s' failed.\n" %ssid)
        else:
            print("Station already disconnected.\n")
        
    def configure_access_point(self, ssid='', ip='', activate=True, max_clients=50):
        self.ap = network.WLAN(network.AP_IF)
        if len(ip) is not 0:
            gateway = ip.split('.')[0] + '.' + ip.split('.')[1] + '.' + ip.split('.')[2] + '.1'
            self.ap.ifconfig([ip, '255.255.255.0', gateway, gateway])
        self.ap.active(activate)
        self.ap.config(essid=ssid, password='')
        self.ap.config(max_clients=max_clients)
        print("Access point started.\n")
        return self.ap
    
