print('**********SAFE-MODE**********')

import Administration as admin
from ConfigManager import Config_File
from MqttManager import MqttClient
from machine import Pin
from time import sleep

light1_conf = Config_File('Light1').fetch_config()
light2_conf = Config_File('Light2').fetch_config()
light1 = Pin(int(light1_conf['PIN']), Pin.OUT)
light2 = Pin(int(light2_conf['PIN']), Pin.OUT)

boot_config_file = Config_File('boot')
boot_config = boot_config_file.fetch_config()
status_led = Pin(int(boot_config['STATUS_LED']), Pin.OUT)
status_led_2 = Pin(int(boot_config['STATUS_LED_2']) ,Pin.OUT)
status_led_3 = Pin(int(boot_config['STATUS_LED_3']) ,Pin.OUT)

print('Turning OFF Light1 and Light2 .....')
light1.value(1)
status_led_2.off()
light2.value(1)
status_led_3.off()
print('DONE !!')

mqttclient = MqttClient()
admin.init(mqttclient)
mqttclient.create_mqtt_client()

while True:
    status_led.on()
    status_led_2.on()
    status_led_3.on()
    sleep(0.5)
    status_led.off()
    status_led_2.off()
    status_led_3.off()
    mqttclient.check_msg()