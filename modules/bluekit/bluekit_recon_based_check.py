import argparse
import logging

from pathlib import Path

from sbleedyCLI.constants import RECON_DIRECTORY, BLUING_BR_LMP, LOG_FILE, DEVICE_INFO
from sbleedyCLI.constants import RETURN_CODE_NOT_VULNERABLE, RETURN_CODE_VULNERABLE, RETURN_CODE_ERROR
from sbleedyCLI.report import report_error, report_not_vulnerable, report_vulnerable
from sbleedyCLI.recon import Recon

#       LE Cont # LE Host #  Sim LE/ER/BDR Cont # im LE/ER/BDR Host # SSP Cont # SSP H # SC Cont # SC H
#           0        1               2                      3           4          5        6        7
#data = [0,0,0,0,0,0,0,0]

LE_SUP_C = "LE Supported (Controller):"
LE_SUP_H = "LE Supported (Host):"
SIM_LE_BR_C = "Simultaneous LE and BR/EDR to Same Device Capable (Controller):"
SIM_LE_BR_H = "Simultaneous LE and BR/EDR to Same Device Capable (Host):"
SSP_SUP_C = "Secure Simple Pairing (Controller Support):"
SSP_SUP_H = "Secure Simple Pairing (Host Support):"
SC_SUP_C = "Secure Connections (Controller Support):"
SC_SUP_H = "Secure Connections (Host Support):"


entry_to_data = {
    LE_SUP_C: 0,
    LE_SUP_H: 1,
    SIM_LE_BR_C: 2,
    SIM_LE_BR_H: 3,
    SSP_SUP_C: 4,
    SSP_SUP_H: 5,
    SC_SUP_C: 6,
    SC_SUP_H: 7
}


def check_prerequisites_not_satisfied(target):
    try:
        lmp_file = Path(RECON_DIRECTORY.format(target=target) + BLUING_BR_LMP[1])
        if lmp_file.exists():
            return False
    except Exception as e:
        pass
    return True


def find_and_extract_data(target, data):
    lmp_file = Path(RECON_DIRECTORY.format(target=target) + BLUING_BR_LMP[1])
    try:
        with open(lmp_file, 'r') as f:
            for line in f:
                s = line.strip()
                for key in list(entry_to_data.keys()):
                    if s.startswith(key):
                        if s.split(key)[1].strip() == 'True':
                            data[entry_to_data[key]] = 1
                        elif s.split(key)[1].strip() == 'False':
                            data[entry_to_data[key]] = 0
    except FileNotFoundError as e:
        logging.info("No file {} found. ".format(lmp_file))
        print("No file {} found. ".format(lmp_file) + ". Please run a recon script first: sbleedy -t {} -r ".format(target) + ". If you already did that, then first pair your attack device with the target, and run a recon script again. If fails -> open an issue on github")
    except Exception as e:
        logging.info("Strange exception {}".format(e))
        print("Strange exception happenned")
    return data

def evaluate_data_sc(target, data=[-1,-1,-1,-1,-1,-1,-1,-1]):
    if check_prerequisites_not_satisfied(target):
        logging.info("Prerequisites for lmp_file are not satisfied. exiting")
        print("There is no lmp file from recon script. Please run a recon script first: sbleedy -t {} -r ".format(target) + ". If you already did that, then first pair your attack device with the target, and run a recon script again. If fails -> open an issue on github")
        report_error("There is no lmp file from recon script")
        return
    
    data = find_and_extract_data(target, data)

    if data[entry_to_data[SC_SUP_C]] == -1 or data[entry_to_data[SC_SUP_H]] == -1:
        report_error("There are required fields missing in the lmp file.")
    elif data[entry_to_data[SC_SUP_C]] and data[entry_to_data[SC_SUP_H]]:
        # Supports SC okay
        report_not_vulnerable("Secure Connections supported")
    else:
        report_vulnerable("No Secure Connections supported")

def evaluate_data_blur(target, data=[-1,-1,-1,-1,-1,-1,-1,-1]):
    if check_prerequisites_not_satisfied(target):
        logging.info("Prerequisites for lmp_file are not satisfied. exiting")
        print("There is no lmp file from recon script. Please run a recon script first: sbleedy -t {} -r ".format(target) + ". If you already did that, then first pair your attack device with the target, and run a recon script again. If fails -> open an issue on github")
        report_error("There is no lmp file from recon script")
        return
    
    r = Recon()
    version = float(r.determine_bluetooth_version(target))
    if version is not None and version < 4.2:
        report_not_vulnerable("Target device doesn't use Bluetooth 4.2+")
        return

    data = find_and_extract_data(target, data)

    if data[entry_to_data[LE_SUP_C]] == -1 or data[entry_to_data[LE_SUP_H]] == -1 or data[entry_to_data[SIM_LE_BR_C]] == -1 or data[entry_to_data[SIM_LE_BR_H]] == -1:
        report_error("There are required fields missing in the lmp file.")
    elif data[entry_to_data[LE_SUP_C]] and data[entry_to_data[LE_SUP_H]]:
        # LE supported 
        if data[entry_to_data[SIM_LE_BR_C]] and data[entry_to_data[SIM_LE_BR_H]]:
            # Simultaneous LE BR/EDR supported
            # Try testing BLUR
            report_vulnerable("Possibly vulnerable to BLUR (device supports BT 4.2+ and simultaneous LE BR/EDR), needs testing")
        else:
            report_not_vulnerable("No simultaneous LE BR/EDR supported, Cross transport attacks are not going to work")
    else:
        report_not_vulnerable("No LE supported (Controller + Host), Cross transport attacks are not going to work")

def evaluate_data_ssp(target, data=[-1,-1,-1,-1,-1,-1,-1,-1]):
    if check_prerequisites_not_satisfied(target):
        logging.info("Prerequisites for lmp_file are not satisfied. exiting")
        print("There is no lmp file from recon script. Please run a recon script first: sbleedy -t {} -r ".format(target) + ". If you already did that, then first pair your attack device with the target, and run a recon script again. If fails -> open an issue on github")
        report_error("There is no lmp file from recon script")
        return
    
    data = find_and_extract_data(target, data)
    
    logging.info("ssp check -> data -> " + str(data))
    
    if data[entry_to_data[SSP_SUP_C]] == -1 or data[entry_to_data[SSP_SUP_H]] == -1:
        report_error("There are required fields missing in the lmp file.")

    if data[entry_to_data[SSP_SUP_C]] and data[entry_to_data[SSP_SUP_H]]:
        # SSP supported
        r = Recon()
        bt_version = r.determine_bluetooth_version(target)
        logging.info("ssp check -> bt version -> " + str(bt_version))

        if bt_version is not None:
            if float(bt_version) <= 4.0:
                # BT version 4.0 and earlier in BT Classic use E0, SAFER ciphers which are weak (Didn't determine practicallity of available attacks, but in case of crypto with strong adversary these algorithms are very weak) 
                # 2 test case
                report_vulnerable("SSP supported, weak cryptography is used due to BT version <= 4.0")
            else:
                # Doesn't support SC, but still uses pretty secure Cryptography. # Note there might be a problem with Message Integrity (Specification doesn't specify whether cryptographic mesage integrity is available for SSP, only that there's no message integrity for Legacy pairing, and there is for SC, but nothing mentioned in case of SSP)
                # 3 test case
                report_not_vulnerable("SSP supported, secure cryptography is used, there might be a problem with Message Intergrity")
        else:
            logging.info("recon_based_exploit.py -> bt version is None couldn't find a BT verison, probably an error")
            report_error("Couldn't determine BT version, run recon script first")
    else:
        # SSP not supported - vulnerable Legacy pairing
        # 1 test case
        logging.info("ssp check -> probablz no SSP supported at all")
        report_vulnerable("SSP not supported")
 

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-t','--target',required=False, type=str, help="target MAC address")
    parser.add_argument('-c','--case', required=False, type=int, help="Test case to run 1 - SC, 2 - SSP, 3 - BLUR")
    args = parser.parse_args()

    logging.basicConfig(filename=LOG_FILE, level=logging.INFO)

    if args.target and args.case:
        logging.info("case -> " + str(args.case))
        if args.case == 3:
            evaluate_data_blur(args.target)
        elif args.case == 1:
            evaluate_data_sc(args.target)
        elif args.case == 2:
            evaluate_data_ssp(args.target)
        else:
            parser.print_help()
    else:
        parser.print_help()
