from MqttManager import MqttClient
from ConfigManager import Config_File
import Administration as admin

def main():
    global admin
    
    config_file = Config_File('main')
    config = config_file.fetch_config()
    
    if config['change_admin_file'] == 'yes':      
      print('Changing admin file.')
      import uos
      from extras import file_exists
      from time import sleep
      if file_exists('Administration_old.py'):
          uos.remove('Administration_old.py')
      uos.rename('Administration.py', 'Administration_old.py')
      uos.rename('Administration_new.py', 'Administration.py')
      try:
          mqttclient = MqttClient()
          import Administration as admin
          admin.init(mqttclient)
          mqttclient.create_mqtt_client()
          admin.send_output('change_admin_file', 'Changed New Administration File Successfully !')
          config_file.change_config('change_admin_file', 'no')
          print('Successfully changed the Administration file')
          sleep(10)
          admin.restart()
      except:
          print('Administration file does not seem to be proper so reverting back to old Administration program.')
          uos.rename('Administration.py', 'Administration_new.py')
          uos.rename('Administration_old.py', 'Administration.py')
          import Administration as admin
          admin.init(mqttclient)
          admin.send_error('Administration file does not seem to be proper so reverted back to old Administration program.', 'change_admin_file')
          config_file.change_config('change_admin_file', 'no')
          sleep(10)
          admin.restart()
    
    if config['send_ack_on_boot'] == 'yes':
        mqttclient = MqttClient()
        admin.init(mqttclient)
        mqttclient.create_mqtt_client()
        admin.send_completion('boot')
        config_file.change_config('send_ack_on_boot', 'no')
        print('Sent Acknwoledgement at boot')

    if config['mode']=='normal':
        execfile('normal.py')
    else:
        execfile('safe.py')
            
main()