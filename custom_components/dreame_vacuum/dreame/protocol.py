import logging
import random
import hashlib
import json
import base64
import hmac
import requests
import time, locale
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

_LOGGER = logging.getLogger(__name__)


class DreameVacuumDeviceProtocol(MiIOProtocol):
    def __init__(self, ip: str, token: str) -> None:
        super().__init__(ip, token, 0, 0, True, 2)
        self.ip = None
        self.token = None
        self.set_credentials(ip, token)

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


class DreameVacuumCloudProtocol:
    def __init__(
        self, username: str, password: str, country: str, auth_key: str = None, device_id: str = None
    ) -> None:
        self._username = username
        self._password = password
        self._country = country
        self._auth_key = auth_key
        self._session = requests.session()
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
        self._client_id = DreameVacuumCloudProtocol.generate_client_id()

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

    def _api_call(self, url, params, retry_count=2):
        response = self.request(
            f"{self.get_api_url()}/{url}",
            {"data": json.dumps(params, separators=(",", ":"))},
            retry_count,
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
        path = "identity/authStart"
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

    def get_supported_devices(self, models, host=None, mac=None) -> Any:
        response = self.get_devices()
        devices = {}
        unsupported_devices = {}
        if response:
            all_devices = list(
                filter(
                    lambda d: not d.get("parent_id"),
                    response,
                )
            )
            for device in all_devices:
                name = device["name"]
                model = device["model"]
                list_name = f"{name} - {model}"
                if model in models:
                    devices[list_name] = device

                    if (host is not None and device.get("localip") == host) or (
                        mac is not None and device.get("mac") == mac
                    ):
                        devices = {list_name: device}
                        break
                elif ".vacuum." in model:
                    unsupported_devices[list_name] = device

            if mac is None:
                try:
                    session_id = random.randint(1000, 100000000)
                    for device in all_devices:
                        model = device["model"]
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
        self._auth_failed = False

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
        params["rc4_hash__"] = DreameVacuumCloudProtocol.generate_enc_signature(url, method, signed_nonce, params)
        for k, v in params.items():
            params[k] = DreameVacuumCloudProtocol.encrypt_rc4(signed_nonce, v)
        params.update(
            {
                "signature": DreameVacuumCloudProtocol.generate_enc_signature(url, method, signed_nonce, params),
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
        device_id: str = None,
        auth_key: str = None,
    ) -> None:
        self._ready = False
        self.prefer_cloud = prefer_cloud
        self._connected = False
        self._mac = None

        if ip and token:
            self.device = DreameVacuumDeviceProtocol(ip, token)
        else:
            self.prefer_cloud = True
            self.device = None

        if username and password and country:
            self.cloud = DreameVacuumCloudProtocol(username, password, country, auth_key, device_id)
        else:
            self.prefer_cloud = False
            self.cloud = None

        self.device_cloud = DreameVacuumCloudProtocol(username, password, country, auth_key) if prefer_cloud else None

    def set_credentials(self, ip: str, token: str, mac: str = None):
        self._mac = mac
        if ip and token:
            if self.device:
                self.device.set_credentials(ip, token)
            else:
                self.device = DreameVacuumDeviceProtocol(ip, token)
        else:
            self.device = None

    def connect(self, message_callback=None, connected_callback=None, retry_count=1) -> Any:
        info = self.send("miIO.info", retry_count=retry_count)
        if info and (self.prefer_cloud or not self.device) and self.device_cloud:
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
                    "did": f"{siid}.{piid}",
                    "siid": siid,
                    "piid": piid,
                    "value": value,
                }
            ],
            retry_count=retry_count,
        )

    def set_properties(self, parameters: Any = None, retry_count: int = 2) -> Any:
        return self.send("set_properties", parameters=parameters, retry_count=retry_count)

    def action(self, siid: int, aiid: int, parameters=[], retry_count: int = 2) -> Any:
        if parameters is None:
            parameters = []

        _LOGGER.debug("Send Action: %s.%s %s", siid, aiid, parameters)
        return self.send(
            "action",
            parameters={
                "did": f"{siid}.{aiid}",
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
