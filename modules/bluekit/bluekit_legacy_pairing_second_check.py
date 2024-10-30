import argparse
import logging

from sbleedyCLI.report import report_not_vulnerable, report_vulnerable, report_error
from sbleedyCLI.recon import Recon
from sbleedyCLI.constants import LOG_FILE

def check_for_legacy_pairing(target):
    recon = Recon()
    output = recon.get_hcidump(target=target)
    
    if output is None:
        report_error("output from hcidump is none")

    for line in output:
        print(line)
        if line.strip().startswith("> HCI Event: PIN Code Request"):
            report_vulnerable("Device request a PIN Code, which is a sign of legacy pairing")
            return
    
    report_not_vulnerable("No PIN was requested")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-t','--target',required=False, type=str, help="target MAC address")
    args = parser.parse_args()

    logging.basicConfig(filename=LOG_FILE, level=logging.INFO)

    if args.target:
        check_for_legacy_pairing(target=args.target)
    else:
        parser.print_help()
