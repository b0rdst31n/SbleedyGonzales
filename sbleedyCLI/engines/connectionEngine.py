import subprocess
import argparse
import re
import time
import os
import signal
import sys
import asyncio
from bleak import BleakScanner
from subprocess import STDOUT, check_output

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

async def check_availability_le(target):
    subprocess.run(["sudo", "rfkill", "unblock", "bluetooth"], check=True)
    subprocess.run(["sudo", "systemctl", "restart", "bluetooth"], check=True)
    subprocess.run(["sudo", "hciconfig", "hci0", "reset"], check=True)
    
    device = await BleakScanner.find_device_by_address(target, cb=dict(use_bdaddr=True))
    if device:
        return True
    return False

def check_availability_bredr(target):
    try:
        output = check_output(["sudo", "l2ping", "-c", "5", target], stderr=STDOUT)
        if "bytes" in output.decode("utf-8"):
            return True
        else:
            return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

def check_availability(target):
    if not check_hci_device():
        return
    if asyncio.run(check_availability_le(target)):
        return True
    else:
        print("[i] The device can't be found by Bleak (LE Scanner). Trying L2Ping now...")
        return check_availability_bredr(target)

def check_target(self, target):
    cont = True
    while cont:
        for i in range(10):
            available = check_availability(target)
            if available:
                return True
        if not available:
            inp = self.connection_lost()

def check_connectivity_classic(target):
    try:
        proc_out = subprocess.check_output(const.COMMAND_CONNECT.format(target=target), shell=True, stderr=subprocess.STDOUT)
        print("Successful check - Device connectivity is checked")
    except subprocess.CalledProcessError as e:
        #print("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))
        text = e.output.decode()
        try:
            mm = re.compile(const.REGEX_COMMAND_CONNECT.format(target=target))
            output = mm.search(text).group()
            print("Partical check - Device connectivity is checked")
            return True
        except AttributeError as e:
            print("Device is offline")
        return False
    #print("Connectability- True")
    return True