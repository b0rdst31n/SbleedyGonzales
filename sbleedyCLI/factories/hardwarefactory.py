import yaml
from os import listdir
from os.path import isfile, join

from sbleedyCLI.constants import HARDWARE_DIRECTORY
from sbleedyCLI.models.hardware import Hardware

class HardwareFactory:
    def __init__(self,base_dir):
        self.hardware_dir = HARDWARE_DIRECTORY
        self.hardware = None

    def get_all_hardware_profiles(self, force_reload=False):
        if self.hardware is None or force_reload:
            onlyfiles = [join(self.hardware_dir, f) for f in listdir(self.hardware_dir) if isfile(join(self.hardware_dir, f))]
            
            hardware_profiles = []
            for filename in onlyfiles:
                hardware_profiles.append(self.read_hardware(filename))    
            self.hardware = hardware_profiles
        return self.hardware

    def read_hardware(self, filename):
        f = open(filename, 'r')
        details = yaml.safe_load(f)
        f.close()
        return Hardware(details)



