from tuyaha.devices.base import TuyaDevice


class TuyaCover(TuyaDevice):
    def state(self):
        state = self.data.get("state")
        return state

    def open_cover(self):
        """Open the cover."""
        self.api.device_control(self.obj_id, "turnOnOff", {"value": "1"})

    def close_cover(self):
        """Close cover."""
        self.api.device_control(self.obj_id, "turnOnOff", {"value": "0"})

    def stop_cover(self):
        """Stop the cover."""
        self.api.device_control(self.obj_id, "startStop", {"value": "0"})

    def support_stop(self):
        support = self.data.get("support_stop")
        if support is None:
            return False
        return support
