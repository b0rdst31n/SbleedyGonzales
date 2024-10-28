import subprocess
import argparse
import re
import os
import logging
import time
import signal
from pathlib import Path
import asyncio
from bleak import BleakScanner

import sbleedyCLI.constants as const
COMMANDS = [const.HCITOOL_INFO]

class Recon():
    def enable_logging(self):
        logging.basicConfig(filename=const.LOG_FILE, level=logging.INFO)

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
        self.enable_logging()
        log_dir = const.RECON_DIRECTORY.format(target=target)
        Path(log_dir).mkdir(exist_ok=True, parents=True)
        for command, filename in COMMANDS:
            self.run_command(target, command, log_dir + filename)
    
    def determine_bluetooth_version(self, target) -> float:
        self.enable_logging()
        file_path = Path(const.RECON_DIRECTORY.format(target=target) + const.HCITOOL_INFO[1])
        if file_path.is_file():
            with file_path.open('r') as f:
                text = f.read()
                mm = re.compile(const.REGEX_BT_VERSION_HCITOOL)
                output = mm.search(text).group()
                return float(output.split(" ")[3])
        else:
            print("Please note: when running the recon script once for the target, the version and profile checks will be much faster.")
            try:
                result = subprocess.run(const.HCITOOL_INFO[0].format(target=target), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if result.returncode != 0:
                    print(f"[!] BT Version Check - Error: {result.stderr.strip()}")
                    return None
                mm = re.compile(const.REGEX_BT_VERSION_HCITOOL)
                output = mm.search(result.stdout).group()
                return float(output.split(" ")[3])
            except Exception as e:
                print(f"[!] BT Version Check - Error: {str(e)}")
                return None 

    def check_bt_profile(self, target) -> str: #TODO: check profile and version without Bluing
        file_path = Path(const.RECON_DIRECTORY.format(target=target) + const.HCITOOL_INFO[1])
        if file_path.is_file():
            with file_path.open('r') as f:
                output = f.read()
        else:       
            try:
                result = subprocess.run(const.HCITOOL_INFO[0].format(target=target), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if result.returncode != 0:
                    print(f"[!] BT Profile Check - Error: {result.stderr.strip()}")
                    return None
                output = result.stdout
            except Exception as e:
                print(f"[!] BT Profile Check - Error: {str(e)}")
                return None 

        br_edr_supported = None
        le_supported = None
        simultaneous_le_br_edr = None

        if "BR/EDR Not Supported:" in output:
            if "BR/EDR Not Supported: False" in output:
                br_edr_supported = True
            elif "BR/EDR Not Supported: True" in output:
                br_edr_supported = False

        if "LE Supported (Controller):" in output:
            if "LE Supported (Controller): True" in output:
                le_supported = True
            elif "LE Supported (Controller): False" in output:
                le_supported = False

        if "Simultaneous LE and BR/EDR to Same Device Capable (Controller):" in output:
            if "Simultaneous LE and BR/EDR to Same Device Capable (Controller): True" in output:
                simultaneous_le_br_edr = True
            elif "Simultaneous LE and BR/EDR to Same Device Capable (Controller): False" in output:
                simultaneous_le_br_edr = False

        if br_edr_supported is True and le_supported is True and simultaneous_le_br_edr is True:
            return "BR/EDR + LE (Dual)"
        elif br_edr_supported is True:
            return "BR/EDR (Classic)"
        elif le_supported is True:
            return "LE (Low Energy)"
        else:
            return "Unknown or unsupported profile"
