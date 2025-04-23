import os
import paho.mqtt.client as mqtt
from collections import deque
import json
from kalman import KalmanFilter
from trilaterate import TrilaterationCalculator
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import threading

app = Flask(__name__)
CORS(app)
app.secret_key = os.urandom(24)
topic = "receiver"
calculator = None

receivers = None
mqttc = None

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
        data = message.payload.decode('utf-8')
        fl_data = float(data)
        filtered_rssi = receivers[message.topic]["filter"].step(fl_data)
        receivers[message.topic]["data"].append(filtered_rssi)
        # print("Received ", fl_data, "filtered: ", filtered_rssi)
        print("Received ", fl_data, "from topic: ", message.topic)
    except Exception as e:
        print(f"Error occured processing message: {e}")

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"Failed to connect: {reason_code}. loop_forever() will retry connection")
    else:
        # we should always subscribe from on_connect callback to be sure
        # our subscribed is persisted across reconnections.
        print(f"Connected to topic: {topic}")
        return client.subscribe("receiver")
    
def prepare_receivers(n):
    receivers = {}
    
    for i in range(1, n+1):
        topic_name = f"receiver/{i}"
        receivers[topic_name] = {"data": deque([-5.0],maxlen=10), "filter": KalmanFilter()}
        # Subscribe to each receiver topic individually
        # Assuming mqttc is globally accessible or passed appropriately
        # mqttc.subscribe(topic_name) # Consider where/how to best manage subscriptions
    return receivers

@app.route("/anchors", methods=['POST'])
def setup_anchors():
    global receivers, calculator
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No JSON data received"}), 400
            
        n_str = data.get("num")
        positions_data = data.get("positions")

        if not n_str or not positions_data:
             return jsonify({"success": False, "error": "Missing 'num' or 'positions' in JSON data"}), 400

        try:
            n = int(n_str)
            if not (3 <= n <= 5):
                 return jsonify({"success": False, "error": "Number of anchors must be between 3 and 5"}), 400
        except ValueError:
            return jsonify({"success": False, "error": "'num' must be an integer"}), 400

        if not isinstance(positions_data, list) or len(positions_data) != n:
            return jsonify({"success": False, "error": f"'positions' must be a list of {n} elements"}), 400

        positions = []
        for i, pos in enumerate(positions_data):
             if not isinstance(pos, list) or len(pos) != 2:
                 return jsonify({"success": False, "error": f"Position {i} must be a list of two numbers [x, y]"}), 400
             try:
                 x = float(pos[0])
                 y = float(pos[1])
                 positions.append(((x, y), -45))
             except (ValueError, TypeError):
                  return jsonify({"success": False, "error": f"Position {i} coordinates must be numbers"}), 400
        print("anchors = ", positions)
        
        # Prepare receivers and subscribe to their topics
        receivers = prepare_receivers(n)
        for topic_name in receivers.keys():
             # Assuming mqttc is accessible here. Consider managing MQTT client lifecycle better.
             # This might fail if mqttc is not connected yet or not global/passed correctly.
             print(f"Subscribing to {topic_name}")
             mqttc.subscribe(topic_name) 

        # Assuming the anchors in trilaterate need coordinates and maybe a default power value?
        # The TrilaterationCalculator expects anchors like [(x,y), power] - using a default power of 0 for now.
        # You might need to adjust this based on your actual TrilaterationCalculator needs.
        # Let's assume TrilaterationCalculator just needs positions for now based on the original code.
        # If it needs power, the format should be: [(x, y, power), ...]
        # Let's update TrilaterationCalculator init if needed. Assuming it only needs [(x, y),...] now.
        calculator = TrilaterationCalculator(positions, 1.7) # Path loss exponent hardcoded?
        
        print(f"Anchors set up: {n} anchors at {positions}")
        return jsonify({"success": True, "message": f"{n} anchors configured."}), 200
        
    except Exception as e:
        print(f"Error setting up anchors: {e}")
        # It's good practice to log the exception e
        return jsonify({"success": False, "error": "An internal server error occurred"}), 500
    

@app.route("/toggle_mode", methods=["POST"])
def send_to_node():
    global mqttc
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No JSON data provided"}), 400

        # Convert data to JSON string
        payload = json.dumps(data)

        # Publish to "node" topic
        mqttc.publish("mode", payload)
        return jsonify({"success": True, "message": "Data published to 'mode' topic."})
    except Exception as e:
        print(f"Error publishing to node: {e}")
        return jsonify({"success": False, "error": "Failed to publish message"}), 500

    
@app.route("/trilaterate")
def get_trilateration_data():
    global calculator, receivers
    
    if not calculator or not receivers:
        return jsonify({"position": None, "error": "Anchors not set up yet."}), 400
        
    try:
        latest_rssi_values = []
        # Ensure we get the latest reading for each configured receiver topic
        for topic_name in receivers.keys():
            if receivers[topic_name]["data"]:
                latest_rssi_values.append(receivers[topic_name]["data"][-1])
            else:
                # Handle case where a receiver hasn't received data yet
                return jsonify({"position": None, "error": f"No data received from {topic_name} yet."}), 400 
     
        if len(latest_rssi_values) != len(receivers):
             return jsonify({"position": None, "error": "Mismatch between expected anchors and received data count."}), 500

        pos = calculator.get_position(latest_rssi_values)
        
        
        # Ensure position is JSON serializable (e.g., list or tuple of numbers)
        if pos and len(pos) == 2:
            serializable_pos = [float(pos[0]), float(pos[1])] # Convert numpy floats if necessary
            return jsonify({"position": serializable_pos})
        else:
             return jsonify({"position": None, "error": "Failed to calculate position."}), 500
             
    except IndexError:
         # This happens if a deque is empty when accessed with [-1]
         return jsonify({"position": None, "error": "Waiting for initial data from all receivers."}), 400
    except Exception as e:
        print(f"Error during trilateration: {e}")
         # Log the exception e
        return jsonify({"position": None, "error": "An internal server error occurred during trilateration."}), 500
    


if __name__ == "__main__":
    # It's better to initialize MQTT client here and pass it or manage its scope carefully.
    # Global 'mqttc' used in setup_anchors might cause issues depending on execution flow.
    def setup_mqqt():
        global mqttc
        mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        mqttc.on_connect = on_connect
        mqttc.on_message = on_message
        mqttc.on_subscribe = on_subscribe
        mqttc.on_unsubscribe = on_unsubscribe

        mqttc.user_data_set([])
        mqttc.connect("localhost")
        print("Connected to broker")
        mqttc.loop_forever()
        
    mqtt_thread = threading.Thread(target=setup_mqqt)
    mqtt_thread.daemon = True
    mqtt_thread.start()
    app.run(host="0.0.0.0", port=5001)
    print("Server started")
    
    
    
    