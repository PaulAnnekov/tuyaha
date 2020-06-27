import json
import logging
import time

import requests
from datetime import datetime
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import HTTPError as RequestsHTTPError
from threading import Lock
from distutils.util import strtobool

from tuyaha.devices.factory import get_tuya_device

TUYACLOUDURL = "https://px1.tuya{}.com"
DEFAULTREGION = "us"

REFRESHTIME = 60 * 60 * 12

_LOGGER = logging.getLogger(__name__)
lock = Lock()


class TuyaSession:

    username = ""
    password = ""
    countryCode = ""
    bizType = ""
    accessToken = ""
    refreshToken = ""
    expireTime = 0
    devices = []
    region = DEFAULTREGION


SESSION = TuyaSession()


class TuyaApi:

    def __init__(self):
        self._discovered_devices = None
        self._last_request = None
        self._discover_wait = 5

    def init(self, username, password, countryCode, bizType=""):
        SESSION.username = username
        SESSION.password = password
        SESSION.countryCode = countryCode
        SESSION.bizType = bizType

        if username is None or password is None:
            return None
        else:
            self.get_access_token()
            self.discover_devices()
            return SESSION.devices

    def get_access_token(self):
        try:
            response = requests.post(
                (TUYACLOUDURL + "/homeassistant/auth.do").format(SESSION.region),
                data={
                    "userName": SESSION.username,
                    "password": SESSION.password,
                    "countryCode": SESSION.countryCode,
                    "bizType": SESSION.bizType,
                    "from": "tuya",
                },
            )
            response.raise_for_status()
        except RequestsConnectionError as ex:
            raise TuyaNetException from ex
        except RequestsHTTPError as ex:
            if response.status_code >= 500:
                raise TuyaServerException from ex

        response_json = response.json()
        if response_json.get("responseStatus") == "error":
            message = response_json.get("errorMsg")
            if message == "error":
                raise TuyaAPIException("get access token failed")
            else:
                raise TuyaAPIException(message)

        SESSION.accessToken = response_json.get("access_token")
        SESSION.refreshToken = response_json.get("refresh_token")
        SESSION.expireTime = int(time.time()) + response_json.get("expires_in")
        areaCode = SESSION.accessToken[0:2]
        if areaCode == "AY":
            SESSION.region = "cn"
        elif areaCode == "EU":
            SESSION.region = "eu"
        else:
            SESSION.region = "us"

    def check_access_token(self):
        if SESSION.username == "" or SESSION.password == "":
            raise TuyaAPIException("can not find username or password")
        if SESSION.accessToken == "" or SESSION.refreshToken == "":
            self.get_access_token()
        elif SESSION.expireTime <= REFRESHTIME + int(time.time()):
            self.refresh_access_token()

    def refresh_access_token(self):
        data = "grant_type=refresh_token&refresh_token=" + SESSION.refreshToken
        response = requests.get(
            (TUYACLOUDURL + "/homeassistant/access.do").format(SESSION.region)
            + "?"
            + data
        )
        response_json = response.json()
        if response_json.get("responseStatus") == "error":
            raise TuyaAPIException("refresh token failed")

        SESSION.accessToken = response_json.get("access_token")
        SESSION.refreshToken = response_json.get("refresh_token")
        SESSION.expireTime = int(time.time()) + response_json.get("expires_in")

    def poll_devices_update(self):
        self.check_access_token()
        return self.discover_devices()

    def call_discovery(self):
        if not self._discovered_devices:
            return True
        difference = (datetime.now() - self._last_request).total_seconds()
        if difference > self._discover_wait:
            return True
        return False

    def discovery(self):
        with lock:
            if self.call_discovery():
                response = self._request("Discovery", "discovery")
                if response and response["header"]["code"] == "SUCCESS":
                    self._discovered_devices = {}
                    for device in response["payload"]["devices"]:
                        self._discovered_devices[device["id"]] = device
                # else:
                #     self._discovered_devices = None
            else:
                _LOGGER.debug("Discovery: Use cached info")
        return list(self._discovered_devices.values())

    def discover_devices(self):
        devices = self.discovery()
        if not devices:
            return None
        SESSION.devices = []
        for device in devices:
            SESSION.devices.extend(get_tuya_device(device, self))
        return devices

    def get_devices_by_type(self, dev_type):
        device_list = []
        for device in SESSION.devices:
            if device.dev_type() == dev_type:
                device_list.append(device)

    def get_all_devices(self):
        return SESSION.devices

    def get_device_by_id(self, dev_id):
        for device in SESSION.devices:
            if device.object_id() == dev_id:
                return device
        return None

    def device_control(self, devId, action, param=None, namespace="control"):
        if param is None:
            param = {}
        response = self._request(action, namespace, devId, param)
        if response and response["header"]["code"] == "SUCCESS":
            success = True
            if (action == "turnOnOff"):
                self._update_device_status(devId, strtobool(param["value"]))
        else:
            success = False
        return success, response

    def _request(self, name, namespace, devId=None, payload={}):
        self._last_request = datetime.now()
        header = {"name": name, "namespace": namespace, "payloadVersion": 1}
        payload["accessToken"] = SESSION.accessToken
        if namespace != "discovery":
            payload["devId"] = devId
        data = {"header": header, "payload": payload}
        _LOGGER.debug("Tuya request pre: %s", data)
        response = requests.post(
            (TUYACLOUDURL + "/homeassistant/skill").format(SESSION.region), json=data
        )
        if not response.ok:
            _LOGGER.warning(
                "request error, status code is %d, device %s",
                response.status_code,
                devId,
            )
            return
        response_json = response.json()
        _LOGGER.debug("Tuya request post: %s", response_json)
        if response_json["header"]["code"] != "SUCCESS":
            error_code = response_json["header"]["code"]
            _LOGGER.debug(
                "request error, error code is %s, name %s, discover wait %d sec",
                response_json["header"]["code"],
                name,
                self._discover_wait,
            )
        return response_json

    def _update_device_status(self, dev_id, new_state):
        if self._discovered_devices[dev_id]:
            self._discovered_devices[dev_id]["data"]["state"] = new_state

class TuyaAPIException(Exception):
    pass


class TuyaNetException(Exception):
    pass


class TuyaServerException(Exception):
    pass
