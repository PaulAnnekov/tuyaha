from tuyaha.devices.base import TuyaDevice


class TuyaFanDevice(TuyaDevice):
    def state(self):
        state = self.data.get("state")
        if state == "true":
            return True
        else:
            return False

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
        self.api.device_control(self.obj_id, "windSpeedSet", {"value": speed})

    def oscillate(self, oscillating):
        if oscillating:
            command = "swingOpen"
        else:
            command = "swingClose"
        self.api.device_control(self.obj_id, command)

    def turn_on(self):
        self.api.device_control(self.obj_id, "turnOnOff", {"value": "1"})

    def turn_off(self):
        self.api.device_control(self.obj_id, "turnOnOff", {"value": "0"})

    def support_oscillate(self):
        if self.oscillating() is None:
            return False
        else:
            return True

    def support_direction(self):
        return False
