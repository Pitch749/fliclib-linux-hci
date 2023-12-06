#!/usr/bin/env python3

import threading
import fliclib
import	os
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()                   

client = fliclib.FlicClient("localhost")
client_mqtt = mqtt.Client()
mqtt_user, mqtt_password = (os.environ.get('MQTT_USER'), os.environ.get('MQTT_PASSWORD'))
# Callback running on connection
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("Photo")


# Callback running on new message
def on_message(client, userdata, msg):
    # We print each message received
    print(msg.topic+" "+str(msg.payload))

def clic_action(channel, click_type, was_queued, time_diff):
	if(click_type == fliclib.ClickType.ButtonDoubleClick): 
		print(f"{channel.bd_addr} {click_type} {was_queued}, {time_diff}")
		
	if(click_type == fliclib.ClickType.ButtonSingleClick): 
		print(f"{channel.bd_addr} {click_type} {was_queued}, {time_diff}")
		res = client_mqtt.publish('Agent/commands', 'cmd=allOn')
		res = client_mqtt.publish('Agent/commands', 'cmd=arm')
	if(click_type == fliclib.ClickType.ButtonHold): 
		print(f"{channel.bd_addr} {click_type} {was_queued}, {time_diff}")
		res = client_mqtt.publish('Agent/commands', 'cmd=disarm')
		res = client_mqtt.publish('Agent/commands', 'cmd=allOff')

def bat_listener(listener, battery_percentage, timestamp):
	print(f" addr: {listener.bd_addr}, batterie %: {battery_percentage}, timestamps: {timestamp}")

def got_button(bd_addr):
	cc = fliclib.ButtonConnectionChannel(bd_addr)
	cc.on_button_single_or_double_click_or_hold = clic_action
	cc.on_connection_status_changed = \
		lambda channel, connection_status, disconnect_reason: \
			print(channel.bd_addr + " " + str(connection_status) + (" " + str(disconnect_reason) if connection_status == fliclib.ConnectionStatus.Disconnected else ""))
	client.add_connection_channel(cc)
	batlist = fliclib.BatteryStatusListener(bd_addr)
	batlist.on_battery_status = bat_listener
	client.add_battery_status_listener(batlist)

def got_info(items):
	#print(items)
	for bd_addr in items["bd_addr_of_verified_buttons"]:
		got_button(bd_addr)

class T(threading.Thread):
	def run(self):
		client_mqtt.on_connect = on_connect
		client_mqtt.on_message = on_message
		client_mqtt.username_pw_set(mqtt_user, mqtt_password)
		client_mqtt.connect("rb2.home", 1883, 60)
		client_mqtt.loop_forever()

T().start()


client.get_info(got_info)
client.on_new_verified_button = got_button
client.handle_events()
