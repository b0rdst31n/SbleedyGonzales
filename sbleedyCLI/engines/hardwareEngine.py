import yaml
import os
import stat
import subprocess
import logging
import re
import serial.tools.list_ports

from sbleedyCLI.constants import HARDWARE_DIRECTORY, FLASH_NRF_FILE
from sbleedyCLI.models.hardware import Hardware

class HardwareEngine:
    def __init__(self):
        self.hardware = None

    def get_all_hardware_profiles(self, force_reload=False):
        if self.hardware is None or force_reload:
            onlyfiles = [os.path.join(HARDWARE_DIRECTORY, f) for f in os.listdir(HARDWARE_DIRECTORY) if os.path.isfile(os.path.join(HARDWARE_DIRECTORY, f))]
            
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
    
    def flash_hardware(self, hw_name):
        available_hardware = self.get_all_hardware_profiles()
        if not any(av.name == hw_name for av in available_hardware):
            print(f"\nHardware {hw_name} not known. Valid names: {', '.join(av.name for av in available_hardware)}")
            return

        hardware_verified = self.verify_setup_multiple_hardware(available_hardware)
        if not hardware_verified[hw_name]:
            print(f"\nHardware {hw_name} not available.")
            return

        for hw in self.hardware:
            if hw.name == hw_name:
                if not hw.firmware:
                    print(f"\nNo firmware available for {hw_name}.")
                    return
                else:
                    selected_hardware = hw
                    break
        
        print(f"\nAvailable firmware for {hw_name}:")
        for idx, fw in enumerate(selected_hardware.firmware):
            print(f"[{idx+1}] {list(fw.keys())[0]}")
        
        try:
            choice = int(input(f"Select the index of the firmware to flash: "))
            if 1 <= choice <= len(selected_hardware.firmware):
                selected_firmware = selected_hardware.firmware[choice-1]
                firmware_name = list(selected_firmware.keys())[0]
                print(f"Flashing {hw_name} with firmware {firmware_name} on {selected_hardware.port}...\n")
                script_path = FLASH_NRF_FILE
                if not os.access(script_path, os.X_OK):
                    os.chmod(script_path, os.stat(script_path).st_mode | stat.S_IEXEC)
                subprocess.run([script_path, selected_hardware.port, selected_firmware[firmware_name]], check=True)
                return
            else:
                print(f"Invalid choice.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")
        except subprocess.CalledProcessError as e:
            print(f"Error during flashing: {e}")

    def check_hardware(self):
        available_hardware = self.get_all_hardware_profiles()
        hardware_verified = self.verify_setup_multiple_hardware(available_hardware)
        print("\nHardware availability:")
        for hardware in available_hardware:
            print(f"{hardware.name} - {'Available' if hardware_verified[hardware.name] else 'Not Available'}")

    @staticmethod
    def check_setup_hci(hardware) -> bool:
        print("\nChecking for hci devices...")
        try:
            output = subprocess.check_output("hciconfig", shell=True, stderr=subprocess.PIPE).decode().split('\n')[:-1]
            matches = re.findall(r"(hci\d+):.*?Bus: (\w+)", " ".join(output))
            if not matches:
                print("No hci devices found.")
                logging.info('HardwareEngine -> check_setup_hci -> No HCI Bluetooth Adapter found')
                return False
            for idx, match in enumerate(matches):
                print(f"[{idx}] Interface: {match[0]}, Bus: {match[1]}")

            if len(matches) == 1:
                hardware.port = matches[0][0]
            else:
                while True:
                    try:
                        hci_choice = int(input(f"\nMultiple HCI devices found. Choose the index of the device to use (0-{len(matches) - 1}): "))
                        if 0 <= hci_choice < len(matches):
                            hardware.port = matches[hci_choice][0]
                            break
                        else:
                            print(f"Invalid choice. Please enter a number between 0 and {len(matches) - 1}.")
                    except ValueError:
                        print("Invalid input. Please enter a valid number.")
            
            try:
                print(f"Restarting {hardware.port}...")
                subprocess.run(['sudo', 'hciconfig', hardware.port, 'down'], check=True)
                subprocess.run(['sudo', 'hciconfig', hardware.port, 'up'], check=True)
                print(f"{hardware.port} restarted successfully.")
                return True
            except subprocess.CalledProcessError as e:
                print(f"Error restarting {hardware.port}: {e}")
                return False
        except subprocess.CalledProcessError as e:
            logging.info("HardwareEngine -> check_setup_hci -> Error during checking hci setup")
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

