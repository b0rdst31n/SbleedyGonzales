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
    print("\nRunning a DoS check...")
    if not check_hci_device():
        print("No hci device found. DoS check needs one.")
        return const.RETURN_CODE_ERROR, "No hci device found"
    try:
        down_times = 0
        for i in range(const.NUMBER_OF_DOS_TESTS):
            available = check_availability(target)
            if available:
                return const.RETURN_CODE_NOT_VULNERABLE, f"Device not down"
            down_times += 1

        if down_times > const.MAX_NUMBER_OF_DOS_TEST_TO_FAIL or down_times == const.NUMBER_OF_DOS_TESTS:
            return const.RETURN_CODE_VULNERABLE, f"Device down (tried {down_times} times)"
        
        return const.RETURN_CODE_NOT_VULNERABLE, f"Device not down (tried {down_times} times)"
    except Exception as e:
        return const.RETURN_CODE_ERROR, str(e)

def check_hci_device():
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

    subprocess.run(["sudo", "rfkill", "unblock", "bluetooth"], check=True)
    subprocess.run(["sudo", "systemctl", "restart", "bluetooth"], check=True)
    subprocess.run(["sudo", "hciconfig", "hci0", "reset"], check=True)
    
    device = await BleakScanner.find_device_by_address(target, cb=dict(use_bdaddr=True)) #TODO: add discover for BR/EDR, e.g. with L2Ping
    if device:
        return True
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