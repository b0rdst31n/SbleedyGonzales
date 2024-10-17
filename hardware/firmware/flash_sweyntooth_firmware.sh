#!/bin/bash

if ! which nrfutil > /dev/null; 
then
  echo "nrfutil not found, installing now..."
  sudo pip install nrfutil 
else
  echo "nrfutil found!"
fi

echo "The nRF has to be in boot mode. Hold the Reset button for 2 seconds until the red LED flashes. Press Enter to continue..."
read REPLY

echo "$1"
sudo nrfutil dfu usb-serial -p "$1" -pkg sweyntooth_nRF52840_firmware.zip