from tuyaha.devices.base import TuyaDevice


class TuyaFanDevice(TuyaDevice):

    def speed(self):
        return self.data.get("speed")

    def speed_list(self):
        speed_list = []
        speed_level = self.data.get("speed_level")
        for i in range(speed_level):
            speed_list.append(str(i + 1))
        return speed_list

    def oscillating(self):
        return self.data.get("direction")

    def set_speed(self, speed):
        if self._control_device("windSpeedSet", {"value": speed}):
            self._update_data("speed", speed)

    def oscillate(self, oscillating):
        if oscillating:
            command = "swingOpen"
        else:
            command = "swingClose"
        if self._control_device(command):
            self._update_data("direction", oscillating)

    def turn_on(self):
        if self._control_device("turnOnOff", {"value": "1"}):
            self._update_data("state", "true")

    def turn_off(self):
        if self._control_device("turnOnOff", {"value": "0"}):
            self._update_data("state", "false")

    def support_oscillate(self):
        if self.oscillating() is None:
            return False
        else:
            return True

    def support_direction(self):
        return False
