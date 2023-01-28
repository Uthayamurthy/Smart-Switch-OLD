class debugger:
    
    def __init__(self, enable, mode=1,client=None):
        self.mqttclient = client
        self.enabled = enable
        self.mode = mode
        self.debug_pub_topic = ''

    def debug_msg(self, msg):
        if self.enabled:
            if self.mode == 1:
                print(msg)
            elif self.mode == 2:
                print(msg)
                self.mqttclient.publish(self.debug_pub_topic, msg, retain=True, qos=1)
            elif self.mode==3:
                self.mqttclient.publish(self.debug_pub_topic, msg, retain=True, qos=1)
                