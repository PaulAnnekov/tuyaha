import time


class TuyaDevice:
    def __init__(self, data, api):
        self.api = api
        self.data = data.get("data")
        self.obj_id = data.get("id")
        self.obj_type = data.get("ha_type")
        self.obj_name = data.get("name")
        self.dev_type = data.get("dev_type")
        self.icon = data.get("icon")

    def name(self):
        return self.obj_name

    def state(self):
        state = self.data.get("state")
        if state is None:
            return None
        elif isinstance(state, str):
            if state == "true":
                return True
            return False
        else:
            return bool(state)

    def device_type(self):
        return self.dev_type

    def object_id(self):
        return self.obj_id

    def object_type(self):
        return self.obj_type

    def available(self):
        return self.data.get("online")

    def iconurl(self):
        return self.icon

    def _update_data(self, key, value, force_val=False):
        if self.data:
            if not force_val and self.data.get(key) is None:
                return
            self.data[key] = value
            self.api.update_device_data(self.obj_id, self.data)

    def _control_device(self, action, param=None):
        success, response = self.api.device_control(self.obj_id, action, param)
        if not success:
            self._update_data("online", False)
        return success

    def _update(self, use_discovery=False):
        """Avoid get cache value after control."""
        time.sleep(0.5)

        if use_discovery:
            # workaround for https://github.com/PaulAnnekov/tuyaha/issues/3
            devices = self.api.discovery()
            if not devices:
                return
            for device in devices:
                if device["id"] == self.obj_id:
                    if not self.data:
                        self.data = device["data"]
                    else:
                        self.data.update(device["data"])
                    return True
            return

        success, response = self.api.device_control(
            self.obj_id, "QueryDevice", namespace="query"
        )
        if success:
            self.data = response["payload"]["data"]
            return True
        return

    def __repr__(self):
        module = self.__class__.__module__
        if module is None or module == str.__class__.__module__:
            module = ""
        else:
            module += "."
        return '<{module}{clazz}: "{name}" ({obj_id})>'.format(
            module=module,
            clazz=self.__class__.__name__,
            name=self.obj_name,
            obj_id=self.obj_id
        )

    def update(self):
        return self._update()
