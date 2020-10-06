from tuyaha.devices.base import TuyaDevice

# The minimum brightness value set in the API that does not turn off the light
MIN_BRIGHTNESS = 10.3

# the default range used to return brightness
BRIGHTNESS_STD_RANGE = (1, 255)

# the default range used to set color temperature
COLTEMP_SET_RANGE = (1000, 10000)

# the default range used to return color temperature (in kelvin)
COLTEMP_KELV_RANGE = (2700, 6500)


class TuyaLight(TuyaDevice):

    def __init__(self, data, api):
        super().__init__(data, api)
        self._support_color = False
        self.brightness_white_range = BRIGHTNESS_STD_RANGE
        self.brightness_color_range = BRIGHTNESS_STD_RANGE
        self.color_temp_range = COLTEMP_SET_RANGE

    # if color support is not reported by API can be forced by this method
    # the attribute _support_color is used by method support_color()
    def force_support_color(self):
        self._support_color = True

    def _color_mode(self):
        work_mode = self.data.get("color_mode", "white")
        return True if work_mode == "colour" else False

    @staticmethod
    def _scale(val, src, dst):
        """Scale the given value from the scale of src to the scale of dst."""
        if val < 0:
            return dst[0]
        return ((val - src[0]) / (src[1] - src[0])) * (dst[1] - dst[0]) + dst[0]

    def brightness(self):
        """Return the brightness based on the light status scaled to standard range"""
        brightness = -1
        if self._color_mode():
            if "color" in self.data:
                brightness = int(self.data.get("color").get("brightness", "-1"))
        else:
            brightness = int(self.data.get("brightness", "-1"))
        # returned value is scaled using standard range
        ret_val = TuyaLight._scale(
            brightness,
            self._brightness_range(),
            BRIGHTNESS_STD_RANGE,
        )
        return round(ret_val)

    def _set_brightness(self, brightness):
        if self._color_mode():
            data = self.data.get("color", {})
            data["brightness"] = brightness
            self._update_data("color", data, force_val=True)
        else:
            self._update_data("brightness", brightness)

    def _brightness_range(self):
        """return the configured brightness range based on the light status"""
        if self._color_mode():
            return self.brightness_color_range
        else:
            return self.brightness_white_range

    def support_color(self):
        """return if the light support color"""
        if not self._support_color:
            if self.data.get("color") or self.data.get("color_mode") == "colour":
                self._support_color = True
        return self._support_color

    def support_color_temp(self):
        """return if the light support color temperature"""
        return self.data.get("color_temp") is not None

    def hs_color(self):
        """return current hs color"""
        if self.support_color():
            color = self.data.get("color")
            if self._color_mode() and color:
                return color.get("hue", 0.0), float(color.get("saturation", 0.0)) * 100
            else:
                return 0.0, 0.0
        else:
            return None

    def color_temp(self):
        """return current color temperature scaled with standard kelvin range"""
        temp = self.data.get("color_temp")
        # convert color temperature to kelvin scale for returned value
        ret_value = TuyaLight._scale(
            temp,
            self.color_temp_range,
            COLTEMP_KELV_RANGE,
        )
        return round(ret_value)

    def min_color_temp(self):
        return COLTEMP_KELV_RANGE[1]

    def max_color_temp(self):
        return COLTEMP_KELV_RANGE[0]

    def turn_on(self):
        if self._control_device("turnOnOff", {"value": "1"}):
            self._update_data("state", "true")

    def turn_off(self):
        if self._control_device("turnOnOff", {"value": "0"}):
            self._update_data("state", "false")

    def set_brightness(self, brightness):
        """Set the brightness(0-255) of light."""
        if int(brightness) > 0:
            # convert to scale 0-100 with MIN_BRIGHTNESS to set the value
            set_value = TuyaLight._scale(
                brightness,
                BRIGHTNESS_STD_RANGE,
                (MIN_BRIGHTNESS, 100),
            )
            if self._control_device("brightnessSet", {"value": round(set_value, 1)}):
                self._update_data("state", "true")
                # convert to scale configured for brightness range to update the cache
                value = TuyaLight._scale(
                    brightness,
                    BRIGHTNESS_STD_RANGE,
                    self._brightness_range(),
                )
                self._set_brightness(round(value))
        else:
            self.turn_off()

    def set_color(self, color):
        """Set the color of light."""
        cur_brightness = self.data.get("color", {}).get(
            "brightness", self.brightness_color_range[0]
        )
        hsv_color = {
            "hue": color[0] if color[1] != 0 else 0,  # color white
            "saturation": color[1] / 100,
        }
        if len(color) < 3:
            hsv_color["brightness"] = cur_brightness
        else:
            hsv_color["brightness"] = color[2]
        # color white
        white_mode = hsv_color["saturation"] == 0
        is_color = self._color_mode()
        if self._control_device("colorSet", {"color": hsv_color}):
            self._update_data("state", "true")
            self._update_data("color", hsv_color, force_val=True)
            if not is_color and not white_mode:
                self._update_data("color_mode", "colour")
            elif is_color and white_mode:
                self._update_data("color_mode", "white")

    def set_color_temp(self, color_temp):
        """Set the color temperature of light."""
        # convert to scale configured for color temperature to update the value
        set_value = TuyaLight._scale(
            color_temp,
            COLTEMP_KELV_RANGE,
            COLTEMP_SET_RANGE,
        )
        if self._control_device("colorTemperatureSet", {"value": round(set_value)}):
            self._update_data("state", "true")
            self._update_data("color_mode", "white")
            # convert to scale configured for color temperature to update the cache
            data_value = TuyaLight._scale(
                color_temp,
                COLTEMP_KELV_RANGE,
                self.color_temp_range,
            )
            self._update_data("color_temp", round(data_value))
