import os
import re
import subprocess
import argparse

currPath = os.path.dirname(os.path.abspath(__file__))
gattDir = os.path.join(currPath, "gatt")

def print_ascii_art():
    ascii_art = r"""
                                                           :
                                                  :=  :*: =:
   .-                                            :*= -#-:*+
  ..==. ::                                      :*+-*#==#=.-:
  .==:+=:++:                               .. .+%**%%*#=-+*-
 ::+:+****++*--:                          :*-*#**###*%%%#+#+:
 .=++##**#***#%##++=-:..               .=#%%@%%#*#%%%%%%%%%=
 .-==*###****#*#%@%#**==+==:          .*%@%%%%%%###%%%%%%%#-
     .=*#######%%%%@@@%*+===+*+=.    .+%%@%%%%%@%%%%%%%%%%.
          :=+*%%%%%%%@@@%*+++**##%*=+#%@%%%%%%@@@@%@@%%%%:
               +*#%%%%@@@@%*=:.:+**%%@%%%%%%%%%@@@%%%%%+.
                 .-+*%%%=.    ..:+#%%@@@%%%%%@@@%@@@@%+
                     .:+-==:. .::=**%%@@@%%%%@@@@%%*=.
                      :-==-=-::-+*###%%%@@@@@@%%=:
                       .    :%%%%%%%%%%##%%*:
                              :#@%%@@%*##%%+--::...
                              .*@@@@@%***%*:.:--::-:::.
                              .*@@%-=+*##*:..::.:-:.::
                              :*##--+*#%%+=::::::::::
                            .==:====:-====:--:::::.
                           :=+-.:+-:   . .--::. .
                           .=:
    """
    print("\033[94m" + ascii_art + "\033[0m")

def enum_mac(target, hci):
    if target is None:
        print("There are arguments missing. Please provide a target address.\n")
        return
    print(f"\nEnumerating services for device with MAC address: {target}")
    command = ["sudo", "go", "run", "enumerator.go", "-m", target]
    if hci:
        command += ["-n", hci]
    try:
        subprocess.run(command, cwd=gattDir, check=True,
                       capture_output=False, text=True)
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e.stderr}")

def scan(timeout=None, rssi=None, hci=None):
    command = ["sudo", "go", "run", "scanner.go", "-n", hciDevice]
    if timeout:
        command += ["-t", str(timeout)]
    if rssi:
        command += ["-r", str(rssi)]
    if hci:
        command += ["-d", str(hci)]
    
    print(f"Scanning for BLE devices (Timeout: {timeout}, RSSI Threshold: {rssi}).")
    print("You can find an overview over the discovered devices in results/discovered_devices.json after the scan.")

    try:
        subprocess.run(command, cwd=gattDir, check=True,
                       capture_output=False, text=True)
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e.stderr}")

def write_gatt(mac=None, handle=None, data=None):
    command = ["sudo", "go", "run", "enumerator.go", "-n", hciDevice]
    if mac:
        command += ["-m", str(mac)]
    else:
        mac = input("\nPlease enter the MAC address of the target device: ")
        command += ["-m", str(mac)]

    if handle:
        command += ["-h", str(handle)]
    else:
        handle = input(
            "Please enter the handle that you want to write to (e.g. 0001): ")
        command += ["-h", str(handle)]

    if data:
        command += ["-d", str(data)]
    else:
        data = input(
            "Please enter the data that you want to write (e.g. Hello): ")
        command += ["-d", str(data)]

    if (mac and handle and data):
        print(f"\nWriting to MAC address: {mac}")
        try:
            subprocess.run(command, cwd=gattDir, check=True,
                           capture_output=False, text=True)
        except subprocess.CalledProcessError as e:
            print(f"An error occurred: {e.stderr}")
    else:
        print("There are arguments missing. Please provide mac, handle and data.\n")
        write_gatt()

def fuzz_gatt():
    print("TODO")

def main():
    parser = argparse.ArgumentParser(description="BLEagle GATT Scanner")
    parser.add_argument('-s','--scan', required=False, action='store_true', help="Scan for advertising devices")
    parser.add_argument('-d','--device', required=False, type=str, help="hci device")
    parser.add_argument('-ti','--timeout', required=False, type=int,  help="Scan timeout")
    parser.add_argument('-r','--rssi', required=False, type=int,  help="RSSI threshold for scanning")
    parser.add_argument('-e','--enumerate', required=False, action='store_true', help="enumerate the GATT services of a given target")
    parser.add_argument('-t','--target', required=False, type=str, help="target mac")
    args = parser.parse_args()

    print_ascii_art()

    if args.scan:
        scan(args.timeout, args.rssi, args.device)
    elif args.enumerate:
        enum_mac(args.target)
    else:
        parser.print_help()


