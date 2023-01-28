from extras import file_exists
from debugger import debugger

class Config_File:
    def __init__(self, name):
        self.name = name
        self.config_dict = dict()
        self.CONFIG_FILE = '/config/{}.conf'.format(self.name)
        self.my_debugger = debugger(False, mode=1)
        
    def fetch_config(self):
        try: 
            try:
                config_file = open(self.CONFIG_FILE)
                self.my_debugger.debug_msg('Config Mgr FC : Opened {} Config file : {}'.format(self.name, self.CONFIG_FILE))
            except:
                self.my_debugger.debug_msg('Config Mgr FC: Check whether proper configuration file exists.')
                raise Exception('Config Mgr FC: Unable to open config file.')
             
            line_num = 1

            for line in config_file:
                line=line.rstrip()
                self.my_debugger.debug_msg('Config Mgr FC : Got line number {} as {} '.format(line_num, line))
                if line == '' or line == ' ':
                    continue
                info = line.split('=')
                self.my_debugger.debug_msg('Config Mgr FC : Info List : {}'.format(info))
                self.config_dict[info[0].strip()] = info[1].strip()
                line_num += 1
            self.my_debugger.debug_msg('Config Mgr FC : Got Config Dictionary : {}'.format(self.config_dict))
            return self.config_dict
        
        except Exception as e:
            self.my_debugger.debug_msg('Config Mgr FC: Encountered {} while obtaining configuration file.'.format(e))
            
        finally:
            config_file.close()
            
    def change_config(self, config, to_replace):
        try: 
            try:
                config_file = open(self.CONFIG_FILE)
                self.my_debugger.debug_msg('Config Mgr CC : Opened {} Config file : {}'.format(self.name, self.CONFIG_FILE))
            except:
                self.my_debugger.debug_msg('Config Mgr CC: Check whether proper configuration file exists.')
                raise Exception('Config Mgr CC: Unable to open config file.')
            
            old_config = config_file.readlines()
            self.my_debugger.debug_msg('Config Mgr CC : Got Old Configuration as {} '.format(old_config))
            config_file.close()
            new_config = []
            found_config = False
            for line in old_config:
                line = line.rstrip()
                if line == '' or line == ' ':
                    continue
                
                contents = list(line.split('='))
                self.my_debugger.debug_msg('Config Mgr CC : Got contents of the old config file as {}'.format(contents))
                if contents[0] == config:
                    contents[1] = to_replace
                    self.my_debugger.debug_msg('Config Mgr CC : current line starts with {} so replacing its option with {}'.format(contents[0], contents[1]))
                    found_config = True
                new_line = str('='.join(contents))
                self.my_debugger.debug_msg('Config Mgr CC : Got New line as {}'.format(new_line))
                new_config.append(new_line)
            
            if not found_config:
                new_line = '{}={}'.format(config, to_replace)
                new_config.append(new_line)
                
            self.my_debugger.debug_msg('Config Mgr CC : Got New Configuration as {} '.format(new_config))
            try:
                config_file = open(self.CONFIG_FILE, 'w')
                self.my_debugger.debug_msg('Config Mgr CC : Opened {} Config file : {} to update.'.format(self.name, self.CONFIG_FILE))
            except:
                self.my_debugger.debug_msg('Config Mgr CC: Check whether proper configuration file exists.')
                raise Exception('Config Mgr CC: Unable to open config file for updating.')
            for line in new_config:
                config_file.write(line)
                config_file.write('\n')
                
            self.my_debugger.debug_msg('Config Mgr CC : Completed Updating the file')
            
        except Exception as e:
            self.my_debugger.debug_msg('Config Mgr FC: Encountered {} while obtaining configuration file.'.format(e))
            
        finally:
            config_file.close()