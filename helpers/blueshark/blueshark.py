import os
import subprocess
import argparse
import time
import threading
import sys
import pathlib
import serial.tools.list_ports
from hackrf import *

BLUESHARK_DIR = str(pathlib.Path(__file__).parent.resolve())
LOG_DIR = BLUESHARK_DIR + "/logs/"

def print_ascii_art():
    ascii_art = """
                                             %%
                                             %%@
                                             %%%@
                                             %%%%@
                                             %%%%@@
                                            %%%%%@@
   @@                                      =--=+*#%*:
     @@@#                            :...:::::-----::...::.
       @@@@%*:         @%*=:....:::::--===-==========-:::::..:::.
        @@@@@@%+     @%+::::::-====+==+++++=====++========-:..:=+*+==
          @@%@@%#==-=+****#%%%%%%%%%%%%%%%%#####**++++=====--::::-=******
            @%%**%%%%%%#####%%%%%%%%%%%%%%%%%#*****#*+=+++++==-::-=**###*##*
             @%%####*#%##***##%%#####%%%%%%%%%%%%##%*###%%%%%#**+===**##%%#####
              @%##     @@%#  %@@%@%******#******##%%%%%%%%@@@@@@@@@@@@@@@%%%%###%
              @@#      @   -=+%%%*+==+***********+*#%%%###%%%%%%%%%%%%%@%%%@@@@@@@
             @@%%                                ***************************###%
             @@%                                        *****************#
             @@
    """
    print("\033[94m" + ascii_art + "\033[0m")

def stop_process_on_user_input(process, stop_event):
    while not stop_event.is_set():
        user_input = input()
        if user_input.lower() == 'stop':
            process.terminate()
            break

def check_setup_nRF():
    print("\n[i] Checking for nRF...")
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("[!] No serial ports found.")
        exit()
    print("Available serial ports, please select the one for the nRF:")
    for i, port in enumerate(ports):
        print(f"{i + 1}: {port.device} with {port.description}")
        try:
            choice = int(input("Select a port by number (or 0 to exit): "))
            if 1 <= choice <= len(ports):
                port = ports[choice - 1]
                print(f"Selected port: {port.device}")
                if "Sniffer" not in port.description:
                    print("[!] Please make sure that the nRF runs with the sniffer firmware (sniffer_nRF52840_4.1.1.zip).\nYou can use the sbleedy firmware installer by running `sbleedy -fhw nRF52840`.")
                    exit()
                return port.device
            elif choice == 0:
                exit()
        except ValueError:
            print("Invalid input.")
            return False

def check_setup_hackRF():
    print("\n[i] Checking for hackRF...")
    try:
        hackrf = HackRF()
        print("[i] HackRF connected.")
        hackrf.close()
    except Exception:
        print("[!] No HackRF devices connected.")
        exit()

def start_scan_nRF(args):
    nRF_port = check_setup_nRF()
    command = ["python", "sniffer.py", nRF_port]

    command += ["-l", str(args.logfile)]
    if args.target:
        command += ["-t", str(args.target)]
    if args.verbose:
        command += ["-v"]
    try:
        print("\nStarting the scan.")
        subprocess.run(command, cwd=BLUESHARK_DIR, check=True,
                       capture_output=False, text=True)
        if args.wireshark:
            pcap_file = LOG_DIR + args.logfile + ".pcap"
            if os.path.exists(pcap_file):
                try:
                    print(f"Opening {pcap_file} in Wireshark")
                    subprocess.run(["wireshark", pcap_file], check=True)
                except subprocess.CalledProcessError as e:
                    print(f"Failed to open Wireshark: {e}")
            else:
                print(f"File not found: {pcap_file}")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e.stderr}")

def start_scan_hackRF(args):
    check_setup_hackRF()
    filepath = os.path.join(BLUESHARK_DIR, "ice9-bluetooth")
    if not (os.path.isfile(filepath) and os.access(filepath, os.X_OK)):
        print("[!] No ice9-bluetooth executable found. See README for instructions.")
        exit()
        
    command = ["./ice9-bluetooth", "-l"]
    if args.frequency:
        command += ["-c", str(args.frequency)]
    if args.channels:
        command += ["-C", str(args.channels)]
    if args.logfile:
        command += ["-w", str(LOG_DIR + args.logfile + ".pcap")]
    if args.verbose:
        command += ["-v"]
    
    try:
        print("\nStarting the scan. Type 'stop' to end the scanning.")
        process = subprocess.Popen(command, cwd=BLUESHARK_DIR, stdout=sys.stdout, stderr=sys.stderr, text=True)

        stop_event = threading.Event()
        input_thread = threading.Thread(target=stop_process_on_user_input, args=(process, stop_event))
        input_thread.start()
        
        while process.poll() is None:
            time.sleep(1)

        stop_event.set()
        if input_thread.is_alive():
            print("Input thread is still running... Type 'stop' to continue.")
            stop_event.set()

        if args.wireshark:
            pcap_file = LOG_DIR + args.logfile + ".pcap"
            if os.path.exists(pcap_file):
                try:
                    print(f"Opening {pcap_file} in Wireshark")
                    subprocess.run(["wireshark", pcap_file], check=True)
                except subprocess.CalledProcessError as e:
                    print(f"Failed to open Wireshark: {e}")
            else:
                print(f"File not found: {pcap_file}")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e.stderr}")


def main():
    os.system('clear')
    print_ascii_art()
    
    parser = argparse.ArgumentParser(description="BlueShark")
    parser.add_argument('-hw','--hardware', choices=['hackRF', 'nRF'], required=True, type=str, help="hardware to use (hackRF, nRF)")
    parser.add_argument('-l','--logfile', required=True, type=str, help="name of the pcap file")
    parser.add_argument('-t','--target', required=False, type=str, help="target MAC address (optional for nRF)")
    parser.add_argument('-f','--frequency', required=False, type=str, help="center channel frequency in MHz, between 2402 and 2480 (required for hackRF)")
    parser.add_argument('-c','--channels', required=False, type=str, help="number of channels to capture, must be >= 4 and divisible by 4 (required for hackRF)")
    parser.add_argument('-v','--verbose', required=False, action='store_true', help="display all serial traffic")
    parser.add_argument('-ws','--wireshark', required=False, action='store_true', help="open the pcap in wireshark after scanning")
    
    args = parser.parse_args()
    if args.hardware:
        pathlib.Path(LOG_DIR).mkdir(exist_ok=True, parents=True)
        if args.hardware == "nRF":
            start_scan_nRF(args)
        elif args.hardware == "hackRF":
            if not args.frequency and not args.channels:
                print("[!] Missing arguments frequency and channels")
                exit()
            start_scan_hackRF(args)
    else:
        parser.print_help()
    
    #else: print("No hardware connected (HackRF One or nRF Sniffer).")

if __name__ == "__main__":
    main()