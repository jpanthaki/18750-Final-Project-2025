import network

# Create a WLAN object in STA mode (Station mode)
wlan = network.WLAN(network.STA_IF)

# Activate the WLAN interface
wlan.active(True)

# Get the MAC address
mac_address = wlan.config('mac')
mac_str = ':'.join(['{:02x}'.format(b) for b in mac_address])
print("MAC Address:", mac_str)
