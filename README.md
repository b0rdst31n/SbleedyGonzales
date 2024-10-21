# SbleedyGonzales

SbleedyGonzales is a CLI tool designed to perform various checks and operations on target devices and networks. It supports multiple functionalities such as running exploits, listing available options, checking connectivity, creating reports, and more.

## Installation

Requires Python3.10 (for the main exploit runner) and Python2.7 (for Sweyntooth)

## Usage

```bash
sbleedy [OPTIONS] [COMMANDS]
```

```console
usage: sbleedy [-h] [-l] [-chw] [-t TARGET] [-ct] [-ex EXCLUDEEXPLOITS [EXCLUDEEXPLOITS ...]] [-e EXPLOITS [EXPLOITS ...]] [-r] [-re] [-rej] [-hw HARDWARE [HARDWARE ...]] ...

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