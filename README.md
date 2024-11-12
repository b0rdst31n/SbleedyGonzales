# SbleedyGonzales

SbleedyGonzales is a command-line tool designed to run various exploits against Bluetooth Low Energy (BLE) devices. With its fast execution and easy-to-use interface, Sbleedy Gonzales allows security researchers and developers to identify vulnerabilities in BLE devices in an automated manner without requiring knowledge about BLE.

## Features

- **Multiple Exploit Support**: Run several BLE vulnerability exploits at once.
- **Custom Exploit Execution**: Easily add new exploits and customize attack parameters.
- **Detailed Reports**: Generates JSON-based reports for each exploit executed against a target device.
- **Cross-Platform**: Compatible with Linux-based platforms with Bluetooth support.
- **Hardware Support**: Easy option to flash the hardware with the necessary firmware.

## Supported BLE Exploits

Sbleedy Gonzales includes various BLE-related exploits, such as:

- **[Sweyntooth](https://asset-group.github.io/disclosures/sweyntooth/)**: A suite of exploits targeting BLE vulnerabilities like L2CAP length overflow, truncated L2CAP, and more, leading to Crashes, Deadlocks and Security Bypasses.
- **[KNOB BLE](https://knobattack.com/)**: A security vulnerability that allows attackers to interfere with the pairing process by reducing the entropy of the encryption key, making it easier to perform brute-force attacks and potentially gain unauthorized access.
- **[BleedingTooth](https://google.github.io/security-research/pocs/linux/bleedingtooth/writeup.html)**: Set of zero-click vulnerabilities in the Linux Bluetooth subsystem that can allow an unauthenticated remote attacker in short distance to execute arbitrary code with kernel privileges on vulnerable devices.
- **And many more...**

Read the [SbleedyGonzales Wiki-Page](https://github.com/b0rdst31n/SbleedyGonzales/wiki/Included-Exploits) for more information about all included exploits.

## Installation

### Prerequisites

- **BLE Adapter**: A compatible Bluetooth adapter that supports BLE (test by running hciconfig)

The framework requires Python2.7 and Python3.10. There is a shell script provided to install these versions and all required dependencies in virtual environments. There's also a Docker image available to use SbleedyGonzales in a container with tools like Podman or Docker. Please refer to the [Installation Wiki Page](https://github.com/b0rdst31n/SbleedyGonzales/wiki/Installation) for further instructions.

## Usage

```console
usage: sbleedy [-h] [-l] [-chw] [-fhw HARDWARE] [-i EXPLOITS] [-t TARGET] [-ct] [-ex EXCLUDEEXPLOITS [EXCLUDEEXPLOITS ...]] [-in EXPLOITS [EXPLOITS ...]] [-wi] [-r] [-re] [-rej] [-hw HARDWARE [HARDWARE ...]] [-v] ...

options:
  -h, --help            show this help message and exit
  -t TARGET, --target TARGET
                        target MAC address
  -l, --listexploits    List exploits or not
  -i, --info EXPLOITS   Prints information about the given exploit-indexes, e.g. --info 12-15,20
  -ct, --checktarget    Check connectivity and availability of the target
  -ch, --checkpoint     Start from a checkpoint (if one exists for the given target)
  -ex EXPLOITS [EXPLOITS ...], --exclude EXPLOITS [EXPLOITS ...]
                        Exclude exploits (e.g. --exclude exploit1, exploit2 OR --exclude 1,5)
  -in EXPLOITS [EXPLOITS ...], --include EXPLOITS [EXPLOITS ...]
                        Scan only for provided (e.g. --include exploit1, exploit2 OR --include 1-4), --exclude is not taken into account
  -wi, --withinput      Also run non automated scripts (that require user input or interaction. e.g. to establish a connection), per default (without this flag) only automated scripts (mass_testing = true) are being executed
  -r, --recon           Run a recon script. Saved in results/{target mac}/recon/
  -re, --report         Create a report for a target device
  -rej, --reportjson    Create a report for a target device
  -hw HARDWARE, --hardware HARDWARE
                        Scan only for provided exploits based on hardware, e.g. --hardware nRF52840; --exclude and --exploit are not taken into account
  -chw, --checkhardware Check for connected hardware
  -fhw, --flashhardware HARDWARE
                        Flash firmware onto connected hardware (e.g. -fhw nRF52840), get hardware names with -chw
  -v, --verbose         Verbosity on/off (additional output during exploit execution in terminal), Regardless of this flag the output is always saved in results/{target}/exploit_output.log

EXAMPLES:
Run sbleedy recon:
   $ sudo sbleedy -t AA:BB:CC:DD:EE:FF -r

Run sbleedy connectivity check:
   $ sudo sbleedy -t AA:BB:CC:DD:EE:FF -ct

Run sbleedy with specific exploits:
   $ sudo sbleedy -t AA:BB:CC:DD:EE:FF -in 1-3,5

Run sbleedy and list all available exploits:
   $ sudo sbleedy -l

Documentation is available at the [SbleedyGonzales Wiki](https://github.com/b0rdst31n/SbleedyGonzales/wiki).
To get the mac address of your target device, there is a helper script available for BLE devices (see Wiki - Helper Scripts), or just use
the standard Linux commands such as 'sudo hcitool scan' (BR/EDR) or 'sudo hcitool lescan' (LE).
```

## Credit

This project builds upon the foundational work provided by [BlueToolkit](https://github.com/sgxgsx/BlueToolkit). While adapting some elements from BlueToolkit's structure and code, I have tailored and expanded upon these components to fit the specific requirements of my framework for automated BLE exploit running. 
Special thanks to the contributors of BlueToolkit for providing a solid foundation and valuable resources for Bluetooth exploration.
This framework includes the following PoC implementations for BLE vulnerabilities:
- [Sweyntooth Bluetooth Low Energy Attacks](https://github.com/Matheus-Garbelini/sweyntooth_bluetooth_low_energy_attacks) by Matheus Garbelini
- Bleedingtooth [BadKarma](https://github.com/google/security-research/security/advisories/GHSA-h637-c88j-47wq), [BadVibes](https://github.com/google/security-research/security/advisories/GHSA-ccx2-w2r4-x649) and [BadChoice](https://github.com/google/security-research/security/advisories/GHSA-7mh3-gq28-gfrq) by Google Security Research
- [KNOB BLE Attack](https://github.com/Matheus-Garbelini/sweyntooth_bluetooth_low_energy_attacks/blob/master/extras/knob_tester_ble.py) by Matheus Garbelini
- BlueBorne [CVE-2017-0785](https://github.com/ojasookert/CVE-2017-0785) and [CVE-2017-0781](https://github.com/ojasookert/CVE-2017-0781) by ojasookert and [CVE-2017-1000251](https://github.com/sgxgsx/blueborne-CVE-2017-1000251) by marcinguy
- [Keystroke Injection](https://github.com/marcnewlin/hi_my_name_is_keyboard) by Marc Newlin
- [Custom BlueToolkit Exploits](https://github.com/sgxgsx/BlueToolkit) by sgxgsx
- [Btlejacking](https://github.com/virtualabs/btlejack) by virtualabs
- [Crackle](https://github.com/mikeryan/crackle) by mikeryan
