import logging
import json
import hashlib
import requests
import time
from .exceptions import DeviceException
from typing import Any, Optional, Tuple
from micloud import miutils
from micloud import MiCloud
from micloud.micloudexception import MiCloudAccessDenied, MiCloudException
from miio.miioprotocol import MiIOProtocol

_LOGGER = logging.getLogger(__name__)
ACCOUNT_BASE = 'https://account.xiaomi.com'

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

    
class DreameVacuumCloudProtocol(MiCloud):
    def __init__(self, username: str, password: str, country: str) -> None:
        super().__init__(username, password)
        self.did = None
        self.two_factor_url = None
        self.captcha_url = None
        self.default_server = country
        self.device_id = None
        self._fail_count = 0
        self._connected = False

    def _api_call(self, url, params):
        try:
            response = self.request(f'{self._get_api_url(self.default_server)}{url}', {"data": json.dumps(params, separators=(",", ":"))})
            if response:
                return json.loads(response)
        except Exception:
            return None        

    def request(self, url, params, **kwargs):
        if not self.service_token or not self.user_id:
            raise MiCloudException('Cannot execute request. service token or userId missing. Make sure to login.')

        self.session = requests.Session()
        self.session.headers.update({
            'X-XIAOMI-PROTOCAL-FLAG-CLI': 'PROTOCAL-HTTP2',
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': self.useragent,
        })
        self.session.cookies.update({
            'userId': str(self.user_id),
            'yetAnotherServiceToken': self.service_token,
            'serviceToken': self.service_token,
            'locale': str(self.locale),
            'timezone': str(self.timezone),
            'is_daylight': str(time.daylight),
            'dst_offset': str(time.localtime().tm_isdst * 60 * 60 * 1000),
            'channel': 'MI_APP_STORE',
        })

        try:
            nonce = miutils.gen_nonce()
            signed_nonce = miutils.signed_nonce(self.ssecurity, nonce)
            signature = miutils.gen_signature(url.replace('/app/', '/'), signed_nonce, nonce, params)
            post_data = {
                'signature': signature,
                '_nonce': nonce,
                'data': params['data'],
            }
            response = self.session.post(url, data=post_data, timeout=3)
            self._fail_count = 0
            self._connected = True
            return response.text
        except MiCloudException as exc:
            _LOGGER.warning('Error while decrypting response of request: %s', exc)
        except Exception as exc:
            if self._connected:
                _LOGGER.warning("Error while executing request: %s", str(exc))

            if self._fail_count == 5:
                self._connected = False
            else:
                self._fail_count = self._fail_count + 1
        
    def _login_step2(self, sign):
        post_data = {
            'sid': "xiaomiio",
            'hash': hashlib.md5(self.password.encode()).hexdigest().upper(),
            'callback': "https://sts.api.io.mi.com/sts",
            'qs': '%3Fsid%3Dxiaomiio%26_json%3Dtrue',
            'user': self.username,
            '_json': 'true'
        }
        if sign:
            post_data['_sign'] = sign

        response = self.session.post(f"{ACCOUNT_BASE}/pass/serviceLoginAuth2", data = post_data)
        response_json = json.loads(response.text.replace("&&&START&&&", ""))

        location = response_json['location']
        if not location:
            if "notificationUrl" in response_json:
                self.two_factor_url = response_json["notificationUrl"]
                if self.two_factor_url[:4] != 'http':
                    self.two_factor_url = f'{ACCOUNT_BASE}{self.two_factor_url}'
                    
                raise MiCloudAccessDenied(f"Additional authentication required. Open following URL using device that has the same public IP, as your Home Assistant instance: {self.two_factor_url}")

            raise MiCloudAccessDenied(f'Login to xiaomi error: {response.text}')

        if response_json['result'] != "ok":
            raise MiCloudAccessDenied("Access denied. Did you set the correct api key and/or username?")

        self.user_id = response_json['userId']
        self.ssecurity = response_json['ssecurity']
        self.cuser_id = response_json['cUserId']
        self.pass_token = response_json['passToken']

        return location

    def login(self):
        try:
            _LOGGER.info("Logging in...")
            self.two_factor_url = None
            self.captcha_url = None
            response = super().login()
            self._fail_count = 0
            self._connected = True
            return response
        except Exception as ex:
            _LOGGER.error("Login failed: %s", ex)
            return None

    def get_file(self, url: str = "") -> Any:
        try:
            session = requests.Session()
            response = session.get(url, timeout=3)
        except Exception as ex:
            _LOGGER.warning("Unable to get file at %s: %s", url, ex)
            response = None
        if response is not None and response.status_code == 200:
            return response.content
        return None

    def get_file_url(self, object_name: str = "") -> Any:
        api_response = self._api_call("/home/getfileurl", {"obj_name": object_name})
        if (
            api_response is None
            or "result" not in api_response
            or "url" not in api_response["result"]
        ):
            return None

        return api_response

    def get_interim_file_url(self, object_name: str = "") -> Any:
        _LOGGER.debug("Get interim file url: %s", object_name)
        api_response = self._api_call("/v2/home/get_interim_file_url", {"obj_name": object_name})
        if (
            api_response is None
            or not api_response.get("result")
            or "url" not in api_response["result"]
        ):
            return None

        return api_response

    def send(self, method, parameters) -> Any:
        api_response = self._api_call(f'/v2/home/rpc/{self.device_id}', {"method": method, "params": parameters})
        if "result" not in api_response:
            return None
        return api_response["result"]

    def get_device_property(self, key, limit=1, time_start=0, time_end=9999999999):
        return self.get_device_data(key, "prop", limit, time_start, time_end)

    def get_device_event(self, key, limit=1, time_start=0, time_end=9999999999):
        return self.get_device_data(key, "event", limit, time_start, time_end)

    def get_device_data(self, key, type, limit=1, time_start=0, time_end=9999999999):
        data = {
            "uid": str(self.user_id),
            "did": str(self.device_id),
            "time_end": time_end,
            "time_start": time_start,
            "limit": limit,
            "key": key,
            "type": type,
        }
        api_response = self._api_call("/user/get_user_device_data", data)
        if api_response is None or "result" not in api_response:
            return None

        return api_response["result"]

    def get_devices(self, country=None, raw=False, save=False, file="devices.json"):
        if not country:
            country = self.default_server

        response = self._get_device_string(country)
        if not response:
            return None

        try:
            json_resp = json.loads(response)
            logging.debug('Devices data: %s', response)

            if save:
                f = open("devices.json", "w")
                f.write(json.dumps(json_resp['result'], indent=4, sort_keys=True))
                f.close()

            if raw:
                return response
            else:
                return json_resp['result']['list']
        except ValueError as e:
            logging.info("Error while parsing devices: %s", str(e))

    def get_info(self, mac: str) -> Tuple[Optional[str], Optional[str]]:
        countries_to_check = ["cn", "de", "us", "ru", "tw", "sg", "in", "i2"]
        if self.default_server is not None:
            countries_to_check = [self.default_server]
        for self.default_server in countries_to_check:
            devices = self.get_devices()
            if devices is None:
                continue
            
            found = list(
                filter(lambda d: str(d["mac"]) ==
                       mac, devices)
            )
            if len(found) > 0:
                self.device_id = found[0]["did"]
                return found[0]["token"], found[0]["localip"]
        return None, None
    
    def get_batch_device_datas(self, props) -> Any:
        data = [{
            "did": self.device_id,
            "props": props
        }]
        api_response = self._api_call("/device/batchdevicedatas", data)
        if api_response is None or "result" not in api_response or self.device_id not in api_response["result"]:
            return None
        return api_response["result"][self.device_id]

    def set_batch_device_datas(self, props) -> Any:
        data = [{
            "did": self.device_id,
            "props": props
        }]
        api_response = self._api_call("/v2/device/batch_set_props", data)
        if api_response is None or "result" not in api_response:
            return None
        return api_response["result"]

    @property
    def logged_in(self) -> bool:
        return bool(self.user_id and self.service_token)

    @property
    def connected(self) -> bool:
        return self._connected

class DreameVacuumProtocol:
    def __init__(
        self,
        ip: str = None,
        token: str = None,
        username: str = None,
        password: str = None,
        country: str = None,
        prefer_cloud: bool = False,
    ) -> None:
        self.prefer_cloud = prefer_cloud
        self._connected = False

        if ip and token:
            self.device = DreameVacuumDeviceProtocol(ip, token)
        else:
            self.prefer_cloud = True
            self.device = None

        if username and password and country:
            self.cloud = DreameVacuumCloudProtocol(username, password, country)
        else:
            self.prefer_cloud = False
            self.cloud = None

    def set_credentials(self, ip: str, token: str):
        if ip and token:
            if self.device:
                self.device.set_credentials(ip, token)
            else:
                self.device = DreameVacuumDeviceProtocol(ip, token)
        else:
            self.device =  None
         
    def connect(self, retry_count=1) -> Any:
        response = self.send("miIO.info", retry_count=retry_count)
        if (self.prefer_cloud or not self.device) and self.cloud and response:
            self._connected = True
        return response

    def send(self, method, parameters: Any = None, retry_count: int = 1) -> Any:
        if (self.prefer_cloud or not self.device) and self.cloud:
            if not self.cloud.logged_in:
                self.cloud.login()

            if not self.cloud.logged_in:
                raise DeviceException("Unable to login")
            
            response = self.cloud.send(method, parameters=parameters)
            if response is None:
                self._connected = False
                raise DeviceException("Unable to discover the device over cloud")
            return response

        if self.device:
            return self.device.send(method, parameters=parameters, retry_count=retry_count)

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
        retry_count: int = 1
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
        if (self.prefer_cloud or not self.device) and self.cloud:
            return self.cloud.logged_in and self._connected

        if self.device:
            return self.device.connected

        return False
