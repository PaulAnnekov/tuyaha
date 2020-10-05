from tuyaha.devices.base import TuyaDevice

UNIT_CELSIUS = "CELSIUS"
UNIT_FAHRENHEIT = "FAHRENHEIT"


class TuyaClimate(TuyaDevice):

    def __init__(self, data, api):
        super().__init__(data, api)
        self._unit = None
        self._divider = 0
        self._divider_set = False
        self._ct_divider = 0

    # this function return the temperature value
    # divided by the _divider attribute previous set
    # this is required because in same case API provide
    # a temperature value that must be divided to provide decimal
    # in other case just return the right temperature values
    def _set_decimal(self, val, divider=0):
        if val is None:
            return None
        if divider == 0:
            divider = self._divider
            if divider == 0:
                if val > 500 or val < -100:
                    # in this case we suppose that returned value
                    # support decimal and must be divided by 100
                    divider = 100
                    self._divider = divider
                else:
                    divider = 1

        return round(float(val / divider), 2)

    # when unit is not provided by the API or the API return
    # incorrect value, it can be forced by this method
    # the _unit attribute is used by the temperature_unit() method
    def set_unit(self, unit):
        """Set temperature unit (CELSIUS or FAHRENHEIT)"""
        if unit != UNIT_CELSIUS and unit != UNIT_FAHRENHEIT:
            raise ValueError(
                f"Unit can only be set to {UNIT_CELSIUS} or {UNIT_FAHRENHEIT}"
            )
        self._unit = unit

    @property
    def temp_divider(self):
        return self._divider if self._divider_set else 0

    @temp_divider.setter
    def temp_divider(self, divider):
        """Set a divider used to calculate returned temperature. Default=0"""
        if divider < 0:
            raise ValueError("Temperature divider must be a positive value")
        # this check is to avoid that divider is reset from
        # calculated value when is set to 0
        if (self._divider_set and divider == 0) or divider > 0:
            self._divider = divider
        self._divider_set = divider > 0

    @property
    def curr_temp_divider(self):
        return self._ct_divider

    @curr_temp_divider.setter
    def curr_temp_divider(self, divider):
        """Set a divider used to calculate returned current temperature
           If not defined standard temperature divider is used"""
        if divider < 0:
            raise ValueError("Current temperature divider must be a positive value")
        self._ct_divider = divider

    def has_decimal(self):
        """Return if temperature values support decimal"""
        return self._divider >= 10

    def temperature_unit(self):
        """Return the temperature unit for the device"""
        if not self._unit:
            self._unit = self.data.get("temp_unit", UNIT_CELSIUS)
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
        """Return current temperature for the device"""
        curr_temp = self._set_decimal(
            self.data.get("current_temperature"), self._ct_divider
        )
        # when current temperature is not available, target temperature is returned
        if curr_temp is None:
            return self.target_temperature()
        return curr_temp

    def target_temperature(self):
        """Return target temperature for the device"""
        return self._set_decimal(self.data.get("temperature"))

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

        # the value used to set temperature is scaled based on the configured divider
        divider = self._divider or 1

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
