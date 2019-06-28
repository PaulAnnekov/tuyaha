from tuyapy.devices.base import TuyaDevice


class TuyaSwitch(TuyaDevice):

    def state(self):
        state = self.data.get('state')
        if state is None:
            return None
        return state

    def turn_on(self):
        self.api.device_control(self.obj_id, 'turnOnOff', {'value': '1'})

    def turn_off(self):
        self.api.device_control(self.obj_id, 'turnOnOff', {'value': '0'})
