__platform__ = 'Raspberry pi'
__version__  = '1.0'

import paho.mqtt.client as mqtt
import os
from http.server import HTTPServer, CGIHTTPRequestHandler
from time import sleep
from ConfigManager import Config_File
from extras import randstr,gen_hash_file,gen_hash
import socket
import os
import tqdm
from pyfiglet import Figlet 

Connected = False
task_done = False
task_error = False
task_error_msg = ''
task_code = ''
output = None
bulk_output = None
serve_files = False
receive_files = False

config_file = Config_File('admin')
config = config_file.fetch_config()

broker_ip = config['BROKER']
port = int(config['PORT'])
user = config['USER']
password = config['PASSWORD']
topic_sub = config['TOPIC_SUB']
topic_pub = config['TOPIC_PUB']

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print('Connected to Broker')
        global Connected
        Connected = True
    else:
        print('Connection Failed !')

def on_message(client, userdata, message):
    global task_done
    global task_code
    global task_error
    global task_error_msg
    global output
    global bulk_output
    msg = str(message.payload.decode("utf-8"))
    msg = msg.rstrip()
    msg = msg.split('-')
    if msg[0] == 'OUTPUT' and msg[1] == task_code:
        task_done = True
        output = msg[2]
        
    elif msg[0] == 'BOUTPUT' and msg[1] == task_code:
        global received_msg_num
        global total_msg_num
        global serve_files
        
        if msg[2] == 'MSG_NUM':
            total_msg_num = int(msg[3])
            received_msg_num = 0
            bulk_output = []
        else:
            if msg[2] == 'DONE':
                print('Got done !!!!')
                task_done = True
                serve_files = False
            else:
                print(f'Got {msg[2]} as message so appending it to the list')
                bulk_output.append(msg[2])
                
    elif msg[0] == 'COMPLETE' and msg[1] == task_code:
        task_done = True
    elif msg[0] == 'ERROR':
        task_error = True
        task_error_msg = msg[2]
    else:
        print('Received Unwanted message.')
        print(f'Message is {msg}')
        
def init():
    global client
    global Connected
    
    client = mqtt.Client(config['CLIENT_ID'])
    client.username_pw_set(user, password=password)
    client.on_connect = on_connect
    client.on_message = on_message
    client.tls_set(f'{config["ROOT_PATH"]}/ssl/ca.crt')
    client.tls_insecure_set(True)
    client.connect(broker_ip, port=port)
    client.loop_start()

    while Connected != True:
        sleep(0.1)

    client.subscribe(topic_sub, qos=1)
    os.system('clear')
    fig = Figlet(font='roman')
    sub_fig = Figlet(font='digital')
    print(fig.renderText(f'Admin V{__version__}'))
    print(sub_fig.renderText('Balcony Lights'))
    
def wait_completion():
    global task_done
    global task_code
    global task_error
    global task_error_msg
    global serve_files
    global receive_files
    
    if serve_files:
        server_object = HTTPServer(server_address=('', 80), RequestHandlerClass=CGIHTTPRequestHandler)
        served_num = 0
        print('Created Web server object.')
    if receive_files:
        receive_file()
    while not task_done:
        if task_error == True:
            print(f'ESP32 was unable to complete the task {task_code} and raised {task_error_msg} as error message.')
            print('Please Try Again !')
            task_error = False
            task_error_msg = ' '
            sleep(1)
            break
        if serve_files:
            server_object.handle_request()
            served_num += 1
            print(f'Served {served_num} time.')
            sleep(1)
    if serve_files:
        serve_files = False
        if __platform__ == 'Raspberry pi':
            os.system('sudo systemctl start nginx.service')

    task_done = False
    receive_files = False
    
def gen_task_code(task):
    known_tasks = {'reboot':'boot', 'push_files':'download_files', 'update':'update', 'get':'upload', 'chmod':'boot'}
    task_name = task.split(' ')

    if task_name[0] in known_tasks:
        task_code = known_tasks[task_name[0]]
        print(f'Task code is : {task_code}')
        return task_code
    else:
        print(f'Task is {task_name}')
        task_code = randstr()
        print(f'Task Code is {task_code}')
        return task_code
    
def prepare_download():
    if __platform__ == 'Raspberry pi':
        os.system('sudo systemctl stop nginx.service')
    global serve_files
    serve_files = True
    os.chdir(f'{config["ROOT_PATH"]}/updates')
    files = os.listdir()
    for file in files:
        if file.startswith('filelist'):
            continue
        if '.sha256' in file:
            continue
        gen_hash_file(file)
    with open('filelist.txt', 'w') as filelist:
        for file in files:
            if file.startswith('filelist'):
                continue
            if '.sha256' in file:
                continue
            filelist.write(file)
            filelist.write('\n')
    return gen_hash('filelist.txt').decode()

def receive_file():
    global task_done
    os.chdir(f'{config["ROOT_PATH"]}/received_files')
    SERVER_HOST = "0.0.0.0"
    SERVER_PORT = int(config['SERVER_PORT'])
    BUFFER_SIZE = 2048
    SEPARATOR = "--"
    s = socket.socket()
    s.bind((SERVER_HOST, SERVER_PORT))
    s.listen(5)
    print(f"[*] Listening as {SERVER_HOST}:{SERVER_PORT}")
    client_socket, address = s.accept()
    print(f"[+] {address} is connected.")
    received = client_socket.recv(BUFFER_SIZE).decode()
    filename, filesize = received.split(SEPARATOR)
    filename = os.path.basename(filename)
    filesize = int(filesize)
    progress = tqdm.tqdm(range(filesize), f"Receiving {filename}", unit="B", unit_scale=True, unit_divisor=1024)
    with open(filename, "wb") as f:
        for _ in progress:
          bytes_read = client_socket.recv(BUFFER_SIZE)
          if not bytes_read:
            break
          f.write(bytes_read)
          progress.update(len(bytes_read))
    client_socket.close()
    s.close()
    sleep(1)
    task_done = True
    
def execute(task):
    global task_code
    global client
    global topic_pub
    global output
    global bulk_output
    global receive_files
    task_code = gen_task_code(task)

    if task.startswith('push_files'):
        file_list_hash = prepare_download()
        task = task.replace('push_files', 'download_files', 1)
        task = task.split(' ')
        if len(task) == 2:
            command = f'{task_code}-{task[0]} {file_list_hash} {task[1]}'.encode()
        else:
            command = f'{task_code}-{task[0]} {file_list_hash}'.encode()
        print(f'Command is {command}')
    elif task.startswith('update'):
        file_list_hash = prepare_download()
        task = task.split(' ')
        if len(task) == 2:
            command = f'{task_code}-{task[0]} {file_list_hash} {task[1]}'.encode()
        else:
            command = f'{task_code}-{task} {file_list_hash}'.encode()
    elif task.startswith('get'):
        task = task.replace('get', 'send', 1)
        command = f'{task_code}-{task}'.encode()
        receive_files = True
    else:
        command = f'{task_code}-{task}'.encode()
    client.publish(topic_pub, command, qos=1, retain=False)


    wait_completion()
    if output != None:
        print(f'Output : {output}')
        output = None
        return output
    
    if bulk_output != None:
        print('Got the following Output : ')
        for msg in bulk_output:
            print(msg)
        bulk_output = None
            
def change_time():
    if __platform__ == 'Raspberry pi':
        print('**********Light1**********')
        light1_start_time = list(input('Start Time (hr:min) : ').split(':'))
        light1_end_time = list(input('End Time (hr:min) : ').split(':'))
        print('**********Light2**********')
        light2_start_time = list(input('Start Time (hr:min) : ').split(':'))
        light2_end_time = list(input('End Time (hr:min) : ').split(':'))

        light1_config = Config_File('light1')
        light2_config = Config_File('light2')

        light1_config.change_config('START_HOUR', light1_start_time[0])
        light1_config.change_config('START_MINUTE', light1_start_time[1])
        light1_config.change_config('END_HOUR', light1_end_time[0])
        light1_config.change_config('END_MINUTE', light1_end_time[1])
        
        light2_config.change_config('START_HOUR', light2_start_time[0])
        light2_config.change_config('START_MINUTE', light2_start_time[1])
        light2_config.change_config('END_HOUR', light2_end_time[0])
        light2_config.change_config('END_MINUTE', light2_end_time[1])

        os.system('sudo systemctl restart balcony-lights.service')
        print('Done changing the time.')
    else:
        print('This command is only applicable in Raspberry pi Iotserver.')

def help():
    print('''This is a simple utility to control esp32 remotely.
             
             Following is the supported commands:
             ping - Checks whether esp32 is accepting commands. Returns Ok if available.
             info - Sends the version number along with current mode.
             ls - Lists the files and folders in its current directory.
             mkdir - Creates a directory with the given file name.
             rmdir - Removes a directory.
             cd - Changes current working directory to another specified direectory.
             pwd - Prints the current working directory.
             rm - Removes a file specified.
             rename- Renames a given file.
             cp - Copy a file to another location.
             mv - Move a file to another location.
             push_files - Pushes all the files in update directory to ESP32.
             update - Pushes all the files in update directory to ESP32 and reads the update.txt file for update instruction.
             get - Get a file from ESP32.
             execute - Execute the file specified in ESP32.
             chmod - Change the mode to normal or safe and reboot.
             chconfig - Change a particular config of a config file to the specified configuration. 
             chtime - Change time treshold in the config file and restart the service. [Works only on Raspberry Pi]
             reboot - Reboots the ESP32.

             ''')
init()    

if __name__ == '__main__':
    while True:
        try:
            cmd = str(input(f'admin@{__platform__} : '))
            if cmd == 'exit':
                break
            elif cmd == '' or cmd == ' ':
                continue
            elif cmd == 'clear':
                os.system('clear')
            elif cmd == 'help':
                help()
            elif cmd == 'chtime':
                change_time()
            elif cmd == ' ' or cmd == '':
                continue
            else:
                execute(cmd)
        except KeyboardInterrupt:
            break