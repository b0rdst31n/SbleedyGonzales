#!/bin/bash

mac=$1 

# turn on bluetooth in case it's off
rfkill unblock bluetooth

bluetoothctl -- power on
bluetoothctl -- discoverable on
bluetoothctl -- pairable on
bluetoothctl -- agent NoInputNoOutput    # if you delete this part it will pair as normal, one would need to accept pairing only on the device (test)
bluetoothctl -- default-agent
bluetoothctl -- remove $mac
sudo hcitool info $mac
bluetoothctl -- trust $mac
bluetoothctl -- connect $mac
bluetoothctl -- remove $mac
bluetoothctl -- disconnect