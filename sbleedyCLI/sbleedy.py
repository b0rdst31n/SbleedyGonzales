import os
import pkg_resources
import sys
import argparse
import logging
import signal
import itertools
import threading
import time
import re
from tqdm import tqdm
from pathlib import Path
from rich.table import Table
from rich.console import Console

from .constants import TOOL_DIRECTORY, LOG_FILE, OUTPUT_DIRECTORY, RESULT_DIRECTORY
from .engines.exploitEngine import ExploitEngine
from .engines.hardwareEngine import HardwareEngine
from .engines.sbleedyEngine import SbleedyEngine
from sbleedyCLI.engines.connectionEngine import check_availability
from .recon import Recon
from .report import Report
from .checkpoint import Checkpoint

class Sbleedy():
    def __init__(self) -> None:
        signal.signal(signal.SIGINT, self.spleedy_signal_handler)
        self.done_exploits = []
        self.exclude_exploits = []
        self.exploits_to_scan = []
        self.target = None
        self.parameters = None
        self.exploitEngine = ExploitEngine()
        self.hardwareEngine = HardwareEngine()
        self.engine = SbleedyEngine()
        self.checkpoint = Checkpoint()
        self.recon = Recon()
        self.report = Report()
    
    def spleedy_signal_handler(self, sig, frame):
        print("Ctrl+C detected. Creating a checkpoint and exiting")
        self.preserve_state()
        os.chdir(TOOL_DIRECTORY)
        sys.exit()
    
    def set_parameters(self, parameters: list):
        self.parameters = parameters

    def set_exclude_exploits(self, exclude_exploits: list):
        only_numbers = all(re.match(r'^[0-9, -]+$', s) for s in exclude_exploits)
        if only_numbers:
            self.exclude_exploits = self.exploitEngine.get_exploits_by_index(exclude_exploits)
        else: 
            self.exclude_exploits = exclude_exploits
    
    def set_exploits(self, exploits_to_scan: list):
        only_numbers = all(re.match(r'^[0-9, -]+$', s) for s in exploits_to_scan)
        if only_numbers:
            self.exploits_to_scan = self.exploitEngine.get_exploits_by_index(exploits_to_scan)
        else: 
            self.exploits_to_scan = exploits_to_scan
    
    def set_exploits_hardware(self, hardware: list):
        available_exploits = self.get_available_exploits()
        available_exploits = [exploit for exploit in available_exploits if exploit.hardware in hardware]
        self.set_exploits(available_exploits)

    def get_available_exploits(self):
        return self.exploitEngine.get_all_exploits()
    
    def get_available_hardware(self):
        return self.hardwareEngine.get_all_hardware_profiles()
    
    def get_exploits_with_setup(self, available_exploits=None):
        if not available_exploits:
            available_exploits = self.get_available_exploits()
        available_hardware = self.get_available_hardware()
        hardware_verified = self.hardwareEngine.verify_setup_multiple_hardware(available_hardware)
        return [exploit for exploit in available_exploits if hardware_verified[exploit.hardware]]

    def print_available_exploits(self):
        available_exploits = self.get_available_exploits()
        available_hardware = self.get_available_hardware()
        hardware_verified = self.hardwareEngine.verify_setup_multiple_hardware(available_hardware)
        
        available_exploits = sorted(available_exploits, key=lambda x: x.type)
        available_exploits = sorted(available_exploits, key=lambda x: x.hardware)
        available_exploits = sorted(available_exploits, key=lambda x: not hardware_verified[x.hardware])

        print("\n")
        table = Table(title="Available Exploits")
        table.add_column("Index", justify="center", style="cyan", no_wrap=True)
        table.add_column("Exploit", style="magenta")
        table.add_column("Type", style="green")
        table.add_column("Hardware", style="blue")
        table.add_column("BT Version", justify="center")
        table.add_column("BT Profile", justify="center")
        table.add_column("Available", justify="center")

        for index, exploit in enumerate(available_exploits, start=1):
            symbol = '[red]X[/red]' 
            if hardware_verified[exploit.hardware]:
                symbol = '[green]✓[/green]'  

            table.add_row(
                str(index),
                ' '.join(word.capitalize() for word in exploit.name.split('_')),
                exploit.type,
                exploit.hardware,
                f"{exploit.bt_version_min} - {exploit.bt_version_max}",
                exploit.profile,
                symbol
            )

        console = Console()
        console.print(table)
    
    def check_target(self, target):
        cont = True
        while cont:
            for i in range(10):
                available = check_availability(target)
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
            print("Invalid input")
            connection_lost(self)
    
    def run_recon(self, target):
        self.recon.run_recon(target)
        v = self.recon.determine_bluetooth_version(target)
        print(f"Bluetooth Version of target device: {v}")
    
    def start_from_cli_all(self, target, parameters) -> None:
        logging.info("start_from_cli_all -> Target: {}".format(target))
        if not check_availability(target):
            sys.exit(1)

        available_exploits = self.get_available_exploits()
        exploits_with_setup = self.exploit_filter(target=target, exploits=self.get_exploits_with_setup())

        print("There are {} out of {} exploits available.".format(len(exploits_with_setup), len(available_exploits)))
        print("Running the following exploits: {}\n".format([exploit.name for exploit in exploits_with_setup]))

        Path(os.path.join(OUTPUT_DIRECTORY.format(target=target))).mkdir(exist_ok=True, parents=True)

        exploit_pool = exploits_with_setup
        self.parameters = parameters
        self.target = target
        self.test_one_by_one(target, self.parameters, exploit_pool)
    
    def exploit_filter(self, target, exploits) -> list:
        print("\nSkipping all exploits that require unavailable hardware.")
        logging.info("start_from_cli_all -> available exploit amount - {}".format(len(exploits)))
        logging.info("start_from_cli_all -> exploits to scan amount - {}".format(len(self.exploits_to_scan)))

        if self.exploits_to_scan:
            exploits = [exploit for exploit in exploits if exploit.name in set(self.exploits_to_scan)]
        elif self.exclude_exploits:
            exploits = [exploit for exploit in exploits if exploit.name not in set(self.exclude_exploits)]
        logging.info(f"start_from_cli_all -> chosen exploit amount - {len(exploits)}")

        #exploits = [exploit for exploit in exploits if exploit.mass_testing]

        version = self.recon.determine_bluetooth_version(target)
        if version is not None:
            print(f"Skipping all exploits that do not apply to the Bluetooth version of the target: {version}")
            logging.info(f"Target Bluetooth version: {version}. Skipping all exploits that do not apply to this version.")
            exploits = [exploit for exploit in exploits if float(exploit.bt_version_min) <= float(version) and float(version) <= float(exploit.bt_version_max)]
            logging.info("There are {} exploits to work on".format(len(exploits)) )

        return exploits
    
    def test_exploit(self, target, current_exploit, parameters) -> tuple:
        current_port = self.hardwareEngine.get_hardware_port(current_exploit.hardware)
        print(f"Currently running {current_exploit.name}... ", end="")
        sys.stdout.flush()

        stop_spinner = False
        def spinner_task():
            spinner = self.spinning_cursor()
            while not stop_spinner:
                sys.stdout.write(next(spinner))  
                sys.stdout.flush()
                time.sleep(0.1)  
                sys.stdout.write('\b')

        spinner_thread = threading.Thread(target=spinner_task)
        spinner_thread.start()

        try:
            result = self.engine.run_test(target, current_port, current_exploit, parameters)
        finally:
            stop_spinner = True
            spinner_thread.join()
        
        return result
        
    def test_one_by_one(self, target, parameters, exploits) -> None:
        for i in tqdm(range(0, len(exploits), 1), desc="Testing exploits"):
            #self.check_target(target)
            response_code, data = self.test_exploit(target, exploits[i], parameters)
            self.done_exploits.append([exploits[i].name, response_code, data])
            logging.info("Sbleedy.test_one_by_one -> done exploits - " + str(self.done_exploits))
            self.report.save_data(exploit_name=exploits[i].name, target=target, data=data, code=response_code)
    
    def spinning_cursor(self):
        spinner = itertools.cycle(['|', '/', '-', '\\'])
        while True:
            yield next(spinner)
    
    def generate_report(self, target):
        table = self.report.generate_report(target=target)
        console = Console()
        console.print(table)
    
    def generate_machine_readable_report(self, target):
        self.report.generate_machine_readable_report(target=target)
    
    def start_from_a_checkpoint(self, target) -> None:
        if self.checkpoint.check_if_checkpoint(target):
            exploit_pool, self.done_exploits, self.parameters, self.target, self.exploits_to_scan, self.exclude_exploits = self.checkpoint.load_state(target)        
            exploit_pool = self.exploit_filter(target=self.target, exploits=self.get_exploits_with_setup(exploit_pool))
            available_exploits = self.get_available_exploits()

            print(f"There are {len(exploit_pool) + len(self.done_exploits)} out of {len(available_exploits)} exploits available. {len(self.done_exploits)} exploits have already been tested.\n")                                                                                   
            print(f"Running the following exploits: {[exploit.name for exploit in exploit_pool]}")

            self.test_one_by_one(self.target, self.parameters, exploit_pool)

    def preserve_state(self) -> None:
        self.checkpoint.preserve_state(self.get_available_exploits(), self.done_exploits, self.target, self.parameters, self.exploits_to_scan, self.exclude_exploits)
        
def print_header():
    terminal_width = (os.get_terminal_size().columns)
    ascii_art = r"""
     ____  _     _               _          ____                      _           
    / ___|| |__ | | ___  ___  __| |_   _   / ___| ___  _ __  ______ _| | ___  ___ 
    \___ \| '_ \| |/ _ \/ _ \/ _` | | | | | |  _ / _ \| '_ \|_  / _` | |/ _ \/ __|
     ___) | |_) | |  __/  __/ (_| | |_| | | |_| | (_) | | | |/ / (_| | |  __/\__ \
    |____/|_.__/|_|\___|\___|\__,_|\__, |  \____|\___/|_| |_/___\__,_|_|\___||___/
                                   |___/                                          
    """
    ascii_lines = ascii_art.splitlines()
    max_width = max(len(line) for line in ascii_lines)
    for line in ascii_lines:
        leading_spaces = (terminal_width - max_width) // 2
        print("\033[94m" + " " * leading_spaces + line + "\033[0m")
    blue = '\033[94m'
    reset = "\033[0m"
    title = "Sbleedy Gonzales - BLE Exploit Runner"
    vertext = "Ver 0.1"
    terminal_width = os.get_terminal_size().columns
    separator = "=" * terminal_width

    print(blue + separator)
    print(reset + title.center(len(separator))) 
    print(blue + vertext.center(len(separator)))
    print(blue + separator + reset)

def main():
    parser = argparse.ArgumentParser(description="SbleedyGonzales CLI tool")
    parser.add_argument('-t','--target', required=False, type=str, help="target MAC address")
    parser.add_argument('-l','--listexploits', required=False, action='store_true', help="List all exploits yes/no")
    parser.add_argument('-ct','--checktarget', required=False, action='store_true',  help="Check connectivity and availability of the target")
    parser.add_argument('-ch','--checkpoint',  required=False, action='store_true', help="Start from a checkpoint")
    parser.add_argument('-ex','--exclude', required=False, nargs='+', default=[], type=str, help="Exclude exploits by index or name (--exclude exploit1, exploit2)")
    parser.add_argument('-in', '--include', required=False, nargs='+', default=[], type=str, help="Only run specific exploits (index or name) (--include exploit1, exploit2), --exclude is not taken into account")
    parser.add_argument('-r', '--recon', required=False, action='store_true', help="Run a recon script")
    parser.add_argument('-re', '--report', required=False, action='store_true', help="Create a report for a target device")
    parser.add_argument('-rej','--reportjson', required=False, action='store_true', help="Create a report for a target device")
    parser.add_argument('-hw', '--hardware', required=False, nargs='+', default=[], type=str, help="Scan only for provided exploits based on hardware --hardware hardware1 hardware2; --exclude and --exploit are not taken into account")
    parser.add_argument('-chw','--checkhardware', required=False, action='store_true',  help="Check for connected hardware")
    parser.add_argument('-fh','--flashhardware', required=False, type=str,  help="Flash connected hardware")
    parser.add_argument('-v','--verbose',  required=False, action='store_true', help="Additional output during exploit execution")
    parser.add_argument('rest', nargs=argparse.REMAINDER)
    args = parser.parse_args()

    if not os.path.exists(RESULT_DIRECTORY):
        try:
            os.makedirs(RESULT_DIRECTORY)
        except OSError as e:
            print(f"Error creating directory {RESULT_DIRECTORY}: {e}")
    with open(LOG_FILE, 'w'):
        pass
    logging.basicConfig(filename=LOG_FILE, level=logging.INFO)
    logging.info('Started')
    script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    logging.info(script_dir)
    distribution = pkg_resources.get_distribution("SbleedyGonzales")
    logging.info(str(distribution))
    logging.info(str(distribution.location))
    logging.info(Path(__file__))

    print_header()

    os.chdir(TOOL_DIRECTORY)
    expRunner = Sbleedy()
    if args.verbose:
        expRunner.engine.verbosity = True
    if args.listexploits:
        expRunner.print_available_exploits()
    elif args.checkhardware:
        expRunner.hardwareEngine.check_hardware()
    elif args.flashhardware:
        expRunner.hardwareEngine.flash_hardware(args.flashhardware)
    elif args.target:
        if len(args.hardware) > 0:
            av_hardware_list = []
            hardware_found = False
            for hw in expRunner.get_available_hardware():
                av_hardware_list.append(hw.name)
            
            for provided_hardware in args.hardware: 
                if provided_hardware in av_hardware_list:
                    expRunner.set_exploits_hardware(provided_hardware)
                    logging.info(f"Provided --hardware parameter -> {provided_hardware}")
                    hardware_found = True
                    break 

            if not hardware_found:
                print(f"\nAvailable hardware: {', '.join(av_hardware_list)}")
                sys.exit(1)
        elif len(args.include) > 0:
            expRunner.set_exploits(args.include)
            logging.info("Provided --exploit parameter -> " + str(args.include))
        elif len(args.exclude) > 0:
            expRunner.set_exclude_exploits(args.exclude)
            logging.info("Provided --exclude parameter -> " + str(args.exclude))

        if args.checktarget:
            expRunner.check_target(args.target)
        else:
            if args.recon:
                expRunner.run_recon(args.target)
            elif args.report:
                expRunner.generate_report(args.target)
            elif args.reportjson:
                expRunner.generate_machine_readable_report(args.target)
            elif args.checkpoint:
                expRunner.start_from_a_checkpoint(args.target)
            else:
                expRunner.start_from_cli_all(args.target, args.rest)
    else:
        parser.print_help()
    
    os.chdir(TOOL_DIRECTORY)

if __name__ == '__main__':
    main()
