import copy
import logging

class ne_shunt_data:

    KEYS = [
        "fresh_water_tank", "grey_waste_tank", "grey_waste_tank2",
        "InternalLights", "ExternalLights", "Aux", "WaterPump",
        "battery1", "battery2"
    ]

    def clone(self): 
        return copy.deepcopy(self)
    
    def __init__(self, rawData = None):
        #read:FF000000FF00D00070FCFA009DA2FF07400000BB
        #                 w   g   g          b1 b2     s       checksum
        #read:FF000000FF0 0 D 0 0 0 70FCFA00 9D A2 FF 07400000 BB
        #read:FF000000FF00D00070FDFA009DA2FF          02A00000  17
        
        #                                    states   cm
        #read:FF000000FF00D00070FEFA009DA3FF 00A00000 17 0 all off
        #read:FF000000FF00D00070FEFA009DA4FF 01A00000 19 1 internal lights on
        #read:FF000000FF00D00070FDFA009DA2FF 02A00000 17 2 external lights on
        #read:FF000000FF00D00070FDFA009DA3FF 04A00000 1A 4 water pump on
        #read:FF000000FF00D00070FCFA009DA4FF 08A00000 1E 8 Aux on

        #read:FF000000FF00D00070FEFA009DA1FF 08C00000 3D
        #read:FF4000003F00D00070FDFA009DA2FF 00230000 98 states 
        
        if rawData is None:
            self.data = {k: "" for k in self.KEYS}
        else:
            self.data = {
                "fresh_water_tank": self._get_tank_level(rawData[11:12]),
                "grey_waste_tank": self._get_tank_level(rawData[13:14]),
                "grey_waste_tank2": self._get_tank_level(rawData[15:16]),
                "InternalLights": self._get_indoor_light_state(rawData[31:32]),
                "ExternalLights": self._get_outdoor_light_state(rawData[31:32]),
                "WaterPump": self._get_pump_state(rawData[31:32]),
                "Aux": self._get_aux_state(rawData[31:32]),
                "battery1": self._get_battery_level(rawData[24:26]),
                "battery2": self._get_battery_level(rawData[26:28]),
            }

    @staticmethod
    def _get_tank_level(data_part):
        val = int(data_part, 16)
        level = 0
        if val & 1: level += 1
        if val & 2: level += 1
        if val & 4: level += 1
        return str(level)

    @staticmethod
    def _get_indoor_light_state(data):
        return 1 if (int(data, 16) & 1) else 0

    @staticmethod
    def _get_outdoor_light_state(data):
        return 1 if (int(data, 16) & 2) else 0

    @staticmethod
    def _get_pump_state(data):
        logging.debug("_get_states: " + data)
        return 1 if (int(data, 16) & 4) else 0
    
    @staticmethod
    def _get_aux_state(data):
        return 1 if (int(data, 16) & 8) else 0
    
    @staticmethod
    def _get_battery_level(data):
        
        encoded_voltage = int(data, 16)
        voltage = (encoded_voltage - 30) / 10
        logging.debug("_get_battery_level: " + data + ", voltage = " + str(f"{voltage:.2f}"))
        return f"{voltage:.2f}"

    def get_value(self, name):
        """Get the value of a specific key."""
        if name in self.KEYS:
            return self.data[name]
        else:
            raise KeyError(f"Invalid key: {name}")
        
    def diff(self, other):
        """Yield (key, value) pairs where value differs from other."""
        for k in self.KEYS:
            if other == None or (self.data[k] != other.data[k]):
                yield k, self.data[k]