import argparse
import subprocess
import time
import re
import sys
import os
import signal

def check_hci_device():
    """Check if any HCI device is available and reset it."""
    try:
        result = subprocess.run(['hciconfig'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            print(f"Error executing hciconfig: {result.stderr.decode()}")
            sys.exit(1)
        output = result.stdout.decode('utf-8')

        hci_devices = re.findall(r'(hci\d+):', output)
        if not hci_devices:
            print("No HCI devices found. Exiting.")
            sys.exit(1)
        hci_device = hci_devices[0]
        print(f"Found HCI device: {hci_device}")
        
        subprocess.run(['sudo', 'hciconfig', hci_device, 'down'], check=True)
        subprocess.run(['sudo', 'hciconfig', hci_device, 'reset'], check=True)
        subprocess.run(['sudo', 'hciconfig', hci_device, 'up'], check=True)
        
        print(f"HCI device {hci_device} is reset and up.")
        
        return hci_device
    
    except subprocess.CalledProcessError as e:
        print(f"Failed to configure HCI device: {e}")
        sys.exit(1)

def scan_bluetooth_le(timeout):
    """Scan for Bluetooth Low Energy (LE) devices using hcitool lescan."""
    print(f"Scanning for Bluetooth LE devices for {timeout} seconds...")
    try:
        process = subprocess.Popen(['sudo', 'hcitool', 'lescan'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(timeout)
        os.kill(process.pid, signal.SIGINT)
        stdout, stderr = process.communicate()
        if stderr:
            print(f"Error during Bluetooth LE scan: {stderr.decode('utf-8')}")
            return
        devices = set(re.findall(r'(([0-9A-F]{2}:){5}[0-9A-F]{2}) (.+)', stdout.decode('utf-8'), re.I))
        if devices:
            print("Found Bluetooth LE devices:")
            for mac, _, name in devices:
                print(f"MAC Address: {mac}, Name: {name}")
        else:
            print("No Bluetooth LE devices found.") 
    except Exception as e:
        print(f"Error during Bluetooth LE scanning: {e}")

def scan_bluetooth_classic(timeout):
    process = subprocess.Popen(['sudo', 'hcitool', 'scan'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(timeout)
    os.kill(process.pid, signal.SIGINT)
    stdout, stderr = process.communicate()
    if stderr:
        print(f"Error during Bluetooth Classic scan: {stderr.decode('utf-8')}")
        return
    devices = re.findall(r'(([0-9A-F]{2}:){5}[0-9A-F]{2})\t(.+)', stdout.decode('utf-8'), re.I)
    if devices:
        print("Found Bluetooth Classic devices:")
        for mac, _, name in devices:
            print(f"MAC Address: {mac}, Name: {name}")
    else:
        print("No Bluetooth Classic devices found.")

def main():
    parser = argparse.ArgumentParser(description="Bluetooth scanner")
    parser.add_argument("-m", "--mode", choices=["le", "classic"], help="Bluetooth mode to use (le for Bluetooth LE, classic for Bluetooth Classic)")
    parser.add_argument("-t", "--timeout", type=int, default=10, help="Scanning timeout in seconds (default: 10 seconds)")
    
    args = parser.parse_args()
    
    if args.mode:
        hci_device = check_hci_device()
        if args.mode == "le":
            scan_bluetooth_le(args.timeout)
        elif args.mode == "classic":
            scan_bluetooth_classic(args.timeout)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
