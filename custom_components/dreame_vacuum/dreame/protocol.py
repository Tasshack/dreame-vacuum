import logging
import random
import hashlib
import json
import base64
import hmac
import time
import locale
import os
import tzlocal
import requests
from typing import Any, Dict, Optional, Tuple
from datetime import datetime
from Crypto.Cipher import ARC4
from miio.miioprotocol import MiIOProtocol

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

    def connect(self, retry_count=2) -> Any:
        return self.send("miIO.info", retry_count=retry_count)

    def get_properties(
        self,
        parameters: Any = None,
        retry_count: int = 1
    ) -> Any:
        return self.send("get_properties", parameters=parameters, retry_count=retry_count)
    
    def set_property(
        self,
        siid: int,
        piid: int,
        value: Any = None,
        retry_count: int = 0
    ) -> Any:
        return self.set_properties([{
                "did": f'{siid}.{piid}',
                "siid": siid,
                "piid": piid,
                "value": value,
            }
        ], retry_count=retry_count)

    def set_properties(
        self,
        parameters: Any = None,
        retry_count: int = 1
    ) -> Any:
        return self.send("set_properties", parameters=parameters, retry_count=retry_count)

    def action(
        self,
        siid: int,
        aiid: int,
        parameters=[],
        retry_count: int = 1
    ) -> Any:
        if parameters is None:
            parameters = []

        return self.send(
            "action",
            parameters={
                "did": f'{siid}.{aiid}',
                "siid": siid,
                "aiid": aiid,
                "in": parameters,
            },
            retry_count=retry_count,
        )

    @property
    def connected(self) -> bool:
        return self._discovered    

    
class DreameVacuumCloudProtocol:
    def __init__(self, username: str, password: str, country: str) -> None:
        self.two_factor_auth_url = None
        self._username = username
        self._password = password
        self._country = country
        self._session = requests.session()
        self._sign = None
        self._ssecurity = None
        self._userId = None
        self._cUserId = None
        self._passToken = None
        self._location = None
        self._code = None
        self._serviceToken = None
        self._logged_in = None
        self._uid = None
        self._did = None
        self._useragent = f"Android-7.1.1-1.0.0-ONEPLUS A3010-136-{DreameVacuumCloudProtocol.get_random_agent_id()} APP/xiaomi.smarthome APPV/62830"
        self._locale = locale.getdefaultlocale()[0]

        timezone = datetime.now(tzlocal.get_localzone()).strftime("%z")
        timezone = "GMT{0}:{1}".format(timezone[:-2], timezone[-2:])
        self._timezone = timezone

    def login_step_1(self) -> bool:
        url = "https://account.xiaomi.com/pass/serviceLogin?sid=xiaomiio&_json=true"
        headers = {
            "User-Agent": self._useragent,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        cookies = {"userId": self._username}
        try:
            response = self._session.get(
                url, headers=headers, cookies=cookies, timeout=2
            )
        except:
            response = None
        successful = (
            response is not None
            and response.status_code == 200
            and "_sign" in self.to_json(response.text)
        )
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
            "_sign": self._sign,
            "_json": "true",
        }
        try:
            response = self._session.post(
                url, headers=headers, params=fields, timeout=5
            )
        except:
            response = None
        successful = response is not None and response.status_code == 200
        if successful:
            json_resp = self.to_json(response.text)
            successful = (
                "ssecurity" in json_resp and len(
                    str(json_resp["ssecurity"])) > 4
            )
            if successful:
                self._ssecurity = json_resp["ssecurity"]
                self._userId = json_resp["userId"]
                self._cUserId = json_resp["cUserId"]
                self._passToken = json_resp["passToken"]
                self._location = json_resp["location"]
                self._code = json_resp["code"]
                self.two_factor_auth_url = None
            else:
                if "notificationUrl" in json_resp:
                    _LOGGER.error(
                        "Additional authentication required. Open following URL using device that has the same public IP, as your Home Assistant instance: %s ",
                        json_resp["notificationUrl"],
                    )
                    self.two_factor_auth_url = json_resp["notificationUrl"]
                    successful = None

        return successful

    def login_step_3(self) -> bool:
        headers = {
            "User-Agent": self._useragent,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        try:
            response = self._session.get(
                self._location, headers=headers, timeout=5)
        except:
            response = None
        successful = (
            response is not None
            and response.status_code == 200
            and "serviceToken" in response.cookies
        )
        if successful:
            self._serviceToken = response.cookies.get("serviceToken")
        return successful

    def login(self) -> bool:
        self._session.close()
        self._session = requests.session()
        self._device_id = DreameVacuumCloudProtocol.generate_device_id()
        self._session.cookies.set(
            "sdkVersion", "accountsdk-18.8.15", domain="mi.com")
        self._session.cookies.set(
            "sdkVersion", "accountsdk-18.8.15", domain="xiaomi.com"
        )
        self._session.cookies.set("deviceId", self._device_id, domain="mi.com")
        self._session.cookies.set(
            "deviceId", self._device_id, domain="xiaomi.com")
        self._logged_in = (
            self.login_step_1() and self.login_step_2() and self.login_step_3()
        )
        return self._logged_in

    def get_file(self, url: str = "") -> Any:
        try:
            response = self._session.get(url, timeout=3)
        except Exception as ex:
            _LOGGER.warning("Unable to get file at %s: %s", url, ex)
            # self._logged_in = False
            response = None
        if response is not None and response.status_code == 200:
            return response.content
        return None

    def get_file_url(self, object_name: str = "") -> Any:
        url = f"{self.get_api_url()}/home/getfileurl"
        params = json.dumps({"obj_name": object_name}, separators=(",", ":"))
        _LOGGER.debug("Get file url: %s %s", url, params)
        api_response = self.execute_api_call_encrypted(url, {"data": params})
        _LOGGER.debug("Get file url result: %s", api_response)
        if (
            api_response is None
            or "result" not in api_response
            or "url" not in api_response["result"]
        ):
            return None

        return api_response

    def get_interim_file_url(self, object_name: str = "") -> Any:
        url = f"{self.get_api_url()}/v2/home/get_interim_file_url"
        params = {"data": f'{{"obj_name": "{object_name}"}}'}
        _LOGGER.debug("Get interim file url: %s", object_name)
        api_response = self.execute_api_call_encrypted(url, params)
        if (
            api_response is None
            or not api_response.get("result")
            or "url" not in api_response["result"]
        ):
            return None

        return api_response

    def send(self, method, params) -> Any:
        url = f"{self.get_api_url()}/v2/home/rpc/{self._did}"
        data = json.dumps(({"method": method, "params": params}))
        api_response = self.execute_api_call_encrypted(url, {"data": data})
        if api_response is None or "result" not in api_response:
            return None

        return api_response["result"]

    def get_device_property(self, key, limit=1, time_start=0, time_end=9999999999):
        return self.get_device_data(key, "prop", limit, time_start, time_end)

    def get_device_event(self, key, limit=1, time_start=0, time_end=9999999999):
        return self.get_device_data(key, "event", limit, time_start, time_end)

    def get_device_data(self, key, type, limit=1, time_start=0, time_end=9999999999):
        url = f"{self.get_api_url()}/user/get_user_device_data"
        data = {
            "uid": str(self._uid),
            "did": str(self._did),
            "time_end": time_end,
            "time_start": time_start,
            "limit": limit,
            "key": key,
            "type": type,
        }
        params = json.dumps(data, separators=(",", ":"))
        api_response = self.execute_api_call_encrypted(url, {"data": params})
        if api_response is None or "result" not in api_response:
            return None

        return api_response["result"]

    def get_info(self, mac: str) -> Tuple[Optional[str], Optional[str]]:
        countries_to_check = ["cn", "de", "us", "ru", "tw", "sg", "in", "i2"]
        if self._country is not None:
            countries_to_check = [self._country]
        for self._country in countries_to_check:
            devices = self.get_devices()
            if devices is None:
                continue
            found = list(
                filter(lambda d: str(d["mac"]) ==
                       mac, devices["result"]["list"])
            )
            if len(found) > 0:
                self._uid = found[0]["uid"]
                self._did = found[0]["did"]
                return found[0]["token"], found[0]["localip"]
        return None, None

    def get_devices(self) -> Any:
        url = f"{self.get_api_url()}/home/device_list"
        params = {"data": '{"getVirtualModel":false,"getHuamiDevices":0}'}
        return self.execute_api_call_encrypted(url, params)

    def get_batch_device_datas(self, props) -> Any:
        url = f"{self.get_api_url()}/device/batchdevicedatas"
        data = {
            "did": self._did,
            "props": props
        }
        params = json.dumps(data, separators=(",", ":"))
        api_response = self.execute_api_call_encrypted(url, {"data": params})
        if api_response is None or self._did not in api_response:
            return None
        return api_response[self._did]

    def execute_api_call_encrypted(self, url: str, params: Dict[str, str]) -> Any:
        headers = {
            "Accept-Encoding": "identity",
            "User-Agent": self._useragent,
            "Content-Type": "application/x-www-form-urlencoded",
            "x-xiaomi-protocal-flag-cli": "PROTOCAL-HTTP2",
            "MIOT-ENCRYPT-ALGORITHM": "ENCRYPT-RC4",
        }
        cookies = {
            "userId": str(self._userId),
            "yetAnotherServiceToken": str(self._serviceToken),
            "serviceToken": str(self._serviceToken),
            "locale": str(self._locale),
            "timezone": str(self._timezone),
            "is_daylight": str(time.daylight),
            "dst_offset": str(time.localtime().tm_isdst * 60 * 60 * 1000),
            "channel": "MI_APP_STORE",
        }
        millis = round(time.time() * 1000)
        nonce = self.generate_nonce(millis)
        signed_nonce = self.signed_nonce(nonce)
        fields = self.generate_enc_params(
            url, "POST", signed_nonce, nonce, params, self._ssecurity
        )

        try:
            response = self._session.post(
                url, headers=headers, cookies=cookies, params=fields, timeout=5
            )
        except Exception as ex:
            _LOGGER.error("Execute api call failed: %s", ex)
            return None

        if response is not None:
            if response.status_code == 200:
                decoded = self.decrypt_rc4(
                    self.signed_nonce(fields["_nonce"]), response.text
                )
                return json.loads(decoded)
            _LOGGER.warn("Execute api call failed with response: %s", response.text())
        return None

    def get_api_url(self) -> str:
        return (
            "https://"
            + ("" if self._country == "cn" else (self._country + "."))
            + "api.io.mi.com/app"
        )

    def signed_nonce(self, nonce: str) -> str:
        hash_object = hashlib.sha256(
            base64.b64decode(self._ssecurity) + base64.b64decode(nonce)
        )
        return base64.b64encode(hash_object.digest()).decode("utf-8")

    @staticmethod
    def generate_nonce(millis: int):
        nonce_bytes = os.urandom(
            8) + (int(millis / 60000)).to_bytes(4, byteorder="big")
        return base64.b64encode(nonce_bytes).decode()

    @staticmethod
    def generate_device_id() -> str:
        return "".join((chr(random.randint(97, 122)) for _ in range(6)))

    @staticmethod
    def generate_signature(
        url, signed_nonce: str, nonce: str, params: Dict[str, str]
    ) -> str:
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
    def generate_enc_signature(
        url, method: str, signed_nonce: str, params: Dict[str, str]
    ) -> str:
        signature_params = [
            str(method).upper(),
            url.split("com")[1].replace("/app/", "/"),
        ]
        for k, v in params.items():
            signature_params.append(f"{k}={v}")
        signature_params.append(signed_nonce)
        signature_string = "&".join(signature_params)
        return base64.b64encode(
            hashlib.sha1(signature_string.encode("utf-8")).digest()
        ).decode()

    @staticmethod
    def generate_enc_params(
        url: str,
        method: str,
        signed_nonce: str,
        nonce: str,
        params: Dict[str, str],
        ssecurity: str,
    ) -> Dict[str, str]:
        params["rc4_hash__"] = DreameVacuumCloudProtocol.generate_enc_signature(
            url, method, signed_nonce, params
        )
        for k, v in params.items():
            params[k] = DreameVacuumCloudProtocol.encrypt_rc4(signed_nonce, v)
        params.update(
            {
                "signature": DreameVacuumCloudProtocol.generate_enc_signature(
                    url, method, signed_nonce, params
                ),
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
