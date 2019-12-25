from tuyaha.devices.base import TuyaDevice


class TuyaClimate(TuyaDevice):
    def temperature_unit(self):
        return self.data.get("temp_unit")

    def current_humidity(self):
        pass

    def target_humidity(self):
        pass

    def current_operation(self):
        return self.data.get("mode")

    def operation_list(self):
        return self.data.get("support_mode")

    def current_temperature(self):
        return self.data.get("current_temperature")

    def target_temperature(self):
        return self.data.get("temperature")

    def target_temperature_step(self):
        return 1

    def current_fan_mode(self):
        """Return the fan setting."""
        fan_speed = self.data.get("windspeed")
        if fan_speed is None:
            return None
        if fan_speed == "1":
            return "low"
        elif fan_speed == "2":
            return "medium"
        elif fan_speed == "3":
            return "high"
        return fan_speed

    def fan_list(self):
        """Return the list of available fan modes."""
        return ["low", "medium", "high"]

    def current_swing_mode(self):
        """Return the fan setting."""
        return None

    def swing_list(self):
        """Return the list of available swing modes."""
        return None

    def min_temp(self):
        return self.data.get("min_temper")

    def max_temp(self):
        return self.data.get("max_temper")

    def min_humidity(self):
        pass

    def max_humidity(self):
        pass

    def set_temperature(self, temperature):
        """Set new target temperature."""
        self.api.device_control(
            self.obj_id, "temperatureSet", {"value": int(temperature)}
        )

    def set_humidity(self, humidity):
        """Set new target humidity."""
        raise NotImplementedError()

    def set_fan_mode(self, fan_mode):
        """Set new target fan mode."""
        self.api.device_control(self.obj_id, "windSpeedSet", {"value": fan_mode})

    def set_operation_mode(self, operation_mode):
        """Set new target operation mode."""
        self.api.device_control(self.obj_id, "modeSet", {"value": operation_mode})

    def set_swing_mode(self, swing_mode):
        """Set new target swing operation."""
        raise NotImplementedError()

    def support_target_temperature(self):
        if self.data.get("temperature") is not None:
            return True
        else:
            return False

    def support_mode(self):
        if self.data.get("mode") is not None:
            return True
        else:
            return False

    def support_wind_speed(self):
        if self.data.get("windspeed") is not None:
            return True
        else:
            return False

    def support_humidity(self):
        if self.data.get("humidity") is not None:
            return True
        else:
            return False

    def turn_on(self):
        self.api.device_control(self.obj_id, "turnOnOff", {"value": "1"})

    def turn_off(self):
        self.api.device_control(self.obj_id, "turnOnOff", {"value": "0"})
