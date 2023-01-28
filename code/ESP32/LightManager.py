from machine import Pin
from ConfigManager import Config_File
from time import sleep
from WifiManager import autoreconnect_func
from debugger import debugger

class Light():
    def __init__(self, name, client):
        self.name = name
        self.config_file = Config_File(self.name)
        self.config = self.config_file.fetch_config()
        self.client = client
        self.light = Pin(int(self.config['PIN']), Pin.OUT)
        self.status_led = Pin(int(self.config['STATUS_LED_PIN']), Pin.OUT)
        self.light.value(1)
        self.status_led.off()
        self.reached_time_treshold = False
        self.motion = False
        self.pir_with_time = False
        self.pir_mode = False
        self.auto_configure()
        
    def manual(self):
        self.client.add_sub_topic_cb(self.config['MANUAL_TOPIC'], self.manual_cb)
    
    def manual_cb(self, topic, msg):
        if msg == 'ON':
            self.light.value(0)
            self.status_led.on()
        elif msg == 'OFF':
            self.light.value(1)
            self.status_led.off()

    def handle_pir_interrupt(self, Pin):
        print('Motion Detected !')
        self.motion = True
        
    def sub_cb_pir(self, topic, msg):
        if msg == b'YES':
            print('{} : Reached Time treashold so enabling .......'.format(self.name))
            self.reached_time_treshold = True
        elif msg == b'NO':
            print('{} : Not reached time threshold so disabling .......'.format(self.name))
            self.reached_time_treshold = False
        print('{} : Value of self.reached_time_treshold is {}'.format(self.name, self.reached_time_treshold))
        
    def auto_pir(self):
        self.pir = Pin(int(self.config['PIR']), Pin.IN)
        self.pir.irq(trigger=Pin.IRQ_RISING, handler=self.handle_pir_interrupt)
        print('{} : Created Interupt for pir'.format(self.name))
        if self.pir_with_time == True:
            print('{} : Chosen pir with time.'.format(self.name))
            self.client.add_sub_topic_cb(self.config['SUB_TOPIC'], self.sub_cb_pir)
            print('{} : Created an mqtt client for pir.'.format(self.name))
        else:
            print('{} : Chosen pir without time.'.format(self.name))
            
    def pir_check(self):
        if not self.pir_with_time:
            if self.motion:
                self.light.value(0)
                self.status_led.on()
                sleep(int(self.config['LIGHT_DELAY']))
                self.light.value(1)
                self.status_led.off()
                self.motion = False
        if self.pir_with_time:
            if self.motion and self.reached_time_treshold:
                self.light.value(0)
                self.status_led.on()
                sleep(int(self.config['LIGHT_DELAY']))
                print('{} : Turning off light as delay over ....'.format(self.name))
                self.light.value(1)
                self.status_led.off()
                print('{} : Turned OFF !'.format(self.name))
                self.motion = False
        sleep(1)
        
    def sub_cb_time_based(self, topic, msg):
        if msg == b'YES':
            print('{} : reached time treshold so turning on'.format(self.name))
            self.light.value(0)
            self.status_led.on()
        elif msg == b'NO':
            print('{} : reached time treshold so turning off'.format(self.name))
            self.light.value(1)
            self.status_led.off()
            
    def time_based_control(self):
        self.client.add_sub_topic_cb(self.config['SUB_TOPIC'] ,self.sub_cb_time_based)
        
    def auto_configure(self):
        if self.config['LOGIC'] == 'PIR_ONLY':
            print('OK')
            print('Choosing {} for {}'.format('PIR_ONLY', self.name))
            self.pir_with_time = False
            self.pir_mode = True
            self.auto_pir()
        elif self.config['LOGIC'] == 'PIR_WITH_TIME':
            print('OK')
            self.pir_with_time = True
            self.pir_mode = True
            print('Choosing {} for {}'.format('PIR_WITH_TIME', self.name))
            self.auto_pir()
        elif self.config['LOGIC'] == 'TIME_BASED':
            print('OK')
            print('Choosing {} for {}'.format('TIME_BASED', self.name))
            self.time_based_control()
        elif self.config['LOGIC'] == 'MANUAL':
            print('OK')
            print('Choosing {} for {}'.format('MANUAL', self.name))
            self.manual()
        else:
            print('No Logic specified in Config File.')