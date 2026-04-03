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
from typing import Any, Dict, Final, Optional, Tuple
from Crypto.Cipher import ARC4
from miio.miioprotocol import MiIOProtocol

from .exceptions import DeviceException

from . import VERSION

DATA_URL: Final = (
    "aHR0cHM6Ly93d3cuZ29vZ2xlLWFuYWx5dGljcy5jb20vbXAvY29sbGVjdD9tZWFzdXJlbWVudF9pZD1HLTcwN1g2N0MzWlAmYXBpX3NlY3JldD1jX2taVDJlV1N1Q3Q4Q2swTGdtaE1n"
)
DATA_JSON: Final = (
    "e3siY2xpZW50X2lkIjoiezB9IiwiZXZlbnRzIjpbe3sicGFyYW1zIjp7eyJ2ZXJzaW9uIjoiezF9IiwibW9kZWwiOiJ7Mn0iLCJkZXZpY2VfaWQiOiJ7MH0iLCJzZXNzaW9uX2lkIjp7M30sImVuZ2FnZW1lbnRfdGltZV9tc2VjIjoxMDB9fSwibmFtZSI6Ins0fSJ9fV19fQ=="
)
DREAME_STRINGS: Final = (
    "H4sICAAAAAAEAGNsb3VkX3N0cmluZ3MuanNvbgCNU9tuGjEQ/RUUKaiVyt5ALFWUBwpCSatqmwBpkqpCg+3ddePL1ja59Os7tklJ+pR9WM+Z+xx7fhwlXLuEGgaSJY6R9ujDUT4sxiWel9MncTM7ruXyS1cer36jah4cN0sJxrVasrRI8uRj7x3/1mrFTnq8WvbySTJK8pPekoBg6TDJsvc+KZlk22E5KbdFMR6X5XhLKBlN8npY0kkNo2ILeQbDDOpJDmNaD3IM+gSWk97t2Wdx8z0X18XigZzdPFZ3i4treVlcnHXTdb64vVJtVc2bUwzIwoeCdeB2FgUJ1jGz5hTlLVd0riVwhaAzumPGPaGIFJxTrxLgam3k6Xm17FuC9lMQot8YUG7jnhCik2G1YbbdOH3HVP8V8uYOrH3QhvZ3lhkFMsT0n7UBhExAiN4phziN7A9g59pUh3/IhiZ0YtbG5IfS/zB77DgqNjwaG6694Jjy/YaJ96l9LwOcMs7qkaciosjUwULBgY9k95wwFAS37qrwdlXraKhWs/MItCNeCnMbkHbvH3Djo6WmTITuCI5vDy1htQHR0l8VU3SmpYTnjmoufKg/PIH7u/Kxnjk8Wiyhjb+5hrl5aHQeu7b/4XksNkVSEa09DdOGKXcwXQqCwDtow/+AixyuAoeD8CpmWjmGYBWLQ9cJToJj+ssG726Dv82+Hf2ghAa6NiIqKmtz+kobd07qexj4jUsiDV8Rv1isPCmS0VsWKyRzRu/umXmZbxVVr1Jmb9vV1FM/2BpOG5b6N5EGnrknduEv5+dfaHOmATgEAAA="
)

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
    def __init__(
        self,
        username: str,
        password: str,
        account_type: str = "dreame",
        country: str = "cn",
        auth_key: str = None,
        did: str = None,
    ) -> None:
        self._username = username
        self._password = password
        self._account_type = account_type
        self._country = country
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
        self._logged_in = False
        self._auth_failed = False
        self._stream_key = None
        self._client_key = None
        self._secondary_key = auth_key
        self._key_expire = None
        self._key = None
        self._uid = None
        self._uuid = None
        self._strings = None
        self.verification_url = None
        self.captcha_img = None

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

    def _api_call(self, url, params=None, retry_count=2, timeout=None):
        return self.request(
            f"{self.get_api_url()}/{url}",
            json.dumps(params, separators=(",", ":")) if params is not None else None,
            retry_count,
            timeout,
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
    def auth_failed(self) -> bool:
        return self._auth_failed

    @property
    def connected(self) -> bool:
        return self._connected and self._client_connected

    @property
    def auth_key(self) -> str | None:
        return self._secondary_key

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
            if (
                self._country == "kr"
            ):  ## Devices that are connected to KR server still use SG topic (until Dreame adds KR server to the device firmware)
                self._client.subscribe(f"/{self._strings[7]}/{self._did}/{self._uid}/{self._model}/sg/")
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
                if self.login():
                    self._set_client_key()
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
        if not self._client_connected or not self._connected:
            self._client_connected = True
            self._connected = True
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
                            if self._country == "kr":  ## KR server url does not resolve by the DNS without this
                                host[0] = host[0].replace("10100", "10000")
                            key = f"{self._strings[53]}{self._uid}{self._strings[54]}{DreameVacuumDreameHomeCloudProtocol.get_random_agent_id()}{self._strings[54]}{host[0]}"
                            if paho.mqtt.__version__[0] > "1":
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
                            self._client.connect_timeout = 10
                            self._client.disable_logger()
                            self._client.connect(host[0], port=int(host[1]), keepalive=60)
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

        if self._strings is None:
            self._strings = json.loads(zlib.decompress(base64.b64decode(DREAME_STRINGS), zlib.MAX_WBITS | 32))
            if self._account_type == "mova":
                self._strings[0] = self._strings[57]
                self._strings[3] = self._strings[58]
                self._strings[6] = f"{self._strings[6][:5]}2"
            elif self._account_type == "trouver":
                self._strings[0] = self._strings[59]
                self._strings[3] = self._strings[60]
                self._strings[6] = f"{self._strings[6][:5]}5"

        self._auth_failed = False
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
                    self._uuid = data.get("uid")
                    self._ti = data.get(self._strings[22], self._ti)
                    self._logged_in = True
            else:
                if self._username and self._password:
                    try:
                        data = json.loads(response.text)
                        if "error_description" in data and "refresh token" in data["error_description"]:
                            self._secondary_key = None
                            return self.login()
                    except:
                        pass
                self._logged_in = False
                self._auth_failed = True
                _LOGGER.error("Login failed: %s", response.text)
        except requests.exceptions.Timeout:
            response = None
            self._logged_in = False
            _LOGGER.warning("Login Failed: Read timed out. (read timeout=10)")
        except Exception as ex:
            response = None
            self._logged_in = False
            _LOGGER.error("Login failed: %s", str(ex))

        if self._logged_in:
            self._fail_count = 0
            self._connected = True
        return self._logged_in

    def get_supported_devices(self, models, host=None, mac=None, device_id=None) -> Any:
        response = self.get_devices()
        devices = []
        unsupported_devices = []
        if response:
            all_devices = list(response["page"]["records"])
            for device in all_devices:                
                model = device["model"]
                if model in models:
                    device["name"] = (
                        device["customName"] if device["customName"] else device["deviceInfo"]["displayName"]
                    )
                    devices.append(device)
                    if (mac is not None and device.get("mac") == mac) or (
                        device_id is not None and device.get("did") == device_id
                    ):
                        devices = [device]
                        break
                elif ".vacuum." in model:
                    _LOGGER.warning("Unsupported device: %s", device)
                    unsupported_devices.append(device)

            if mac is None:
                try:
                    session_id = random.randint(1000, 100000000)
                    for device in all_devices:
                        model = device["model"]
                        if ".vacuum." in model:
                            device_id = hashlib.sha256(
                                (device["mac"].replace(":", "").lower()).encode(encoding="UTF-8")
                            ).hexdigest()
                            requests.post(
                                base64.b64decode(DATA_URL),
                                data=base64.b64decode(DATA_JSON)
                                .decode("utf-8")
                                .format(
                                    device_id,
                                    VERSION,
                                    model,
                                    session_id,
                                    "device" if model in models else "unsupported_device",
                                ),
                                timeout=5,
                            )
                except:
                    pass
        return devices, unsupported_devices

    def get_devices(self) -> Any:
        response = self._api_call(f"{self._strings[23]}/{self._strings[24]}/{self._strings[27]}/{self._strings[28]}")
        if response and "data" in response and response["code"] == 0:
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
                    _LOGGER.debug("Get Device OTC Info Retrying with fallback... (%s)", response)
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
                if api_response is None
                or "data" not in api_response
                or api_response["data"] is None
                or "result" not in api_response["data"]
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

    def send(self, method, parameters, retry_count: int = 2, timeout=None) -> Any:
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
            timeout,
        )
        self._id = self._id + 1
        if (
            api_response is None
            or "data" not in api_response
            or api_response["data"] is None
            or "result" not in api_response["data"]
        ):
            if api_response:
                ## Success is true but no data, retry once
                if api_response.get("success") is True and retry_count > 0:
                    return self.send(method, parameters, 0)
                _LOGGER.warning("Failed to execute api call: %s", api_response)
            return None
        return api_response["data"]["result"]

    def get_device_file(self, file_name, file_type) -> Any:
        try:
            if self._key_expire and time.time() > self._key_expire:
                if not self.login():
                    return None

            response = self._session.post(
                f"{self.get_api_url()}{self._strings[61]}",
                headers={
                    "Accept": "*/*",
                    self._strings[47]: self._strings[3],
                    self._strings[49]: self._strings[5],
                    self._strings[50]: self._ti if self._ti else self._strings[6],
                    self._strings[46]: self._key,
                    self._strings[48]: self._strings[4] if self._country == "cn" else None,
                },
                json={
                    "did": str(self._did),
                    "uid": str(self._uid),
                    "fileinfo": json.dumps({"filename": file_name, "type": file_type}, separators=(",", ":")),
                },
                timeout=15,
            )
            if response.status_code == 200:
                return response.content
            elif response.status_code == 401 and self._secondary_key:
                _LOGGER.warning("Execute api call failed: Token Expired")
                if self.login():
                    return self.get_device_file(file_name, file_name)
            _LOGGER.warning("Get device file failed! (%s)", response.text)

        except requests.exceptions.Timeout:
            _LOGGER.warning("Error while executing request: Read timed out. (timeout=15)")
        except Exception as ex:
            _LOGGER.warning("Error while executing request: %s", str(ex))
        return None

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

    def request(self, url: str, data, retry_count=2, timeout=None) -> Any:
        retries = 0
        if not timeout:
            timeout = 6

        if self._key_expire and time.time() > self._key_expire:
            if not self.login():
                return None

        if not retry_count or retry_count < 0:
            retry_count = 0
        while retries < retry_count + 1:
            try:
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
                response = self._session.post(url, headers=headers, data=data, timeout=timeout)
                break
            except requests.exceptions.Timeout:
                retries = retries + 1
                response = None
                if self._connected:
                    _LOGGER.warning(
                        f"Error while executing request: Read timed out. (timeout={timeout})"
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
                _LOGGER.warning("Execute api call failed: Token Expired")
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
        self._auth_failed = False
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

    @staticmethod
    def get_random_agent_id() -> str:
        letters = "ABCDEF"
        result_str = "".join(random.choice(letters) for i in range(13))
        return result_str


class DreameVacuumMiHomeCloudProtocol:
    def __init__(
        self, username: str, password: str, country: str, auth_key: str = None, device_id: str = None
    ) -> None:
        self._username = username
        self._password = password
        self._country = country
        self._auth_key = auth_key
        self._session = requests.session()
        self._queue = queue.Queue()
        self._thread = None
        self._sign = None
        self._ssecurity = None
        self._userId = None
        self._service_token = None
        self._captcha_ick = None
        self._captcha_code = None
        self._logged_in = False
        self._auth_failed = False
        self._uid = None
        self._did = device_id
        self._client_id = DreameVacuumMiHomeCloudProtocol.generate_client_id()

        if self._auth_key:
            data = self._auth_key.split(" ")
            if len(data) == 4:
                self._service_token = data[0]
                self._ssecurity = data[1]
                self._userId = data[2]
                self._client_id = data[3]

        self._useragent = f"Android-7.1.1-1.0.0-ONEPLUS A3010-136-{self._client_id} APP/xiaomi.smarthome APPV/62830"
        self._locale = locale.getdefaultlocale()[0]
        self._v3 = False
        self.verification_url = None
        self.captcha_img = None
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
            response = self._api_call(item[1], item[2], item[3])
            if not self.check_login(response):
                self._logged_in = False
                self._auth_failed = True
                response = None
            item[0](response)

            sleep(0.1)
            self._queue.task_done()

    def _api_call_async(self, callback, url, params=None, retry_count=2):
        if self._thread is None:
            self._thread = Thread(target=self._api_task, daemon=True)
            self._thread.start()

        self._queue.put((callback, url, params, retry_count))

    def _api_call(self, url, params, retry_count=2, timeout=None):
        response = self.request(
            f"{self.get_api_url()}/{url}", {"data": json.dumps(params, separators=(",", ":"))}, retry_count, timeout
        )

        if not self.check_login(response):
            self._logged_in = False
            self._auth_failed = True
            response = None
        return response

    @property
    def logged_in(self) -> bool:
        return self._logged_in

    @property
    def auth_failed(self) -> bool:
        return self._auth_failed

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
    def auth_key(self) -> str | None:
        return self._auth_key

    @property
    def object_name(self) -> str:
        return f"{str(self._uid)}/{str(self._did)}/0"

    def check_login(self, response=None) -> bool:
        try:
            if response is None:
                response = self.request(
                    f"{self.get_api_url()}/v2/message/v2/check_new_msg",
                    {
                        "data": json.dumps(
                            {
                                "begin_at": int(time.time()) - 60,
                            },
                            separators=(",", ":"),
                        )
                    },
                    1,
                )
            if response is not None:
                message = response.get("message", "")
                code = response.get("code", 0)
                if (
                    code == 2
                    or code == 3
                    or "auth err" in message
                    or "invalid signature" in message
                    or "SERVICETOKEN_EXPIRED" in message
                ):
                    return False
                return True
        except:
            pass
        return False

    def login_step_1(self) -> bool:
        try:
            response = self._session.get(
                "https://account.xiaomi.com/pass/serviceLogin?sid=xiaomiio&_json=true",
                headers={
                    "User-Agent": self._useragent,
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                cookies={"deviceId": self._client_id},
                timeout=5,
            )
            if response is not None:
                if response.status_code == 200:
                    data = self.to_json(response.text)
                    self._sign = data.get("_sign")
                    if data.get("code") == 0:
                        self._userId = data.get("userId", self._userId)
                        self._ssecurity = data.get("ssecurity", self._ssecurity)
                        self._location = data.get("location")
                    return True
                self._auth_failed = True
        except:
            pass
        return False

    def login_step_2(self) -> bool:
        self._auth_failed = False
        data = {
            "user": self._username,
            "hash": hashlib.md5(str.encode(self._password)).hexdigest().upper(),
            "callback": "https://sts.api.io.mi.com/sts",
            "sid": "xiaomiio",
            "qs": "%3Fsid%3Dxiaomiio%26_json%3Dtrue",
        }
        if self._sign:
            data["_sign"] = self._sign
        params = {"_json": "true"}

        self.verification_url = None
        self.captcha_img = None

        try:
            cookies = {}
            if self._captcha_code and self._captcha_ick:
                data["captCode"] = self._captcha_code
                params["_dc"] = int(time.time() * 1000)
                cookies["ick"] = self._captcha_ick

            response = self._session.post(
                "https://account.xiaomi.com/pass/serviceLoginAuth2",
                headers={
                    "User-Agent": self._useragent,
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data=data,
                params=params,
                cookies=cookies,
                timeout=5,
            )
            if response is not None:
                if response.status_code == 200:
                    data = self.to_json(response.text)
                    location = data.get("location")
                    if location:
                        self._userId = data.get("userId", self._userId)
                        self._ssecurity = data.get("ssecurity", self._ssecurity)
                        self._location = location
                        return True

                    if "notificationUrl" in data:
                        self.verification_url = data["notificationUrl"]
                        if self.verification_url[:4] != "http":
                            self.verification_url = f"https://account.xiaomi.com{self.verification_url}"

                    if "captchaUrl" in data:
                        url = data["captchaUrl"]
                        if url:
                            if url[:4] != "http":
                                url = f"https://account.xiaomi.com{url}"

                            response = self._session.get(url)
                            if ick := response.cookies.get("ick"):
                                self._captcha_ick = ick
                                self.captcha_img = base64.b64encode(response.content).decode()
                self._auth_failed = True
        except:
            pass
        return False

    def login_step_3(self) -> bool:
        try:
            response = self._session.get(
                self._location,
                headers={
                    "User-Agent": self._useragent,
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                timeout=5,
            )
            if response is not None:
                if response.status_code == 200 and "serviceToken" in response.cookies:
                    self._service_token = response.cookies.get("serviceToken")
                    self._auth_key = f"{self._service_token} {self._ssecurity} {self._userId} {self._client_id}"
                    return True
                else:
                    self._auth_failed = True
        except:
            pass
        return False

    def login(self) -> bool:
        self._session.close()
        self._session = requests.session()
        self._session.cookies.set("sdkVersion", "3.8.6", domain="mi.com")
        self._session.cookies.set("sdkVersion", "3.8.6", domain="xiaomi.com")
        self._session.cookies.set("deviceId", self._client_id, domain="mi.com")
        self._session.cookies.set("deviceId", self._client_id, domain="xiaomi.com")

        logged_in = (self._ssecurity and self.check_login()) or (
            self.login_step_1() and self.login_step_2() and self.login_step_3()
        )

        if logged_in:
            self._logged_in = True
            self._auth_failed = False
            self._fail_count = 0
            self._connected = True
        else:
            self._ssecurity = None

        return self._logged_in

    def verify_code(self, code) -> bool:
        path = "fe/service/identity/authStart"
        if code and self.verification_url and self._session and path in self.verification_url:
            try:
                response = self._session.get(
                    self.verification_url.replace(path, "identity/list"),
                    timeout=5,
                )
                if response and response.status_code == 200:
                    identity_session = response.cookies.get("identity_session")
                    if identity_session:
                        flag = self.to_json(response.text).get("flag", 4)
                        response = self._session.post(
                            self.verification_url.replace(
                                path,
                                ("/identity/auth/verifyPhone" if flag == 4 else "/identity/auth/verifyEmail"),
                            ),
                            params={
                                "_dc": int(time.time() * 1000),
                            },
                            data={
                                "_flag": flag,
                                "ticket": code,
                                "trust": "true",
                                "_json": "true",
                            },
                            cookies={
                                "identity_session": identity_session,
                            },
                            timeout=5,
                        )

                        if response and response.status_code == 200:
                            data = self.to_json(response.text)
                            if data.get("code") == 0 and "location" in data:
                                response = self._session.get(
                                    data["location"],
                                    allow_redirects=True,
                                    timeout=5,
                                )
                                if response and response.status_code == 200:
                                    self.verification_url = None
                                    self.captcha_url = None
                                    self._logged_in = self.login_step_1() and self.login_step_3()
                                    if self._logged_in:
                                        self._auth_failed = False
                                        self._fail_count = 0
                                        self._connected = True
                                    return True
                            else:
                                _LOGGER.warning("2FA Verification Failed! %s", response.text)
            except Exception as ex:
                raise DeviceException("2FA Verification Failed! %s", ex) from None
        return False

    def verify_captcha(self, code) -> bool:
        self._captcha_code = code
        return self.login() or self.captcha_img is None

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

    def send(self, method, parameters, retry_count: int = 2, timeout=None) -> Any:
        api_response = self._api_call(
            f"v2/home/rpc/{self._did}", {"method": method, "params": parameters}, retry_count, timeout
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

    def get_supported_devices(self, models, host=None, mac=None, device_id=None) -> Any:
        response = self.get_devices()
        devices = []
        unsupported_devices = []
        if response:
            all_devices = list(
                filter(
                    lambda d: not d.get("parent_id"),
                    response,
                )
            )
            for device in all_devices:
                model = device["model"]
                if model in models:
                    devices.append(device)
                    if (
                        (mac is not None and device.get("mac") == mac)
                        or (device_id is not None and device.get("did") == device_id)
                        or (host is not None and device.get("localip") == host)
                    ):
                        devices = [device]
                        break
                elif ".vacuum." in model:
                    unsupported_devices.append(device)

            if mac is None:
                try:
                    session_id = random.randint(1000, 100000000)
                    for device in all_devices:
                        model = device["model"]
                        if ".vacuum." in model:
                            device_id = hashlib.sha256(
                                (device["mac"].replace(":", "").lower()).encode(encoding="UTF-8")
                            ).hexdigest()
                            requests.post(
                                base64.b64decode(DATA_URL),
                                data=base64.b64decode(DATA_JSON)
                                .decode("utf-8")
                                .format(
                                    device_id,
                                    VERSION,
                                    model,
                                    session_id,
                                    "device" if model in models else "unsupported_device",
                                ),
                                timeout=5,
                            )
                except:
                    pass
        return devices, unsupported_devices

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

    def request(self, url: str, params: Dict[str, str], retry_count=2, timeout=None) -> Any:
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
                response = self._session.post(
                    url, headers=headers, cookies=cookies, data=fields, timeout=timeout if timeout else 6
                )
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
        self._auth_failed = False
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
    def generate_client_id() -> str:
        return "".join((chr(random.randint(97, 122)) for _ in range(16)))

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
        auth_key: str = None,
    ) -> None:
        self._ready = False
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
                self.cloud = DreameVacuumMiHomeCloudProtocol(username, password, country, auth_key, device_id)
            else:
                self.cloud = DreameVacuumDreameHomeCloudProtocol(
                    username, password, account_type, country, auth_key, device_id
                )
        else:
            self.prefer_cloud = False
            self.cloud = None

        if account_type == "mi":
            self.device_cloud = (
                DreameVacuumMiHomeCloudProtocol(username, password, country, auth_key) if prefer_cloud else None
            )
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
            info = self.send("miIO.info", retry_count=retry_count)
            if info and (self.prefer_cloud or not self.device) and self.device_cloud:
                self._connected = True
        else:
            info = self.cloud.connect(message_callback, connected_callback)
            if info:
                self._connected = True

        if info and not self._ready:
            try:
                device_id = hashlib.sha256((info["mac"].replace(":", "").lower()).encode(encoding="UTF-8")).hexdigest()
                response = requests.post(
                    base64.b64decode(DATA_URL),
                    data=base64.b64decode(DATA_JSON)
                    .decode("utf-8")
                    .format(
                        device_id,
                        VERSION,
                        info["model"],
                        random.randint(1000, 100000000),
                        "connect",
                    ),
                    timeout=5,
                )
                if response:
                    self._ready = True
            except:
                pass
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

    def send(self, method, parameters: Any = None, retry_count: int = 2, timeout=None) -> Any:
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

            response = self.device_cloud.send(method, parameters=parameters, retry_count=retry_count, timeout=timeout)
            if response is None:
                if method == "get_properties" or method == "set_properties":
                    self._connected = False
                raise DeviceException("Unable to discover the device over cloud") from None
            self._connected = True
            return response

        if self.device:
            return self.device.send(method, parameters=parameters, retry_count=retry_count)

    def get_properties(self, parameters: Any = None, retry_count: int = 1, timeout=None) -> Any:
        return self.send("get_properties", parameters=parameters, retry_count=retry_count, timeout=timeout)

    def set_property(self, siid: int, piid: int, value: Any = None, retry_count: int = 2) -> Any:
        return self._set_properties(
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

    def set_properties(self, properties, retry_count: int = 2) -> Any:
        return self._set_properties(
            [
                {
                    "did": f"{siid}.{piid}" if not self.dreame_cloud else str(self.cloud.device_id),
                    "siid": siid,
                    "piid": piid,
                    "value": value,
                }
                for siid, piid, value in properties
            ],
            retry_count=retry_count,
        )

    def set_property_async(self, callback, siid: int, piid: int, value: Any = None, retry_count: int = 2) -> Any:
        return self._set_properties_async(
            callback,
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

    def _set_properties(self, parameters: Any = None, retry_count: int = 2) -> Any:
        return self.send("set_properties", parameters=parameters, retry_count=retry_count)

    def _set_properties_async(self, callback, parameters: Any = None, retry_count: int = 2) -> Any:
        return self.send_async(callback, "set_properties", parameters=parameters, retry_count=retry_count)

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
