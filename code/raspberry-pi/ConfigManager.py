import os
from extras import file_exists

class Config_File:
    def __init__(self, name):
        self.name = name
        self.config_dict = dict()
        self.CONFIG_FILE = '/home/pi/SmartHome/config/{}.conf'.format(self.name)

    def fetch_config(self):
        try:
            config_file = open(self.CONFIG_FILE)
            for line in config_file:
                line=line.rstrip()
                if line == '' or line == ' ':
                    continue
                info = line.split('=')
                self.config_dict[info[0].strip()] = info[1].strip()
            return self.config_dict

        except Exception as e:
            print('Config Mgr FC: Encountered {} while obtaining configuration file.'.format(e))

    def change_config(self, config, to_replace):
        try: 
            try:
                config_file = open(self.CONFIG_FILE)
            except:
                raise Exception('Config Mgr CC: Unable to open config file.')
            
            old_config = config_file.readlines()
            config_file.close()
            new_config = []
            found_config = False
            for line in old_config:
                line = line.rstrip()
                if line == '' or line == ' ':
                    continue
                
                contents = list(line.split('='))
                if contents[0] == config:
                    contents[1] = to_replace
                    found_config = True
                new_line = str('='.join(contents))
                new_config.append(new_line)
            
            if not found_config:
                new_line = f'{config}={to_replace}'
                new_config.append(new_line)
                
            try:
                config_file = open(self.CONFIG_FILE, 'w')
            except:
                raise Exception('Config Mgr CC: Unable to open config file for updating.')
            for line in new_config:
                config_file.write(line)
                config_file.write('\n')
            
        except Exception as e:
            print('Config Mgr FC: Encountered {} while obtaining configuration file.'.format(e))
            
        finally:
            config_file.close()