import json
import logging
import re
import os
from tabulate import tabulate
from colorama import Fore, Back, Style, init
from pathlib import Path
from rich.table import Table
from rich import box
from rich.console import Console

import sbleedyCLI.constants as const
from sbleedyCLI.recon import get_device_info
from sbleedyCLI.engines.exploitEngine import ExploitEngine

REPORT_OUTPUT_FILE = os.path.join(const.OUTPUT_DIRECTORY, "{exploit}.json")
CLEAN_EXPLOIT_NAME = ""

def report_data(code, data):
    logging.info("SBLEEDY_GONZALES DATA: code={code}, data={data}".format(code=code, data=data))
    print("SBLEEDY_GONZALES DATA: code={code}, data={data}".format(code=code, data=data))

def report_not_vulnerable(data):
    report_data(const.RETURN_CODE_NOT_VULNERABLE, data)

def report_vulnerable(data):
    report_data(const.RETURN_CODE_VULNERABLE, data)

def report_none_of_4_state_observed(data):
    report_data(const.RETURN_CODE_NONE_OF_4_STATE_OBSERVED, data)

def report_error(data):
    report_data(const.RETURN_CODE_ERROR, data)

def report_undefined(data):
    report_data(const.RETURN_CODE_UNDEFINED, data)

class Report:
    def __init__(self):
        self.exploitEngine = ExploitEngine()

    def save_data(self, exploit, target, data, code):
        exploit_name = exploit.name
        doc = {
            "code": code,
            "data": data,
            "cve": exploit.cve 
        }
        logging.info("Report - save_data -> document -> " + str(doc))

        jsonfile = open(REPORT_OUTPUT_FILE.format(target=target, exploit=exploit_name), 'w')
        json.dump(doc, jsonfile, indent=6)
        jsonfile.close()

    def read_data(self, exploit_name, target):
        logging.info("Loading report output data")
        path = REPORT_OUTPUT_FILE.format(target=target, exploit=exploit_name)
        if Path(path).exists():
            jsonfile = open(REPORT_OUTPUT_FILE.format(target=target, exploit=exploit_name),)
            doc = json.load(jsonfile)
            logging.info("Report output data is loaded")
            logging.info("Report - read_data -> document -> " + str(doc))
            return doc["code"], doc["data"], doc["cve"]
        return None, None, None

    def get_done_exploits(self, target):
        path = Path(const.OUTPUT_DIRECTORY.format(target=target))
        exploits = [entry.stem for entry in path.iterdir() if entry.is_file() and entry.suffix == '.json' and not entry.stem.startswith(('.checkpoint', 'whole_report')) and entry.stem not in const.SKIP_DIRECTORIES]
        logging.info("Extracted following completed exploits: " + str(exploits))
        return exploits

    def generate_report(self, target):
        done_exploits = self.get_done_exploits(target=target)
        all_exploits = self.exploitEngine.get_all_exploits()
        skipped_exploits = [exploit.name for exploit in all_exploits if exploit.name not in done_exploits]

        logging.info("Report.generate_report -> done_exploits = " + str(done_exploits))
        logging.info("Report.generate_report -> all_exploits = " + str(all_exploits))
        logging.info("Report.generate_report -> skipped_exploits = " + str(skipped_exploits))

        headers = ['Exploit', 'Result', 'Data', 'CVE']
        sorted_done_exploits = sorted(done_exploits, key=lambda x: x[2])

        print("\n")
        table = Table(title="Exploit Report", padding=[0,1,1,1])

        for header in headers:
            table.add_column(header, justify="center")

        for exploit in sorted_done_exploits:
            code, data, cve = self.read_data(exploit_name=exploit, target=target)
            if code is None:
                code = const.RETURN_CODE_NONE_OF_4_STATE_OBSERVED
                data = "Error during loading the report"
            logging.info("data - " + str(data))
            if data is None:
                data = "Error with data"
            symbol = ''
            if code == const.RETURN_CODE_VULNERABLE:
                symbol = '❗'
            elif code == const.RETURN_CODE_ERROR or code == const.RETURN_CODE_NONE_OF_4_STATE_OBSERVED:
                symbol = '⚠'
            
            if code == const.RETURN_CODE_VULNERABLE:
                table.add_row(f"[red]{exploit}[/red]", f"[red]Vulnerable {symbol}[/red]", data[:const.MAX_CHARS_DATA_TRUNCATION], cve)
            elif code == const.RETURN_CODE_NOT_VULNERABLE:
                table.add_row(f"[green]{exploit}[/green]", f"[green]Not vulnerable {symbol}[/green]", data[:const.MAX_CHARS_DATA_TRUNCATION], cve)
            elif code == const.RETURN_CODE_ERROR:
                table.add_row(f"[yellow]{exploit}[/yellow]", f"[yellow]Error {symbol}[/yellow]", data[:const.MAX_CHARS_DATA_TRUNCATION], cve)
            elif code == const.RETURN_CODE_UNDEFINED:
                table.add_row(f"[white]{exploit}[/white]", f"[white]Undefined {symbol}[/white]", data[:const.MAX_CHARS_DATA_TRUNCATION], cve)
            elif code == const.RETURN_CODE_NONE_OF_4_STATE_OBSERVED:
                table.add_row(f"[yellow]{exploit}[/yellow]", f"[yellow]Toolkit error {symbol}[/yellow]", data[:const.MAX_CHARS_DATA_TRUNCATION], cve)
            else:
                table.add_row(f"[yellow]{exploit}[/yellow]", f"[yellow]Toolkit error during report generation {symbol}[/yellow]", data[:const.MAX_CHARS_DATA_TRUNCATION], cve)

        for skipped_exploit in skipped_exploits:
            table.add_row(f"[white]{skipped_exploit}[/white]", "[white]Not tested[/white]", "", "")

        logging.info("Report.generate_report -> table_data created")

        console = Console()
        console.print(table)

    def generate_machine_readable_report(self, target):
        done_exploits = self.get_done_exploits(target=target)
        all_exploits = self.exploitEngine.get_all_exploits()
        skipped_exploits = [exploit.name for exploit in all_exploits if exploit.name not in done_exploits]

        logging.info("Report.generate_report -> done_exploits = " + str(done_exploits))
        logging.info("Report.generate_report -> all_exploits = " + str(all_exploits))
        logging.info("Report.generate_report -> skipped_exploits = " + str(skipped_exploits))

        sorted_done_exploits = sorted(done_exploits, key=lambda x: x[2])

        output_json = {}
        sorted_done_exploits_json = []
        skipped_exploits_json = []
        for exploit in sorted_done_exploits:
            code, data, cve = self.read_data(exploit_name=exploit, target=target)
            if code is None:
                code = const.RETURN_CODE_NONE_OF_4_STATE_OBSERVED
                data = "Error during loading the report"
            logging.info("data - " + str(data))
            sorted_done_exploits_json.append({
                "name":exploit,
                "code": code,
                "data": data,
                "cve": cve 
            })
        for skipped_exploit in skipped_exploits:
            skipped_exploits_json.append({
                "name": skipped_exploit,
                "code": 6,
                "data": "Not tested",
                "cve": ""
            })
        
        output_json["done_exploits"] = sorted_done_exploits_json
        output_json["skipped_exploits"] = skipped_exploits_json
        output_json['manually_added_exploits'] = list()
        output_json['mac_address'] = target
        
        version, profile, manufacturer = get_device_info(target)
        output_json["bt_version"] = version
        output_json["bt_profile"] = profile
        output_json['manufacturer'] = manufacturer
        
        jsonfile = open(const.MACHINE_READABLE_REPORT_OUTPUT_FILE.format(target=target), 'w')
        json.dump(output_json, jsonfile, indent=6)
        jsonfile.close()
        
        print(f"\nReport saved to {jsonfile.name}")

if __name__ == "__main__":
    pass 


