import gc
import uhashlib
import ubinascii
import urequests as requests
import uos            
from machine import Pin

def file_exists(file):
    try:
        open(file)
        return True
    except:
        return False
    
def gen_hash(file_name):
    BLOCKSIZE = 1024
    hasher = uhashlib.sha256()
    try:
        gc.collect()
        with open(file_name, 'rb') as afile:
            buf = afile.read(BLOCKSIZE)
            while len(buf) > 0:
                hasher.update(buf)
                buf = afile.read(BLOCKSIZE)
        gen_hash = ubinascii.hexlify(hasher.digest())
        print('Generated Hash : {}'.format(gen_hash))
        return gen_hash
    except MemoryError as error:
        print(gc.mem_free())
        print('Got a memory error !')
        gc.collect()
        print(gc.mem_free())
        return None

def gen_hash_file(file_name):
    try:
        hash_val = None
        while hash_val == None:
            hash_val = gen_hash(file_name)
        file = list(file_name.split('.'))
        with open('{}.sha256'.format(file[0]), 'wb') as hash_file:
            hash_file.write(hash_val)
        print('Generated Hash File Successfully !')
    except:
        print('Encountered Error while Generating Hash file.')

def verify_hash(file_name, hash_file=None):
    if hash_file == None:
        hash_file = '{}.sha256'.format(file_name.split('.')[0])
    print('Hash file is : {}'.format(hash_file))
    with open(hash_file, 'rb') as hfile:
        given_hash = hfile.read()
    hash_val = gen_hash(file_name)
    print('Given Hash : {}'.format(given_hash))
    if hash_val == given_hash:
        print('Verified Hash Successfully !!!')
        return True
    else:
        print('Hash Does Not seem to match :( ')
        return False
    
def download(filename, url):
    r = requests.get(url)
    with open(filename,'wb') as output_file:
        output_file.write(r.content)
        
def copy(file_to_copy, destination):
    BLOCKSIZE = 2048
    file_to_write='{}/{}'.format(destination, file_to_copy)
    with open(file_to_copy, 'rb') as afile:
        with open(file_to_write, 'wb') as bfile:
            for buf in afile:
                bfile.write(buf)
                
def move(file_to_move, destination):
    copy(file_to_move, destination)
    uos.remove(file_to_move)

def safe_shutdown():
    from ConfigManager import Config_File
    
    boot_config_file = Config_File('boot')
    light1_config_file = Config_File('Light1')
    light2_config_file = Config_File('Light2')

    boot_config = boot_config_file.fetch_config()
    light1_config = light1_config_file.fetch_config()
    light2_config = light2_config_file.fetch_config()

    light1 = Pin(light1_config['PIN'], Pin.OUT)
    light2 = Pin(light2_config['Pin'], Pin.OUT)
    status_led = Pin(int(boot_config['STATUS_LED']), Pin.OUT)
    status_led_2 = Pin(int(boot_config['STATUS_LED_2']), Pin.OUT)
    status_led_3 = Pin(int(boot_config['STATUS_LED_3']), Pin.OUT)

    light1.value(1)
    light2.value(1)

    status_led.off()
    status_led_2.off()
    status_led_3.off()