import logging
import time

import requests
from datetime import datetime
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import HTTPError as RequestsHTTPError
from threading import Lock

from tuyaha.devices.factory import get_tuya_device

TUYACLOUDURL = "https://px1.tuya{}.com"
DEFAULTREGION = "us"

MIN_DISCOVERY_INTERVAL = 60.0
DEF_DISCOVERY_INTERVAL = 305.0
MIN_QUERY_INTERVAL = 10.0
DEF_QUERY_INTERVAL = 60.0
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

    def __init__(self, log_level_warn=True):
        self._log_level_warn = log_level_warn
        self._requestSession = None
        self._discovered_devices = None
        self._last_discover = None
        self._force_discovery = False
        self._discovery_interval = 0.0
        self._query_interval = 0.0
        self._discovery_fail_count = 0

    @property
    def discovery_interval(self):
        return self._discovery_interval or DEF_DISCOVERY_INTERVAL

    @discovery_interval.setter
    def discovery_interval(self, val):
        if val >= MIN_DISCOVERY_INTERVAL:
            self._discovery_interval = val

    @property
    def query_interval(self):
        return self._query_interval or DEF_QUERY_INTERVAL

    @query_interval.setter
    def query_interval(self, val):
        if val >= MIN_QUERY_INTERVAL:
            self._query_interval = val

    def log_message(self, message, *args):
        if self._log_level_warn:
            _LOGGER.warning(message, *args)
        else:
            _LOGGER.debug(message, *args)

    def init(self, username, password, countryCode, bizType=""):
        SESSION.username = username
        SESSION.password = password
        SESSION.countryCode = countryCode
        SESSION.bizType = bizType

        self._requestSession = requests.Session()

        if username is None or password is None:
            return None
        else:
            self.get_access_token()
            self.discover_devices()
            return SESSION.devices

    def get_access_token(self):
        try:
            response = self._requestSession.post(
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
            self._force_discovery = True
        elif SESSION.expireTime <= REFRESHTIME + int(time.time()):
            self.refresh_access_token()
            self._force_discovery = True

    def refresh_access_token(self):
        data = "grant_type=refresh_token&refresh_token=" + SESSION.refreshToken
        response = self._requestSession.get(
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

    def update_device_data(self, dev_id, data):
        for device in self._discovered_devices:
            if device["id"] == dev_id:
                device["data"] = data

    def _call_discovery(self):
        if not self._last_discover or self._force_discovery:
            self._last_discover = datetime.now()
            self._force_discovery = False
            return True
        difference = (datetime.now() - self._last_discover).total_seconds()
        if difference > self.discovery_interval:
            self._last_discover = datetime.now()
            return True
        return False

    def discovery(self):
        with lock:
            if self._call_discovery():
                response = self._request("Discovery", "discovery")
                if response:
                    result_code = response["header"]["code"]
                    if result_code == "SUCCESS":
                        self._discovery_fail_count = 0
                        self._discovered_devices = response["payload"]["devices"]

                    # Logging FrequentlyInvoke
                    elif result_code == "FrequentlyInvoke":
                        self._discovery_fail_count += 1
                        self.log_message(
                            "Method [Discovery] fails %s time(s) using poll interval %s - error: %s",
                            self._discovery_fail_count,
                            self.discovery_interval,
                            response["header"].get("msg", result_code),
                        )
            else:
                _LOGGER.debug("Discovery: Use cached info")
        return self._discovered_devices

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
            if device.device_type() == dev_type:
                device_list.append(device)
        return device_list

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
        else:
            success = False
        return success, response

    def _request(self, name, namespace, devId=None, payload={}):
        header = {"name": name, "namespace": namespace, "payloadVersion": 1}
        payload["accessToken"] = SESSION.accessToken
        if namespace != "discovery":
            payload["devId"] = devId
        data = {"header": header, "payload": payload}
        try:
            response = self._requestSession.post(
                (TUYACLOUDURL + "/homeassistant/skill").format(SESSION.region), json=data
            )
        except RequestsConnectionError as ex:
            _LOGGER.debug(
                "request error, error code is %s, device %s",
                ex,
                devId,
            )
            return

        if not response.ok:
            _LOGGER.warning(
                "request error, status code is %d, device %s",
                response.status_code,
                devId,
            )
            return
        response_json = response.json()
        if response_json["header"]["code"] != "SUCCESS":
            _LOGGER.debug(
                "control device error, error code is " + response_json["header"]["code"]
            )
        return response_json


class TuyaAPIException(Exception):
    pass


class TuyaNetException(Exception):
    pass


class TuyaServerException(Exception):
    pass
