from tuyaha.devices.base import TuyaDevice


class TuyaCover(TuyaDevice):

    def state(self):
        state = self.data.get("state")
        return state

    def open_cover(self):
        """Open the cover."""
        if self._control_device("turnOnOff", {"value": "1"}):
            self._update_data("state", 1)

    def close_cover(self):
        """Close cover."""
        if self._control_device("turnOnOff", {"value": "0"}):
            self._update_data("state", 2)

    def stop_cover(self):
        """Stop the cover."""
        if self._control_device("startStop", {"value": "0"}):
            self._update_data("state", 3)

    def support_stop(self):
        support = self.data.get("support_stop")
        if support is None:
            return False
        return support
