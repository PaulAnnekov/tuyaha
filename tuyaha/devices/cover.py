from tuyaha.devices.base import TuyaDevice


class TuyaCover(TuyaDevice):
    def open_cover(self):
        """Open the cover."""
        result = self.api.device_control(self.obj_id, "turnOnOff", {"value": "1"})
        if result[0]:
            self.data["state"] = "true"

    def close_cover(self):
        """Close cover."""
        result = self.api.device_control(self.obj_id, "turnOnOff", {"value": "0"})
        if result[0]:
            self.data["state"] = "false"

    def stop_cover(self):
        """Stop the cover."""
        self.api.device_control(self.obj_id, "startStop", {"value": "0"})

    def support_stop(self):
        support = self.data.get("support_stop")
        if support is None:
            return False
        return support
