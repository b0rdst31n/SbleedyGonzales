import os
from pathlib import Path

TOOL_DIRECTORY = os.getcwd()
LOG_FILE = TOOL_DIRECTORY + '/results/application.log'
EXPLOIT_YAML_DIRECTORY = TOOL_DIRECTORY + '/exploits/'
EXPLOIT_TOOL_DIRECTORY = TOOL_DIRECTORY + '/modules/'
HARDWARE_DIRECTORY = TOOL_DIRECTORY + '/hardware/'

TIMEOUT = 40