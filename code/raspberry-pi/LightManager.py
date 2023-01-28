import paho.mqtt.client as mqtt
from time import sleep
from datetime import datetime
from ConfigManager import Config_File

class Light():
    def __init__(self, name):
        self.name = name
        self.Connected = False
        self.sent_on = False
        self.sent_off = False
        self.config_file = Config_File(self.name)
        self.config = self.config_file.fetch_config()
        self.create_mqtt_client()
        print(f'Opening {self.name} prev_on file')
        self.prev_on_file = f'/home/pi/SmartHome/main/data/prev_on_{self.name}.dat'
        with open(self.prev_on_file) as file:
            prev_on = file.read()
        prev_on = prev_on.rstrip()
        print(f'{self.name} : Got prev_on as {prev_on}')
        if prev_on == 'ON':
            print(f'{self.name} seems to be ON before so sending off signal .........')
            for n in range(5):
                self.client.publish(self.config['TOPIC'], b'NO', qos=1, retain=True)
                print(f'Sent {n+1} time!')
            self.sent_off = True
            with open(self.prev_on_file, 'w') as file:
                file.write('OFF')
        else:
            print(f'Nothing to do as {self.name} is off already!')
            self.sent_off = True
        self.end_hour = int(self.config['END_HOUR'])
        self.end_minute = int(self.config['END_MINUTE'])
        self.start_hour = int(self.config['START_HOUR'])
        self.start_minute = int(self.config['START_MINUTE'])
    
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f'Connected to Broker for {self.name} !')
            self.Connected = True
        else:
            print(f'Connection Failed for {self.name} !')
    
    def create_mqtt_client(self):
        print('Entered mqtt client create function.')
        self.client = mqtt.Client(self.config['CLIENT_ID'])
        self.client.username_pw_set(self.config['USER'], password=self.config['PASSWORD'])
        self.client.on_connect= self.on_connect
        self.client.tls_set('/home/pi/SmartHome/main/ssl/ca.crt')
        self.client.tls_insecure_set(True)
        self.client.connect(self.config['BROKER'], port=int(self.config['PORT']))
        self.client.loop_start()
        
        while self.Connected != True:
            sleep(0.1)
            print('Waiting for connection ......')
            
    def handle_time_threshold(self):
        try:
            hour = int(datetime.now().hour)
            minute = int(datetime.now().minute)
            if hour == self.end_hour and minute >= self.end_minute:
                if self.sent_off == False:
                    for n in range(5):
                        self.client.publish(self.config['TOPIC'], b'NO', qos=1, retain=True)
                        print(f'{self.name} : Reached Time-threshold at {datetime.now()} so sending OFF Signal')
                    with open(self.prev_on_file, 'w') as file:
                        file.write('OFF')
                    print(f'{self.name} : Written OFF to prev_on file.')
                    self.sent_off = True
                    self.sent_on = False
                print(f'Done Turning OFF for {self.name}')
                sleep(2)
            elif hour == self.start_hour and minute >= self.start_minute:
                if self.sent_on == False:
                    for n in range(5):
                        self.client.publish(self.config['TOPIC'], b'YES', qos=1, retain=True)
                        print(f'{self.name} : Reached Time-threshold at {datetime.now()} so sending ON Signal')
                    with open(self.prev_on_file, 'w') as file:
                        file.write('ON')
                    print(f'{self.name}: Written On to prev_on file')
                    self.sent_on = True
                    self.sent_off = False
                print(f'Done Turning ON for {self.name}')
                sleep(2)
            else:
                print(f'{self.name} : Nothing to do !')
                sleep(5)
                
        except KeyboardInterrupt:
            self.client.disconnect()
            self.client.loop_stop()
