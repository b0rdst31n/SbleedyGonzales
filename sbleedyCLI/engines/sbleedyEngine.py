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
import select
import itertools
import threading

from sbleedyCLI.models.exploit import Exploit
from sbleedyCLI.engines.connectionEngine import dos_checker
import sbleedyCLI.constants as const

class SbleedyEngine:
    def __init__(self):
        self.logger = logging.getLogger('sbleedy_logger')
        self.logger.setLevel(logging.DEBUG)
        self.verbosity = False

    def construct_exploit_command(self, target: str, ports: str, current_exploit: Exploit, parameters: list, directory: str) -> str:
        exploit_command = current_exploit.command.split(' ')
        
        parameters_dict = self.process_additional_parameters(parameters)
        parameters_list = self.get_parameters_list(parameters)

        if current_exploit.file_type == "python2.7":
            exploit_command = [os.path.join(const.VENV2_PATH, "python")] + exploit_command
        elif current_exploit.file_type == "python3":
            exploit_command.insert(0, "python")
        elif current_exploit.file_type == "c":
            exploit_command.insert(0, "sudo")
            os.chdir(directory)
            poc_file = current_exploit.command.lstrip("./")
            if not os.path.isfile(poc_file):
                compile_command = ["gcc", "-o", poc_file, poc_file + ".c", "-lbluetooth"]
                compile_process = subprocess.run(compile_command, check=True)
                if compile_process.returncode != 0:
                    logging.error(f"Error during gcc compilation for file {poc_file}")
        
        for param in current_exploit.parameters:
            if param['name'] in parameters_list:
                logging.info("SbleedyEngine.construct_exploit_command -> parameter_name in parameters_list {}".format(param))

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
            elif param['name'] in ['target', '-target', '--target']:
                if param['name_required']:
                    if param['parameter_connector'] != " ":
                        exploit_command.append(param['name'] + param['parameter_connector'] + target)
                    else:
                        exploit_command.append(param['name'])
                        exploit_command.append(target)
                else:
                    exploit_command.append(target)
            elif param['name'].startswith("port_"):
                device = param['name'].split("_", 1)[1]
                device_clean = re.sub(r'[^a-zA-Z0-9]', '', device)
                port = ports.get(device_clean)
                if port:  
                    if param['name_required']:
                        if param['parameter_connector'] != " ":
                            exploit_command.append(device + param['parameter_connector'] + port)
                        else:
                            exploit_command.append(device)
                            exploit_command.append(port)
                    else:
                        exploit_command.append(port)
            elif param['required']:
                self.logger.error("Parameter {} is required, but was not found in your command".format(param['name']))
                raise Exception("Parameter {} is required, but was not found in your command".format(param['name']))
        
        logging.info("SbleedyEngine.construct_exploit_command -> exploit_command list -> " + str(exploit_command))

        return exploit_command
        
    def run_test(self, target: str, ports: str, current_exploit: Exploit, parameters: list) -> None:
        new_directory = const.EXPLOIT_TOOL_DIRECTORY
        new_directory += current_exploit.directory

        exploit_command = self.construct_exploit_command(target, ports, current_exploit, parameters, new_directory)

        stop_spinner = False
        def spinner_task():
            spinner = self.spinning_cursor()
            while not stop_spinner:
                sys.stdout.write(next(spinner))  
                sys.stdout.flush()
                time.sleep(0.1)  
                sys.stdout.write('\b')
        spinner_thread = None

        if current_exploit.automated and not self.verbosity:
            spinner_thread = threading.Thread(target=spinner_task)
            spinner_thread.start()
        try:
            if_failed, data = self.execute_command(target, exploit_command, current_exploit, timeout=current_exploit.max_timeout, directory=new_directory)
        finally:
            if current_exploit.automated and not self.verbosity:
                stop_spinner = True
                spinner_thread.join()

        if current_exploit.type == "DoS":
            response_code, data = dos_checker(target)
        else:
            logging.info('SbleedyEngine.run_test -> data ' + str(data))
            response_code, data = self.process_raw_data(data, if_failed)

        return response_code, data
        
    def execute_command(self, target: str, exploit_command: list, exploit: Exploit, timeout: int, directory=None) -> tuple:
        os.chdir(directory)
        logging.info("SbleedyEngine.execute_command -> chdir to {}".format(directory))

        data = False, b''

        try:
            self.logger.info("Starting the next exploit - name {} and command {}".format(exploit.name, exploit_command))
            if self.verbosity or not exploit.automated:
                print("\n")
            with open(const.EXPLOIT_LOG_FILE.format(target=target), "w") as f:
                f.write(f"\n\nEXPLOIT: {exploit.name}\n")

                process = subprocess.Popen(exploit_command, stdout=subprocess.PIPE, text=True)
                start_time = time.time()
                output_bytes = b''

                while True:
                    if timeout != -1 and time.time() - start_time > timeout:
                        raise subprocess.TimeoutExpired(exploit_command, timeout)
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        output_bytes += output.strip().encode()
                        f.write(output.strip() +  "\n")
                        f.flush()
                        if self.verbosity or not exploit.automated:
                            print(output.strip())
                            sys.stdout.flush()
                
                process.wait()
                data = True, output_bytes
        except subprocess.TimeoutExpired as e:
            logging.info("SbleedyEngine.execute_command -> Killing the exploit due to timeout")
            if self.verbosity:
                print("[i] Timeout reached\n")
            process.terminate()
            process.kill()
            time.sleep(1)
            data = True, b"Timeout reached"
        except Exception as e:
            logging.error(f"Error in execute_command: {str(e)}")
            return False, str(e)
        finally:
            os.chdir(const.TOOL_DIRECTORY)
            logging.info("SbleedyEngine.execute_command -> data -> " + str(data))

        return data
    
    def process_raw_data(self, data, if_failed):
        #TODO: INEFFICIENTLY processes data line by line (there is room for improvement)
        keyword = b"SBLEEDY_GONZALES DATA"
        keyword_index = data.find(keyword)
        if keyword_index != -1:
            data = data[keyword_index:]
            newline_index = data.find(b' STOP')
            if newline_index != -1:
                data = data[:newline_index]
        try:
            mm = re.compile(const.REGEX_EXPLOIT_OUTPUT_DATA, re.DOTALL)
            output = mm.search(data)
            if output is None:
                return const.RETURN_CODE_NONE_OF_4_STATE_OBSERVED, "No result data returned from exploit"
            else:
                output = output.group()
            logging.info("SbleedyEngine.process_raw_data -> Found data from the exploit {}".format(output))
            
            mm2 = re.compile(const.REGEX_EXPLOIT_OUTPUT_DATA_CODE)
            mm3 = re.compile(const.REGEX_EXPLOIT_OUTPUT_DATA_DATA)
            
            output2 = int(mm2.search(output).group().rstrip(b",").split(b"=")[1])
            logging.info("SbleedyEngine.process_raw_data -> Found data from the exploit, code -> {}".format(output2))
            output3 = (mm3.search(output).group().split(b"=")[1]).decode()
            logging.info("SbleedyEngine.process_raw_data -> Found data from the exploit, data -> {}".format(output3))

            return int(output2), output3    
        except Exception as e:
            logging.info("SbleedyEngine.process_raw_data -> Error during extracting information from the regex " + str(e))
            return const.RETURN_CODE_NONE_OF_4_STATE_OBSERVED, "Error during extracting information from the regex (probably no SBLEEDY_GONZALES DATA found)"
        
    def process_additional_parameters(self, parameters: list) -> dict:
        logging.info("SbleedyEngine.process_additional_parameters -> list parameters " + str(parameters))
        param_dict = {}
        for i in range(0, len(parameters), 2):
            param_dict[parameters[i]] = parameters[i + 1] if i + 1 < len(parameters) else None
        return param_dict 

    def get_parameters_list(self, parameters: list) -> list:
        return [parameters[i] for i in range(0, len(parameters), 2)]
    
    def spinning_cursor(self):
        spinner = itertools.cycle(['|', '/', '-', '\\'])
        while True:
            yield next(spinner)