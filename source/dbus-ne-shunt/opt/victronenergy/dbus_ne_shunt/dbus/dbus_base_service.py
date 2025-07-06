#!/usr/bin/env python3

"""
A class to put a simple service on the dbus, according to victron standards, with constantly updating
paths. See example usage below. It is used to generate dummy data for other processes that rely on the
dbus. See files in dbus_vebus_to_pvinverter/test and dbus_vrm/test for other usage examples.

To change a value while testing, without stopping your dummy script and changing its initial value, write
to the dummy data via the dbus. See example.

https://github.com/victronenergy/dbus_vebus_to_pvinverter/tree/master/test
"""

from gi.repository import GLib
import platform
import logging
import os
from dbus_constants import dbus_constants
from dbus_connection import dbusconnection
from ext.vedbus import VeDbusService

class dbus_base_service(object):
 
    # Create the mandatory objects
    def unregister(self):
        """
        Unregister the dbus service.
        """
        if self._dbusservice:
            self._dbusservice.__del__()
            self._dbusservice = None
            logging.debug("Unregistered %s" % (self._dbusservice))
        else:
            logging.debug("No dbus service to unregister")
            
    def _registerCore(self, port, serviceType, paths, deviceName = 0, onvalueChanged = None):
        
        logging.debug("_registerCore in")

        portName = os.path.basename(port)
        serviceName = "{}.{}.{}_id_{}.{}".format(dbus_constants.BASE_DBUS_NAME,
                                              serviceType, dbus_constants.PRODUCT_NAME, deviceinstance, portName)
        
        self._dbusservice = VeDbusService(serviceName, bus=dbusconnection(), register=False)
        self._paths = paths
        self._dbusservice
        logging.debug("%s /DeviceInstance = %d" % (serviceName, deviceinstance))

        # Create the management objects, as specified in the ccgx dbus-api document
        
        self._dbusservice.add_path('/Mgmt/ProcessName', __file__)
        self._dbusservice.add_path('/Mgmt/ProcessVersion', 'Unkown version, and running on Python ' + platform.python_version())
        self._dbusservice.add_path('/Mgmt/Connection', portName)

        self._dbusservice.add_path('/DeviceInstance', deviceinstance)
        self._dbusservice.add_path('/ProductId', dbus_constants.PRODUCT_ID)
        self._dbusservice.add_path('/ProductName', dbus_constants.PRODUCT_NAME)
        self._dbusservice.add_path('/FirmwareVersion', dbus_constants.FIRMWARE_VERSION)
        self._dbusservice.add_path('/HardwareVersion', dbus_constants.HARDWARE_VERSION)
        self._dbusservice.add_path('/Connected', 1, writeable=True)
 
        for path, settings in self._paths.items():
            self._dbusservice.add_path(
                path, 
                value = settings[dbus_constants.PATH_SETTING_INITIAL],
                writeable = settings[dbus_constants.PATH_SETTING_WRITABLE], 
                onchangecallback = onvalueChanged)
        
        self._dbusservice.register()
        

    def get_value(self, path):
        """
        Get the value of a path.
        """
        with self._dbusservice as s:
            return s[path]
    
    
    def set_value(self, path, value):
        """
        Set the value of a path.
        """
        with self._dbusservice as s:
            s[path] = value
            logging.debug("Set %s to %s" % (path, value))
        return True
 

