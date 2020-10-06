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

# Tuya API do not allow call to discovery command below specific limits
# Use discovery_interval property to set correct value based on API discovery limits
# Next 2 parameter define the default and minimum allowed value for the property
MIN_DISCOVERY_INTERVAL = 10.0
DEF_DISCOVERY_INTERVAL = 60.0

# Tuya API do not allow call to query command below specific limits
# Use query_interval property to set correct value based on API query limits
# Next 2 parameter define the default and minimum allowed value for the property
MIN_QUERY_INTERVAL = 10.0
DEF_QUERY_INTERVAL = 30.0

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
        self._requestSession = None
        self._discovered_devices = None
        self._last_discovery = None
        self._force_discovery = False
        self._discovery_interval = DEF_DISCOVERY_INTERVAL
        self._query_interval = DEF_QUERY_INTERVAL
        self._discovery_fail_count = 0

    @property
    def discovery_interval(self):
        """The interval in seconds between 2 consecutive device discovery"""
        return self._discovery_interval

    @discovery_interval.setter
    def discovery_interval(self, val):
        if val < MIN_DISCOVERY_INTERVAL:
            raise ValueError(
                f"Discovery interval below {MIN_DISCOVERY_INTERVAL} seconds is invalid"
            )
        self._discovery_interval = val

    @property
    def query_interval(self):
        """The interval in seconds between 2 consecutive device query"""
        return self._query_interval

    @query_interval.setter
    def query_interval(self, val):
        if val < MIN_QUERY_INTERVAL:
            raise ValueError(
                f"Query interval below {MIN_QUERY_INTERVAL} seconds is invalid"
            )
        self._query_interval = val

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
        if not self._last_discovery or self._force_discovery:
            self._force_discovery = False
            return True
        difference = (datetime.now() - self._last_discovery).total_seconds()
        if difference > self.discovery_interval:
            return True
        return False

    # if discovery is called before that configured polling interval has passed
    # it return cached data retrieved by previous successful call
    def discovery(self):
        with lock:
            if self._call_discovery():
                try:
                    response = self._request("Discovery", "discovery")
                finally:
                    self._last_discovery = datetime.now()
                if response:
                    result_code = response["header"]["code"]
                    if result_code == "SUCCESS":
                        self._discovery_fail_count = 0
                        self._discovered_devices = response["payload"]["devices"]
                        self._load_session_devices()
            else:
                _LOGGER.debug("Discovery: Use cached info")
        return self._discovered_devices

    def _load_session_devices(self):
        SESSION.devices = []
        for device in self._discovered_devices:
            SESSION.devices.extend(get_tuya_device(device, self))

    def discover_devices(self):
        devices = self.discovery()
        if not devices:
            return None
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
        result_code = response_json["header"]["code"]
        if result_code != "SUCCESS":
            if result_code == "FrequentlyInvoke":
                self._raise_frequently_invoke(
                    name, response_json["header"].get("msg", result_code), devId
                )
            else:
                _LOGGER.debug(
                    "control device error, error code is " + response_json["header"]["code"]
                )
        return response_json

    def _raise_frequently_invoke(self, action, error_msg, dev_id):
        if action == "Discovery":
            self._discovery_fail_count += 1
            text = (
                "Method [Discovery] fails {} time(s) using poll interval {} - error: {}"
            )
            message = text.format(
                self._discovery_fail_count, self.discovery_interval, error_msg
            )
        else:
            text = "Method [{}] for device {} fails {}- error: {}"
            msg_interval = ""
            if action == "QueryDevice":
                msg_interval = "using poll interval {} ".format(self.query_interval)
            message = text.format(action, dev_id, msg_interval, error_msg)

        raise TuyaFrequentlyInvokeException(message)


class TuyaAPIException(Exception):
    pass


class TuyaNetException(Exception):
    pass


class TuyaServerException(Exception):
    pass


class TuyaFrequentlyInvokeException(Exception):
    pass
