#!/usr/bin/python3 -u

# helper class for detecting an added usb serial device
# called durin installation from the ipk installer (CONTROL/postinst)

import os
import time
import sys
 
_dbus_message_path = None

SERIAL_STARTER_RULES_TEXT_MATCH='RUN+="/opt/victronenergy/serial-starter/cleanup.sh %k"'

def _create_serial_starter_rule(serial_starter_rule_file, service_name, serial_starter_config_mapping_name):
 
    new_device = _detect_inserted_serial_usb_device()
    if (new_device is None):
        _progress("No new USB device found.")
        return False
 
    _progress(f"Found new USB device: {new_device}")
    
    # Extract the bus and device number from the line
    parts = new_device.split()
    bus = parts[1]
    device = parts[3][:-1]  # Remove the trailing ':'

    command = f"lsusb -v -s {bus}:{device} | grep -e 'idVendor' -e 'idProduct' -e 'iSerial'"
    usb_info_lines = os.popen(command).read().strip().splitlines()

    vendor_id = usb_info_lines[0].strip().split()[1]
    product_id = usb_info_lines[1].strip().split()[1]
    serial_id = usb_info_lines[2].strip().split()[2]
    if (serial_id == None):
        _progress("No serial ID found for the device.")
        return False

    usb_rule = f"# {service_name}\n"
    usb_rule += f'ACTION=="add", ENV{{ID_BUS}}=="usb", ENV{{ID_VENDOR_ID}}=="{vendor_id}", ENV{{ID_MODEL_ID}}=="{product_id}", ENV{{ID_SERIAL_SHORT}}=="{serial_id}", ENV{{VE_SERVICE}}="{serial_starter_config_mapping_name}"'
 
    # save the rule to a file. which is used to add and uninstall the value
 
    with open(serial_starter_rule_file, 'w') as file:
        file.write(usb_rule)
 
    return True

def _detect_inserted_serial_usb_device():
 
    counter = 0
    timeout_counter = 0

    progress_header_msg = "Please connect the serial device (or remove and reconnect it) to the USB port."
    _progress(progress_header_msg)
    _progress("Waiting for USB device to be connected...")
 
    before_usb_devices = os.popen("lsusb").read().strip().splitlines() 
    while True:
        # Wait for the device to be connected 
        time.sleep(1)
        after_usb_devices = os.popen("lsusb").read().strip().splitlines() 
 
        if len(after_usb_devices) == (len(before_usb_devices) + 1):
            for line in after_usb_devices:
                if line not in before_usb_devices:
                    return line
            break
        else:
            before_usb_devices = after_usb_devices

        counter += 1
        if counter > 3: counter = 1

        timeout_counter += 1
        if timeout_counter > 60: 
            _progress("Timeout, exiting...")
            return False

        update_msg = f"No new USB device detected, retrying{'.' * counter}  "
 
        _progress(update_msg, f"{progress_header_msg}\n{update_msg}", end='\r') #end just for terminal output
 
def _progress(msg, dbusMsg = None, end='\n'):
 
    if _dbus_message_path:
        if dbusMsg is None:
            dbusMsg = msg

        command = f"dbus-send --system --print-reply --dest={_dbus_message_path} com.victronenergy.BusItem.SetValue variant:string:{dbusMsg}"

        os.popen(command).read()
 
    print(msg, end=end)

def _remove_string_with_newline_variants(source, string_to_remove):
    source_len = len(source)
    source = source.replace("\n" + string_to_remove + "\n")
    if (len(source) < source_len):
        return source
    source = source.replace("\n" + string_to_remove)
    if (len(source) < source_len):
        return source
    source = source.replace(string_to_remove + "\n")
    if (len(source) < source_len):
        return source
    source = source.replace(string_to_remove)
    if (len(source) < source_len):
        return source

def _do_serial_starter_rule_files_exist(serial_starter_rules_file, serial_starter_rule_file):
    
    if not os.path.exists(serial_starter_rules_file):
        print(f"Error: {serial_starter_rules_file} does not exist.")
        return False

    if not os.path.exists(serial_starter_rule_file):
        print(f"Error: {serial_starter_rule_file} does not exist.")
        return False

    return True

def _add_rule_to_serial_starter_rules_file(serial_starter_rules_file, serial_starter_rule_file):
 
    if (not _do_serial_starter_rule_files_exist()):
        return
        
    with open(serial_starter_rules_file, 'r') as file:
        rules = file.readlines()

    with open(serial_starter_rule_file, 'r') as file:
        rule = file.readlines()

    # Check if the rule already exists (for multi-line, check if all lines are present in order)
    rule_lines = [line.rstrip('\n') for line in rule.splitlines() if line.strip()]
    rules_str = ''.join([line.rstrip('\n') for line in rules])
 
    if ''.join(rule_lines) in rules_str:
        print("Rule already exists in the file.")
        return True
 
    # Check if the rule already exists
    for line in rules:
        if rule in line:
            print("Rule already exists in the file.")
            return True

    # Add the new rule before the placeholder
    print("Adding new rule to serial starter rules file...")
    found = False
 
    for i, line in enumerate(rules):
        line = line.strip()
        if line.endswith(SERIAL_STARTER_RULES_TEXT_MATCH):
            rules.insert(i+1, "\n" + rule + "\n")
            found = True
            break
 
    if not found:
        return False
    
    with open(serial_starter_rule_file, 'w') as file:
        file.writelines(rules)

    print("Rule added successfully.")
    return True
 
def _remove_rule_from_serial_starter_rules_file(serial_starter_rules_file, serial_starter_rule_file):

    if (not _do_serial_starter_rule_files_exist()):
        return
        
    with open(serial_starter_rules_file, 'r') as file:
        rules = file.readlines()

    with open(serial_starter_rule_file, 'r') as file:
        rule = file.readlines()

    rules_len = len(rules)  
    rules = _remove_string_with_newline_variants(rules, rule)
    if (len(rules) < rules_len)

    with open(serial_starter_rules_file, 'w') as file:
        file.write(rules)


if __name__ == "__main__":

    print(sys.argv)
    if len(sys.argv) >= 4:
        action = sys.argv[1]
        serial_starter_rules_file = sys.argv[2]
        #_serialStarterRuleFile = sys.argv[2]
        serial_tarter_config_mapping_name = sys.argv[3]
        if len(sys.argv) >= 4:
            _dbusMessagePath = sys.argv[4]
    else:
        print("Error invalid arguments passed. Requires:\narg 1 (string): The path to the serial-starter.rules file\narg 2 (string): The path to store the rule to be added to or removed from the serial-starter.rules file.\narg 3 (string): The ve service environment name.\narg 4 (string) The dbus path to optionaly send messages to. Can be an empty string if not using dbus")
        exit(1)
        return
    #
    
    service_path = os.path.dirname(__file__)
    service_name = os.path.basename(service_path)
    serial_starter_rule_file = os.path.join(service_path, "serial-starter.rule")
 
    if (action == "detect" | action == "detect+add"): 
        if (not _create_serial_starter_rule(serial_starter_rule_file, service_name, serial_tarter_config_mapping_name)):
            print(f"Usb device not found. Please manualy update {serial_starter_rule_file}")
            exit(1) 
            return

    if (action == "add" | action == "detect+add" ):
        if _add_rule_to_serial_starter_rules_file(serial_starter_rules_file, serial_starter_rule_file):
            exit(0)
            return
        else:
            print(f"Cound not update {serial_starter_rules_file}. Please manualy update")
            
    elif (action == "remove" | action == "detect+add" ):
        if _remove_rule_from_serial_tarter_rules_file(serial_starter_rules_file, serial_starter_rule_file):
            exit(0)
            return
        else:
            print(f"Warning: Could not remove rule from {serial_starter_rules_file}. Please manualy update")
 
    exit(1)
