import paho.mqtt.client as mqtt
from time import sleep
import os
from datetime import datetime

Connected = False
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print('Connected to Broker')
        global Connected
        Connected = True
    else:
        print('Connection Failed !')
        
def on_message(client, userdata, message):
    msg = message.payload.decode()
    if msg == 'BOOTED':
       os.system('clear')
       print('Welcome To Balcony-Lights Debug Messages')
       print('Waiting for debug messages.......')
    current_time_raw = datetime.now()
    current_time = f'{current_time_raw.hour}:{current_time_raw.minute}:{current_time_raw.second}'
    print(f'**********New Debug Message arrived [{current_time}] **********')
    print(f'{message.payload.decode()}')

def start():
    global Connected
    client = mqtt.Client('iotserver_balconyESP32-1_DEBUG')
    client.username_pw_set('raspberrypi-iotserver', password='Kalam2020')
    client.on_connect = on_connect
    client.on_message = on_message
    client.tls_set('/home/pi/SmartHome/ssl/ca.crt')
    client.connect('iotserver', port=8883)
    sleep(5)
    client.subscribe('home/balcony/esp32-1/debug', qos=1)
    sleep(2)
    os.system('clear')
    print('Welcome To Balcony-Lights Debug Messages')
    print('Waiting for debug messages.......')
    sleep(1)
    client.loop_forever()

start()
