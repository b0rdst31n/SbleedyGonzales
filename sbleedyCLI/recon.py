import subprocess
import re
import logging
import time
from pathlib import Path

from sbleedyCLI.engines.connectionEngine import check_connectivity_classic
import sbleedyCLI.constants as const
COMMANDS = [const.HCITOOL_INFO, const.BLUING_BR_SDP, const.BLUING_BR_LMP, const.BLUING_LE_SCAN]

class Recon():
    def enable_logging(self):
        logging.basicConfig(filename=const.LOG_FILE, level=logging.INFO)

    def run_command(self, target, command, filename):
        print(f"Running command -> {command.format(target=target)}")
        try:
            output = subprocess.check_output(command.format(target=target), shell=True).decode()
            f = open(filename, 'w')
            if "bluing_le.log" in filename:
                device_sections = output.split("Addr:")
                for section in device_sections:
                    if target in section:
                        output = f"Addr:{section}"
                        f.write(output)
                        f.close()
                        break
            else:
                f.write(output)
                f.close()
        except subprocess.CalledProcessError:
            print(f"Error during running command {command}")
        return False

    def run_recon(self, target):
        self.enable_logging()
        log_dir = const.RECON_DIRECTORY.format(target=target)
        Path(log_dir).mkdir(exist_ok=True, parents=True)
        for command, filename in COMMANDS:
            self.run_command(target, command, log_dir + filename)
        
        f = open(const.DEVICE_INFO.format(target=target), 'w')
        bt_version = self.determine_bluetooth_version(target)
        f.write(f"Bluetooth Version: {bt_version}\n")
        print(f"\nBluetooth Version: {bt_version}")
        bt_profile = self.determine_bluetooth_profile(target)
        f.write(f"Bluetooth Profile: {bt_profile}\n")
        print(f"Bluetooth Profile: {bt_profile}")
        bt_manufacturer = self.determine_manufacturer(target)
        f.write(f"Manufacturer {bt_manufacturer}\n")
        print(f"Manufacturer {bt_manufacturer}")
        f.close()
    
    def determine_bluetooth_version(self, target) -> str:
        self.enable_logging()
        file_path = Path(const.RECON_DIRECTORY.format(target=target) + const.BLUING_BR_LMP[1])
        if file_path.is_file():
            with file_path.open('r') as f:
                text = f.read()
                REGEX_BT_VERSION = r"Bluetooth Core Specification [0-9]{1}(\.){0,1}[0-9]{0,1}\ "
                mm = re.compile(REGEX_BT_VERSION)
                output = mm.search(text).group()
                return output.split(" ")[3]
        else:
            return "Unknown"

    def determine_bluetooth_profile(self, target) -> str: 
        br_edr_supported = None
        le_supported = None
        simultaneous_le_br_edr = None
        
        file_path = Path(const.RECON_DIRECTORY.format(target=target) + const.BLUING_BR_LMP[1])
        if file_path.is_file():
            with file_path.open('r') as f:
                output = f.read()
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
        else:       
            file_path = Path(const.RECON_DIRECTORY.format(target=target) + const.BLUING_LE_SCAN[1])
            if file_path.is_file():
                with file_path.open('r') as f:
                    output = f.read()
                    if "BR/EDR Not Supported" in output:
                        br_edr_supported = False
                        le_supported = True
                        simultaneous_le_br_edr = False
                    elif "Simultaneous LE + BR/EDR to Same Device Capable" in output:
                        br_edr_supported = True
                        le_supported = True
                        simultaneous_le_br_edr = True      
            
        if br_edr_supported is True and le_supported is True and simultaneous_le_br_edr is True:
            return "BR/EDR + LE (Dual)"
        elif br_edr_supported is True:
            return "BR/EDR (Classic)"
        elif le_supported is True:
            return "LE (Low Energy)"
        else:
            return "Unknown"
    
    def determine_manufacturer(self, target) -> str:
        file_path = Path(const.RECON_DIRECTORY.format(target=target) + const.BLUING_BR_LMP[1])
        if file_path.is_file():
            with file_path.open('r') as f:
                text = f.read()
                pattern = r"Manufacturer name: .*\n"
                mm = re.compile(pattern)
                output = mm.search(text).group()
                return "(Bluetooth): " + output.split(":")[1].strip()
        else:
            file_path = Path(const.RECON_DIRECTORY.format(target=target) + const.BLUING_LE_SCAN[1])
            if file_path.is_file():
                with file_path.open('r') as f:
                    output = f.read()
                    pattern = r"Company ID: 0x[0-9A-Fa-f]+ \(([^)]+)\)"
                    match = re.search(pattern, output)
                    return "(Device): " + match.group(1) if match else ": Unknown"
        return ": Unknown"

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

def get_device_info(target):
    file_path = Path(const.DEVICE_INFO.format(target=target))
    if file_path.is_file():
        with file_path.open('r') as f:
            version = None
            profile = None
            manufacturer = None
            output = f.read()
            version_pattern = r"Bluetooth Version: ([\d.]+|Unknown)"
            profile_pattern = r"Bluetooth Profile: (.+)"
            manufacturer_pattern = r"Manufacturer \(.*?\): (.+)"
            version_match = re.search(version_pattern, output)
            if version_match:
                version_str = version_match.group(1)
                if version_str != "Unknown":
                    version = float(version_str)
            profile_match = re.search(profile_pattern, output)
            if profile_match:
                profile_str = profile_match.group(1)
                if profile_str != "Unknown":
                    profile = re.sub(r'\s*\(.*?\)', '', profile_str).strip()
            manufacturer_match = re.search(manufacturer_pattern, output)
            if manufacturer_match:
                manufacturer_str = manufacturer_match.group(1)
                if manufacturer_str != "Unknown":
                    manufacturer = manufacturer_str
            return version, profile, manufacturer
    else:  
        print("Please run the recon script once for the target to get the bluetooth version, profile and manufacturer.")  
        return None, None, None