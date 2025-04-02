import paho.mqtt.client as mqtt
from collections import deque
import json

topic = "receiver"

def on_subscribe(client, userdata, mid, reason_code_list, properties):
    # Since we subscribed only for a single channel, reason_code_list contains
    # a single entry
    if reason_code_list[0].is_failure:
        print(f"Broker rejected you subscription: {reason_code_list[0]}")
    else:
        print(f"Broker granted the following QoS: {reason_code_list[0].value}")

def on_unsubscribe(client, userdata, mid, reason_code_list, properties):
    # Be careful, the reason_code_list is only present in MQTTv5.
    # In MQTTv3 it will always be empty
    if len(reason_code_list) == 0 or not reason_code_list[0].is_failure:
        print("unsubscribe succeeded (if SUBACK is received in MQTTv3 it success)")
    else:
        print(f"Broker replied with failure: {reason_code_list[0]}")
    client.disconnect()

def on_message(client, userdata, message):
    try:
        dmessage = message.payload.decode('utf-8')
        data = json.loads(dmessage)
        
        filtered_rssi = kalman_filter(receivers[message.topic]["filter"], data["rssi"])
        receivers[message.topic]["data"].append(filtered_rssi)
    except Exception as e:
        print(f"Error occured processing message: {e}")
    print(message.payload.decode('utf-8'))

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"Failed to connect: {reason_code}. loop_forever() will retry connection")
    else:
        # we should always subscribe from on_connect callback to be sure
        # our subscribed is persisted across reconnections.
        print(f"Connected to topic: {topic}")
        return client.subscribe("receiver")

def kalman_filter():
    pass
def create_filter():
    return None      
def prepare_receivers(n):
    receivers = {}
    
    for i in range(n):
        receivers[f"receiver/{i}"] = {"data": deque(maxlen=10), "filter": create_filter()}
    return receivers
import argparse



parser = argparse.ArgumentParser(description="WNA Localization")

#Number of receivers
parser.add_argument("-n","--num", type=int, required=True, help="Number of receivers")
args = parser.parse_args()

receivers = prepare_receivers(args.num)

mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect
mqttc.on_message = on_message
mqttc.on_subscribe = on_subscribe
mqttc.on_unsubscribe = on_unsubscribe

mqttc.user_data_set([])
mqttc.connect("localhost")
mqttc.loop_forever()
print(f"Received the following message: {mqttc.user_data_get()}")