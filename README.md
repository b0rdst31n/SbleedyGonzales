# SbleedyGonzales

SbleedyGonzales is a command-line tool designed to run various exploits against Bluetooth Low Energy (BLE) devices. With its fast execution and easy-to-use interface, Sbleedy Gonzales allows security researchers and developers to identify vulnerabilities in BLE devices in an automated manner without requiring knowledge about BLE.

## Features

- **Multiple Exploit Support**: Run several BLE vulnerability exploits at once.
- **Custom Exploit Execution**: Easily add new exploits and customize attack parameters.
- **Detailed Reports**: Generates JSON-based reports for each exploit executed against a target device.
- **Cross-Platform**: Compatible with Linux-based platforms with Bluetooth support.

## Supported BLE Exploits

Sbleedy Gonzales includes various BLE-related exploits, such as:

- **[Sweyntooth](https://github.com/Matheus-Garbelini/sweyntooth_bluetooth_low_energy_attacks)**: A suite of exploits targeting BLE vulnerabilities like L2CAP length overflow, truncated L2CAP, and more.
- **More to come**

## Installation

### Prerequisites

- **Python**: Python 2.7 (for certain exploits) and Python 3.x (for the CLI tool)
- **Pip**: Ensure pip is installed for both Python versions
- **BLE Adapter**: A compatible Bluetooth adapter that supports BLE (test by running hciconfig)

### Step-by-Step Installation

1. **Clone the Repository**:

    ```bash
    git clone https://github.com/b0rdst31n/SbleedyGonzales.git --recurse-submodules
    cd sbleedy_gonzales
    ```

2. **Create and Activate Virtual Environments**:
    Sbleedy Gonzales requires separate environments for Python 2.7 and Python 3.x. You can use `virtualenv` to create them:
   
    - Python 3.10:

      ```bash
      python3.10 -m virtualenv -p python3.10 venv3
      source venv3/bin/activate
      ```

    - Python 2.7 (for Sweyntooth):

      ```bash
      python2.7 -m virtualenv -p python2.7 venv2
      source venv2/bin/activate
      ```

      If you choose a different name for this virtualenv, please adapt the VENV2_PATH in sbleedyCLI/constants.py.

3. **Install Dependencies**:
    Install the required Python packages using pip:
   
    For Python 3 environment (in `venv3`):

    ```bash
    pip install .
    ```

    For Python 2.7 (in `venv2`):

    ```bash
    cd modules/sweyntooth
    pip install -r requirements.txt
    ```

## Installation

Requires Python3.10 (for the main exploit runner) and Python2.7 (for Sweyntooth)

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
  -e EXPLOITS [EXPLOITS ...], --exploits EXPLOITS [EXPLOITS ...]
                        Scan only for provided (e.g. --exploits exploit1, exploit2 OR --exploits 1-4), --exclude is not taken into account
  -r, --recon           Run a recon script. Saved in results/{target mac}/recon/
  -re, --report         Create a report for a target device
  -rej, --reportjson    Create a report for a target device
  -hw HARDWARE [HARDWARE ...], --hardware HARDWARE [HARDWARE ...]
                        Scan only for provided exploits based on hardware --hardware hardware1 hardware2; --exclude and --exploit are not taken into account
  -chw, --checkhardware Check for connected hardware
  -fh, --flashhardware HARDWARE
                        Flash firmware onto connected hardware (e.g. -fh nRF52840), get hardware names with -chw
  -v, --verbose         Verbosity on/off (additional output during exploit execution), saved in results/{target}/exploit_output.log

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
