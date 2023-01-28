from LightManager import Light
import Administration as admin
from MqttManager import MqttClient
from time import sleep
from machine import Pin
from debugger import debugger
from ConfigManager import Config_File

print('**********NORMAL-MODE**********')

mqttclient = MqttClient()
admin.init(mqttclient)

light1 = Light('Light1', mqttclient)
light2 = Light('Light2', mqttclient)

my_debugger = debugger(True, mode = 3, client=mqttclient)

mqttclient.create_mqtt_client()

boot_config_file = Config_File('boot')
boot_config = boot_config_file.fetch_config()
status_led = Pin(int(boot_config['STATUS_LED']), Pin.OUT)

my_debugger.debug_msg(('**********NORMAL-MODE**********'))

for n in range(4):
    status_led.on()
    sleep(1)
    status_led.off()
    sleep(1)

sleep(2)
status_led.on()

while True:
    status_led.on()
    mqttclient.check_msg()
    if light1.pir_mode:
        light1.pir_check()
    if light2.pir_mode:
        light2.pir_check()