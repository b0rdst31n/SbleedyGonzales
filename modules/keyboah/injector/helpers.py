import logging
import re
import subprocess
import sys

class Log:
  def status(self, msg):
    print(msg)
  def success(self, msg):
    print(msg)
  def error(self, msg):
    print(msg)
  def debug(self, msg):
    print(msg)
  def notice(self, msg):
    print(msg)
  def info(self, msg):
    print(msg)
    
log = Log()

def run(command):
  assert(isinstance(command, list))
  log.debug("executing '%s'" % " ".join(command))
  return subprocess.check_output(command, stderr=subprocess.PIPE)

def assert_address(addr):
  if not re.match(r"^([a-fA-F0-9]{2}:{0,1}){5}[a-fA-F0-9]{2}$", addr):
    log.error("Error! This not look like a Bluetooth address: '%s'" % addr)
    sys.exit(1)
