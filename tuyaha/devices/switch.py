
from tuyaha.devices.base import TuyaDevice


class TuyaSwitch(TuyaDevice):

    def turn_on(self):
        if self._control_device("turnOnOff", {"value": "1"}):
            self._update_data("state", True)

    def turn_off(self):
        if self._control_device("turnOnOff", {"value": "0"}):
            self._update_data("state", False)

    def update(self, use_discovery=True):
        return self._update(use_discovery=True)
