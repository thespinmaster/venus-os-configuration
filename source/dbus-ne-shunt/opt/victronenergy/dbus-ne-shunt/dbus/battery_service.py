import dbus_base_service
import i

class battery_service(dbus_base_service):

    def __init__(self, name, port, deviceinstance, capacity):

        self._registerCore(
            port,
            serviceType = dbus_constants.SERVICE_TYPE_BATTERY,
            paths =  {
                '/Voltage': {'initial': None,'writable': True},
                '/CustomName': {'initial': name,'writable': True},
                '/Soc': {'initial': None,'writable': True},
                '/Capacity': {'initial': capacity,'writable': True},
            },
            deviceinstance = deviceinstance,
            )
    
    @staticmethod
    def calcVehicleSoc(value):
        if (value == None):
            return 0
        #V_MAX = 12.89 # 100% charged
        V_MIN = 11.63 # 0% dead
        V_RANGE = 1.26 # (V_MAX - V_MIN)
        #soc = (float(value) - V_MIN) / (V_MAX - V_MIN)
        soc = (float(value) - V_MIN) / (V_RANGE)
        
        return soc
        