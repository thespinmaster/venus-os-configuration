import dbus_base_service
import dbus_constants

class tank_service(dbus_base_service):


    def __init__(self, name, port, fluidType, deviceName, capacity):

        self._registerCore(
            port,
            serviceType = dbus_constants.SERVICE_TYPE_TANK,
            paths =  {
                '/Capacity': {'initial': capacity,'writable': True},
                '/CustomName': {'initial': name,'writable': True},
                '/FluidType': {'initial': fluidType, 'writable': False},
                '/Level': {'initial': 8, 'writable': True},
            },
            deviceName = deviceName,
            )