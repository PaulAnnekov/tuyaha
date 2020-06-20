import time

from tuyaha.devices.base import TuyaDevice


class TuyaSwitch(TuyaDevice):
    def turn_on(self):
        result = self.api.device_control(self.obj_id, "turnOnOff", {"value": "1"})
        if result[0]:
            self.data["state"] = True

    def turn_off(self):
        result = self.api.device_control(self.obj_id, "turnOnOff", {"value": "0"})
        if result[0]:
            self.data["state"] = False
