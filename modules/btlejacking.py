import subprocess
import argparse
import threading
import sys
import time

from sbleedyCLI.report import report_not_vulnerable, report_vulnerable, report_error

def call_btlejack(target):
    command = ["btlejack", "-c", target]

    print(f"\n[i] Btlejack will listen for a connection to {target}. Try to connect a BLE device to the target device. When the connection is established: \n- Btlejack will print details about the sniffed connection --> vulnerable\nOR\n- No details will be printed --> not vulnerable\n\nAfter trying to establish a connection type 's' to terminate Btlejack.")

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    stop_event = threading.Event()

    def listen_for_stop():
        while not stop_event.is_set():
            user_input = input()
            if user_input.strip().lower() == "s":
                print("\nWere details about the connection printed? (y/n) ")
                sys.stdout.flush()
                user_input = input()
                if user_input.strip().lower() == "y":
                    report_vulnerable("Device is potentially vulnerable to BTLEJacking")
                elif user_input.strip().lower() == "n":
                    report_not_vulnerable("The connection couldn't be sniffed")
                else:
                    print("Invalid choice.")
                    report_error("Invalid feedback by user")
                process.terminate()
                stop_event.set()
                break

    # Start the input listening thread
    input_thread = threading.Thread(target=listen_for_stop)
    input_thread.daemon = True
    input_thread.start()

    try:
        # Read the output of the process
        for line in process.stdout:
            print(line, end='', flush=True)
    finally:
        process.wait()
        stop_event.set() 
    
    input_thread.join()

def main():
    parser = argparse.ArgumentParser(description="Btlejack")
    parser.add_argument('-t','--target', required=True, type=str, help="target MAC address")
    args = parser.parse_args()

    if args.target:
        target = args.target

        if len(target) != 17 or not all(c in "0123456789abcdefABCDEF:" for c in target):
            print("Invalid MAC address format.")
            report_error("Invalid mac address format")
            return
        
        call_btlejack(target)
        
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
