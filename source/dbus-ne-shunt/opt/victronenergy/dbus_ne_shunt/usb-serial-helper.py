#!/usr/bin/python3 -u
import os
import time
import sys

runFromPm = False
SERIAL_STARTER_RULE_PLACEHOLDER = "# ---neshunt action placeholder---"

def serial_starter_helper():
    # vendorId1 = 0x9876
    # productid1 = 0x1234
    # serialId1 = "1234567890"
    # _update_serial_starter_rules(vendorId1, productid1, serialId1)
    # exit(0)

    new_device = _find_usb_serial_device()
    if (new_device is None):
        _progress("No new USB device found.")
        return False
 
    _progress(f"Found new USB device: {new_device}")
    
    # Extract the bus and device number from the line
    parts = new_device.split()
    bus = parts[1]
    device = parts[3][:-1]  # Remove the trailing ':'

    command = f"lsusb -v -s {bus}:{device} | grep -e 'idVendor' -e 'idProduct' -e 'iSerial'"
    usbInfoLines = os.popen(command).read().strip().splitlines()

    vendorId = usbInfoLines[0].strip().split()[1]
    productId = usbInfoLines[1].strip().split()[1]
    serialId = usbInfoLines[2].strip().split()[2]
    if (serialId == None):
        _progress("No serial ID found for the device.")
        return False

    _update_serial_starter_rules(vendorId, productId, serialId)

    return True

def _find_usb_serial_device():

    before_usb_devices = os.popen("lsusb").read().strip().splitlines() 
    counter = 0
    timeout_counter = 0

    standardmsg = "Please connect the serial device (or remove and reconnect it) to the USB port."
    _progress(standardmsg)
    _progress("Waiting for USB device to be connected...")
 
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
            _progress(f"Timeout, exiting...")
            exit(1)

        updateMsg = (f"{standardmsg}\n" if runFromPm else "") + f"No new USB device detected, retrying{'.' * counter}  "
        _progress(updateMsg, end='\r') #end just for terminal output

def _update_serial_starter_rules(vendorId, productId, serialId):

    sta = f'ACTION=="add", ENV{{ID_BUS}}=="usb", ENV{{ID_VENDOR_ID}}=="{vendorId}", ENV{{ID_MODEL_ID}}=="{productId}", ENV{{ID_SERIAL_SHORT}}=="{serialId}", ENV{{VE_SERVICE}}="neshunt"'
 
    _progress("updating serial starter rules" + f":\n{sta}" if not runFromPm else "")
 
    # Read in the placeholder file
    with open(serial_starter_rules_basepath + ".placeholder", 'r') as file:
        rules = file.read()

    # Replace the placeholder string with our ACTION string
    rules = rules.replace(SERIAL_STARTER_RULE_PLACEHOLDER, sta)

    # Write the file out again
    with open(serial_starter_rules_basepath + ".edited", 'w') as file:
        file.write(rules)
    
    # create patch file
    os.popen(f"diff -u {serial_starter_rules_basepath}.orig {serial_starter_rules_basepath}.edited > {serial_starter_rules_basepath}.patch")

def _progress(msg, end='\n'):
    if runFromPm == 'True':
        os.popen(f"dbus -y com.victronenergy.packageManager /GuiEditStatus SetValue '{msg}'").read()
    else:
        print(msg, end=end)

if __name__ == "__main__":
    if len(sys.argv) == 3:
        print(sys.argv)
        
        # note arg 0 is the name of this script filename
        runFromPm = sys.argv[1]
        serial_starter_rules_basepath = sys.argv[2]
    else:
        print(sys.argv)
        print("invalid arguments passed, requires: arg1 runFromPm, arg2 is the path to the setup copy of the serial-starter.rules file")
        exit(1)

    serial_starter_helper()