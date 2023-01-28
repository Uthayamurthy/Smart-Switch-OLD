import esp
import WifiManager
import gc
import _thread as th
from extras import *
from time import sleep
from machine import Pin
from debugger import debugger
from ConfigManager import Config_File

config_file = Config_File('boot')
config = config_file.fetch_config()

esp.osdebug(None)
my_debugger = debugger(True, mode=1)
try :
    gc.enable()
    my_debugger.debug_msg('Boot: Successfully Enabled Automatic Garbage Collection !')
except Exception as e :
    my_debugger.debug_msg('Boot: I encountered {} when enabling garbage collection'.format(e))

WifiManager.connect()
WifiManager.autoreconnect_start_thread()
gc.collect()

my_debugger.debug_msg('Boot: Completed Bootup !')

# Define status LEDS
status_led = Pin(int(config['STATUS_LED']), Pin.OUT)
status_led_2 = Pin(int(config['STATUS_LED_2']) ,Pin.OUT)
status_led_3 = Pin(int(config['STATUS_LED_3']) ,Pin.OUT)

# Blink status led as boot is completed ....
for x in range(5):
    status_led.on()
    sleep(0.5)
    status_led_2.on()
    sleep(0.5)
    status_led_3.on()
    sleep(1)
    status_led.off()
    status_led_2.off()
    status_led_3.off()
    sleep(1)