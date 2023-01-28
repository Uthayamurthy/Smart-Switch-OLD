from network import WLAN, STA_IF
from time import sleep
from debugger import debugger
from ConfigManager import Config_File
import _thread as th
from machine import Pin

my_debugger = debugger(False, mode=1)

def init():
    global mynet
    mynet = WLAN(STA_IF)
    config_file = Config_File('Wifi')
    global config
    config = config_file.fetch_config()      
    my_debugger.debug_msg('Wifi Mgr init: Completed Initialisation Successfully !')
    boot_config_file = Config_File('boot')
    boot_config = boot_config_file.fetch_config()
    global status_led
    status_led = Pin(int(boot_config['STATUS_LED']), Pin.OUT)

def activate():
    if mynet.active() == True:
        return
    mynet.active(True)
    my_debugger.debug_msg('Wifi Mgr Activate : Activated Wifi !')

def deactivate():
    mynet.active(False)
    my_debugger.debug_msg('Wifi Mgr Deactivate: Deactivated Wifi !')

def scan(verbose=1):
    activate()
    my_debugger.debug_msg('Wifi Mgr Scan: Scanning..........')
    available_networks = mynet.scan()
    num = 1
    ssid_list = []
    for some_info in available_networks:
        ssid = str(some_info[0], 'utf-8')
        ssid_list.append(ssid)
        if verbose == 1:
            print('{}. {}'.format(num, ssid))
            num += 1
    my_debugger.debug_msg('Wifi Mgr Scan:Scan Complete ! Found {} SSID'.format(ssid_list))        
    return ssid_list

def isconnected():
    return mynet.isconnected()

def connect(reconnect=False):
    activate()
    global config
    
    if mynet.isconnected()==True and reconnect == False:
        my_debugger.debug_msg('Wifi Mgr Connect: Already Connected to Network.')
        return
    if reconnect==True:
        disconnect()
    if config['SSID'] == ' ':
        my_debugger.debug_msg('Wifi Mgr Connect: Set a valid value to SSID variable and then continue .')
        return
    available_ssid = scan(0)
    my_debugger.debug_msg('Wifi Mgr Connect: Scan returned {} as a list of available ssids'.format(available_ssid))
    if config['SSID'] not in available_ssid:
        my_debugger.debug_msg('Wifi Mgr Connect: Specified Network SSID does not exist.Check whether the router is turned on.')
        return
    if config['IP_ADDR'] == ' ' or config['SUBNET'] == ' ' or config['GATEWAY'] == ' ' or config['DNS'] == ' ':
        my_debugger.debug_msg('Wifi Mgr Connect: Setting up DHCP Network Configuration........')
        try:
            mynet.connect(config['SSID'],config['PASSWORD'])
            global status_led
            for n in range(10):
                status_led.on()
                sleep(0.3)
                status_led.off()
                sleep(0.3)
                
            my_debugger.debug_msg('Wifi Mgr Connect: Connected to {} Successfully'.format(config['SSID']))
        except Exception as e:
            my_debugger.debug_msg('Wifi Mgr Connect: Encountered {} while connecting with dhcp network configuration.'.format(e))
    else:
        my_debugger.debug_msg('Wifi Mgr Connect: Setting up Static Network Configuration........')
        try:
            mynet.ifconfig((config['IP_ADDR'],config['SUBNET'],config['GATEWAY'],config['DNS']))
            mynet.connect(config['SSID'],config['PASSWORD'])
            global status_led
            for n in range(10):
                status_led.on()
                sleep(0.3)
                status_led.off()
                sleep(0.3)
            my_debugger.debug_msg('Wifi Mgr Connect: Connected to {} Successfully !'.format(config['SSID']))
        except Exception as e:
            my_debugger.debug_msg('Wifi Mgr Connect: Encountered {} while Setting up network .'.format(e))
    while not isconnected():
        sleep(0.2)
        
def disconnect():
    mynet.disconnect()
    my_debugger.debug_msg('Wifi Mgr Disconnect: Disconnected from Wifi Network.')


def info():
    activate()
    global config
    if mynet.isconnected() == True:
        net_details = mynet.ifconfig()
        print('Connected to {}'.format(config['SSID']))
        print('My IP address now is : {}'.format(net_details[0]))
        print('My Subnet is : {}'.format(net_details[1]))
        print('My Gateway is : {}'.format(net_details[2]))
        print('My current DNS Server is : {}'.format(net_details[3]))       
    else:
        print('You are not yet connected to a Wifi Network.')
        print('Please connect to a Network first.')
        
def status():
    if mynet.active() == True:
        print('Wifi is up')
        if mynet.isconnected() == True:
            connected_status = 'Yes'
        else:
            connected_status = 'No'
        print('Connected to a access point : {}'.format(connected_status))
    else:
        print('Wifi is Down')

def autoreconnect_func():
    while True:
        try:
            if mynet.isconnected() == False:
                my_debugger.debug_msg('Wifi Mgr Autoreconnect: I Seem to be Disconnected from Wifi so trying to restablish connection...')
                connect()
                for n in range(7):
                    status_led.on()
                    sleep(0.3)
                    status_led.off()
                    sleep(0.3)
                sleep(20)
        except KeyboardInterrupt:
            my_debugger.debug_msg('Wifi Mgr Autoreconnect: Encountered KeyboardInterrupt .....')
                     
def autoreconnect_start_thread():
    th.start_new_thread(autoreconnect_func,())
    my_debugger.debug_msg('Wifi Mgr Autoreconnect Thread Starter: Wifi autoreconnect thread started !')

def help():
    print('''This is a simple module to make configuration of wifi in your esp32 much easier.
             Following are its attributes :-
             init() - This function Initialises the interface (but does not activate it).Usually there is no need
                      to use this function as this function is run when you import the library.
             activate() - This function activates the Wifi .
             deactivate() - This function deactivates Wifi .
             scan(verbose) - Scans for available Wifi Networks and my_debugger.debug_msgs the available ssids as well as returns a list
                          of available ssids too.It takes a optional attribute verbose which can have a value of 0 or 1 . 
                          The default value of mode is 1 which enables my_debugger.debug_msging of Available ssids.
             connect(reconnect) - Connects to a Wifi network specified in this script.To change the wifi network edit
                                  the ssid and password variable in the begining of the WifiManager.py file.IP_ADDR,
                                  SUBNET and GATEWAY are optional variables which can be changed if static local ip
                                  configuration is prefered else can be left blank (' ') for dhcp configuration..
                                  It has a optional reconnect argument , which can take value of True or False.If True
                                  it basically disconnects from the currently connected network then reconnects to the
                                  same network.The default is false.
             disconnect()- Disconnects from the currently connected Wifi Network.
             info() - Provides information about the network currently connected to and ip address,subnet,gateway and
                      dns server of your device.
             status() - Provides status of your WLAN interface (active or not) and if active is it connected to some Wifi Network.
                                                                                                                   ''')
init()
activate()
