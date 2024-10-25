import os
from pathlib import Path

TOOL_DIRECTORY = os.getcwd()
RESULT_DIRECTORY = TOOL_DIRECTORY + '/results/'
LOG_FILE = TOOL_DIRECTORY + '/results/application.log'
EXPLOIT_YAML_DIRECTORY = TOOL_DIRECTORY + '/exploits/'
EXPLOIT_TOOL_DIRECTORY = TOOL_DIRECTORY + '/modules/'
HARDWARE_DIRECTORY = TOOL_DIRECTORY + '/hardware/'
FIRMWARE_DIRECTORY = HARDWARE_DIRECTORY + 'firmware/'
OUTPUT_DIRECTORY = TOOL_DIRECTORY + '/results/{target}/'
EXPLOIT_LOG_FILE = OUTPUT_DIRECTORY + 'exploit_output.log'
RECON_DIRECTORY = OUTPUT_DIRECTORY + 'recon/'
MACHINE_READABLE_REPORT_OUTPUT_FILE = OUTPUT_DIRECTORY + 'whole_report.json'
VENV2_PATH = TOOL_DIRECTORY + '/venv2/bin/'
SKIP_DIRECTORIES = ['recon']
CHECKPOINT_PATH = OUTPUT_DIRECTORY + '.checkpoint_{target}.json'
FLASH_NRF_FILE = TOOL_DIRECTORY + '/helpers/flash_nRF_firmware.sh'

NUMBER_OF_DOS_TESTS = 10
MAX_NUMBER_OF_DOS_TEST_TO_FAIL = 5

RETURN_CODE_ERROR = 0
RETURN_CODE_NOT_VULNERABLE = 1
RETURN_CODE_VULNERABLE = 2
RETURN_CODE_UNDEFINED = 3
RETURN_CODE_NONE_OF_4_STATE_OBSERVED = 4
RETURN_CODE_NOT_TESTED = 5

LESCAN = "sudo hcitool lescan"
L2PING = "sudo l2ping {target}"
HCITOOL_INFO = ("sudo hcitool info {target}", "hciinfo.log")
BLUING_BR_SDP = ("sudo bluing br --sdp {target}", "bluing_sdp.log")
BLUING_BR_LMP = ("sudo bluing br --lmp-features {target}", "bluing_lmp.log")
REGEX_BT_VERSION = r"Bluetooth Core Specification [0-9]{1}(\.){0,1}[0-9]{0,1}\ "
REGEX_BT_VERSION_HCITOOL = r"\(0x[0-f]{1}\) LMP Subversion:"
REGEX_BT_MANUFACTURER = r"Manufacturer name: .*\n"

REGEX_EXPLOIT_OUTPUT_DATA = b"SBLEEDY_GONZALES DATA:.*\n"
REGEX_EXPLOIT_OUTPUT_DATA_CODE = b" code=[0-4],"
REGEX_EXPLOIT_OUTPUT_DATA_DATA = b", data=.*"
MAX_CHARS_DATA_TRUNCATION = 80