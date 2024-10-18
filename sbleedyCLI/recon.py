import subprocess
import argparse
import re
import os
import logging
import time
import signal
from pathlib import Path

from .constants import LESCAN, HCITOOL_INFO, BLUING_BR_LMP, BLUING_BR_SDP, OUTPUT_DIRECTORY, REGEX_BT_VERSION, REGEX_BT_VERSION_HCITOOL, LOG_FILE, REGEX_BT_MANUFACTURER, VERSION_TABLE

COMMANDS = [HCITOOL_INFO, BLUING_BR_SDP, BLUING_BR_LMP]

logging.basicConfig(filename=LOG_FILE, level=logging.INFO)

class Recon():
    def run_command(self, target, command, filename):
        print("Running command -> {}".format(command))
        try:
            output = subprocess.check_output(command.format(target=target), shell=True).decode()
            f = open(filename, 'w')
            f.write(output)
            f.close()
        except subprocess.CalledProcessError as e:
            print("Error during running command")
            print(e.output)
        return False

    def run_recon(self, target):
        log_dir = OUTPUT_DIRECTORY.format(target=target) + "recon/"
        Path(log_dir).mkdir(exist_ok=True, parents=True)
        for command, filename in COMMANDS:
            self.run_command(target, command, log_dir + filename)
    
    def determine_bluetooth_version(self, target) -> float:
        file_path = Path(OUTPUT_DIRECTORY.format(target=target) + "recon/" + BLUING_BR_LMP[1])
        if file_path.is_file():
            with file_path.open('r') as f:
                text = f.read()
                mm = re.compile(REGEX_BT_VERSION)
                output = mm.search(text).group()
                return float(output.split(" ")[3])
        else:
            file_path = Path(OUTPUT_DIRECTORY.format(target=target) + "recon/" + HCITOOL_INFO[1])
            if file_path.is_file():
                with file_path.open('r') as f:
                    text = f.read()
                    mm = re.compile(REGEX_BT_VERSION_HCITOOL)
                    output = mm.search(text).group()
                    version = output.split('(')[1].split(')')[0]
                    try:
                        num_version = VERSION_TABLE[version]
                        return num_version
                    except Exception as e:
                        print("Error during retrieving a version")
        return None 

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-t','--target',required=False, type=str, help="target MAC address")
    parser.add_argument('-a','--availability',required=False, type=bool, help="check availability")
    args = parser.parse_args()

    if args.target:
        recon = Recon()
        v = recon.determine_bluetooth_version(args.target)
        print(v)
        recon.run_recon(args.target, COMMANDS)
    else:
        parser.print_help()



