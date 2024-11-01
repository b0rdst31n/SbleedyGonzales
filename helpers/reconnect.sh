#!/bin/bash

# Check if MAC address is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <MAC_ADDRESS>"
    exit 1
fi

MAC_ADDRESS=$1

# Ensure Bluetooth is unblocked and active
rfkill unblock bluetooth
sudo service bluetooth restart
sudo hciconfig hci0 up

# Start bluetoothctl process to configure and connect
bluetoothctl -- power on
bluetoothctl -- discoverable on
bluetoothctl -- pairable on
bluetoothctl -- agent NoInputNoOutput
bluetoothctl -- default-agent
bluetoothctl -- remove $MAC_ADDRESS
bluetoothctl --timeout 5 scan on

bluetoothctl -- trust $MAC_ADDRESS
bluetoothctl -- connect $MAC_ADDRESS

bluetoothctl -- disconnect $MAC_ADDRESS
bluetoothctl -- remove $MAC_ADDRESS
