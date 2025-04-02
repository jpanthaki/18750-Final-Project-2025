import network
import time

# Specify your Wi-Fi network name (SSID)
ssid = 'CMU-DEVICE'  # Replace with the actual SSID of your network

# Set up the Wi-Fi interface in station mode (STA_IF)
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

# Attempt to connect to Wi-Fi (no password needed)
wlan.connect(ssid)

# Wait for the connection to establish
print("Connecting to Wi-Fi...")
while not wlan.isconnected():
    time.sleep(1)  # Wait for the connection to establish

# Once connected, print the IP address assigned by the router
print('Connection successful!')
print('IP address:', wlan.ifconfig()[0])

