import paho.mqtt.client as mqtt
import json
import time

# MQTT Broker details
broker = "rule28.i4t.swin.edu.au"
port = 1883
username = "<103795587>"
password = username

# Define thresholds that will be compared with the received metrics
thresholds = {
    'cpu_usage': 80,
    'ram_usage': 80,
    'syn_packet_count': 700,
    'active_tcp_connections': 400
}

# callback func when connect successfully to the broker
def on_connect(client, userdata, flags, rc):
    print(f"Monitor app connected with result code {rc}")
    client.subscribe(f'{username}/bank_server/metrics/#')  # subscribe to all metric updates
    client.subscribe('public/#')  # subscribe to the public channel

def on_message(client, userdata, msg):
    try:
        if msg.payload:  # if msg payload is not empty
            try:
                # decode the payload as JSON
                data = json.loads(msg.payload.decode())
                print(f"\nReceived from topic: {msg.topic}: {data}")

                # Check for alerts or anomalies in the data
                # send alert and cmd to scale up server if cpu > 80%
                if 'cpu_usage' in data and data['cpu_usage'] > thresholds['cpu_usage']:
                    control_command = {'command': 'scale_up_servers'}
                    client.publish(f'{username}/bank_server/control/command', json.dumps(control_command))
                    print(f"Published command: {control_command} to {username}/bank_server/control/command")  # print the published cmd
                    client.publish(f'{username}/bank_server/alerts', json.dumps({'timestamp': time.time(), 'alert': 'CPU usage exceeded threshold'}))
                    print(f"Published alert: {{'timestamp': {data['timestamp']}, 'alert': 'CPU usage exceeded threshold'}} to {username}/bank_server/alerts")  # print the published alert
                
                # send alert and cmd to scale up server if ram > 80%
                if 'ram_usage' in data and data['ram_usage'] > thresholds['ram_usage']:
                    control_command = {'command': 'scale_up_servers'}
                    client.publish(f'{username}/bank_server/control/command', json.dumps(control_command))
                    print(f"Published command: {control_command} to {username}/bank_server/control/command")
                    client.publish(f'{username}/bank_server/alerts', json.dumps({'timestamp': time.time(), 'alert': 'RAM usage exceeded threshold'}))
                    print(f"Published alert: {{'timestamp': {data['timestamp']}, 'alert': 'RAM usage exceeded threshold'}} to {username}/bank_server/alerts")

                # send alert and cmd to enable rate limiting if syn packet count > 700
                if 'syn_packet_count' in data and data['syn_packet_count'] > thresholds['syn_packet_count']:
                    control_command = {'command': 'enable_rate_limiting'}
                    client.publish(f'{username}/bank_server/control/command', json.dumps(control_command))
                    print(f"Published command: {control_command} to {username}/bank_server/control/command")
                    client.publish(f'{username}/bank_server/alerts', json.dumps({'timestamp': time.time(), 'alert': 'SYN packet count exceeded threshold'}))
                    print(f"Published alert: {{'timestamp': {data['timestamp']}, 'alert': 'SYN packet count exceeded threshold'}} to {username}/bank_server/alerts")
                
                # send alert and cmd to enable rate limiting if active tcp conn count > 400
                if 'active_tcp_connections' in data and data['active_tcp_connections'] > thresholds['active_tcp_connections']:
                    control_command = {'command': 'enable_rate_limiting'}
                    client.publish(f'{username}/bank_server/control/command', json.dumps(control_command))
                    print(f"Published command: {control_command} to {username}/bank_server/control/command")
                    client.publish(f'{username}/bank_server/alerts', json.dumps({'timestamp': time.time(), 'alert': 'Active TCP connections exceeded threshold'}))
                    print(f"Published alert: {{'timestamp': {data['timestamp']}, 'alert': 'Active TCP connections exceeded threshold'}} to {username}/bank_server/alerts")

            except json.JSONDecodeError:
                # if the payload is not JSON format, print its raw msg directly 
                print(f"\nReceived from topic: {msg.topic}: {msg.payload.decode()}")
        else: # if payload is empty
            print("Received an empty message.")
    except Exception as e: # err hanlding
        print(f"An error occurred: {e}")

# setting up MQTT client
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.username_pw_set(username, password)
client.connect(broker, port)

client.loop_forever()
