from tuyaha.devices.base import TuyaDevice


class TuyaLight(TuyaDevice):
    def state(self):
        state = self.data.get("state")
        if state == "true":
            return True
        else:
            return False

    def brightness(self):
        work_mode = self.data.get("color_mode")
        if work_mode == "colour" and "color" in self.data:
            brightness = int(self.data.get("color").get("brightness") * 255 / 100)
        else:

            # Tuya API return 25 as a brightness value when the brightness is set to 1% in the app
            # And it return 255 when the brightness is 100% in the app
            # So we need to convert that values to HA brightnes

            # So we need to convert Tuya API value to HA value:
            #
            #  Tuya |   HA
            # ------------
            #    25 |    1
            #   255 |  255

            x1 = 25
            y1 = 1

            x2 = 255
            y2 = 255

            m = (y2 - y1) / (x2 - x1)
            b = y1 - m * x1

            brightness = round(int(self.data.get("brightness")) * m + b)

        return brightness

    def _set_brightness(self, brightness):
        work_mode = self.data.get("color_mode")
        if work_mode == "colour":
            self.data["color"]["brightness"] = brightness
        else:
            self.data["brightness"] = brightness

    def support_color(self):
        if self.data.get("color") is None:
            return False
        else:
            return True

    def support_color_temp(self):
        if self.data.get("color_temp") is None:
            return False
        else:
            return True

    def hs_color(self):
        if self.data.get("color") is None:
            return None
        else:
            work_mode = self.data.get("color_mode")
            if work_mode == "colour":
                color = self.data.get("color")
                return color.get("hue"), color.get("saturation")
            else:
                return 0.0, 0.0

    def color_temp(self):
        if self.data.get("color_temp") is None:
            return None
        else:
            return self.data.get("color_temp")

    def min_color_temp(self):
        return 10000

    def max_color_temp(self):
        return 1000

    def turn_on(self):
        self.api.device_control(self.obj_id, "turnOnOff", {"value": "1"})

    def turn_off(self):
        self.api.device_control(self.obj_id, "turnOnOff", {"value": "0"})

    def set_brightness(self, brightness):
        """Set the brightness(0-255) of light."""

        # 'brightness' is the value from the Home Assistant point of view:
        # Integer between 0 and 255 for how bright the light should be, where 0
        # means the light is off, 1 is the minimum brightness and 255 is the
        # maximum brightness supported by the light
        #
        # https://www.home-assistant.io/integrations/light/

        # Tuya API method "brightnessSet" want to recieve int number from 11 to 100
        #
        #  * 11 is show as 1% in the TuyaSmart app
        #  * 100 is show as 100% in the TuyaSmart app
        #
        # Sending value less than 11 to "brightnessSet" just turns the light off

        # So we need to convert HA value to Tuya API value:
        #
        #   HA | Tuya
        # ------------
        #    1 |   11
        #  255 |  100

        x1 = 1
        y1 = 11

        x2 = 255
        y2 = 100

        m = (y2 - y1) / (x2 - x1)
        b = y1 - m * x1

        tuya_value = round(brightness * m + b)

        self.api.device_control(self.obj_id, "brightnessSet", {"value": tuya_value})

    def set_color(self, color):
        """Set the color of light."""
        hsv_color = {}
        hsv_color["hue"] = color[0]
        hsv_color["saturation"] = color[1] / 100
        if len(color) < 3:
            hsv_color["brightness"] = int(self.brightness()) / 255.0
        else:
            hsv_color["brightness"] = color[2]
        # color white
        if hsv_color["saturation"] == 0:
            hsv_color["hue"] = 0
        self.api.device_control(self.obj_id, "colorSet", {"color": hsv_color})

    def set_color_temp(self, color_temp):
        self.api.device_control(
            self.obj_id, "colorTemperatureSet", {"value": color_temp}
        )
