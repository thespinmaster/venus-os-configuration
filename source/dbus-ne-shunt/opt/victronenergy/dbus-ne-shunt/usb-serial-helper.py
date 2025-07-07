#!/usr/bin/python3 -u

# helper class for detecting an added usb serial device
# called durin installation from the ipk installer (CONTROL/postinst)

import os
import time
import sys
 
_serialStarterVeEnvServiceName = None
_serialStarterRuleFile = None
_dbusMessagePath = None

SERIAL_STARTER_RULE_PLACEHOLDER = "# ---neshunt action placeholder---"

def _createSerialStarterRule():
 
    newDevice = _detectInsertedSerialUsbDevice()
    if (newDevice is None):
        _progress("No new USB device found.")
        return False
 
    _progress(f"Found new USB device: {newDevice}")
    
    # Extract the bus and device number from the line
    parts = newDevice.split()
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

    usbRule = f"# {os.path.basename(os.path.dirname(__file__))}\n"
    usbRule += f'ACTION=="add", ENV{{ID_BUS}}=="usb", ENV{{ID_VENDOR_ID}}=="{vendorId}", ENV{{ID_MODEL_ID}}=="{productId}", ENV{{ID_SERIAL_SHORT}}=="{serialId}", ENV{{VE_SERVICE}}="{_serialStarterVeEnvServiceName}"'
 
    # save the rule to a file. which is used to add and uninstall the value
    with open(_serialStarterRuleFile, 'w') as file:
        file.write(usbRule)
 
    return True

def _detectInsertedSerialUsbDevice():

    beforeUsbDevices = os.popen("lsusb").read().strip().splitlines() 
    counter = 0
    timeoutCounter = 0

    progressHeaderMsg = "Please connect the serial device (or remove and reconnect it) to the USB port."
    _progress(progressHeaderMsg)
    _progress("Waiting for USB device to be connected...")
 
    while True:
        # Wait for the device to be connected 
        time.sleep(1)
        afterUsbDevices = os.popen("lsusb").read().strip().splitlines() 
 
        if len(afterUsbDevices) == (len(beforeUsbDevices) + 1):
            for line in afterUsbDevices:
                if line not in beforeUsbDevices:
                    return line
            break
        else:
            beforeUsbDevices = afterUsbDevices

        counter += 1
        if counter > 3: counter = 1

        timeoutCounter += 1
        if timeoutCounter > 60: 
            _progress(f"Timeout, exiting...")
            return False

        updateMsg = f"No new USB device detected, retrying{'.' * counter}  "
 
        _progress(updateMsg, f"{progressHeaderMsg}\n{updateMsg}", end='\r') #end just for terminal output
 
def _progress(msg, dbusMsg = None, end='\n'):
 
    if _dbusMessagePath:
        if dbusMsg is None:
            dbusMsg = msg

        os.popen(f"dbus -y {_dbusMessagePath} SetValue '{dbusMsg}'").read()
 
    print(msg, end=end)

if __name__ == "__main__":
    if len(sys.argv) == 4:
        print(sys.argv)
 
        # note arg 0 is the name of this script filename
        _serialStarterVeEnvServiceName = sys.argv[1]
        _serialStarterRuleFile = sys.argv[2]
        _dbusMessagePath = sys.argv[3]
    else:
        print(sys.argv)
        print("Error invalid arguments passed. Requires:\narg 1 (string): The ve service environment name.\narg 2 (string): The path to store the rule text added to the serial-starter.rules file. Used to remove the value when uninstalling\narg 3 (string) The dbus path to optionaly send messages to. Can be an empty string if not using dbus")
        exit(1)

    if _createSerialStarterRule() :
        print(f"Serial starter rule successuly added to {_serialStarterRuleFile}")
        exit(0)
    else:
        print(f"Usb device not found. Please manualy update {_serialStarterRuleFile}")
        exit(1)
