from tuyaha.devices.base import TuyaDevice

"""The minimum brightness value set in the API that does not turn off the light."""
MIN_BRIGHTNESS = 10.3
BRIGHTNESS_WHITE_RANGE = (10, 1000)
BRIGHTNESS_COLOR_RANGE = (1, 255)
BRIGHTNESS_STD_RANGE = (1, 255)

COLTEMP_STATUS_RANGE = (1000, 36294)
COLTEMP_SET_RANGE = (1000, 10000)
COLTEMP_KELV_RANGE = (2700, 6500)


class TuyaLight(TuyaDevice):
    def __init__(self, data, api):
        super().__init__(data, api)
        self._support_color = False

    def set_support_color(self, supported):
        self._support_color = supported

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
        brightness = -1
        if self._color_mode():
            if "color" in self.data:
                brightness = int(self.data.get("color").get("brightness", "-1"))
        else:
            brightness = int(self.data.get("brightness", "-1"))
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
        if self._color_mode():
            return BRIGHTNESS_COLOR_RANGE
        else:
            return BRIGHTNESS_WHITE_RANGE

    def support_color(self):
        if not self._support_color:
            if self.data.get("color") or self.data.get("color_mode") == "colour":
                self._support_color = True
        return self._support_color

    def support_color_temp(self):
        return self.data.get("color_temp") is not None

    def hs_color(self):
        if self.support_color():
            color = self.data.get("color")
            if self._color_mode() and color:
                return color.get("hue", 0.0), float(color.get("saturation", 0.0)) * 100
            else:
                return 0.0, 0.0
        else:
            return None

    def color_temp(self):
        temp = self.data.get("color_temp")
        ret_value = TuyaLight._scale(
            temp,
            COLTEMP_STATUS_RANGE,
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
            """convert to scale 0-100 with MIN_BRIGHTNESS."""
            set_value = TuyaLight._scale(
                brightness,
                BRIGHTNESS_STD_RANGE,
                (MIN_BRIGHTNESS, 100),
            )
            value = TuyaLight._scale(
                brightness,
                BRIGHTNESS_STD_RANGE,
                self._brightness_range(),
            )
            if self._control_device("brightnessSet", {"value": round(set_value, 1)}):
                self._update_data("state", "true")
                self._set_brightness(round(value))
        else:
            self.turn_off()

    def set_color(self, color):
        """Set the color of light."""
        cur_brightness = self.data.get("color", {}).get(
            "brightness", BRIGHTNESS_COLOR_RANGE[0]
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
        set_value = TuyaLight._scale(
            color_temp,
            COLTEMP_KELV_RANGE,
            COLTEMP_SET_RANGE,
        )
        if self._control_device("colorTemperatureSet", {"value": round(set_value)}):
            self._update_data("state", "true")
            self._update_data("color_mode", "white")
            data_value = TuyaLight._scale(
                color_temp,
                COLTEMP_KELV_RANGE,
                COLTEMP_STATUS_RANGE,
            )
            self._update_data("color_temp", round(data_value))

    def update(self):
        return self._update(use_discovery=True)
