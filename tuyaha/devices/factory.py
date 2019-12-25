from tuyaha.devices.climate import TuyaClimate
from tuyaha.devices.cover import TuyaCover
from tuyaha.devices.fan import TuyaFanDevice
from tuyaha.devices.light import TuyaLight
from tuyaha.devices.lock import TuyaLock
from tuyaha.devices.scene import TuyaScene
from tuyaha.devices.switch import TuyaSwitch


def get_tuya_device(data, api):
    dev_type = data.get("dev_type")
    devices = []

    if dev_type == "light":
        devices.append(TuyaLight(data, api))
    elif dev_type == "climate":
        devices.append(TuyaClimate(data, api))
    elif dev_type == "scene":
        devices.append(TuyaScene(data, api))
    elif dev_type == "fan":
        devices.append(TuyaFanDevice(data, api))
    elif dev_type == "cover":
        devices.append(TuyaCover(data, api))
    elif dev_type == "lock":
        devices.append(TuyaLock(data, api))
    elif dev_type == "switch":
        devices.append(TuyaSwitch(data, api))
    return devices
