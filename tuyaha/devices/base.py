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
        if state == "true":
            return True
        else:
            return False

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

    def update(self):
        """Avoid get cache value after control."""
        time.sleep(0.5)
        success, response = self.api.device_control(
            self.obj_id, "QueryDevice", namespace="query"
        )
        if success:
            self.data = response["payload"]["data"]
            return True
        return
