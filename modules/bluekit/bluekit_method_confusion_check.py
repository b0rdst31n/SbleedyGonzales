import argparse
import logging

from sbleedyCLI.report import report_not_vulnerable, report_vulnerable, report_error
from sbleedyCLI.recon import Recon
from sbleedyCLI.constants import LOG_FILE

def check_for_method_confusion(target):
    recon = Recon()
    capability = recon.get_capabilities(target=target)
    if capability is None:
        report_not_vulnerable("Device didn't show its capabilities, most likely Legacy Pairing")
    elif capability not in ['DisplayYesNo', 'NoInputNoOutput', 'DisplayOnly', 'KeyboardOnly', 'KeyboardDisplay']:
        report_error("Capability - {} is None or not in ".format(capability) + str(['DisplayYesNo', 'NoInputNoOutput', 'DisplayOnly', 'KeyboardOnly', 'KeyboardDisplay']))
    elif capability != "DisplayYesNo":
        report_vulnerable("Device capability is {}, susceptible to Method Confusion MitM")
    else:
        report_not_vulnerable("Device uses DisplayYesNo")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-t','--target',required=False, type=str, help="target MAC address")
    args = parser.parse_args()

    logging.basicConfig(filename=LOG_FILE, level=logging.INFO)

    if args.target:
        check_for_method_confusion(target=args.target)
    else:
        parser.print_help()
