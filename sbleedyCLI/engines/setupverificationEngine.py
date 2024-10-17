import subprocess
import logging
import re
import serial.tools.list_ports

class SetupVerifierEngine():
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
            logging.info('SetupVerifierEngine -> check_setup_hci -> No HCI Bluetooth Adapter found')
        except subprocess.CalledProcessError as e:
            logging.info("SetupVerifierEngine -> check_setup_hci -> Error during checking hci setup")
        print("No hci devices found.")
        return False
    
    @staticmethod
    def check_setup_nRF(hardware) -> bool:
        print("\nChecking for nRF...")
        ports = list(serial.tools.list_ports.comports())
        if not ports:
            print("No serial ports found.")
            logging.info("SetupVerifierEngine -> check_setup_nRF -> No available port found")
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
                    logging.info("SetupVerifierEngine -> check_setup_nRF -> No available port found")
                    return True
            except ValueError:
                print("Invalid input.")
                return False

# Add your hardware verification function
hardware_verifier = {
    "hci": SetupVerifierEngine.check_setup_hci,
    "nRF52840": SetupVerifierEngine.check_setup_nRF
}
