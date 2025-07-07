#!/usr/bin/python3 -u

# helper class for detecting an added usb serial device
# called durin installation from the ipk installer (CONTROL/postinst)
#
import os
import time
import sys
 
serial_starter_ve_env_service_name = None
serial_starter_rule_file = None
dbus_message_path = None

SERIAL_STARTER_RULE_PLACEHOLDER = "# ---neshunt action placeholder---"

def _create_serial_starter_rule():
 
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
    usbInfoLines = os.popen(command).read().strip().splitlines()

    vendorId = usbInfoLines[0].strip().split()[1]
    productId = usbInfoLines[1].strip().split()[1]
    serialId = usbInfoLines[2].strip().split()[2]
    if (serialId == None):
        _progress("No serial ID found for the device.")
        return False

    usb_rule = "# {os.path.basename(os.path.dirname(__file__))}\n"
    usb_rule += f'ACTION=="add", ENV{{ID_BUS}}=="usb", ENV{{ID_VENDOR_ID}}=="{vendorId}", ENV{{ID_MODEL_ID}}=="{productId}", ENV{{ID_SERIAL_SHORT}}=="{serialId}", ENV{{VE_SERVICE}}="{serial_starter_ve_env_service_name}"'
 
    # save the rule to a file. which is used to add and uninstall the value
    with open(serial_starter_rule_file, 'w') as file:
        file.write(usb_rule)
 
    return True

def _detect_inserted_serial_usb_device():

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
 
def _progress(msg, end='\n'):
    if dbus_message_path:
        os.popen(f"dbus -y {dbus_message_path} SetValue '{msg}'").read()
 
    print(msg, end=end)

if __name__ == "__main__":
    if len(sys.argv) == 4:
        print(sys.argv)
 
        # note arg 0 is the name of this script filename
        serial_starter_ve_env_service_name = sys.argv[1]
        serial_starter_rule_file = sys.argv[2]
        dbus_message_path = sys.argv[3]
    else:
        print(sys.argv)
        print("Error invalid arguments passed. Requires:\narg 1 (string): The ve service environment name.\narg 2 (string): The path to store the rule text added to the serial-starter.rules file. Used to remove the value when uninstalling\narg 3 (string) The dbus path to optionaly send messages to. Can be an empty string if not using dbus")
        exit(1)

    if _create_serial_starter_rule :
        print("Serial starter rule successuly added to {serial_starter_rule_file}")
        exit(0)
    else:
        print("Usb device not found. Please manualy update {serial_starter_rule_file}")
        exit(1)
