import yaml
from os import listdir
from os.path import isfile, join
import subprocess
import logging
import re
import serial.tools.list_ports

from sbleedyCLI.constants import HARDWARE_DIRECTORY
from sbleedyCLI.models.hardware import Hardware

class HardwareEngine:
    def __init__(self):
        self.hardware_dir = HARDWARE_DIRECTORY
        self.hardware = None

    def get_all_hardware_profiles(self, force_reload=False):
        if self.hardware is None or force_reload:
            onlyfiles = [join(self.hardware_dir, f) for f in listdir(self.hardware_dir) if isfile(join(self.hardware_dir, f))]
            
            hardware_profiles = []
            for filename in onlyfiles:
                hardware_profiles.append(self.read_hardware(filename))    
            self.hardware = hardware_profiles
        return self.hardware

    def read_hardware(self, filename):
        f = open(filename, 'r')
        details = yaml.safe_load(f)
        f.close()
        return Hardware(details)

    def get_hardware_port(self, hardware_name):
        for hw in self.hardware:
            if hw.name == hardware_name:
                return hw.port
    
    def verify_setup(self, hardware) -> bool:
        if hardware.needs_setup_verification:
            try:
                verify_func = hardware_verifier[hardware.name]
                return verify_func(hardware)
            except Exception as e:
                logging.info("Hardware - {} is not registered".format(hardware.name))
                return False
        return True

    def verify_setup_multiple_hardware(self, multiple_hardware) -> dict:
        hardware_verification = {}
        for hardware in multiple_hardware:
            hardware_verification[hardware.name] = self.verify_setup(hardware)
        return hardware_verification

    @staticmethod
    def check_setup_hci(hardware) -> bool:
        print("\nChecking for hci devices...")
        try:
            output = subprocess.check_output("hciconfig", shell=True, stderr=subprocess.PIPE).decode().split('\n')[:-1]
            match = re.search(r"(hci\d+):.*?Bus: (\w+)", " ".join(output))
            if match:
                hci_number = match.group(1)
                bus_type = match.group(2)
                print(f"{hci_number}: {bus_type}")
                hardware.port = hci_number
                
                try:
                    print(f"Restarting {hci_number}...")
                    subprocess.run(['sudo', 'hciconfig', hci_number, 'down'], check=True)
                    subprocess.run(['sudo', 'hciconfig', hci_number, 'up'], check=True)
                    print(f"{hci_number} restarted successfully.")
                except subprocess.CalledProcessError as e:
                    print(f"Error restarting {hci_number}: {e}")

                return True
            logging.info('HardwareEngine -> check_setup_hci -> No HCI Bluetooth Adapter found')
        except subprocess.CalledProcessError as e:
            logging.info("HardwareEngine -> check_setup_hci -> Error during checking hci setup")
        print("No hci devices found.")
        return False
    
    @staticmethod
    def check_setup_nRF(hardware) -> bool:
        print("\nChecking for nRF...")
        ports = list(serial.tools.list_ports.comports())
        if not ports:
            print("No serial ports found.")
            logging.info("HardwareEngine -> check_setup_nRF -> No available port found")
            return False
        for port in ports:
            if "nRF" in port.description:
                print(f"Automatically selected port: {port.device} with {port.description}")
                hardware.port = port.device
                return True
        print("Available serial ports, please select the one for the nRF:")
        for i, port in enumerate(ports):
            print(f"{i + 1}: {port.device} with {port.description}")
            try:
                choice = int(input("Select a port by number: "))
                if 1 <= choice <= len(ports):
                    port = ports[choice - 1]
                    print(f"Selected port: {port.device}")
                    hardware.port = port.device
                    logging.info("HardwareEngine -> check_setup_nRF -> No available port found")
                    return True
            except ValueError:
                print("Invalid input.")
                return False

# Add your hardware verification function
hardware_verifier = {
    "hci": HardwareEngine.check_setup_hci,
    "nRF52840": HardwareEngine.check_setup_nRF
}

