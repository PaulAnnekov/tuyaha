from tuyaha.devices.base import TuyaDevice


class TuyaLock(TuyaDevice):
    def state(self):
        state = self.data.get("state")
        if state == "true":
            return True
        elif state == "false":
            return False
        else:
            return None
