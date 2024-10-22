import subprocess
import argparse
import re
import time
import os
import signal
import sys

import sbleedyCLI.constants as const

def dos_checker(target):
    if not check_hci_device():
        print("No hci device found. DoS check needs one.")
        return const.RETURN_CODE_ERROR, "No hci device"
    try:
        try:
            cont = True
            down_times = 0
            not_pairable = 0
            while cont:
                for i in range(const.NUMBER_OF_DOS_TESTS):
                    available = check_availability(target)
                    if available:
                        break
                    else:
                        down_times += 1
                break
        except Exception as e:
            return const.RETURN_CODE_ERROR, str(e)
        
        if down_times > const.MAX_NUMBER_OF_DOS_TEST_TO_FAIL:
            if not_pairable > const.MAX_NUMBER_OF_DOS_TEST_TO_FAIL:
                return const.RETURN_CODE_VULNERABLE, str(down_times)
            elif down_times == const.NUMBER_OF_DOS_TESTS: 
                return const.RETURN_CODE_VULNERABLE, str(down_times)
        else:
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

def check_availability(target):
    if not check_hci_device():
        return False

    print("Checking device availability...")
    process = subprocess.Popen(const.LESCAN.split(), stdout=subprocess.PIPE)
    time.sleep(10)
    os.kill(process.pid, signal.SIGINT)
    output = process.communicate()[0].decode("utf-8")
    if target in output:
        print("Device is available.")
        return True
    print("Device is not available.")
    return False

def check_target(self, target):
    cont = True
    while cont:
        for i in range(10):
            available = check_availability(target)
            if available:
                return True
        if not available:
            inp = self.connection_lost()