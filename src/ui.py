import tkinter as tk
from tkinter import ttk
import paho.mqtt.client as mqtt
import json
from datetime import datetime

# MQTT Broker details
broker = "rule28.i4t.swin.edu.au"
port = 1883
username = "<103795587>"
password = username

# custom tikinter widget class to create scrollable text areas
class ScrollableText(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        # text displaying actual data
        self.text = tk.Text(self, wrap=tk.WORD, height=20, width=60)
        # vertical scrollbar 
        self.scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.text.yview)
        self.text.configure(yscrollcommand=self.scrollbar.set) # link the scrollbar to the text's vertical scroll
        
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True) # text (i.e., actual data) will expand all of the left
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y) # scrollbar will take the vertical space in the right side
    
    # append msg to the text area with timestamp
    def append(self, message):
        self.text.insert(tk.END, f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')} - {message}\n")
        self.text.see(tk.END) # auto scroll text to the bottom
    
    # clear all the content from the text area - for Clear All Logs button
    def clear(self):
        self.text.delete(1.0, tk.END)

# main UI window
class UI:
    def __init__(self, root):
        self.root = root
        self.root.title("Bank Server DoS Monitoring System")
        self.root.geometry("800x600") # window size
        
        # create notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # create tabs for different metrics and status info
        self.cpu_tab = ttk.Frame(self.notebook)
        self.ram_tab = ttk.Frame(self.notebook)
        self.network_tab = ttk.Frame(self.notebook)
        self.alerts_tab = ttk.Frame(self.notebook)
        self.status_tab = ttk.Frame(self.notebook)
        self.public_tab = ttk.Frame(self.notebook)
        
        # add tabs to notebook
        self.notebook.add(self.cpu_tab, text="CPU Metrics")
        self.notebook.add(self.ram_tab, text="RAM Metrics")
        self.notebook.add(self.network_tab, text="Network Metrics")
        self.notebook.add(self.alerts_tab, text="Alerts")
        self.notebook.add(self.status_tab, text="Command Status")
        self.notebook.add(self.public_tab, text="Public Messages")
        
        # create labels i.e., topic name for each tab
        ttk.Label(self.cpu_tab, text=f"Topic: {username}/bank_server/metrics/cpu").pack(pady=5)
        ttk.Label(self.ram_tab, text=f"Topic: {username}/bank_server/metrics/ram").pack(pady=5)
        ttk.Label(self.network_tab, text=f"Topic: {username}/bank_server/metrics/network").pack(pady=5)
        ttk.Label(self.alerts_tab, text=f"Topic: {username}/bank_server/alerts").pack(pady=5)
        ttk.Label(self.status_tab, text=f"Topic: {username}/bank_server/status/#").pack(pady=5)
        ttk.Label(self.public_tab, text="Topic: public/#").pack(pady=5)
        
        # create scrollable text areas for each tab
        self.cpu_text = ScrollableText(self.cpu_tab)
        self.ram_text = ScrollableText(self.ram_tab)
        self.network_text = ScrollableText(self.network_tab)
        self.alerts_text = ScrollableText(self.alerts_tab)
        self.status_text = ScrollableText(self.status_tab)
        self.public_text = ScrollableText(self.public_tab)
        
        # Pack text areas so they appear in the GUI
        self.cpu_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.ram_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.network_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.alerts_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.status_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.public_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # create control panel that has buttons at the bottom of window
        self.control_panel = ttk.Frame(root)
        self.control_panel.pack(fill=tk.X, padx=5, pady=5) # control panel will take all horizontal space
        
        # Add buttons for actions
        # click on this button will send enable_rate_limiting to command topic
        ttk.Button(self.control_panel, text="Enable Rate Limiting", command=lambda: self.send_command('enable_rate_limiting')).pack(side=tk.LEFT, padx=5) 
        ttk.Button(self.control_panel, text="Scale Up Servers", command=lambda: self.send_command('scale_up_servers')).pack(side=tk.LEFT, padx=5)
        # click on this button will call clear_logs()
        ttk.Button(self.control_panel, text="Clear All Logs", command=self.clear_logs).pack(side=tk.RIGHT, padx=5) 
        
        # Setup MQTT client
        self.setup_mqtt()

    # setting up mqtt method
    def setup_mqtt(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.username_pw_set(username, password)
        self.client.connect(broker, port)
        self.client.loop_start()

    # callback function when connecting to the broker
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0: # if connect successfully
            self.alerts_text.append("Successfully connected to MQTT broker")
            # subscribe to topics
            client.subscribe(f'{username}/bank_server/metrics/#') # for all metrics cpu, ram, network
            client.subscribe(f'{username}/bank_server/status/#') # for command status e.g., failed, success
            client.subscribe(f'{username}/bank_server/alerts') # for alerts topic
            client.subscribe('public/#') # for all public subtopics
        else: # err handling
            self.show_error(f"Failed to connect to MQTT broker with code {rc}")

    # callback func when receive msg
    def on_message(self, client, userdata, msg):
        try:
            if msg.payload: # if msg is not empty
                data = json.loads(msg.payload.decode())
                
                # update UI by calling update_ui method after 0ms i.e., constantly update ui to reflect new messages
                self.root.after(0, self.update_ui, msg.topic, data)
        except json.JSONDecodeError: # if incoming msg is not json format
            self.root.after(0, self.alerts_text.append, 
                           f"Received message on topic '{msg.topic}': {msg.payload.decode()}")
        except Exception as e: # general err handling
            self.root.after(0, self.alerts_text.append, 
                           f"Error processing message: {str(e)}")

    # update UI with data based on the MQTT topic
    def update_ui(self, topic, data):
        message = f"Received: {json.dumps(data, indent=2)}"
        
        # check which tab should receive the data based on the topic
        if topic.endswith('/metrics/cpu'):
            self.cpu_text.append(message)
        elif topic.endswith('/metrics/ram'):
            self.ram_text.append(message)
        elif topic.endswith('/metrics/network'):
            self.network_text.append(message)
        elif topic.endswith('/alerts'):
            self.alerts_text.append(message)
        elif topic.startswith(f'{username}/bank_server/status'):
            self.status_text.append(f"Topic '{topic}': {message}")  # append to status_text for /status/# topics
        elif topic.startswith('public'):
            self.public_text.append(f"Topic '{topic}': {message}") # for public msg

    # send control cmd to the /command topic
    def send_command(self, command):
        try:
            command = {'command': command}
            self.client.publish(f'{username}/bank_server/control/command', json.dumps(command))
            self.alerts_text.append(f"Sent command: {command}")
        except Exception as e: # err handling
            self.show_error(f"Failed to send command: {str(e)}")

    def clear_logs(self): # for Clear All Logs button that clear all text in all tabs
        self.cpu_text.clear()
        self.ram_text.clear()
        self.network_text.clear()
        self.alerts_text.clear()
        self.public_text.clear()
        self.status_text.clear()

    def show_error(self, message): # display err msg in Alerts tab
        self.alerts_text.append(f"ERROR: {message}")

if __name__ == "__main__":
    root = tk.Tk() # create main window of tkinter
    app = UI(root) # initialise the ui
    root.mainloop() # start ui loop
