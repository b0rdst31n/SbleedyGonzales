import os
import pkg_resources
import sys
import argparse
import logging
import signal
from pathlib import Path
from rich.table import Table
from rich.console import Console

from .constants import TOOL_DIRECTORY, LOG_FILE
from .engines.exploitEngine import ExploitEngine
from .engines.hardwareEngine import HardwareEngine
from .engines.setupverificationEngine import SetupVerifierEngine
from .recon import Recon

class Sbleedy():
    def __init__(self) -> None:
        signal.signal(signal.SIGINT, self.spleedy_signal_handler)
        self.done_exploits = []
        self.exclude_exploits = []
        self.exploits_to_scan = []
        self.target = None
        self.parameters = None
        self.exploitEngine = ExploitEngine(TOOL_DIRECTORY)
        self.hardwareEngine = HardwareEngine(TOOL_DIRECTORY)
        #self.engine = Engine()
        #self.checkpoint = Checkpoint()
        self.setupverifier = SetupVerifierEngine()
        self.recon = Recon()
        #self.report = Report()
    
    def spleedy_signal_handler(self, sig, frame):
        print("Ctrl+C detected. Creating a checkpoint and exiting")
        self.preserve_state()
        os.chdir(TOOL_DIRECTORY)
        sys.exit()
    
    def set_parameters(self, parameters: list):
        self.parameters = parameters

    def set_explude_exploits(self, exclude_exploits: list):
        self.exclude_exploits = exclude_exploits
    
    def set_exploits(self, exploits_to_scan: list):
        self.exploits_to_scan = exploits_to_scan
    
    def set_exploits_hardware(self, hardware: list):
        available_exploits = self.get_available_exploits()
        available_exploits = [exploit for exploit in available_exploits if exploit.hardware in hardware]
        self.set_exploits(available_exploits)

    def get_available_exploits(self):
        return self.exploitEngine.get_all_exploits()
    
    def get_available_hardware(self):
        return self.hardwareEngine.get_all_hardware_profiles()
    
    def check_hardware(self):
        available_hardware = self.hardwareEngine.get_all_hardware_profiles()
        hardware_verified = self.setupverifier.verify_setup_multiple_hardware(available_hardware)
        print("Hardware availability:")
        for hardware in available_hardware:
            print("{hardware} - status {availability}".format(hardware=hardware.name, availability=hardware_verified[hardware.name]))
    
    def get_exploits_with_setup(self):
        available_exploits = self.get_available_exploits()
        available_hardware = self.get_available_hardware()
        hardware_verified = self.setupverifier.verify_setup_multiple_hardware(available_hardware)
        return [exploit for exploit in available_exploits if hardware_verified[exploit.hardware]]

    def print_available_exploits(self):
        available_exploits = self.get_available_exploits()
        available_hardware = self.get_available_hardware()
        hardware_verified = self.setupverifier.verify_setup_multiple_hardware(available_hardware)
        
        available_exploits = sorted(available_exploits, key=lambda x: x.type)
        available_exploits = sorted(available_exploits, key=lambda x: x.hardware)
        available_exploits = sorted(available_exploits, key=lambda x: not hardware_verified[x.hardware])

        table = Table(title="Available Exploits")
        table.add_column("Index", justify="center", style="cyan", no_wrap=True)
        table.add_column("Exploit", style="magenta")
        table.add_column("Type", style="green")
        table.add_column("Hardware", style="blue")
        table.add_column("Available", justify="center")
        table.add_column("BT min", justify="center")
        table.add_column("BT max", justify="center")

        for index, exploit in enumerate(available_exploits, start=1):
            symbol = '[red]X[/red]' 
            if hardware_verified[exploit.hardware]:
                symbol = '[green]✓[/green]'  

            table.add_row(
                str(index),
                exploit.name,
                exploit.type,
                exploit.hardware,
                symbol,
                str(exploit.bt_version_min),
                str(exploit.bt_version_max)
            )

        console = Console()
        console.print(table)
    
    def check_target(self, target):
        cont = True
        while cont:
            for i in range(10):
                available = self.recon.check_availability(target)
                if available:
                    return True
            if not available:
                inp = self.connection_lost()
    
    def connection_lost(self) -> None:
        command = input("The target device is not available. Try restoring the connectivity. After that enter 1 of the following commands: continue, backup:\n")
        if command == "continue":
            print("Trying to verify connectivity again")
        elif command == "backup":
            print("Backing up")
            self.preserve_state()
            raise SystemExit
        else:
            print("Didn't understand your input")
            connection_lost(self)
    
    def run_recon(self, target):
        self.recon.run_recon(target)
        v = self.recon.determine_bluetooth_version(target)
        print(f"Bluetooth Version of target device: {v}")

def main():
    parser = argparse.ArgumentParser(description="SbleedyGonzales CLI tool")
    parser.add_argument('-t','--target', required=False, type=str, help="target MAC address")
    parser.add_argument('-l','--listexploits', required=False, action='store_true', help="List all exploits yes/no")
    parser.add_argument('-ct','--checktarget', required=False, action='store_true',  help="Check connectivity and availability of the target")
    parser.add_argument('-ch','--checkpoint',  required=False, action='store_true', help="Start from a checkpoint")
    parser.add_argument('-ex','--exclude', required=False, nargs='+', default=[], type=str, help="Exclude exploits (--exclude exploit1, exploit2)")
    parser.add_argument('-e', '--exploits', required=False, nargs='+', default=[], type=str, help="Only run specific exploits (--exploits exploit1, exploit2), --exclude is not taken into account")
    parser.add_argument('-r', '--recon', required=False, action='store_true', help="Run a recon script")
    parser.add_argument('-re', '--report', required=False, action='store_true', help="Create a report for a target device")
    parser.add_argument('-rej','--reportjson', required=False, action='store_true', help="Create a report for a target device")
    parser.add_argument('-hw', '--hardware', required=False, nargs='+', default=[], type=str, help="Scan only for provided exploits based on hardware --hardware hardware1 hardware2; --exclude and --exploit are not taken into account")
    parser.add_argument('-chw','--checkhardware', required=False, action='store_true',  help="Check for connected hardware")
    args = parser.parse_args()

    logging.basicConfig(filename=LOG_FILE, level=logging.INFO)
    logging.info('Started')
    script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    logging.info(script_dir)
    distribution = pkg_resources.get_distribution("SbleedyGonzales")
    logging.info(str(distribution))
    logging.info(str(distribution.location))
    logging.info(Path(__file__))

    os.chdir(TOOL_DIRECTORY)
    expRunner = Sbleedy()
    if args.listexploits:
        expRunner.print_available_exploits()
    elif args.checkhardware:
        expRunner.check_hardware()
    elif args.target:
        if len(args.hardware) > 0:
            expRunner.set_exploits_hardware(args.hardware)
            logging.info("Provided --hardware parameter -> " + str(args.hardware))
        elif len(args.exploits) > 0:
            expRunner.set_exploits(args.exploits)
            logging.info("Provided --exploit parameter -> " + str(args.exploits))
        elif len(args.exclude) > 0:
            expRunner.set_explude_exploits(args.exclude)
            logging.info("Provided --exclude parameter -> " + str(args.exclude))

        if args.checktarget:
            expRunner.check_target(args.target)
        else:
            if args.recon:
                expRunner.run_recon(args.target)
            elif args.report:
                print("TODO")
                #expRunner.generate_report(args.target)
            elif args.reportjson:
                print("TODO")
                #expRunner.generate_machine_readble_report(args.target)
            elif args.checkpoint:
                print("TODO")
                #expRunner.start_from_a_checkpoint(args.target)
            else:
                print("TODO")
                #expRunner.start_from_cli_all(args.target, addition_parameters)
    else:
        parser.print_help()
    
    os.chdir(TOOL_DIRECTORY)

if __name__ == '__main__':
    main()
