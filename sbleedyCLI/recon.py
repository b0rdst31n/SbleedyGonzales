import subprocess
import argparse
import re
import os
import logging
import time
import signal
from pathlib import Path

import sbleedyCLI.constants as const
COMMANDS = [const.HCITOOL_INFO, const.BLUING_BR_SDP, const.BLUING_BR_LMP]

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
        file_path = Path(const.RECON_DIRECTORY.format(target=target) + const.BLUING_BR_LMP[1])
        if file_path.is_file():
            with file_path.open('r') as f:
                text = f.read()
                mm = re.compile(const.REGEX_BT_VERSION)
                output = mm.search(text).group()
                return float(output.split(" ")[3])
        else:
            file_path = Path(const.RECON_DIRECTORY.format(target=target) + const.HCITOOL_INFO[1])
            if file_path.is_file():
                with file_path.open('r') as f:
                    text = f.read()
                    mm = re.compile(const.REGEX_BT_VERSION_HCITOOL)
                    output = mm.search(text).group()
                    version = output.split('(')[1].split(')')[0]
                    try:
                        num_version = const.VERSION_TABLE[version]
                        return num_version
                    except Exception as e:
                        print("Error during retrieving a version")
        return None 



