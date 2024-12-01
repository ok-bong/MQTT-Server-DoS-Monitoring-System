import paho.mqtt.client as mqtt
import json
import time
import random

# MQTT Broker details
broker = "rule28.i4t.swin.edu.au"
port = 1883
username = "<103795587>"
password = username

def on_connect(client, userdata, flags, rc):
    print(f"Controller connected with result code {rc}")
    client.subscribe(f'{username}/bank_server/control/command')  # subscribe to control commands
    client.subscribe('public/#')  # subscribe to all public messages

def on_message(client, userdata, msg):
    # print all public messages with their sub-topic
    if msg.topic.startswith('public'):
        print(f"Public message received on topic '{msg.topic}': {msg.payload.decode()}")
        return

    # if it's msg from /control/command topic, process control commands
    try:
        command = json.loads(msg.payload.decode())
    except json.JSONDecodeError:
        # if the payload is not JSON format, print it directly
        print(f"\nReceived from topic: {msg.topic}: {msg.payload.decode()}")
        return # return (not proceed with sending the actual cmd) since we are expecting JSON format coming from the auth sensors

    print(f"Received control command: {command}")

    # if 'command' not exists in the data
    if 'command' not in command:
        print(f"Error: Received command without 'command' field: {command}")
        return

    if command['command'] == 'scale_up_servers':
        scale_up_servers()
    elif command['command'] == 'enable_rate_limiting':
        enable_rate_limiting()
    else: # if unknown cmd
        print(f"Warning: Unknown command received: {command['command']}")

def scale_up_servers():
    print("Scaling up servers...")
    # publish status of the commands for logging purposes
    response = {
        'command': 'scale_up_servers',
        'status': random.choices(['success', 'failed'], weights=[80, 20], k=1)[0], # success has 80% chance, failed has 20% chance
        'timestamp': time.time()
    }
    client.publish(f'{username}/bank_server/status/scaling', json.dumps(response))

def enable_rate_limiting():
    print("Enabling rate limiting...")
    # publish status of the commands for logging purposes
    response = {
        'command': 'enable_rate_limiting',
        'status': random.choices(['success', 'failed'], weights=[80, 20], k=1)[0], # success has 80% chance, failed has 20% chance
        'timestamp': time.time()
    }
    client.publish(f'{username}/bank_server/status/rate_limiting', json.dumps(response))

# setting up MQTT client
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.username_pw_set(username, password)
client.connect(broker, port)

client.loop_forever()