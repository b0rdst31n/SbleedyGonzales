import subprocess
import re
import logging
import time
from pathlib import Path

from sbleedyCLI.engines.connectionEngine import check_connectivity_classic
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
            print("Please note: when running the recon script once for the target, the version and profile checks will be much faster.")
            try:
                result = subprocess.run(const.BLUING_BR_LMP[0].format(target=target), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if result.returncode == 0:
                    mm = re.compile(const.REGEX_BT_VERSION)
                    output = mm.search(result.stdout).group()
                    return float(output.split(" ")[3])
                print("[!] BT Version Check - Error")
                return None
            except Exception:
                print("[!] BT Version Check - Error")
                return None 

    def check_bt_profile(self, target) -> str: 
        file_path = Path(const.RECON_DIRECTORY.format(target=target) + const.BLUING_BR_LMP[1])
        if file_path.is_file():
            with file_path.open('r') as f:
                output = f.read()
        else:       
            try:
                result = subprocess.run(const.BLUING_BR_LMP[0].format(target=target), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if result.returncode != 0:
                    print("[!] BT Profile Check - Error")
                    return None
                output = result.stdout
            except Exception:
                print("[!] BT Profile Check - Error")
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

    def start_hcidump(self):
        logging.info("Starting hcidump -X...")
        process = subprocess.Popen(["hcidump", "-X"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return process

    def stop_hcidump(self, process):
        logging.info("Stopping hcidump -X...")
        process.send_signal(subprocess.signal.SIGINT)
        output, _ = process.communicate()
        logging.info("hcidump -> " + str(output.decode()))
        logging.info("hcidump -X stopped.")
        return output

    def get_hcidump(self, target):
        hcidump_process = self.start_hcidump()
        try:
            time.sleep(2)
            check_connectivity_classic(target)
        finally:
            return self.stop_hcidump(hcidump_process).decode().split("\n")
    
    def get_capabilities(self, target):
        output = self.get_hcidump(target)
        # Our capability is set as NoInputNoOutput so the other one should be a target device capability
        capabilities = set()
        numb_of_capabilities = 0 
        for line in output:
            if line.strip().startswith("Capability:"):
                capabilities.add(line.strip().split(" ")[1])
                numb_of_capabilities += 1
        logging.info("recon.py -> found the following capabilities " + str(capabilities))
        if len(capabilities) == 0:
            logging.info("recon.py -> most likely legacy pairing")
            return None
        elif numb_of_capabilities == 1:
            logging.info("recon.py -> got only 1 capability " + str(capabilities))
            return capabilities.pop()
        capabilities.remove('NoInputNoOutput')
        if len(capabilities) == 0:
            return "NoInputNoOutput"
        else:
            return capabilities.pop()