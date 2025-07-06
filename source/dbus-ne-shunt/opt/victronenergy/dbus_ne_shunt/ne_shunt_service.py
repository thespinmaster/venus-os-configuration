import sys
import os
import logging

sys.path.append(os.path.join(os.path.dirname(__file__), 'ext'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'dbus'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'serial')) 

from dbus.switch_service import switch_service
from dbus.tank_service import tank_service
from dbus.battery_service import battery_service
from dbus.dbus_constants import dbus_constants
from dbus.dbus_connection import dbusconnection
from ext.settingsdevice import SettingsDevice  # available in the velib_python repository

from serial.ne_shunt_serial_service import ne_shunt_serial_service
from serial.ne_shunt_data import ne_shunt_data

############################################
# manages the reading and writing of data
# between the dbus and the serial device (ne-shunt)
############################################
class ne_shunt_service:

    _serialService = None
    _curData = None
    _serialPort = None
    _inUpdate = False
    _settingsPath = None
    
    ############################################
    # constructor 
    # serial port is passed from the SerialStarter 
    # service. i.e. /dev/ttyACM0
    ############################################
    def __init__(self, serialPort):
        self._serialPort = serialPort

    ############################################
    # Starts and stops the serial service as 
    # required
    ############################################
    def _start_stop_serial_service(self):
        logging.debug('_start_stop_serial_service')

        #state 0 (nothing running ... so close)
        if (self._serialService and len(self._services) == 0): 
            self._serialService.close()
            self._serialService = None

        if (self._serialService == None and len(self._services) > 0):
            self._serialService = ne_shunt_rs485_SerialService(self._serialPort)
 
    ############################################
    # Occurs when the a device setting value is 
    # changed such as ShowControls
    ############################################
    def _handle_changed_setting(self, setting, oldvalue, newvalue):
        logging.debug('setting changed, setting: %s, old: %s, new: %s' % (setting, oldvalue, newvalue))

        self._start_stop_services(setting, newvalue)
        return True
    
    ############################################
    # Initializes the dbus device settings
    # Needs custom UI
    ############################################ 
    def _initializeSettings(self):

        logging.debug("Initializing settings")
        
        # unique path used to generate unique ClassAndVrmInstance value 
        # see https://github.com/victronenergy/localsettings#using-addsetting-to-allocate-a-vrm-device-instance
        settingsPath = f'{dbus_constants.SETTINGS_PATH}_{self._serialPort}'

        self._settings = SettingsDevice(
            bus = dbusconnection(),
            supportedSettings = {
                'ShowFreshWaterTank': [f'{settingsPath}/ShowFreshWaterTank', 1, 0, 1],
                'ShowGreyWasteTank': [f'{settingsPath}/ShowGreyWasteTank', 1, 0, 1],  # When empty, default path will be used.
                'ShowGreyWasteTank2': [f'{settingsPath}/ShowGreyWasteTank2', 1, 0, 1],
                'ShowInternalLightSwitch': [f'{settingsPath}/ShowInternalLightSwitch', 1, 0, 1],
                'ShowExternalLightSwitch': [f'{settingsPath}/ShowExternalLightSwitch', 1, 0, 1],
                'ShowWaterPumpSwitch': [f'{settingsPath}/ShowWaterPumpSwitch', 1, 0, 1],
                'ShowAuxSwitch': [f'{settingsPath}/ShowAuxSwitch', 1, 0, 1],
                'FreshWaterTank_ClassAndVrmInstance' : [f'{settingsPath}_fresh_water_tank/ClassAndVrmInstance', 
                                                    "{SERVICE_TYPE_TANK}:{DEFAULT_DEVICE_INSTANCE}", 0, 0],
                'GreyWasteTank_ClassAndVrmInstance' : [f'{settingsPath}_grey_waste_tank/ClassAndVrmInstance', 
                                                    "{SERVICE_TYPE_TANK}:{DEFAULT_DEVICE_INSTANCE}", 0, 0],
                'GreyWasteTank2_ClassAndVrmInstance' : [f'{settingsPath}_grey_waste_tank_2/ClassAndVrmInstance', 
                                                    "{SERVICE_TYPE_TANK}:{DEFAULT_DEVICE_INSTANCE}", 0, 0],
                'CabBattery_ClassAndVrmInstance' : [f'{settingsPath}_cab_battery/ClassAndVrmInstance', 
                                                    "{SERVICE_TYPE_BATTERY}}:{DEFAULT_DEVICE_INSTANCE}", 0, 0],
                'Switches_ClassAndVrmInstance' : [f'{settingsPath}_switches/ClassAndVrmInstance', 
                                                    "{SERVICE_TYPE_SWITCH}}:{DEFAULT_DEVICE_INSTANCE}", 0, 0]
                },
            eventCallback = self._handle_changed_setting)
    
    ############################################
    # Occurs when a switch is toggled in the UI
    ############################################
    def _dbus_switch_value_changed(self, path, newvalue):

        logging.debug('dbus value changed, path: %s, newvalue: %s' % (path, newvalue))
        if (self._serialService == None or self._curData == None):
            return False
        
        if (path == '/SwitchableOutput/ExternalLights/State'):    
            self._try_toggle_serial_switch_value("ExternalLights", newvalue)
        elif (path == "/SwitchableOutput/InternalLights/State"):
            self._try_toggle_serial_switch_value("InternalLights", newvalue)
        elif (path == "/SwitchableOutput/WaterPump/State" ):
            self._try_toggle_serial_switch_value("WaterPump", newvalue)
        elif (path == "/SwitchableOutput/Aux/State" ):
            self._try_toggle_serial_switch_value("Aux", newvalue)

        return True
    
    ############################################
    # if the value recieved has changed it
    # sends the toggle switch serial message to
    # the pysical device
    ############################################
    def _try_toggle_serial_switch_value(self, name, newvalue):

        try:
            if not (newvalue == 1 or newvalue == 0):
                logging.debug('_try_toggle_serial_switch_value: invalid value. value must be 0 or 1 for ' + name)
                return False

            logging.debug('getting current value for ' + name)
            curValue = self._curData.get_value(name)
            logging.debug(f"{name}: curValue = {str(curValue)}")
            if (curValue != newvalue):
                logging.debug(f"value changed, toggle {name} switch")
                return self._serialService.toggle_switch(name)
        
        except Exception as ex:
            logging.error("Error in _try_change_value %s" % (ex))

        return False
    
    ############################################ 
    # starts and stops the dbus tank service
    # There can be upto 3 three tanks. 
    # FreshWater, GreyWaste1 and GreyWaste2
    ############################################ 
    def _start_stop_tank_service(self, name, createcallback):
        logging.debug(f"_start_stop_tank_service: {name}")
        service = self._services.get(name, None)
        
        if (self._settings['Show' + name] == 1):
            if (service is None):
                logging.debug(f"_start_stop_tank_service: {name} creating")
                service = createcallback()
                self._services[name] = service
            else:
                logging.debug(f"_start_stop_tank_service: {name} already running")
        elif (service):
            logging.debug(f"_start_stop_tank_service: {name} removing")
            self._services.pop(name)
            service.unregister()

    ############################################ 
    # starts and stops the dbus switch service
    # The nord electornics 194 has 4 service 
    # switches. Aux, Water Pump, Internal Lights & 
    # External Lights
    ############################################ 
    def _start_stop_switch_service(self):
        logging.debug("_start_stop_switch_service in")

        service = self._services.get("switches", None)
        if service:
            logging.debug("_start_stop_switch_service: unregister")
            service.unregister()
            service = None
            self._services.pop("switches")
        else:
            logging.debug("_start_stop_switch_service: Not running")


        switches = []
        #if (switches.ShowUIControl("InternalLights") == 1):
        switches.append("Internal Lights")

        #if (switches.ShowUIControl("ExternalLights") == 1):
        switches.append("External Lights")

        #if (switches.ShowUIControl("WaterPump") == 1):
        switches.append("Water Pump")
            
        #if (switches.ShowUIControl("Aux") == 1):
        switches.append("Aux")

        if len(switches) != 0:
            logging.debug("_start_stop_switch_service: starting")
            
            deviceInstance = self._settings['Switches_ClassAndVrmInstance']
            self._services["switches"] = switch_service(
                                            "Electrics", 
                                            self._serialPort, 
                                            switches,
                                            deviceInstance,
                                            onvaluechanged = self._dbus_switch_value_changed)
    
    ############################################
    # Starts the dbus vehicle battery service
    # the ne shunt also has a leisure battery 
    # but this is not likely needed in Victron
    # setup
    ############################################
    def _start_vehicle_battery_service(self):
        logging.debug("_start_vehicle_battery_service in")
        service = self._services.get("vehicle_battery", None)
        if (service == None):
            deviceInstance = self._settings['CabBattery_ClassAndVrmInstance']
            self._services["vehicle_battery"] = battery_service("Vehicle Battery",
                                                        self._serialPort,
                                                        deviceInstance,
                                                        capacity = None)
            
    ############################################
    # starts and stops all services 
    # note: only starts the vehicle battery service
    ############################################
    def _start_stop_services(self, name = ""):
        if (name == "" or name.endswith("FreshWaterTank")):
            deviceInstance = self._settings['FreshWaterTank_ClassAndVrmInstance']
            self._start_stop_tank_service("FreshWaterTank", 
                                        createcallback=lambda: tank_service("Fresh Water", 
                                        self._serialPort,
                                        dbus_constants.FLUID_TYPE_FRESH_WATER, 
                                        deviceInstance, 0.1))
            
        if (name == "" or name.endswith("GreyWasteTank")):
            deviceInstance = self._settings['GreyWasteTank_ClassAndVrmInstance']
            self._start_stop_tank_service("GreyWasteTank", 
                                        createcallback=lambda: tank_service("Grey Waste", 
                                        self._serialPort,
                                        dbus_constants.FLUID_TYPE_WindASTE_WATER, 
                                        deviceInstance, 0.1))
        
        if (name == "" or name.endswith("GreyWasteTank2")):
            deviceInstance = self._settings['GreyWasteTank2_ClassAndVrmInstance']
            self._start_stop_tank_service("GreyWasteTank2", 
                                        createcallback=lambda: tank_service("Grey Waste 2", 
                                        self._serialPort,
                                        dbus_constants.FLUID_TYPE_WASTE_WATER, 
                                        deviceInstance,0.1))
        
        if (name == "" or name.endswith("Switch")):
            self._start_stop_switch_service()

        if (name == "" or name.endswith("")):
            self._start_vehicle_battery_service()

        # start stop the serial service as required.
        self._start_stop_serial_service()

    ############################################
    # initial setup of services and settings
    ############################################
    def initialize(self):
        
        self._services = dict()
        self._initializeSettings()
 
        self._start_stop_services()

    ############################################
    # updates a dbus service value from the 
    # passed physical device value
    ############################################
    def update_dbus_item(self, serviceName, servicePath, newValue):
        logging.debug("update_dbus_item in")

        dbus_service = self._services.get(serviceName, None)
        if dbus_service:
            logging.debug(f"update_dbus_item set_value: {servicePath}/newValue = {newValue}")
            dbus_service.set_value(servicePath, newValue)
 
        else:
            logging.debug(f"update_dbus_item: serviceName = None ({serviceName})" )
        
        logging.debug("update_dbus_item out")

    ############################################
    # reads the 485 serial data from from the
    # ne-shunt and passes any changed values
    # to the dbus
    # returns True to continue
    # calling code should call this code continualy
    # for example: GLib.timeout_add(1000, nuss._update)
    ############################################
    def _update(self):
        logging.debug("_update in")
 
        if (self._serialService == None):
            return True
 
        data = self._serialService.read_data()
        if not data:
            logging.debug("_update out: no data returned")
            return True
        
        logging.debug("_update out: parsing new data for changes")
        newData = ne_shunt_data(data)

        #copy curData so we can update _curData and we don't get
        # recursive updates from update_item
        curData = self._curData.clone() if self._curData else None
 
        self._curData = newData

        for key, value in newData.diff(curData):
            
            logging.debug(f"_update diff value: {key} = {value}")

        match key:
            case 'fresh_water_tank':
                self.update_dbus_item("FreshWaterTank", "/Level", value)
            case 'grey_waste_tank':
                self.update_dbus_item("GreyWasteTank", "/Level", value)
            case 'grey_waste_tank2':
                self.update_dbus_item("GreyWasteTank2", "/Level", value)
            case 'ExternalLights':
                self.update_dbus_item("switches", "/SwitchableOutput/ExternalLights/State", value)
            case 'InternalLights':
                self.update_dbus_item("switches", "/SwitchableOutput/InternalLights/State", value)
            case 'WaterPump':
                self.update_dbus_item("switches", "/SwitchableOutput/WaterPump/State", value)
            case 'Aux':
                self.update_dbus_item("switches", "/SwitchableOutput/Aux/State", value)
            case 'battery1':
                self.update_dbus_item("vehicle_battery", "/Voltage", value)
                self.update_dbus_item("vehicle_battery", "/Soc", battery_service.calcVehicleSoc(value))
           
        logging.debug("_update out")

        return True