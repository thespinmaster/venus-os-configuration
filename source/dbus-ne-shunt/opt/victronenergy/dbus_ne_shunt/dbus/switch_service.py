import dbus_base_service
import dbus_constants

class switch_service(dbus_base_service):

    OUTPUT_TYPE_LATCHING = 1
    MODULE_STATE_CONNECTED = 0x100

    STATUS_OFF = 0x00
    STATUS_ON = 0x09
    STATUS_OUTPUT_FAULT = 0x08
    STATUS_DISABLED = 0x20

    OUTPUT_FUNCTION_MANUAL = 2

    def __init__(self, name, port, switches, deviceinstance, onvaluechanged):

        validTypesLatching = 1 << self.OUTPUT_TYPE_LATCHING

        paths = {f'/State': {'initial': self.MODULE_STATE_CONNECTED, 'writable': True},
                 f'/CustomName': {'initial': name, 'writable': True}
            }

        for switchName in switches:
            #group = name if group == "" else group
            dbusName = switchName.replace(" ", "")
            paths[f'/SwitchableOutput/{dbusName}/State'] = {'initial': 0, 'writable': True}
            paths[f'/SwitchableOutput/{dbusName}/Name'] = {'initial': switchName, 'writable': False}
            paths[f'/SwitchableOutput/{dbusName}/Status'] = {'initial': self.STATUS_OFF, 'writable': True}
            paths[f'/SwitchableOutput/{dbusName}/Settings/Type'] = {'initial': self.OUTPUT_TYPE_LATCHING, 'writable': False}
            paths[f'/SwitchableOutput/{dbusName}/Settings/ValidTypes'] = {'initial': validTypesLatching, 'writable': False}
            paths[f'/SwitchableOutput/{dbusName}/Settings/Group'] = {'initial': "", 'writable': True}
            paths[f'/SwitchableOutput/{dbusName}/Settings/CustomName'] = {'initial': "", 'writable': True}
            paths[f'/SwitchableOutput/{dbusName}/Settings/ShowUIControl'] = {'initial': 1, 'writable': True}
            paths[f'/SwitchableOutput/{dbusName}/Settings/Function'] = {'initial': (1 << self.OUTPUT_FUNCTION_MANUAL), 'writable': False}
            paths[f'/SwitchableOutput/{dbusName}/Settings/ValidTypes'] = {'initial': validTypesLatching, 'writable': False}

        self._registerCore(
            port,
            serviceType = dbus_constants.SERVICE_TYPE_SWITCH,
            paths = paths,
            deviceinstance = deviceinstance,
            onvalueChanged = onvaluechanged
        )

        def ShowUIControl(self, name):
            return self.get_value(f"/SwitchableOutput/{name}/Settings/ShowUIControl")