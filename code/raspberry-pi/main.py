from LightManager import Light

light1 = Light('light1')
light2 = Light('light2')

while True:
    light1.handle_time_threshold()
    light2.handle_time_threshold()