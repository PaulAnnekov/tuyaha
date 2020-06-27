import time

from tuyaha.devices.base import TuyaDevice


class TuyaSwitch(TuyaDevice):
    def turn_on(self):
        self.api.device_control(self.obj_id, "turnOnOff", {"value": "1"})

    def turn_off(self):
        self.api.device_control(self.obj_id, "turnOnOff", {"value": "0"})
