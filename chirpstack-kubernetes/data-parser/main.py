#!/usr/bin/env python3

import paho.mqtt.client as mqtt
import json
import base64
import argparse


from parser.smart_water import smart_water
from parser.people_counter import people_counter
from parser.wind import wind


devEUI_file = 'conf/devEUI.json'
with open(devEUI_file) as f:
  devEUI_dict = json.load(f)

location_file = 'conf/location.json'
with open(location_file) as f:
  location_dict = json.load(f)

def get_sensor_type(devEUI):
    sensor_type = None
    for key, value in devEUI_dict.items():
        if devEUI in value:
            sensor_type = key
            break
    return sensor_type

def get_sensor_location(devEUI):
    sensor_location = None
    for key, value in location_dict.items():
        if key == devEUI:
            sensor_location = value
            break
    return sensor_location

def data_parser(payload_dict):
    mqtt_message = {}

    devEUI = payload_dict["devEUI"]

    sensor_location = get_sensor_location(devEUI)
    sensor_type = get_sensor_type(devEUI)
    # print(sensor_type)

    #TODO: define the topic
    if sensor_location != None: 
        topic = sensor_type + "/" + sensor_location
    else:
        print("The sensor is not included yet")
        return None, None
    
    mqtt_message['SensorID'] = devEUI
    
    if 'data' not in payload_dict.keys():
        print('No data in sensor data')
        return None, None 

    data = payload_dict['data']
    data_hex = base64.b64decode(data).hex()

    if sensor_type == 'smart_water':
        protocol_file = './parser/smart_water.csv'
        mqtt_dict = smart_water(data_hex, protocol_file)
    elif sensor_type == 'smart_water_lon':
        protocol_file = './parser/smart_water_lon.csv'
        mqtt_dict = smart_water(data_hex, protocol_file)  
    elif sensor_type == 'people_counter':
        mqtt_dict = people_counter(data_hex)
    elif sensor_type == 'wind':
        mqtt_dict = wind(data_hex)

    mqtt_message['SensorData'] = mqtt_dict


    return topic, mqtt_message

# This is the Subscriber
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("application/#")

def on_message(client, userdata, msg):
    payload = msg.payload.decode() # string
    payload_dict = json.loads(payload) # dict
    print(payload_dict)

    topic, mqtt_message = data_parser(payload_dict)

    if topic is not None and mqtt_message is not None: 
        mqtt_message_string = json.dumps(mqtt_message, ensure_ascii=False)
    
        print(topic, mqtt_message_string)
        client.publish(topic, mqtt_message_string)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    # Required positional argument
    parser.add_argument('mqtt_server', type=str,
                        help='the ip address of mqtt server')
    
    args = parser.parse_args()
    mqtt_server = args.mqtt_server

    client = mqtt.Client()
    client.connect(mqtt_server)
    
    client.on_connect = on_connect
    client.on_message = on_message
    
    client.loop_forever()