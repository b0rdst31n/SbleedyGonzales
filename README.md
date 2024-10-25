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
- **More to come**

## Installation

### Prerequisites

- **Python**: Python 2.7 (for certain exploits) and Python 3.10 (for the CLI tool).
- **Pip**: Ensure pip is installed for both Python versions
- **BLE Adapter**: A compatible Bluetooth adapter that supports BLE (test by running hciconfig)

### Step-by-Step Installation

1. **Clone the Repository**:

    ```bash
    git clone https://github.com/b0rdst31n/SbleedyGonzales.git --recurse-submodules
    cd SbleedyGonzales
    ```

2. **Create Virtual Environments and Install Dependencies**:
    Sbleedy Gonzales requires separate environments for Python 2.7 and Python 3.10.
    You can run the shell script helpers/venv_installer.sh to get both python versions and their corresponding virtualenv versions, create a venv3 and venv2 and install the necessary requirements in both venvs.

      ```bash
      ./helpers/venv_installer.sh
      ```

      If you choose a different name for the Python 2.7 venv please adapt the VENV2_PATH in sbleedyCLI/constants.py.

      If you don't want to use the shell script and created the virtual environments, don't forget to install the required Python packages:

      For Python 3.10 environment (in `venv3`):

      ```bash
      pip install .
      ```

      For Python 2.7 (in `venv2`):

      ```bash
      cd modules/sweyntooth
      pip install -r requirements.txt
      ```

2. **Check Installation**:
   If everything worked, you should now be able to activate the venv3 and run sbleedy.
   
   ```bash
   source venv3/bin/activate
   sbleedy -h #should print usage info
   ```


## Usage

```console
usage: sbleedy [-h] [-l] [-chw] [-t TARGET] [-ct] [-ex EXCLUDEEXPLOITS [EXCLUDEEXPLOITS ...]] [-e EXPLOITS [EXPLOITS ...]] [-r] [-re] [-rej] [-hw HARDWARE [HARDWARE ...]] [-fh HARDWARE] [-v] ...

options:
  -h, --help            show this help message and exit
  -t TARGET, --target TARGET
                        target MAC address
  -l, --listexploits    List exploits or not
  -ct, --checktarget    Check connectivity and availability of the target
  -ch, --checkpoint     Start from a checkpoint (if one exists for the given target)
  -ex EXPLOITS [EXPLOITS ...], --exclude EXPLOITS [EXPLOITS ...]
                        Exclude exploits (e.g. --exclude exploit1, exploit2 OR --exclude 1,5)
  -in EXPLOITS [EXPLOITS ...], --include EXPLOITS [EXPLOITS ...]
                        Scan only for provided (e.g. --exploits exploit1, exploit2 OR --exploits 1-4), --exclude is not taken into account
  -r, --recon           Run a recon script. Saved in results/{target mac}/recon/
  -re, --report         Create a report for a target device
  -rej, --reportjson    Create a report for a target device
  -hw HARDWARE [HARDWARE ...], --hardware HARDWARE [HARDWARE ...]
                        Scan only for provided exploits based on hardware --hardware hardware1 hardware2; --exclude and --exploit are not taken into account
  -chw, --checkhardware Check for connected hardware
  -fh, --flashhardware HARDWARE
                        Flash firmware onto connected hardware (e.g. -fh nRF52840), get hardware names with -chw
  -v, --verbose         Verbosity on/off (additional output during exploit execution in terminal), Regardless of this flag the output is always saved in results/{target}/exploit_output.log

EXAMPLES:
Run sbleedy recon:
   $ sudo sbleedy -t AA:BB:CC:DD:EE:FF -r

Run sbleedy connectivity check:
   $ sudo sbleedy -t AA:BB:CC:DD:EE:FF -ct

Run sbleedy with specific exploits:
   $ sudo sbleedy -t AA:BB:CC:DD:EE:FF -e invalid_max_slot au_rand_flooding internalblue_knob

Run sbleedy and list all available exploits:
   $ sudo sbleedy -l

Documentation is available at: [... to be added]
```
