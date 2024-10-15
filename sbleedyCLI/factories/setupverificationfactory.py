import subprocess
import logging

HCI_CHECK_SETUP = 'hciconfig'

class SetupVerifier():
    def verify_setup(self, hardware) -> bool:
        if hardware.needs_setup_verification:
            try:
                return hardware_verifier[hardware.name]()
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
    def check_setup_hci() -> bool:
        try:
            output = subprocess.check_output(HCI_CHECK_SETUP, shell=True, stderr=subprocess.PIPE).decode().split('\n')[:-1]
            if output:
                print('HCI Bluetooth Adapter found')
                return True
            logging.info('SetupVerfier -> check_setup_hci -> No HCI Bluetooth Adapter found')
        except subprocess.CalledProcessError as e:
            logging.info("SetupVerfier -> check_setup_hci -> Error during checking hci setup")
        return False

# Add your hardware verification function
hardware_verifier = {
    "hci": SetupVerifier.check_setup_hci
}
