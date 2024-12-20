import argparse
import os
import logging
import subprocess
import signal
import psutil
import time
import sys

from sbleedyCLI.report import report_vulnerable, report_not_vulnerable, report_error
from sbleedyCLI.constants import LOG_FILE

HCITOOL_SCAN = "sudo -S hcitool scan"
HCITOOL_INFO = "sudo -S hcitool info {target}"
BLUETOOTHCTL_PAIR = "bluetoothctl pair {target}"
BLUETOOTHCTL_REMOVE = "bluetoothctl remove {target}"
BLUETOOTHCTL_CONNECT = "bluetoothctl connect {target}"
BT_AGENT_NINO = "bt-agent -c NoInputNoOutput"


INSTRUCTIONS = """
1. Have your target device in discoverable and pairable mode. Always keep it that way
2. Once the promt to connect appears - press yes
3. If device is vulnerable it would pair and connect.
"""


def check_nino(target):
    try:
        # Changing BT Agent to NoInputNoOutput
        process = subprocess.Popen(BT_AGENT_NINO, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        time.sleep(1)

        try:
            subprocess.check_output(BLUETOOTHCTL_REMOVE.format(target=target), shell=True)
        except subprocess.CalledProcessError as e:
            logging.info("nino_check.py -> Error removing the device: {}".format(e.output))
            #return

        pid = None
        # Running a scan to find the target device
        try:
            command = subprocess.Popen(HCITOOL_SCAN, stdout=subprocess.PIPE, shell=True, preexec_fn=os.setsid)         # for some reason doesn't accept tokenized exploit_command (leads to a bug)
            pid = command.pid
            command.wait(timeout=30)
            output = command.communicate()[0].decode()
            logging.info("nino_check.py -> output from HCITOOL_SCAN : " + str(output))
        except subprocess.TimeoutExpired as e:
            for child in psutil.Process(pid).children(recursive=True):
                child.kill()
            os.killpg(os.getpgid(command.pid), signal.SIGTERM)
            time.sleep(1)

        if output is not None and target in output:
            time.sleep(1)

            # Required to get information about the device, otherwise won't connect
            try:
                subprocess.check_output(HCITOOL_INFO.format(target=target), shell=True)
            except subprocess.CalledProcessError as e:
                logging.info("nino_check.py -> Error getting information about the device: {}".format(e.output))

            # Pair with the target device
            try:
                subprocess.check_output(BLUETOOTHCTL_PAIR.format(target=target), shell=True)
            except subprocess.CalledProcessError as e:
                logging.info("nino_check.py -> Error pairing with the device: {}".format(e.output))
                print(str(e))
                return
            
            # Connect to the paired device
            try:
                output = subprocess.check_output(BLUETOOTHCTL_CONNECT.format(target=target), shell=True).decode()
                if "Connection successful" in output:
                    report_vulnerable("Vulnerable to NiNo attack as allows NiNo devices to connect (Unauthenticated keys)")
                    logging.info("nino_check.py -> removing a device from saved")
                    try:
                        subprocess.check_output(BLUETOOTHCTL_REMOVE.format(target=target), shell=True)
                    except subprocess.CalledProcessError as e:
                        logging.info("nino_check.py -> Error removing the device: {}".format(e.output))
                else:
                    report_not_vulnerable("Not vulnerable to NiNo attack as doesn't allow to connect")
            except subprocess.CalledProcessError as e:
                logging.info("nino_check.py -> Error connecting to the device: {}".format(e.output))
                report_error("Couldn't connect to a device, error while connecting")
        else:
            report_not_vulnerable("Target not found by HCITOOL SCAN. Does it support BR/EDR?")
    except Exception as e:
        logging.info("nino_check.py -> Error: {}".format(str(e)))
        report_error("nino_check.py -> strange error: {}".format(str(e)))
    finally:
        if 'process' in locals():
            process.terminate()
            try:
                process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        logging.info("nino_check.py -> Finished")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--target', required=False, type=str, help="target MAC address")
    args = parser.parse_args()

    logging.basicConfig(filename=LOG_FILE, level=logging.INFO)

    if args.target:
        print(INSTRUCTIONS, flush=True)
        check_nino(args.target)
    else:
        parser.print_help()
