#!/bin/bash

if ! which nrfutil > /dev/null; 
then
  echo "nrfutil not found, installing now..."
  sudo pip install nrfutil 
fi

echo "ATTENTION: if you're working within a VM like VirtualBox, the nRF will be disconnected during the flashing process (at about 83%). You will have to select it in the VM USB settings again."
echo "The nRF has to be in boot mode. Hold the Reset button for 2 seconds until the red LED flashes. Press Enter to continue..."
read REPLY

FIRMWARE_DIR="$(dirname "$0")/../hardware/firmware"
nrfutil dfu usb-serial -p "$1" -pkg "$FIRMWARE_DIR/$2"