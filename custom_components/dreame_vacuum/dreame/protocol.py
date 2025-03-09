import logging
import random
import hashlib
import json
import base64
import hmac
import requests
import zlib
import ssl
import queue
from threading import Thread, Timer
from time import sleep
import time, locale
import paho.mqtt
from paho.mqtt.client import Client
from typing import Any, Dict, Optional, Tuple
from Crypto.Cipher import ARC4
from miio.miioprotocol import MiIOProtocol

from .exceptions import DeviceException
from .const import DREAME_STRINGS

_LOGGER = logging.getLogger(__name__)


class DreameVacuumDeviceProtocol(MiIOProtocol):
    def __init__(self, ip: str, token: str) -> None:
        super().__init__(ip, token, 0, 0, True, 2)
        self.ip = None
        self.token = None
        self._queue = queue.Queue()
        self._thread = None
        self.set_credentials(ip, token)

    def _api_task(self):
        while True:
            item = self._queue.get()
            if len(item) == 0:
                self._queue.task_done()
                return
            response = self.send(item[1], item[2], item[3])
            if item[0]:
                item[0](response)
            self._queue.task_done()

    def send_async(self, callback, command, parameters=None, retry_count=2):
        if self._thread is None:
            self._thread = Thread(target=self._api_task, daemon=True)
            self._thread.start()

        self._queue.put((callback, command, parameters, retry_count))

    def set_credentials(self, ip: str, token: str):
        if self.ip != ip or self.token != token:
            self.ip = ip
            self.port = 54321
            self.token = token

            if token is None or token == "":
                token = 32 * "0"
            self.token = bytes.fromhex(token)
            self._discovered = False

    @property
    def connected(self) -> bool:
        return self._discovered

    def disconnect(self):
        self._discovered = False
        if self._thread:
            self._queue.put([])


class DreameVacuumDreameHomeCloudProtocol:
    def __init__(self, username: str, password: str, country: str = "cn", did: str = None) -> None:
        self.two_factor_url = None
        self._username = username
        self._password = password
        self._country = country
        self._location = country
        self._did = did
        self._session = requests.session()
        self._queue = queue.Queue()
        self._thread = None
        self._client_queue = queue.Queue()
        self._client_thread = None
        self._id = random.randint(1, 100)
        self._reconnect_timer = None
        self._host = None
        self._model = None
        self._ti = None
        self._fail_count = 0
        self._connected = False
        self._client_connected = False
        self._client_connecting = False
        self._client = None
        self._message_callback = None
        self._connected_callback = None
        self._logged_in = None
        self._stream_key = None
        self._client_key = None
        self._secondary_key = None
        self._key_expire = None
        self._key = None
        self._uid = None
        self._uuid = None
        self._strings = None

    def _api_task(self):
        while True:
            item = self._queue.get()
            if len(item) == 0:
                self._queue.task_done()
                self._thread = None
                return
            try:
                item[0](self._api_call(item[1], item[2], item[3]))
                sleep(0.1)
            except:
                pass
            self._queue.task_done()

    def _api_call_async(self, callback, url, params=None, retry_count=2):
        if self._thread is None:
            self._thread = Thread(target=self._api_task, daemon=True)
            self._thread.start()

        self._queue.put((callback, url, params, retry_count))

    def _api_call(self, url, params=None, retry_count=2):
        return self.request(
            f"{self.get_api_url()}/{url}",
            json.dumps(params, separators=(",", ":")) if params is not None else None,
            retry_count,
        )

    def get_api_url(self) -> str:
        return f"https://{self._country}{self._strings[0]}:{self._strings[1]}"

    @property
    def device_id(self) -> str:
        return self._did

    @property
    def dreame_cloud(self) -> bool:
        return True

    @property
    def object_name(self) -> str:
        return f"{self._model}/{self._uid}/{str(self._did)}/0"

    @property
    def logged_in(self) -> bool:
        return self._logged_in

    @property
    def connected(self) -> bool:
        return self._connected and self._client_connected

    def _reconnect_timer_cancel(self):
        if self._reconnect_timer is not None:
            self._reconnect_timer.cancel()
            del self._reconnect_timer
            self._reconnect_timer = None

    def _reconnect_timer_task(self):
        self._reconnect_timer_cancel()
        if self._client_connecting and self._client_connected:
            self._client_connected = False
            _LOGGER.warning("Device client reconnect failed! Retrying...")

    def _set_client_key(self) -> bool:
        if self._client_key != self._key:
            self._client_key = self._key
            self._client.username_pw_set(self._uuid, self._client_key)
            return True
        return False
    
    def _client_task(self):
        while True:
            item = self._client_queue.get()
            if len(item) == 0:
                self._client_queue.task_done()
                self._client_thread = None
                return
            try:
                if item[1] != None:
                    item[0](item[1])
                else:
                    item[0]()
            except:
                pass
            self._client_queue.task_done()

    @staticmethod
    def _on_client_connect(client, self, flags, rc):
        self._client_connecting = False
        self._reconnect_timer_cancel()
        if rc == 0:
            if not self._client_connected:
                self._client_connected = True
                _LOGGER.info("Connected to the device client")
            client.subscribe(f"/{self._strings[7]}/{self._did}/{self._uid}/{self._model}/{self._country}/")
            if self._connected_callback:
                self._client_queue.put((self._connected_callback, None))
        else:
            _LOGGER.warning("Device client connection failed: %s", rc)
            if not self._set_client_key():
                self._client_connected = False

    @staticmethod
    def _on_client_disconnect(client, self, rc):
        if rc != 0 and not self._set_client_key():
            if rc == 5 and self._key_expire:
                self.login()
            if self._client_connected:
                if not self._client_connecting:
                    self._client_connecting = True
                    _LOGGER.info("Device Client disconnected (%s) Reconnecting...", rc)
                self._reconnect_timer_cancel()
                self._reconnect_timer = Timer(10, self._reconnect_timer_task)
                self._reconnect_timer.start()

    @staticmethod
    def _on_client_message(client, self, message):
        ## Dirty patch for devices are stuck disconnected, will be refactored later...
        if not self._client_connected:
            self._client_connected = True
            if self._connected_callback:
                self._client_queue.put((self._connected_callback, None))

        if self._message_callback:
            try:
                response = json.loads(message.payload.decode("utf-8"))
                if "data" in response and response["data"]:
                    self._client_queue.put((self._message_callback, response["data"]))
            except:
                pass

    def _handle_device_info(self, info):
        self._uid = info[self._strings[8]]
        self._did = info["did"]
        self._model = info[self._strings[35]]
        self._host = info[self._strings[9]]
        prop = info[self._strings[10]]
        if prop and prop != "":
            prop = json.loads(prop)
            if self._strings[11] in prop:
                self._stream_key = prop[self._strings[11]]

    def connect(self, message_callback=None, connected_callback=None):
        if self._logged_in:
            info = self.get_device_info()
            if info:
                if message_callback:
                    self._message_callback = message_callback
                    self._connected_callback = connected_callback
                    if self._client is None:
                        _LOGGER.info("Connecting to the device client")
                        if self._client_thread is None:
                            self._client_thread = Thread(target=self._client_task, daemon=True)
                            self._client_thread.start()
                            
                        try:
                            host = self._host.split(":")
                            key = f"{self._strings[53]}{self._uid}{self._strings[54]}{DreameVacuumMiHomeCloudProtocol.get_random_agent_id()}{self._strings[54]}{host[0]}"
                            if paho.mqtt.__version__[0] > '1':
                                self._client = Client(
                                    paho.mqtt.client.CallbackAPIVersion.VERSION1,
                                    key,
                                    clean_session=True,
                                    userdata=self,
                                )
                            else:
                                self._client = Client(
                                    key,
                                    clean_session=True,
                                    userdata=self,
                                )
                            self._client.on_connect = DreameVacuumDreameHomeCloudProtocol._on_client_connect
                            self._client.on_disconnect = DreameVacuumDreameHomeCloudProtocol._on_client_disconnect
                            self._client.on_message = DreameVacuumDreameHomeCloudProtocol._on_client_message
                            self._client.reconnect_delay_set(1, 15)
                            self._client.tls_set(cert_reqs=ssl.CERT_NONE)
                            self._client.tls_insecure_set(True)
                            self._set_client_key()
                            self._client.connect(host[0], int(host[1]), 50)
                            self._client.loop_start()
                        except Exception as ex:
                            _LOGGER.error("Connecting to the device client failed: %s", ex)
                    elif not self._client_connected:
                        self._set_client_key()
                self._connected = True
                return info
        return None

    def login(self) -> bool:
        self._session.close()
        self._session = requests.session()
        self._logged_in = False

        if self._strings is None:
            self._strings = json.loads(zlib.decompress(base64.b64decode(DREAME_STRINGS), zlib.MAX_WBITS | 32))

        try:
            if self._secondary_key:
                data = f"{self._strings[12]}{self._strings[13]}{self._secondary_key}"
            else:
                data = f"{self._strings[12]}{self._strings[14]}{self._username}{self._strings[15]}{hashlib.md5((self._password + self._strings[2]).encode('utf-8')).hexdigest()}{self._strings[16]}"

            headers = {
                "Accept": "*/*",
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept-Language": "en-US;q=0.8",
                "Accept-Encoding": "gzip, deflate",
                self._strings[47]: self._strings[3],
                self._strings[49]: self._strings[5],
                self._strings[50]: self._ti if self._ti else self._strings[6],
            }

            if self._country == "cn":
                headers[self._strings[48]] = self._strings[4]

            response = self._session.post(
                self.get_api_url() + self._strings[17],
                headers=headers,
                data=data,
                timeout=10,
            )
            if response.status_code == 200:
                data = json.loads(response.text)
                if self._strings[18] in data:
                    self._key = data.get(self._strings[18])
                    self._secondary_key = data.get(self._strings[19])
                    self._key_expire = time.time() + data.get(self._strings[20]) - 120
                    self._logged_in = True
                    self._uuid = data.get("uid")
                    self._location = data.get(self._strings[21], self._location)
                    self._ti = data.get(self._strings[22], self._ti)
            else:
                try:
                    data = json.loads(response.text)
                    if "error_description" in data and "refresh token" in data["error_description"]:
                        self._secondary_key = None
                        return self.login()
                except:
                    pass
                _LOGGER.error("Login failed: %s", response.text)
        except requests.exceptions.Timeout:
            response = None
            _LOGGER.warning("Login Failed: Read timed out. (read timeout=10)")
        except Exception as ex:
            response = None
            _LOGGER.error("Login failed: %s", str(ex))

        if self._logged_in:
            self._fail_count = 0
            self._connected = True
        return self._logged_in

    def get_devices(self) -> Any:
        response = self._api_call(f"{self._strings[23]}/{self._strings[24]}/{self._strings[27]}/{self._strings[28]}")
        if response:
            if "data" in response and response["code"] == 0:
                return response["data"]
        return None

    def get_device_info(self) -> Any:
        response = self._api_call(
            f"{self._strings[23]}/{self._strings[24]}/{self._strings[27]}/{self._strings[29]}",
            {"did": self._did},
        )
        if response and "data" in response and response["code"] == 0:
            data = response["data"]
            self._handle_device_info(data)
            response = self._api_call(
                f"{self._strings[23]}/{self._strings[25]}/{self._strings[30]}",
                {"did": self._did},
            )
            if response and "data" in response and response["code"] == 0:
                if self._strings[31] in response["data"]:
                    data = {
                        **response["data"][self._strings[31]][self._strings[32]],
                        **data,
                    }
                else:
                    _LOGGER.warning("Get Device OTC Info Retrying with fallback... (%s)", response)
                    devices = self.get_devices()
                    if devices is not None:
                        found = list(
                            filter(
                                lambda d: str(d["did"]) == self._did,
                                devices[self._strings[34]][self._strings[36]],
                            )
                        )
                        if len(found) > 0:
                            self._handle_device_info(found[0])
                            return found[0]
                    _LOGGER.error("Get Device OTC Info Failed!")
                    return None
            return data
        return None

    def get_info(self, mac: str) -> Tuple[Optional[str], Optional[str]]:
        if self._did is not None:
            return " ", self._host
        devices = self.get_devices()
        if devices is not None:
            found = list(
                filter(
                    lambda d: str(d["mac"]) == mac,
                    devices[self._strings[34]][self._strings[36]],
                )
            )
            if len(found) > 0:
                self._handle_device_info(found[0])
                return " ", self._host
        return None, None

    def send_async(self, callback, method, parameters, retry_count: int = 2):
        host = ""
        if self._host and len(self._host):
            host = f"-{self._host.split('.')[0]}"

        self._id = self._id + 1
        self._api_call_async(
            lambda api_response: callback(
                None
                if api_response is None or "data" not in api_response or "result" not in api_response["data"]
                else api_response["data"]["result"]
            ),
            f"{self._strings[37]}{host}/{self._strings[27]}/{self._strings[38]}",
            {
                "did": str(self._did),
                "id": self._id,
                "data": {
                    "did": str(self._did),
                    "id": self._id,
                    "method": method,
                    "params": parameters,
                },
            },
            retry_count,
        )

    def send(self, method, parameters, retry_count: int = 2) -> Any:
        host = ""
        if self._host and len(self._host):
            host = f"-{self._host.split('.')[0]}"

        api_response = self._api_call(
            f"{self._strings[37]}{host}/{self._strings[27]}/{self._strings[38]}",
            {
                "did": str(self._did),
                "id": self._id,
                "data": {
                    "did": str(self._did),
                    "id": self._id,
                    "method": method,
                    "params": parameters,
                },
            },
            retry_count,
        )
        self._id = self._id + 1
        if api_response is None or "data" not in api_response or "result" not in api_response["data"]:
            return None
        return api_response["data"]["result"]

    def get_file(self, url: str, retry_count: int = 4) -> Any:
        retries = 0
        if not retry_count or retry_count < 0:
            retry_count = 0
        while retries < retry_count + 1:
            try:
                response = self._session.get(url, timeout=6)
            except Exception as ex:
                response = None
                _LOGGER.warning("Unable to get file at %s: %s", url, ex)
            if response is not None and response.status_code == 200:
                return response.content
            retries = retries + 1
        return None

    def get_file_url(self, object_name: str = "") -> Any:
        api_response = self._api_call(
            f"{self._strings[23]}/{self._strings[39]}/{self._strings[56]}",
            {
                "did": str(self._did),
                "uid": str(self._uid),
                self._strings[35]: self._model,
                "filename": object_name[1:],
                self._strings[21]: self._country,
            },
        )
        if api_response is None or "data" not in api_response:
            return None

        return api_response["data"]

    def get_interim_file_url(self, object_name: str = "") -> str:
        api_response = self._api_call(
            f"{self._strings[23]}/{self._strings[39]}/{self._strings[55]}",
            {
                "did": str(self._did),
                self._strings[35]: self._model,
                self._strings[40]: object_name,
                self._strings[21]: self._country,
            },
        )
        if api_response is None or "data" not in api_response:
            return None

        return api_response["data"]

    def get_properties(self, keys):
        params = {"did": str(self._did), "keys": keys}
        api_response = self._api_call(f"{self._strings[23]}/{self._strings[25]}/{self._strings[41]}", params)
        if api_response is None or "data" not in api_response:
            return None

        return api_response["data"]

    def get_device_property(self, key, limit=1, time_start=0, time_end=9999999999):
        return self.get_device_data(key, "prop", limit, time_start, time_end)

    def get_device_event(self, key, limit=1, time_start=0, time_end=9999999999):
        return self.get_device_data(key, "event", limit, time_start, time_end)

    def get_device_data(self, key, type, limit=1, time_start=0, time_end=9999999999):
        data_keys = key.split(".")
        params = {
            "uid": str(self._uid),
            "did": str(self._did),
            "from": time_start if time_start else 1687019188,
            "limit": limit,
            "siid": data_keys[0],
            self._strings[21]: self._country,
            self._strings[42]: 3,
        }
        param_name = "piid"
        if type == "event":
            param_name = "eiid"
        elif type == "action":
            param_name = "aiid"

        params[param_name] = data_keys[1]
        api_response = self._api_call(f"{self._strings[23]}/{self._strings[25]}/{self._strings[43]}", params)
        if api_response is None or "data" not in api_response or self._strings[33] not in api_response["data"]:
            return None

        return api_response["data"][self._strings[33]]

    def get_batch_device_datas(self, props) -> Any:
        api_response = self._api_call(
            f"{self._strings[23]}/{self._strings[26]}/{self._strings[44]}",
            {"did": self._did, self._strings[35]: props},
        )
        if api_response is None or "data" not in api_response:
            return None
        return api_response["data"]

    def set_batch_device_datas(self, props) -> Any:
        api_response = self._api_call(
            f"{self._strings[23]}/{self._strings[26]}/{self._strings[45]}",
            {"did": self._did, self._strings[35]: props},
        )
        if api_response is None or "result" not in api_response:
            return None
        return api_response["result"]

    def request(self, url: str, data, retry_count=2) -> Any:
        retries = 0
        if not retry_count or retry_count < 0:
            retry_count = 0
        while retries < retry_count + 1:
            try:
                if self._key_expire and time.time() > self._key_expire:
                    self.login()

                headers = {
                    "Accept": "*/*",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept-Language": "en-US;q=0.8",
                    "Accept-Encoding": "gzip, deflate",
                    self._strings[47]: self._strings[3],
                    self._strings[49]: self._strings[5],
                    self._strings[50]: self._ti if self._ti else self._strings[6],
                    self._strings[51]: self._strings[52],
                    self._strings[46]: self._key,
                }
                if self._country == "cn":
                    headers[self._strings[48]] = self._strings[4]

                response = self._session.post(
                    url,
                    headers=headers,
                    data=data,
                    timeout=3,
                )
                break
            except requests.exceptions.Timeout:
                retries = retries + 1
                response = None
                if self._connected:
                    _LOGGER.warning(
                        "Error while executing request: Read timed out. (read timeout=3): %s",
                        data,
                    )
            except Exception as ex:
                retries = retries + 1
                response = None
                if self._connected:
                    _LOGGER.warning("Error while executing request: %s", str(ex))

        if response is not None:
            if response.status_code == 200:
                self._fail_count = 0
                self._connected = True
                return json.loads(response.text)
            elif response.status_code == 401 and self._secondary_key:
                _LOGGER.debug("Execute api call failed: Token Expired")
                self.login()
            else:
                _LOGGER.warning("Execute api call failed with response: %s", response.text)

        if self._fail_count == 5:
            self._connected = False
        else:
            self._fail_count = self._fail_count + 1
        return None

    def disconnect(self):
        self._session.close()
        self._connected = False
        self._logged_in = False
        if self._client is not None:
            self._client.disconnect()
            self._client.loop_stop()
            self._client = None
            self._client_connected = False
            self._client_connecting = False
        if self._thread:
            self._queue.put([])
        if self._client_thread:
            self._client_queue.put([])
        self._message_callback = None
        self._connected_callback = None


class DreameVacuumMiHomeCloudProtocol:
    def __init__(self, username: str, password: str, country: str) -> None:
        self._username = username
        self._password = password
        self._country = country
        self._session = requests.session()
        self._queue = queue.Queue()
        self._thread = None
        self._sign = None
        self._ssecurity = None
        self._userId = None
        self._cUserId = None
        self._passToken = None
        self._location = None
        self._code = None
        self._service_token = None
        self._logged_in = None
        self._uid = None
        self._did = None
        self.two_factor_url = None
        self._useragent = f"Android-7.1.1-1.0.0-ONEPLUS A3010-136-{DreameVacuumMiHomeCloudProtocol.get_random_agent_id()} APP/xiaomi.smarthome APPV/62830"
        self._locale = locale.getdefaultlocale()[0]
        self._v3 = False

        self._fail_count = 0
        self._connected = False
        try:
            offset = (time.timezone if (time.localtime().tm_isdst == 0) else time.altzone) / 60 * -1
            self._timezone = "GMT{}{:02d}:{:02d}".format(
                "+" if offset >= 0 else "-", abs(int(offset / 60)), int(offset % 60)
            )
        except:
            self._timezone = "GMT+00:00"

    def _api_task(self):
        while True:
            item = self._queue.get()
            if len(item) == 0:
                self._queue.task_done()
                self._thread = None
                return
            item[0](self._api_call(item[1], item[2], item[3]))
            sleep(0.1)
            self._queue.task_done()

    def _api_call_async(self, callback, url, params=None, retry_count=2):
        if self._thread is None:
            self._thread = Thread(target=self._api_task, daemon=True)
            self._thread.start()

        self._queue.put((callback, url, params, retry_count))

    def _api_call(self, url, params, retry_count=2):
        return self.request(
            f"{self.get_api_url()}/{url}",
            {"data": json.dumps(params, separators=(",", ":"))},
            retry_count,
        )

    @property
    def logged_in(self) -> bool:
        return self._logged_in

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def device_id(self) -> str:
        return self._did

    @property
    def dreame_cloud(self) -> bool:
        return False

    @property
    def object_name(self) -> str:
        return f"{str(self._uid)}/{str(self._did)}/0"

    def login_step_1(self) -> bool:
        url = "https://account.xiaomi.com/pass/serviceLogin?sid=xiaomiio&_json=true"
        headers = {
            "User-Agent": self._useragent,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        cookies = {"userId": self._username}
        try:
            response = self._session.get(url, headers=headers, cookies=cookies, timeout=5)
        except:
            response = None
        successful = response is not None and response.status_code == 200 and "_sign" in self.to_json(response.text)
        if successful:
            self._sign = self.to_json(response.text)["_sign"]
        return successful

    def login_step_2(self) -> bool:
        url = "https://account.xiaomi.com/pass/serviceLoginAuth2"
        headers = {
            "User-Agent": self._useragent,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        fields = {
            "sid": "xiaomiio",
            "hash": hashlib.md5(str.encode(self._password)).hexdigest().upper(),
            "callback": "https://sts.api.io.mi.com/sts",
            "qs": "%3Fsid%3Dxiaomiio%26_json%3Dtrue",
            "user": self._username,
            "_json": "true",
        }
        if self._sign:
            fields["_sign"] = self._sign

        try:
            response = self._session.post(url, headers=headers, params=fields, timeout=5)
        except:
            response = None
        successful = response is not None and response.status_code == 200
        if successful:
            json_resp = self.to_json(response.text)
            successful = "ssecurity" in json_resp and len(str(json_resp["ssecurity"])) > 4
            if successful:
                self._ssecurity = json_resp["ssecurity"]
                self._userId = json_resp["userId"]
                self._cUserId = json_resp["cUserId"]
                self._passToken = json_resp["passToken"]
                self._location = json_resp["location"]
                self._code = json_resp["code"]
                self.two_factor_url = None
            else:
                if "notificationUrl" in json_resp and self.two_factor_url is None:
                    self.two_factor_url = json_resp["notificationUrl"]
                    if self.two_factor_url[:4] != "http":
                        self.two_factor_url = f"https://account.xiaomi.com{self.two_factor_url}"

                    _LOGGER.error(
                        "Additional authentication required. Open following URL using device that has the same public IP, as your Home Assistant instance: %s ",
                        self.two_factor_url,
                    )

                successful = False

        if successful:
            self.two_factor_url = None

        return successful

    def login_step_3(self) -> bool:
        headers = {
            "User-Agent": self._useragent,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        try:
            response = self._session.get(self._location, headers=headers, timeout=5)
        except:
            response = None
        successful = response is not None and response.status_code == 200 and "serviceToken" in response.cookies
        if successful:
            self._service_token = response.cookies.get("serviceToken")
        return successful

    def login(self) -> bool:
        self._session.close()
        self._session = requests.session()
        self._device = DreameVacuumMiHomeCloudProtocol.generate_device_id()
        self._session.cookies.set("sdkVersion", "3.8.6", domain="mi.com")
        self._session.cookies.set("sdkVersion", "3.8.6", domain="xiaomi.com")
        self._session.cookies.set("deviceId", self._device, domain="mi.com")
        self._session.cookies.set("deviceId", self._device, domain="xiaomi.com")
        self._logged_in = self.login_step_1() and self.login_step_2() and self.login_step_3()
        if self._logged_in:
            self._fail_count = 0
            self._connected = True
        return self._logged_in

    def get_file(self, url: str, retry_count: int = 4) -> Any:
        retries = 0
        if not retry_count or retry_count < 0:
            retry_count = 0
        while retries < retry_count + 1:
            try:
                response = self._session.get(url, timeout=6)
            except Exception as ex:
                response = None
                _LOGGER.warning("Unable to get file at %s: %s", url, ex)
            if response is not None and response.status_code == 200:
                return response.content
            retries = retries + 1
        return None

    def get_file_url(self, object_name: str = "") -> Any:
        api_response = self._api_call(f'home/getfileurl{("_v3" if self._v3 else "")}', {"obj_name": object_name})
        _LOGGER.debug("Get file url result: %s = %s", object_name, api_response)
        if api_response is None or "result" not in api_response or "url" not in api_response["result"]:
            if api_response and api_response.get("code") == -8 and self._v3:
                _LOGGER.info("get_file_url fallback to V2")
                self._v3 = False
                return self.get_file_url(object_name)
            return None

        return api_response["result"]["url"]

    def get_interim_file_url(self, object_name: str = "") -> str:
        api_response = self._api_call(
            f'v2/home/get_interim_file_url{("_pro" if self._v3 else "")}',
            {"obj_name": object_name},
        )
        _LOGGER.debug("Get interim file url result: %s = %s", object_name, api_response)
        if api_response is None or not api_response.get("result") or "url" not in api_response["result"]:
            if api_response and api_response.get("code") == -8 and self._v3:
                _LOGGER.info("get_interim_file_url fallback to V2")
                self._v3 = False
                return self.get_interim_file_url(object_name)
            return None

        return api_response["result"]["url"]

    def send_async(self, callback, method, parameters, retry_count: int = 2):
        self._api_call_async(
            lambda api_response: callback(
                None if api_response is None or "result" not in api_response else api_response["result"]
            ),
            f"v2/home/rpc/{self._did}",
            {"method": method, "params": parameters},
            retry_count,
        )

    def send(self, method, parameters, retry_count: int = 2) -> Any:
        api_response = self._api_call(
            f"v2/home/rpc/{self._did}",
            {"method": method, "params": parameters},
            retry_count,
        )
        if api_response is None or "result" not in api_response:
            return None
        return api_response["result"]

    def get_device_property(self, key, limit=1, time_start=0, time_end=9999999999):
        return self.get_device_data(key, "prop", limit, time_start, time_end)

    def get_device_event(self, key, limit=1, time_start=0, time_end=9999999999):
        return self.get_device_data(key, "event", limit, time_start, time_end)

    def get_device_data(self, key, type, limit=1, time_start=0, time_end=9999999999):
        api_response = self._api_call(
            "user/get_user_device_data",
            {
                "uid": str(self._uid),
                "did": str(self._did),
                "time_end": time_end,
                "time_start": time_start,
                "limit": limit,
                "key": key,
                "type": type,
            },
        )
        if api_response is None or "result" not in api_response:
            return None

        return api_response["result"]

    def get_info(self, mac: str) -> Tuple[Optional[str], Optional[str]]:
        devices = self.get_devices()
        if devices:
            found = list(filter(lambda d: str(d["mac"]) == mac, devices))

            if len(found) > 0:
                self._uid = found[0]["uid"]
                self._did = found[0]["did"]
                self._v3 = bool("model" in found[0] and "xiaomi.vacuum." in found[0]["model"])
                return found[0]["token"], found[0]["localip"]
        return None, None

    def get_devices(self) -> Any:
        device_list = []
        response = self._api_call(
            "v2/homeroom/gethome",
            {
                "fg": True,
                "fetch_share": True,
                "fetch_share_dev": True,
                "limit": 100,
                "app_ver": 7,
            },
        )
        if response and "result" in response and response["result"]:
            homes = {}
            for home in response["result"].get("homelist"):
                homes[home["id"]] = self._userId

            response = self._api_call(
                "v2/user/get_device_cnt",
                {
                    "fetch_own": True,
                    "fetch_share": True,
                },
            )
            if (
                response
                and "result" in response
                and response["result"]
                and "share" in response["result"]
                and response["result"]["share"]
            ):
                for device in response["result"]["share"].get("share_family"):
                    homes[device["home_id"]] = device["home_owner"]

            if homes:
                for k, v in homes.items():
                    response = self._api_call(
                        "v2/home/home_device_list",
                        {
                            "home_id": int(k),
                            "home_owner": v,
                            "limit": 100,
                            "get_split_device": True,
                            "support_smart_home": True,
                        },
                    )
                    if (
                        response
                        and "result" in response
                        and response["result"]
                        and "device_info" in response["result"]
                        and response["result"]["device_info"]
                    ):
                        device_list.extend(response["result"]["device_info"])

            response = self._api_call("home/device_list", {"getVirtualModel": False, "getHuamiDevices": 0})
            if (
                response
                and "result" in response
                and response["result"]
                and "list" in response["result"]
                and response["result"]["list"]
            ):
                for device in response["result"]["list"]:
                    if (
                        len(
                            list(
                                filter(
                                    lambda d: str(d["mac"]) == device["mac"],
                                    device_list,
                                )
                            )
                        )
                        == 0
                    ):
                        device_list.append(device)

            return device_list

    def get_batch_device_datas(self, props) -> Any:
        api_response = self._api_call("device/batchdevicedatas", [{"did": self._did, "props": props}])
        if api_response is None or self._did not in api_response:
            return None
        return api_response[self._did]

    def set_batch_device_datas(self, props) -> Any:
        api_response = self._api_call("v2/device/batch_set_props", [{"did": self._did, "props": props}])
        if api_response is None or "result" not in api_response:
            return None
        return api_response["result"]

    def request(self, url: str, params: Dict[str, str], retry_count=2) -> Any:
        retries = 0
        if not retry_count or retry_count < 0:
            retry_count = 0
        headers = {
            "User-Agent": self._useragent,
            "Accept-Encoding": "identity",
            "x-xiaomi-protocal-flag-cli": "PROTOCAL-HTTP2",
            "content-type": "application/x-www-form-urlencoded",
            "MIOT-ENCRYPT-ALGORITHM": "ENCRYPT-RC4",
        }
        cookies = {
            "userId": str(self._userId),
            "yetAnotherServiceToken": self._service_token,
            "serviceToken": self._service_token,
            "locale": str(self._locale),
            "timezone": str(self._timezone),
            "is_daylight": str(time.daylight),
            "dst_offset": str(time.localtime().tm_isdst * 60 * 60 * 1000),
            "channel": "MI_APP_STORE",
        }

        nonce = self.generate_nonce()
        signed_nonce = self.signed_nonce(nonce)
        fields = self.generate_enc_params(url, "POST", signed_nonce, nonce, params, self._ssecurity)

        while retries < retry_count + 1:
            try:
                response = self._session.post(url, headers=headers, cookies=cookies, data=fields, timeout=5)
                break
            except Exception as ex:
                retries = retries + 1
                response = None
                if self._connected:
                    _LOGGER.warning("Error while executing request: %s %s", url, str(ex))

        if response is not None:
            if response.status_code == 200:
                self._fail_count = 0
                self._connected = True
                decoded = self.decrypt_rc4(self.signed_nonce(fields["_nonce"]), response.text)
                return json.loads(decoded) if decoded else None
            _LOGGER.warning("Execute api call failed with response: %s", response.text)

        if self._fail_count == 5:
            self._connected = False
        else:
            self._fail_count = self._fail_count + 1
        return None

    def get_api_url(self) -> str:
        return f"https://{('' if self._country == 'cn' else (self._country + '.'))}api.io.mi.com/app"

    def signed_nonce(self, nonce: str) -> str:
        hash_object = hashlib.sha256(base64.b64decode(self._ssecurity) + base64.b64decode(nonce))
        return base64.b64encode(hash_object.digest()).decode("utf-8")

    def disconnect(self):
        self._session.close()
        self._connected = False
        self._logged_in = False
        if self._thread:
            self._queue.put([])

    @staticmethod
    def generate_nonce():
        millis = int(round(time.time() * 1000))
        b = (random.getrandbits(64) - 2**63).to_bytes(8, "big", signed=True)
        part2 = int(millis / 60000)
        b += part2.to_bytes(((part2.bit_length() + 7) // 8), "big")
        return base64.b64encode(b).decode("utf-8")

    @staticmethod
    def generate_device_id() -> str:
        return "".join((chr(random.randint(97, 122)) for _ in range(6)))

    @staticmethod
    def generate_signature(url, signed_nonce: str, nonce: str, params: Dict[str, str]) -> str:
        signature_params = [url.split("com")[1], signed_nonce, nonce]
        for k, v in params.items():
            signature_params.append(f"{k}={v}")
        signature_string = "&".join(signature_params)
        signature = hmac.new(
            base64.b64decode(signed_nonce),
            msg=signature_string.encode(),
            digestmod=hashlib.sha256,
        )
        return base64.b64encode(signature.digest()).decode()

    @staticmethod
    def generate_enc_signature(url, method: str, signed_nonce: str, params: Dict[str, str]) -> str:
        signature_params = [
            str(method).upper(),
            url.split("com")[1].replace("/app/", "/"),
        ]
        for k, v in params.items():
            signature_params.append(f"{k}={v}")
        signature_params.append(signed_nonce)
        signature_string = "&".join(signature_params)
        return base64.b64encode(hashlib.sha1(signature_string.encode("utf-8")).digest()).decode()

    @staticmethod
    def generate_enc_params(
        url: str,
        method: str,
        signed_nonce: str,
        nonce: str,
        params: Dict[str, str],
        ssecurity: str,
    ) -> Dict[str, str]:
        params["rc4_hash__"] = DreameVacuumMiHomeCloudProtocol.generate_enc_signature(
            url, method, signed_nonce, params
        )
        for k, v in params.items():
            params[k] = DreameVacuumMiHomeCloudProtocol.encrypt_rc4(signed_nonce, v)
        params.update(
            {
                "signature": DreameVacuumMiHomeCloudProtocol.generate_enc_signature(url, method, signed_nonce, params),
                "ssecurity": ssecurity,
                "_nonce": nonce,
            }
        )
        return params

    @staticmethod
    def to_json(response_text: str) -> Any:
        return json.loads(response_text.replace("&&&START&&&", ""))

    @staticmethod
    def encrypt_rc4(password: str, payload: str) -> str:
        r = ARC4.new(base64.b64decode(password))
        r.encrypt(bytes(1024))
        return base64.b64encode(r.encrypt(payload.encode())).decode()

    @staticmethod
    def decrypt_rc4(password: str, payload: str) -> bytes:
        r = ARC4.new(base64.b64decode(password))
        r.encrypt(bytes(1024))
        return r.encrypt(base64.b64decode(payload))

    @staticmethod
    def get_random_agent_id() -> str:
        letters = "ABCDEF"
        result_str = "".join(random.choice(letters) for i in range(13))
        return result_str


class DreameVacuumProtocol:
    def __init__(
        self,
        ip: str = None,
        token: str = None,
        username: str = None,
        password: str = None,
        country: str = None,
        prefer_cloud: bool = False,
        account_type: str = "mi",
        device_id: str = None,
    ) -> None:
        self.prefer_cloud = prefer_cloud
        self._connected = False
        self._mac = None
        self._account_type = account_type

        if ip and token:
            self.device = DreameVacuumDeviceProtocol(ip, token)
        else:
            self.prefer_cloud = True
            self.device = None

        if username and password and country:
            if account_type == "mi":
                self.cloud = DreameVacuumMiHomeCloudProtocol(username, password, country)
            else:
                self.cloud = DreameVacuumDreameHomeCloudProtocol(username, password, country, device_id)
        else:
            self.prefer_cloud = False
            self.cloud = None

        if account_type == "mi":
            self.device_cloud = DreameVacuumMiHomeCloudProtocol(username, password, country) if prefer_cloud else None
        else:
            self.prefer_cloud = True
            self.device_cloud = self.cloud

    def set_credentials(self, ip: str, token: str, mac: str = None, account_type: str = "mi"):
        self._mac = mac
        self._account_type = account_type
        if ip and token and account_type == "mi":
            if self.device:
                self.device.set_credentials(ip, token)
            else:
                self.device = DreameVacuumDeviceProtocol(ip, token)
        else:
            self.device = None

    def connect(self, message_callback=None, connected_callback=None, retry_count=1) -> Any:
        if self._account_type == "mi" or self.cloud is None:
            response = self.send("miIO.info", retry_count=retry_count)
            if (self.prefer_cloud or not self.device) and self.device_cloud and response:
                self._connected = True
            return response
        else:
            info = self.cloud.connect(message_callback, connected_callback)
            if info:
                self._connected = True
            return info

    def disconnect(self):
        if self.device is not None:
            self.device.disconnect()
        if self.cloud is not None:
            self.cloud.disconnect()
        if self.device_cloud is not None:
            self.device_cloud.disconnect()
        self._connected = False

    def send_async(self, callback, method, parameters: Any = None, retry_count: int = 2):
        if (self.prefer_cloud or not self.device) and self.device_cloud:
            if not self.device_cloud.logged_in:
                # Use different session for device cloud
                self.device_cloud.login()
                if self.device_cloud.logged_in and not self.device_cloud.device_id:
                    if self.cloud.device_id:
                        self.device_cloud._did = self.cloud.device_id
                    elif self._mac:
                        self.device_cloud.get_info(self._mac)

            if not self.device_cloud.logged_in:
                raise DeviceException("Unable to login to device over cloud") from None

            def cloud_callback(response):
                if response is None:
                    if method == "get_properties" or method == "set_properties":
                        self._connected = False
                    raise DeviceException("Unable to discover the device over cloud") from None
                self._connected = True
                callback(response)

            self.device_cloud.send_async(cloud_callback, method, parameters=parameters, retry_count=retry_count)
            return

        if self.device:
            self.device.send_async(callback, method, parameters=parameters, retry_count=retry_count)

    def send(self, method, parameters: Any = None, retry_count: int = 2) -> Any:
        if (self.prefer_cloud or not self.device) and self.device_cloud:
            if not self.device_cloud.logged_in:
                # Use different session for device cloud
                self.device_cloud.login()
                if self.device_cloud.logged_in and not self.device_cloud.device_id:
                    if self.cloud.device_id:
                        self.device_cloud._did = self.cloud.device_id
                    elif self._mac:
                        self.device_cloud.get_info(self._mac)

            if not self.device_cloud.logged_in:
                raise DeviceException("Unable to login to device over cloud") from None

            response = self.device_cloud.send(method, parameters=parameters, retry_count=retry_count)
            if response is None:
                if method == "get_properties" or method == "set_properties":
                    self._connected = False
                raise DeviceException("Unable to discover the device over cloud") from None
            self._connected = True
            return response

        if self.device:
            return self.device.send(method, parameters=parameters, retry_count=retry_count)

    def get_properties(self, parameters: Any = None, retry_count: int = 1) -> Any:
        return self.send("get_properties", parameters=parameters, retry_count=retry_count)

    def set_property(self, siid: int, piid: int, value: Any = None, retry_count: int = 2) -> Any:
        return self.set_properties(
            [
                {
                    "did": f"{siid}.{piid}" if not self.dreame_cloud else str(self.cloud.device_id),
                    "siid": siid,
                    "piid": piid,
                    "value": value,
                }
            ],
            retry_count=retry_count,
        )

    def set_properties(self, parameters: Any = None, retry_count: int = 2) -> Any:
        return self.send("set_properties", parameters=parameters, retry_count=retry_count)

    def action_async(self, callback, siid: int, aiid: int, parameters=[], retry_count: int = 2):
        if parameters is None:
            parameters = []

        _LOGGER.debug("Send Action Async: %s.%s %s", siid, aiid, parameters)
        self.send_async(
            callback,
            "action",
            parameters={
                "did": f"{siid}.{aiid}" if not self.dreame_cloud else str(self.cloud.device_id),
                "siid": siid,
                "aiid": aiid,
                "in": parameters,
            },
            retry_count=retry_count,
        )

    def action(self, siid: int, aiid: int, parameters=[], retry_count: int = 2) -> Any:
        if parameters is None:
            parameters = []

        _LOGGER.debug("Send Action: %s.%s %s", siid, aiid, parameters)
        return self.send(
            "action",
            parameters={
                "did": f"{siid}.{aiid}" if not self.dreame_cloud else str(self.cloud.device_id),
                "siid": siid,
                "aiid": aiid,
                "in": parameters,
            },
            retry_count=retry_count,
        )

    @property
    def connected(self) -> bool:
        if (self.prefer_cloud or not self.device) and self.device_cloud:
            return self.device_cloud.logged_in and self.device_cloud.connected and self._connected

        if self.device:
            return self.device.connected

        return False

    @property
    def dreame_cloud(self) -> bool:
        if self.cloud:
            return self.cloud.dreame_cloud
        return False
