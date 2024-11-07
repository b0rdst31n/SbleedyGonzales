import subprocess
import os
import sys
import re

from sbleedyCLI import constants as const
from sbleedyCLI.report import report_not_vulnerable, report_vulnerable, report_error

def main():
    if len(sys.argv) != 3 or sys.argv[1] != "--target":
        print("Usage: python script.py --target <Bluetooth MAC address>", flush=True)
        report_error("Wrong usage")
        return

    target_mac = sys.argv[2]
    formatted_mac = target_mac.replace(":", "").lower()

    pcap_filename = f"{formatted_mac}.pcap"
    pcap_dir = const.OUTPUT_DIRECTORY.format(target=target_mac)
    pcap_path = os.path.join(pcap_dir, pcap_filename)
    
    print("[i] Crackle needs a pcap with a captured connection. Please review https://github.com/mikeryan/crackle/blob/master/FAQ.md for more information.", flush=True)
    print(f"\nThe script requires the file '{pcap_filename}' at '{pcap_dir}'. Is it there? (y/n): ")
    sys.stdout.flush()
    response = input()
    if response != 'y':
        report_error("Pcap file not found")
        exit()

    if not os.path.isfile(pcap_path):
        print(f"Error: The pcap file '{pcap_filename}' does not exist in {pcap_dir}.", flush=True)
        report_error("Pcap file not found")
        return

    script_dir = os.path.dirname(os.path.abspath(__file__))
    crackle_exe = os.path.join(script_dir, "crackle")
    if not os.path.isfile(crackle_exe):
        print(f"Error: 'crackle' executable not found in {script_dir}.", flush=True)
        report_error("Crackle executable not found")
        return

    try:
        result = subprocess.run([crackle_exe, '-i', pcap_path], capture_output=True, text=True, check=True)
        print(result.stdout, flush=True)
        match = re.search(r'(\d+)\s+encrypted packets', result.stdout)
        if match:
            encrypted_packets = int(match.group(1))
        if encrypted_packets == 0:
            report_not_vulnerable("Crackle couldn't find encrypted packets, device probably not using Link Layer encryption")
        elif encrypted_packets > 0:
            if "TK found" in result.stdout:
                report_vulnerable("Crackle was able to get the TK from encrypted packets")
            elif "Secure Connections" in result.stdout:
                report_not_vulnerable("Crackle couldn't decrypt packets, device using LE Secure Connections")
    except subprocess.CalledProcessError as e:
        print(f"Error running 'crackle': {e}", flush=True)
        report_error("Error running crackle")

if __name__ == "__main__":
    main()
