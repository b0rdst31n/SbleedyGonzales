# BlueShark - Bluetooth Low Energy Packet Sniffing and Analysis Tool

BlueShark can sniff BLE data using an nRF Sniffer or an HackRF and save it as a `.pcap` file for analysis in Wireshark.

The [nRF52840 dongle](https://www.nordicsemi.com/Products/Development-hardware/nRF52840-Dongle) is recommended because it supports:
- LE Secure Connections
- Radio Fast Ramp-up
- LE 2M PHY
- LE Coded PHY
- USB support  
It is also relatively inexpensive.

## Installation

### nRF52840
Before using BlueShark, ensure you have flashed the nRF Sniffer firmware and set up Wireshark for BLE. Follow the instructions in this [manual](https://infocenter.nordicsemi.com/index.jsp?topic=%2Fug_sniffer_ble%2FUG%2Fsniffer_ble%2Finstalling_sniffer.html&cp=11_5_2).

Dependencies: pyserial >= 3.5, psutil
```bash
pip install "pyserial>=3.5" psutil
```
### HackRF One
Please follow the instructions on <https://github.com/mikeryan/ice9-bluetooth-sniffer>.
Install the required dependencies, clone the repository and follow the build instructions ('make install' is not necessary).
After the exe (ice9-bluetooth) is being compiled, copy it to helpers/blueshark.

## Usage

### General Options

**-hw [hardware]**
  - Specifies the hardware to use (nRF or hackRF)

**-l [filename]**
  - Specifies a filename for the capture. Captures are saved in `helpers/blueshark/logs`.
  - **Example**: `-l test` → saves the capture as `helpers/blueshark/logs/test.pcap`.

**-v**
  - Enable verbose mode to display all serial traffic. Default is off.

**-ws**
  - Open the capture file in Wireshark after sniffing is done (if Wireshark is installed and -l is provided).

### nRF Options

**-t [target_mac]**
  - (optional) Specifies the device address to target.

### HackRF Options

**-c [channel_freq]**
  - (required) Specifies the center frequency (in MHz).
  - The BLE spectrum extends from 2402 MHz to 2480 MHz. The main advertising channels are:
    - Channel 37: 2402 MHz
    - Channel 38: 2426 MHz
    - Channel 39: 2480 MHz

**-C [number_of_channels]**
  - (required) Specifies the number of channels to capture (must be >= 4 and divisible by 4).


## Credit

The SnifferAPI is being provided by <https://www.nordicsemi.com/Products/Development-tools/nrf-sniffer-for-bluetooth-le/download>.
The HackRF Sniffer is from <https://github.com/mikeryan/ice9-bluetooth-sniffer>.
