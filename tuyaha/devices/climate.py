from tuyaha.devices.base import TuyaDevice


class TuyaClimate(TuyaDevice):

    def __init__(self, data, api):
        super().__init__(data, api)
        self._unit = None
        self._divider = 0
        self._ct_divider = 0

    def _set_decimal(self, val, divider=0):
        if val is None:
            return None
        if divider == 0:
            divider = self._divider
            if divider == 0:
                if val > 500 or val < -100:
                    divider = 100
                else:
                    divider = 1
                self._divider = divider

        return round(float(val / divider), 2)

    def set_unit(self, unit):
        self._unit = unit

    def set_temp_divider(self, divider):
        self._divider = divider

    def set_curr_temp_divider(self, divider):
        self._ct_divider = divider

    def has_decimal(self):
        return self._divider >= 10

    def temperature_unit(self):
        if not self._unit:
            if self._divider == 0:
                self.max_temp()
            curr_temp = self.current_temperature()
            if curr_temp is None:
                self._unit = "CELSIUS"
                return self._unit
            if curr_temp > 50 and not self.has_decimal():
                self._unit = "FAHRENHEIT"
            else:
                self._unit = self.data.get("temp_unit", "CELSIUS")
        return self._unit

    def current_humidity(self):
        pass

    def target_humidity(self):
        pass

    def current_operation(self):
        return self.data.get("mode")

    def operation_list(self):
        return self.data.get("support_mode")

    def current_temperature(self):
        curr_temp = self._set_decimal(self.data.get("current_temperature"), self._ct_divider)
        if curr_temp is None:
            return self.target_temperature()
        return curr_temp

    def target_temperature(self):
        return self._set_decimal(self.data.get("temperature"), self._ct_divider)

    def target_temperature_step(self):
        if self.has_decimal():
            return 0.5
        return 1.0

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
        return self._set_decimal(self.data.get("min_temper"))

    def max_temp(self):
        return self._set_decimal(self.data.get("max_temper"))

    def min_humidity(self):
        pass

    def max_humidity(self):
        pass

    def set_temperature(self, temperature):
        """Set new target temperature."""
        if self._ct_divider > 0:
            divider = self._ct_divider
        else:
            divider = self._divider
        if divider == 0:
            divider = 1

        if not self.has_decimal():
            temp_val = round(float(temperature))
            set_val = temp_val * divider
        else:
            temp_val = set_val = round(float(temperature) * divider)
        if self._control_device("temperatureSet", {"value": temp_val}):
            self._update_data("temperature", set_val)

    def set_humidity(self, humidity):
        """Set new target humidity."""
        raise NotImplementedError()

    def set_fan_mode(self, fan_mode):
        """Set new target fan mode."""
        if self._control_device("windSpeedSet", {"value": fan_mode}):
            fanList = self.fan_list()
            if fan_mode in fanList:
                val = str(fanList.index(fan_mode) + 1)
            else:
                val = fan_mode
            self._update_data("windspeed", val)

    def set_operation_mode(self, operation_mode):
        """Set new target operation mode."""
        if self._control_device("modeSet", {"value": operation_mode}):
            self._update_data("mode", operation_mode)

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
        if self._control_device("turnOnOff", {"value": "1"}):
            self._update_data("state", "true")

    def turn_off(self):
        if self._control_device("turnOnOff", {"value": "0"}):
            self._update_data("state", "false")
