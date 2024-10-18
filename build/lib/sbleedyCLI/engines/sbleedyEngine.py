import logging
import shutil
import sys
import time
import os
import re
import psutil
import subprocess
import signal
from pathlib import Path

from sbleedyCLI.models.exploit import Exploit
from sbleedyCLI.constants import TIMEOUT, OUTPUT_DIRECTORY, TOOL_DIRECTORY, EXPLOIT_TOOL_DIRECTORY, REGEX_EXPLOIT_OUTPUT_DATA, REGEX_EXPLOIT_OUTPUT_DATA_DATA, REGEX_EXPLOIT_OUTPUT_DATA_CODE
from sbleedyCLI.constants import RETURN_CODE_ERROR, RETURN_CODE_UNDEFINED, RETURN_CODE_NONE_OF_4_STATE_OBSERVED, RETURN_CODE_NOT_VULNERABLE, RETURN_CODE_VULNERABLE

class SbleedyEngine:
    def __init__(self):
        self.logger = logging.getLogger('sbleedy_logger')
        self.logger.setLevel(logging.DEBUG)

    def construct_exploit_command(self, target: str, current_exploit: Exploit, parameters: list) -> str:
        exploit_command = current_exploit.command.split(' ')
        
        parameters_dict = self.process_additional_paramters(parameters)
        parameters_list = self.get_parameters_list(parameters)
        
        for param in current_exploit.parameters:
            if param['name'] in parameters_list:
                logging.info("SbleedyEngine.construct_exploit_command -> parameter_name in parameter_List {}".format(param))

                if param['name_required']:
                    if param['parameter_connector'] != " ":
                        exploit_command.append(param['name'] + param['parameter_connector'] + parameters_dict[param['name']])
                    else:
                        exploit_command.append(param['name'])
                        exploit_command.append(parameters_dict[param['name']])
                else:
                    exploit_command.append(parameters_dict[param['name']])
                parameters_list.remove(param['name'])
                parameters_dict.pop(param['name'])
            elif param['is_target_param']:
                if param['name_required']:
                    if param['parameter_connector'] != " ":
                        exploit_command.append(param['name'] + param['parameter_connector'] + target)
                    else:
                        exploit_command.append(param['name'])
                        exploit_command.append(target)
                else:
                    exploit_command.append(target)
            elif param['required']:
                self.logger.error("Parameter {} is required, but was not found in your command".format(param['name']))
                raise Exception("Parameter {} is required, but was not found in your command".format(param['name']))
        
        logging.info("SbleedyEngine.construct_exploit_command -> exploit_command list -> " + str(exploit_command))
        logging.info("SbleedyEngine.construct_exploit_command -> exploit command together -> {}".format(' '.join(exploit_command)))
        
        return exploit_command
        
    def run_test(self, target: str, current_exploit: Exploit, parameters: list) -> None:
        exploit_command = self.construct_exploit_command(target, current_exploit, parameters)

        new_directory = EXPLOIT_TOOL_DIRECTORY
        new_directory += current_exploit.directory['directory']

        if_failed, data = self.execute_command(target, exploit_command, current_exploit.name, timeout=current_exploit.max_timeout, directory=new_directory)

        if current_exploit.type == "DoS":
            #response_code, data = dos_checker(target)
            print("TODO: add dos checker")
        else:
            logging.info('SbleedyEngine.run_test -> data ' + str(data))
            response_code, data = self.process_raw_data(data, if_failed)

        return response_code, data
        
    def execute_command(self, target: str, exploit_command: list, exploit_name: str, timeout=TIMEOUT, directory=None) -> tuple:
        pid = None
        os.chdir(directory)
        logging.info("SbleedyEngine.execute_command -> chdir to {}".format(directory))
  
        data = False, b''

        try:
            self.logger.info("Starting the next exploit - name {} and command {}".format(exploit_name, exploit_command))
            command = subprocess.Popen(' '.join(exploit_command), stdout=subprocess.PIPE, shell=True, preexec_fn=os.setsid)         # for some reason doesn't accept tokenized exploit_command (leads to a bug)
            pid = command.pid
            
            logging.info("SbleedyEngine.execute_command -> sleeping for {} seconds".format(timeout))
                
            new_xdata = command.wait(timeout=timeout)
            new_data = command.communicate()
            logging.info("SbleedyEngine.execute_command -> command.communicate " + str(new_data))
            if type(new_data) is int:
                print(new_data)
            else:
                new_data = new_data[0]
            data = True, new_data
        except subprocess.TimeoutExpired as e:
            logging.info("SbleedyEngine.execute_command -> Killing the exploit and sleeping for another 1 second")
            for child in psutil.Process(pid).children(recursive=True):
                child.kill()
            os.killpg(os.getpgid(command.pid), signal.SIGTERM)
            time.sleep(1)
        
        os.chdir(TOOL_DIRECTORY)
        
        logging.info("SbleedyEngine.execute_command -> data -> " + str(data))
        return data
    
    def process_raw_data(self, data, if_failed):
        # INEFFICIENTLY processes data line by line (there is room for improvement)
        try:
            mm = re.compile(REGEX_EXPLOIT_OUTPUT_DATA)
            output = mm.search(data).group()
            print(output)
            logging.info("SbleedyEngine.process_raw_data -> Found data from the exploit {}".format(output))
            
            mm2 = re.compile(REGEX_EXPLOIT_OUTPUT_DATA_CODE)
            mm3 = re.compile(REGEX_EXPLOIT_OUTPUT_DATA_DATA)
            
            output2 = int(mm2.search(output).group().rstrip(b",").split(b"=")[1])
            logging.info("SbleedyEngine.process_raw_data -> Found data from the exploit, code -> {}".format(output2))
            output3 = (mm3.search(output).group().split(b"=")[1]).decode()
            logging.info("SbleedyEngine.process_raw_data -> Found data from the exploit, data -> {}".format(output3))

            return int(output2), output3    
        except Exception as e:
            logging.info("SbleedyEngine.process_raw_data -> Error during extracting information from the regex " + str(e))
            return RETURN_CODE_NONE_OF_4_STATE_OBSERVED, "Error during extracting information from the regex"
        
    def process_additional_paramters(self, parameters: list) -> dict:
        logging.info("SbleedyEngine.process_additional_paramters -> list parameters " + str(parameters))
        param_dict = {}
        for i in range(0, len(parameters), 2):
            param_dict[parameters[i]] = parameters[i + 1]
        return param_dict 

    def get_parameters_list(self, parameters: list) -> list:
        return [parameters[i] for i in range(0, len(parameters), 2)]

