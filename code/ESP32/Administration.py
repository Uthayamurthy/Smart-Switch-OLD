__version__ = '1.0'

from ConfigManager import Config_File
from time import sleep
from extras import *
import uos as os
import machine
import socket
import gc
from debugger import debugger

task_code = ''

config_file = Config_File('admin')
config = config_file.fetch_config()

download_server = config['SERVER']

main_config_file = Config_File('main')
main_config = main_config_file.fetch_config()
mode = main_config['mode']

def sub_cb(topic, msg):
    global task_code
    try:
        msg = list(str(msg, 'utf-8').split('-'))
        task_code = msg[0]
        task = msg[1]
        task_handler(task, task_code)
    except Exception as e:
        send_error('Encountered Exception : {}'.format(e), task_code)
    
def init(client):
    try:
        global mqttclient, admin_debugger
        
        mqttclient = client
        mqttclient.add_sub_topic_cb(config['SUB_TOPIC'], sub_cb)
        sleep(1)
        admin_debugger = debugger(True, mode=2, client=mqttclient)
        admin_debugger.debug_msg('Administration : Done initialisation !!')
    except Exception as e:
        print('Encountered {} Exception while initialising.'.format(e))

def send_completion(task_code):
    global mqttclient, admin_debugger
    
    mqttclient.publish(config['PUB_TOPIC'].encode(), 'COMPLETE-{}'.format(task_code), retain = False, qos=1)
    admin_debugger.debug_msg('Successfully sent completion !')

def send_error(error_msg, task_code):
    global mqttclient
    mqttclient.publish(config['PUB_TOPIC'].encode(), 'ERROR-{}-{}'.format(task_code, error_msg), retain = False, qos=1)

def send_output(task_code, output):
    global mqttclient
    mqttclient.publish(config['PUB_TOPIC'].encode(), 'OUTPUT-{}-{}'.format(task_code, output), retain = False, qos=1)
    
def send_bulk_output(task_code, output):
    global mqttclient, admin_debugger
    total_msg = len(output)
    mqttclient.publish(config['PUB_TOPIC'].encode(), 'BOUTPUT-{}-MSG_NUM-{}'.format(task_code, total_msg), retain = False, qos=1)
    for msg in output:
        mqttclient.publish(config['PUB_TOPIC'].encode(), 'BOUTPUT-{}-{}'.format(task_code, msg), retain = False, qos=1)
        admin_debugger.debug_msg('Sending boutput : {}'.format(msg))
    mqttclient.publish(config['PUB_TOPIC'].encode(), 'BOUTPUT-{}-DONE'.format(task_code), retain = False, qos=1)
    admin_debugger.debug_msg('Boutput : Sent Messages !!!')
    
def get_files(task, task_code, args, send_output = True, server=None):
    global admin_debugger
    admin_debugger.debug_msg('Getting files ......')
    if server == None:
        global download_server
    else:
        download_server = server
    admin_debugger.debug_msg('Download Server is {}'.format(download_server))
    file_list_hash = args[0].encode()
    file_list_url = 'http://{}/filelist.txt'.format(download_server)
    download('filelist.txt', file_list_url)
    admin_debugger.debug_msg('Downloaded filelist.txt !')
    gen_file_hash = gen_hash('filelist.txt')
    admin_debugger.debug_msg('Generated hash of filelist.txt as {}'.format(gen_file_hash))
    if gen_file_hash == file_list_hash:
        admin_debugger.debug_msg('Received proper file list, so continuing .....')
        files = []
        with open('filelist.txt') as filelist:
            for file in filelist:
                file = file.rstrip()
                if file == '' or file == ' ':
                    continue
                admin_debugger.debug_msg('Got {} as filename from filelist.txt'.format(file))
                files.append(file)
        final_output = []
        for file in files:
            hash_file = '{}.sha256'.format(file.split('.')[0])
            admin_debugger.debug_msg('File is {} and Hash  file is {}'.format(file, hash_file))
            hash_url = 'http://{}/{}'.format(download_server, hash_file)
            file_url = 'http://{}/{}'.format(download_server, file)
            admin_debugger.debug_msg('Hash file url is "{}" and the file url is "{}"'.format(hash_url, file_url))
            download(hash_file, hash_url)
            admin_debugger.debug_msg('Downloaded Hash File {}'.format(hash_file))
            download(file, file_url)
            admin_debugger.debug_msg('Downloaded File {}'.format(file))
            try:
                if verify_hash(file, hash_file):
                    final_output.append('Successfully Downloaded and verified the {} file.'.format(file))
                else:
                    final_output.append('Failed to verify the integrity of {} file, please check the file and its checksum.'.format(file))
            finally:
                os.remove(hash_file)
        os.remove('filelist.txt')
        if send_output:
            send_bulk_output(task_code, final_output)
    else:
        send_error('Invalid File Download List received.', task_code)
        admin_debugger.debug_msg('Sending Error.......')    

def update(task, task_code, args, server=None):
    global admin_debugger
    if file_exists('update.txt'):
        os.remove('update.txt')
        admin_debugger.debug_msg('Updater: Found existing update file so removing it......')
    admin_debugger.debug_msg('Updater: Getting files........')
    if server == None:
        get_files(task, task_code, args, send_output = False)
    else:
        get_files(task, task_code, args, send_output = False, server=server)
    admin_debugger.debug_msg('Updater: Got files !')
    admin_debugger.debug_msg('Updater: Reading update instructions .........')
    line_num = 1
    with open('update.txt') as updatefile:
        for line in updatefile:
            line = line.rstrip()
            if line == '' or line == ' ':
                admin_debugger.debug_msg('Updater: Skipping empty line')
                continue
            
            if line.startswith('--'):
                file = line.split(' ')[1]
                if file_exists(file):
                    os.remove(file)
                    admin_debugger.debug_msg('Updater: Removed {}'.format(file))
                else:
                    admin_debugger.debug_msg('Updater: {} does not exist so not removing.'.format(file))
            
            elif line.startswith('->'):    
                files = line.split(' ')[1:]
                if file_exists(files[0]):
                    os.rename(files[0], files[1])
                    admin_debugger.debug_msg('Updater: {} renamed to {}'.format(files[0], files[1]))
                else:
                    admin_debugger.debug_msg('Updater: {} file does not exist so not renaming.'.format(files[0]))
            
            elif line.startswith('<->'):
                admin_debugger.debug_msg('Updater: Got line as {}'.format(line))
                file, to_location = line.split(' ')[1:]
                admin_debugger.debug_msg('Updater: File to copy is {} and file is {}'.format(file, to_location))
                if file_exists(file):
                    move(file, to_location)
                    admin_debugger.debug_msg('Updater: {} copied to {}'.format(file, to_location))
                else:
                    admin_debugger.debug_msg('Updater: {} file does not exist so not copying.'.format(file))
                    
            elif line.startswith('++'):
                dir_name = line.split(' ')[1]
                os.mkdir(dir_name)
                admin_debugger.debug_msg('Updater: Created {} directory.'.format(dir_name))
                
            elif line.startswith('#'):
                continue
            
            else:
                send_error('Unknown instruction in update file in line number {}'.format(line_num), task_code)
                break
            line_num += 1
            
    os.remove('update.txt')        
    send_output(task_code, 'Updated successfully !!!')
    admin_debugger.debug_msg('Updater: Sent Output !')

def upload_file(filename, host=None, port=None):
    global admin_debugger
    
    admin_debugger.debug_msg('Started Upload File function !!')
    SEPARATOR = "--"
    BUFFER_SIZE = 2048
    if host == None:
        host = config['SERVER']
    if port == None:
        port = int(config['UPLOAD_PORT'])
    filesize = os.stat(filename)[6]
    s = socket.socket()
    admin_debugger.debug_msg("File Uploader: Connecting to {}:{}".format(host, port))
    s.connect((host, port))
    admin_debugger.debug_msg("File Uploader: Connected!")
    s.send("{}{}{}".format(filename, SEPARATOR, filesize).encode())
    with open(filename, "rb") as f:
        for _ in range(filesize):
            bytes_read = f.read(BUFFER_SIZE)
            if not bytes_read:
                break
            s.sendall(bytes_read)
    s.close()
    admin_debugger.debug_msg('File Uploader: Uploaded File successfully !!')
    
def task_handler(task, task_code):
    global mode
    global admin_debugger
    admin_debugger.debug_msg('Got task {} with the code {}'.format(task, task_code))
    args = ''
    try:
       task = list(task.split(' '))
       args = task[1:]
       task = task[0]
    except:
        task = task[0]
        pass
    
    if task == 'ping':
        msg = 'Ok'
        send_output(task_code, msg)
        
    elif task == 'info':
        msg = 'ESP32 Balcony Lights Controller V{} ; Current Mode : {}'.format(__version__, mode)
        send_output(task_code, msg)
        
    elif task == 'ls':
        if len(args) != 0:
            output = os.listdir(args[0])
        else:
            output = os.listdir()
        send_output(task_code, output)
        
    elif task == 'mkdir':
        os.mkdir(args[0])
        send_completion(task_code)
        
    elif task == 'rmdir':
        os.rmdir(args[0])
        send_completion(task_code)
    
    elif task == 'cd':
        if len(args) == 0:
            os.chdir('/')
        else:    
            os.chdir(args[0])
        output = os.getcwd()
        send_output(task_code, 'Current Working folder is {}'.format(output))
    
    elif task == 'pwd':
        output = os.getcwd()
        send_output(task_code, 'Current Working folder is {}'.format(output))
        
    elif task == 'rm':
        os.remove(args[0])
        send_completion(task_code)
        
    elif task == 'rename':
        os.rename(args[0], args[1])
        send_completion(task_code)
    
    elif task == 'cp':
        copy(args[0], args[1])
        send_completion(task_code)
        
    elif task == 'mv':
        move(args[0], args[1])
        send_completion(task_code)
    
    elif task == 'download_files':
        if len(args) == 2:
            get_files(task, task_code, args, server=args[1])
        else:
            get_files(task, task_code, args)
    
    elif task == 'update':
        if len(args) == 2:
            update(task, task_code, args, server=args[1])
        else:
            update(task, task_code, args)
    
    elif task == 'send':
        if len(args) == 1:
            upload_file(args[0])
            send_output(task_code, 'Transferred {} successfully !'.format(args[0]))
        elif len(args) == 2:
            upload_file(args[0], host=args[1])
            send_output(task_code, 'Transferred {} successfully !'.format(args[0]))
        elif len(args) == 3:
            upload_file(args[0], host=args[1], port=args[2])
            send_output(task_code, 'Transferred {} successfully !'.format(args[0]))
        else:
            send_error('Invalid Arguments Received, Please try again later', task_code)
    
    elif task == 'execute':
        execfile(args[0])
        send_output(task_code, 'Completed Executing {} file.'.format(args[0]))
        
    elif task == 'reboot':
        main_config = Config_File('main')
        main_config.change_config('send_ack_on_boot', 'yes')
        safe_shutdown()
        machine.reset()
    
    elif task == 'chmod':
        known_modes = ['normal', 'safe']
        if args[0] in known_modes:
            main_config = Config_File('main')
            main_config.change_config('mode', args[0])
            main_config.change_config('send_ack_on_boot', 'yes')
            safe_shutdown
            machine.reset()
        else:
            send_error('Unknown mode sent. Please check the mode name and try again', task_code)

    elif task == 'chconfig':
        config_file = Config_File(args[0])
        config_file.change_config(args[1], args[2])
        send_output(task_code, 'Done !')

    else:
        send_error('Received Unknown Task', task_code)