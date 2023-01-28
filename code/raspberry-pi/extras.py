import random
import string
import hashlib

def debug(mode):
    global enable_debug_msg
    if mode == True:
        enable_debug_msg = True
    else:
        enable_debug_msg = False

def debug_msg(msg):
    global enable_debug_msg
    if enable_debug_msg == True:
        print(msg)

def file_exists(file):
    try:
        open(file)
        return True
    except:
        return False

def randstr(length=5):
    letters = string.ascii_letters
    return ''.join(random.sample(letters, length))

def gen_hash(file_name):
    BLOCKSIZE = 1024
    hasher = hashlib.sha256()
    try:
        with open(file_name, 'rb') as afile:
            buf = afile.read(BLOCKSIZE)
            while len(buf) > 0:
                hasher.update(buf)
                buf = afile.read(BLOCKSIZE)
        gen_hash = hasher.hexdigest()
        print('Generated Hash : {}'.format(gen_hash))
        return gen_hash.encode()
    except Exception as e:
        print(f'Encountered Exception: {e}')
        return None
    
def gen_hash_file(file_name):
    try:
        gen_hash_val = gen_hash(file_name)
        file = list(file_name.split('.'))
        with open('{}.sha256'.format(file[0]), 'wb') as hash_file:
            hash_file.write(gen_hash_val)
        print('Generated Hash File Successfully !')
    except:
        print('Encountered Error while Generating Hash file.')
        
def verify_hash(file_name, hash_file):
    with open(hash_file, 'rb') as hfile:
        given_hash = hfile.read()
    gen_hash_val = gen_hash(file_name)
    print('Given Hash : {}'.format(given_hash.decode()))
    if gen_hash_val == given_hash:
        return True
    else:
        return False