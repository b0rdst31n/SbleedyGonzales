import subprocess
import argparse
import re
import time
import os
import signal
import sys
import asyncio
from bleak import BleakScanner

import sbleedyCLI.constants as const

def dos_checker(target):
    if not check_hci_device():
        print("No hci device found. DoS check needs one.")
        return const.RETURN_CODE_ERROR, "No hci device"
    try:
        down_times = 0
        for i in range(const.NUMBER_OF_DOS_TESTS):
            available = check_availability(target)
            if available:
                break
            down_times += 1

        if down_times > const.MAX_NUMBER_OF_DOS_TEST_TO_FAIL or down_times == const.NUMBER_OF_DOS_TESTS:
            return const.RETURN_CODE_VULNERABLE, str(down_times)
        
        return const.RETURN_CODE_NOT_VULNERABLE, str(down_times)
    except Exception as e:
        return const.RETURN_CODE_ERROR, str(e)

def check_hci_device():
    """Check if an HCI device is available."""
    try:
        process = subprocess.Popen(['hciconfig'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, _ = process.communicate()

        if b'hci' not in output:
            print("No HCI device found. Please connect a Bluetooth adapter.")
            return False
        return True
    except Exception as e:
        print(f"Error checking HCI device: {e}")
        return False

async def check_availability_async(target):
    if not check_hci_device():
        return False

    print("\nChecking device availability...")
    try:
        subprocess.run(['sudo', 'systemctl', 'restart', 'bluetooth'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to restart Bluetooth service: {e}")
    devices = await BleakScanner.discover(timeout=10.0)
    if target in [device.address for device in devices]:
        print("Device is available.")
        return True
    print("Device is not available.")
    return False

def check_availability(target):
    return asyncio.run(check_availability_async(target))

def check_target(self, target):
    cont = True
    while cont:
        for i in range(10):
            available = check_availability(target)
            if available:
                return True
        if not available:
            inp = self.connection_lost()