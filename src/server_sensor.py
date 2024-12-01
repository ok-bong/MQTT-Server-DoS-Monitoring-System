import paho.mqtt.client as mqtt
import json
import time
import random  # for simulating metric values

# MQTT Broker details
broker = "rule28.i4t.swin.edu.au"
port = 1883
username = "<103795587>"
password = username

def get_system_metrics():
    return {
        'timestamp': time.time(),  # current timestamp
        'cpu_usage': round(random.uniform(20, 95), 2),  # simulated CPU usage between 20-95%
        'ram_usage': round(random.uniform(40, 90), 2),   # simulated RAM usage between 40-90%
        'active_tcp_connections': random.randint(50, 500),  # simulated active TCP connections
        'syn_packet_count': random.randint(0, 1000)  # simulated SYN packet count
    }

def on_connect(client, userdata, flags, rc):
    print(f"Sensor connected with result code {rc}")

# setting up MQTT client
client = mqtt.Client()
client.on_connect = on_connect
client.username_pw_set(username, password)
client.connect(broker, port)

client.loop_start() # non-blocking loop of mqtt client

# infinite loop to randomise data and publish data to metrics topic every 5 seconds
while True:
    metrics = get_system_metrics()
    
    # prepare metrics data
    cpu_message = json.dumps({'cpu_usage': metrics['cpu_usage'], 'timestamp': metrics['timestamp']})
    ram_message = json.dumps({'ram_usage': metrics['ram_usage'], 'timestamp': metrics['timestamp']})
    network_message = json.dumps({
        'active_tcp_connections': metrics['active_tcp_connections'],
        'syn_packet_count': metrics['syn_packet_count'],
        'timestamp': metrics['timestamp']
    })

    # publish metrics to each relevant topic
    client.publish(f'{username}/bank_server/metrics/cpu', cpu_message)
    print(f"\nPublished CPU metrics: {cpu_message}")

    client.publish(f'{username}/bank_server/metrics/ram', ram_message)
    print(f"Published RAM metrics: {ram_message}")

    client.publish(f'{username}/bank_server/metrics/network', network_message)
    print(f"Published Network metrics: {network_message}\n")

    time.sleep(5)  # every 5 seconds
