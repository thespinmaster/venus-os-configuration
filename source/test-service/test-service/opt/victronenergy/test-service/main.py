#!/usr/bin/python3 -u

from gi.repository import GLib
import time
import logging
from argparse import ArgumentParser
log = logging.getLogger()


class test_service:
 
    ############################################
    # constructor 
    # serial port is passed from the SerialStarter 
    # service. i.e. /dev/ttyACM0
    ############################################
    def __init__(self, serialPort):
        self._serialPort = serialPort

    def initialize():
        pass

    def mainloop():
        import datetime, timezone
        utc_time = datetime.now(timezone.utc)
        print(utc_time.now(timezone.utc) +  ":hello from test-service")

def main():

    parser = ArgumentParser(description='test-service', add_help=True)
    parser.add_argument('-d', '--debug', help='enable debug logging',
                        action='store_true')
    parser.add_argument('-s', '--serial', help='tty')

    args = parser.parse_args()
    if not args.serial:
        log.error('No serial port specified, see -h')
        exit(1)

    logging.basicConfig(format='%(levelname)-8s %(message)s',
                        level=(logging.DEBUG if args.debug else logging.INFO))

    log.info('Serial port arg:' + args.serial)
 
    from dbus.mainloop.glib import DBusGMainLoop
    # Have a mainloop, so we can send/receive asynchronous calls to and from dbus
    DBusGMainLoop(set_as_default=True)
 
    ts = test_service(args.serial)
    ts.initialize()
    
    time.sleep(1)

    ONE_MINUTE = 60000    
    GLib.timeout_add(ONE_MINUTE, ts.mainloop)

    log.info('Connected to dbus, and switching over to GLib.MainLoop() (= event based)')
 
    mainloop = GLib.MainLoop()
    mainloop.run()

if __name__ == "__main__":
    main()
