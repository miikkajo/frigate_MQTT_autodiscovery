import os
import yaml
import json
import paho.mqtt.client as mqtt
import time

FRIGATE_VARS = {k: v for k, v in os.environ.items() if k.startswith('FRIGATE_')}
CONFIG_FILE = os.environ.get('CONFIG_FILE', './config.yml')

if CONFIG_FILE.endswith(".yml"):
    with open(CONFIG_FILE) as f:
        CONFIG = yaml.safe_load(f)
elif CONFIG_FILE.endswith(".json"):
    with open(CONFIG_FILE) as f:
        CONFIG = json.load(f)

MQTT_HOST = CONFIG['mqtt']['host']
MQTT_PORT = CONFIG.get('mqtt', {}).get('port', 1883)
MQTT_TOPIC_PREFIX = CONFIG.get('mqtt', {}).get('topic_prefix', 'frigate')
MQTT_USER = CONFIG.get('mqtt', {}).get('user')
MQTT_PASS = CONFIG.get('mqtt', {}).get('password')
if not MQTT_PASS is None:
    MQTT_PASS = MQTT_PASS.format(**FRIGATE_VARS)
MQTT_CLIENT_ID = CONFIG.get('mqtt', {}).get('client_id', 'frigate_autodiscovery')

def main():
    # connect to mqtt and setup last will
    def on_connect(client, userdata, flags, rc):
        print("On connect called")
        if rc != 0:
            if rc == 3:
                print ("MQTT Server unavailable")
            elif rc == 4:
                print ("MQTT Bad username or password")
            elif rc == 5:
                print ("MQTT Not authorized")
            else:
                print ("Unable to connect to MQTT: Connection refused. Error code: " + str(rc))
    
    def on_message(client,userdata,msg):
        if msg.payload:
            client.publish(topic=msg.topic,payload='',retain=True)
        print (f"mesg: {msg.retain}")

    client = mqtt.Client(client_id=MQTT_CLIENT_ID)
    client.on_connect = on_connect
    client.on_message = on_message
    client.will_set(MQTT_TOPIC_PREFIX+'/available', payload='offline', qos=1, retain=True)
    if not MQTT_USER is None:
        client.username_pw_set(MQTT_USER, password=MQTT_PASS)

    client.connect(MQTT_HOST, MQTT_PORT, 60)

    # Remove old configurations
    client.subscribe([('homeassistant/camera/frigate/+/config',0),('homeassistant/binary_sensor/frigate/+/config',0)])
    client.loop_start()
    time.sleep(2)

    # Send MQTT autodiscovery configurations
    for camera in CONFIG.get('cameras').keys():
        objects = []
        objects += CONFIG.get('objects',{}).get('track',[])
        objects += CONFIG.get('cameras',{}).get(camera,{}).get('objects',{}).get('track',())
        for object in CONFIG.get('cameras',{}).get(camera,{}).get('objects',{}).get('track',()):

            # configure binary sensors
            config_topic = f"homeassistant/binary_sensor/{MQTT_TOPIC_PREFIX}/{camera}_{object}/config"
            message = f'{{"name":"{camera}_{object}_detected","state_topic": "{MQTT_TOPIC_PREFIX}/{camera}/{object}","device_class":"motion","availability_topic":"{MQTT_TOPIC_PREFIX}/available"}}'
            print(config_topic)
            print(message)
            ret = client.publish(topic=config_topic,payload=message,retain=True)
            
            # configure camera entities for snapshots
            config_topic = f"homeassistant/camera/{MQTT_TOPIC_PREFIX}/{camera}_{object}_snapshot/config"
            message = f'{{"name":"{camera}_{object}_snapshot","topic": "{MQTT_TOPIC_PREFIX}/{camera}/{object}/snapshot","availability_topic":"{MQTT_TOPIC_PREFIX}/available"}}'
            print(config_topic)
            print(message)
            ret = client.publish(topic=config_topic,payload=message,retain=True)

    client.disconnect()
    client.loop_stop()

if __name__ == "__main__":
    main()
