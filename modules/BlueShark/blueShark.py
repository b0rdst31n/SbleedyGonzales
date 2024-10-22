import os
import subprocess
import argparse
import time
import threading
import sys

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

def start_scan_nRF(port, logfile=None, target=None, verbose=None, wireshark=None):
    command = ["python", "sniffer.py", port]
    currPath = os.path.dirname(os.path.realpath(__file__))
    if logfile:
        command += ["-l", str(logfile + ".pcap")]
    if target:
        command += ["-t", str(target)]
    if verbose:
        command += ["-v"]
    try:
        print("\nStarting the scan. Type 'stop' to end the scanning.")
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        stop_event = threading.Event()
        input_thread = threading.Thread(target=stop_process_on_user_input, args=(process, stop_event))
        input_thread.start()

        try:
            for line in process.stdout:
                print(line)
        except KeyboardInterrupt:
            print("If you want to interrupt, type 'stop'.")
            process.terminate()
            stop_event.set()

        process.wait()

        stop_event.set()
        input_thread.join()
        if input_thread.is_alive():
            print("Input thread is still running... Type 'stop' to continue.")
            stop_event.set()

        if wireshark:
            pcap_file = os.getcwd() + "/results/" + logfile + ".pcap"
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
    parser = argparse.ArgumentParser(description="BlueShark")
    parser.add_argument('-p','--port', required=True, type=str, help="port of device (e.g. /dev/ttyACM0)")
    parser.add_argument('-t','--target', required=False, type=str, help="target mac")
    parser.add_argument('-l','--logfile', required=False, type=str, help="logfile name")
    parser.add_argument('-ws','--wireshark', required=False, action="store_true", help="open wireshark after sniffing (only in combination with -l)")
    parser.add_argument('-v','--verbose', required=False, action="store_true", help="verbose mode (all serial traffic is displayed)")

    args = parser.parse_args()

    print_ascii_art()
    
    if args.port:
        start_scan_nRF(args.port, args.logfile, args.target, args.verbose, args.wireshark)
    else:
        parser.print_help()
