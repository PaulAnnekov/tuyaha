from tuyaha.devices.base import TuyaDevice

class TuyaSwitch(TuyaDevice):

    def state(self):
        devices = self.api.discover_devices()
        state = None
        for device in devices:
            if device['id'] == self.obj_id:
                state = device['data']['state']
                return state
        if state is None:
            return None
        return state

    def turn_on(self):
        self.api.device_control(self.obj_id, 'turnOnOff', {'value': '1'})

    def turn_off(self):
        self.api.device_control(self.obj_id, 'turnOnOff', {'value': '0'})
