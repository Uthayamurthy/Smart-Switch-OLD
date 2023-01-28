from umqtt.simple import MQTTClient
from ConfigManager import Config_File
from time import sleep
import machine
from machine import Pin
from debugger import debugger

class MqttClient():
    def __init__(self):
        self.config_file = Config_File('Mqtt')
        self.config = self.config_file.fetch_config()
        self.sub_list = dict()
        
    def create_mqtt_client(self):
        self.client = MQTTClient(self.config['CLIENT_ID'].encode(),self.config['BROKER'],port=int(self.config['PORT']),user=self.config['USER'],password=self.config['PASSWORD'],ssl=True)
        self.client.set_callback(self.cb_func)
        connected = False
        boot_config_file = Config_File('boot')
        boot_config = boot_config_file.fetch_config()
        status_led = Pin(int(boot_config['STATUS_LED']), Pin.OUT)
        print('MQTT : Connecting to the server ...')
        while not connected:
            try:
                self.client.connect()
                sleep(2)
                connected = True
            except OSError as e:
                e = str(e)
                print('Mqtt Mgr : Encountered OSError " {} " when connecting to MQTT Broker !'.format(type(e)))
                print('>>>{}<<<'.format(e))
                status_led.on()
                sleep(5)
                status_led.off()
                if e == '23':
                    print('Mqtt Mgr : Rebooting in 20 seconds as 23 is returned as the error code.......')
                    for x in range(20):
                        status_led.on()
                        sleep(0.5)
                        status_led.off()
                        sleep(0.5)
                    machine.reset()
                print('MQTT Mgr : Trying to establish connection once again ...')
                sleep(5)
        
        for n in range(3):
            status_led.on()
            sleep(1.5)
            status_led.off()
            sleep(1.5)
        
        print('MQTT : Connected!!')
        print('MQTT : Subscribing to the required topics ...')
        self.subscribe()
        print('MQTT : Subcribed to the Topics !!')
        status_led.on()
        
    def add_sub_topic_cb(self, topic, cb_func):
        if topic not in self.sub_list:
            self.sub_list[topic] = cb_func
            print('MQTT sub : Added {} topic and {} function to the subscribe list.'.format(topic, cb_func))
        else:
            print('MQTT sub : Did not add the topic {} and function {} as it exists already.'.format(topic, cb_func))
    
    def subscribe(self):
        print('MQTT: Got {} as SUB LIST.'.format(self.sub_list))
        for topic in self.sub_list:
            self.client.subscribe(topic.encode(), qos=1)
            print('MQTT sub : Subscribed to topic {}'.format(topic))
            
    def cb_func(self, topic, msg):
        print('MQTT cb: Got msg {} from topic {}.'.format(msg, topic))
        self.sub_list[topic.decode()](topic, msg)
        
    def check_msg(self):
        try:
            self.client.check_msg()
            print('MQTT: Checked msg')
            sleep(1)
        except:
            print('MQTT : Unable to Check Message')
            print('MQTT : Trying to reconnect ...')
            self.create_mqtt_client()
    
    def publish(self, topic, msg, retain=False, qos=1):
        self.client.publish(topic, msg, retain, qos)