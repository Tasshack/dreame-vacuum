import binascii
import codecs
import logging
import socket
import random
import calendar
import hashlib
import json
import base64
import hmac
import time
import locale
import datetime
import os
import tzlocal
from Crypto.Cipher import ARC4
import requests
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, List, Tuple
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from .exceptions import DeviceException, InvalidValueException
from construct import (
    core,
    Adapter,
    Bytes,
    Checksum,
    Const,
    Default,
    GreedyBytes,
    Hex,
    IfThenElse,
    Int16ub,
    Int32ub,
    Pointer,
    RawCopy,
    Rebuild,
    Struct,
)

_LOGGER = logging.getLogger(__name__)


class Utils:
    """This class is adapted from the original xpn.py code by gst666."""

    @staticmethod
    def verify_token(token: bytes) -> None:
        """Checks if the given token is of correct type and length."""
        if not isinstance(token, bytes):
            raise InvalidValueException("Token must be bytes")
        if len(token) != 16:
            raise InvalidValueException("Wrong token length")

    @staticmethod
    def md5(data: bytes) -> bytes:
        """Calculates a md5 hashsum for the given bytes object."""
        checksum = hashlib.md5()  # nosec
        checksum.update(data)
        return checksum.digest()

    @staticmethod
    def key_iv(token: bytes) -> Tuple[bytes, bytes]:
        """Generate an IV used for encryption based on given token."""
        key = Utils.md5(token)
        iv = Utils.md5(key + token)
        return key, iv

    @staticmethod
    def encrypt(plaintext: bytes, token: bytes) -> bytes:
        """Encrypt plaintext with a given token.

        :param bytes plaintext: Plaintext (json) to encrypt
        :param bytes token: Token to use
        :return: Encrypted bytes
        """
        if not isinstance(plaintext, bytes):
            raise TypeError("plaintext requires bytes")
        Utils.verify_token(token)
        key, iv = Utils.key_iv(token)
        padder = padding.PKCS7(128).padder()

        padded_plaintext = padder.update(plaintext) + padder.finalize()
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv),
                        backend=default_backend())

        encryptor = cipher.encryptor()
        return encryptor.update(padded_plaintext) + encryptor.finalize()

    @staticmethod
    def decrypt(ciphertext: bytes, token: bytes) -> bytes:
        """Decrypt ciphertext with a given token.

        :param bytes ciphertext: Ciphertext to decrypt
        :param bytes token: Token to use
        :return: Decrypted bytes object
        """
        if not isinstance(ciphertext, bytes):
            raise TypeError("ciphertext requires bytes")
        Utils.verify_token(token)
        key, iv = Utils.key_iv(token)
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv),
                        backend=default_backend())

        decryptor = cipher.decryptor()
        padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()

        unpadder = padding.PKCS7(128).unpadder()
        unpadded_plaintext = unpadder.update(padded_plaintext)
        unpadded_plaintext += unpadder.finalize()
        return unpadded_plaintext

    @staticmethod
    def checksum_field_bytes(ctx: Dict[str, Any]) -> bytearray:
        """Gather bytes for checksum calculation."""
        x = bytearray(ctx["header"].data)
        x += ctx["_"]["token"]
        if "data" in ctx:
            x += ctx["data"].data
            # print("DATA: %s" % ctx["data"])

        return x

    @staticmethod
    def get_length(x) -> int:
        """Return total packet length."""
        datalen = x._.data.length  # type: int
        return datalen + 32

    @staticmethod
    def is_hello(x) -> bool:
        """Return if packet is a hello packet."""
        # not very nice, but we know that hellos are 32b of length
        if "length" in x:
            val = x["length"]
        else:
            val = x.header.value["length"]

        return bool(val == 32)


class TimeAdapter(Adapter):
    """Adapter for timestamp conversion."""

    def _encode(self, obj, context, path):
        return calendar.timegm(obj.timetuple())

    def _decode(self, obj, context, path):
        return datetime.utcfromtimestamp(obj)


class EncryptionAdapter(Adapter):
    """Adapter to handle communication encryption."""

    def _encode(self, obj, context, path):
        """Encrypt the given payload with the token stored in the context.

        :param obj: JSON object to encrypt
        """
        # pp(context)
        return Utils.encrypt(
            json.dumps(obj).encode("utf-8") + b"\x00", context["_"]["token"]
        )

    def _decode(self, obj, context, path):
        """Decrypts the given payload with the token stored in the context.

        :return str: JSON object
        """
        try:
            # pp(context)
            decrypted = Utils.decrypt(obj, context["_"]["token"])
            decrypted = decrypted.rstrip(b"\x00")
        except Exception:
            if obj:
                _LOGGER.debug(
                    "Unable to decrypt, returning raw bytes: %s", obj)
            return obj

        # list of adaption functions for malformed json payload (quirks)
        decrypted_quirks = [  # try without modifications first
            lambda decrypted_bytes: decrypted_bytes,
            # powerstrip returns malformed JSON if the device is not
            # connected to the cloud, so we try to fix it here carefully.
            lambda decrypted_bytes: decrypted_bytes.replace(
                b',,"otu_stat"', b',"otu_stat"'
            ),
            # xiaomi cloud returns malformed json when answering
            # _sync.batch_gen_room_up_url
            # command so try to sanitize it
            lambda decrypted_bytes: decrypted_bytes[: decrypted_bytes.rfind(
                b"\x00")]
            if b"\x00" in decrypted_bytes
            else decrypted_bytes,
        ]

        for i, quirk in enumerate(decrypted_quirks):
            try:
                decoded = quirk(decrypted).decode("utf-8")
                return json.loads(decoded)
            except Exception as ex:
                # log the error when decrypted bytes couldn't be loaded
                # after trying all quirk adaptions
                if i == len(decrypted_quirks) - 1:
                    _LOGGER.debug("Unable to parse json '%s': %s", decoded, ex)
                    raise DeviceException(
                        "Unable to parse message payload") from ex

        return None


Message = Struct(  # for building we need data before anything else.
    "data" / Pointer(32, RawCopy(EncryptionAdapter(GreedyBytes))),
    "header"
    / RawCopy(
        Struct(
            Const(0x2131, Int16ub),
            "length" / Rebuild(Int16ub, Utils.get_length),
            "unknown" / Default(Int32ub, 0x00000000),
            "device_id" / Hex(Bytes(4)),
            "ts" / TimeAdapter(Default(Int32ub, datetime.utcnow())),
        )
    ),
    "checksum"
    / IfThenElse(
        Utils.is_hello,
        Bytes(16),
        Checksum(Bytes(16), Utils.md5, Utils.checksum_field_bytes),
    ),
)


class MiIODeviceProtocol:
    """miIO protocol implementation. This module contains the implementation of routines to send handshakes, send commands and discover devices (MiIOProtocol)."""

    def __init__(self, ip: str, token: str) -> None:
        """Create a :class:`MiIODeviceProtocol` instance."""
        self.ip = None
        self._token = None
        self.set_credentials(ip, token)
        self.lazy_discover = True

    def connect(self, retry_count=2) -> Any:
        return self.send("miIO.info")

    def set_credentials(self, ip: str, token: str):
        if self.ip != ip or self.token != token:
            self.ip = ip
            self.port = 54321
            self._token = token

            if token is None or token == "":
                token = 32 * "0"
            self.token = bytes.fromhex(token)

            self.__id = 0
            self._discovered = False
            self._device_ts: datetime = datetime.utcnow()
            self._device_id = bytes()

    def send_handshake(self, *, retry_count=2) -> Message:
        """Send a handshake to the device."""
        try:
            m = MiIODeviceProtocol.discover(self.ip)
        except DeviceException as ex:
            if retry_count > 0:
                return self.send_handshake(retry_count=retry_count - 1)
            raise ex

        if m is None:
            raise DeviceException("Unable to discover the device %s" % self.ip)

        header = m.header.value
        self._device_id = header.device_id
        self._device_ts = header.ts
        self._discovered = True

        _LOGGER.debug(
            "Discovered %s with ts: %s, token: %s",
            binascii.hexlify(self._device_id).decode(),
            self._device_ts,
            codecs.encode(m.checksum, "hex"),
        )

        return m

    @staticmethod
    def discover(addr: str = None, timeout: int = 2) -> Any:
        """Scan for devices in the network. This method is used to discover supported
        devices by sending a handshake message to the broadcast address on port 54321.
        If the target IP address is given, the handshake will be send as an unicast
        packet."""
        is_broadcast = addr is None
        seen_addrs = []  # type: List[str]
        if is_broadcast:
            addr = "<broadcast>"
            is_broadcast = True
            _LOGGER.info(
                "Sending discovery to %s with timeout of %ss..", addr, timeout)
        # magic, length 32
        helobytes = bytes.fromhex(
            "21310020ffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
        )

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.settimeout(timeout)
        for _ in range(3):
            s.sendto(helobytes, (addr, 54321))
        while True:
            try:
                data, recv_addr = s.recvfrom(1024)
                m = Message.parse(data)  # type: Message
                _LOGGER.debug("Got a response: %s", m)
                if not is_broadcast:
                    return m

                if recv_addr[0] not in seen_addrs:
                    _LOGGER.info(
                        "  IP %s (ID: %s) - token: %s",
                        recv_addr[0],
                        binascii.hexlify(m.header.value.device_id).decode(),
                        codecs.encode(m.checksum, "hex"),
                    )
                    seen_addrs.append(recv_addr[0])
            except socket.timeout:
                if is_broadcast:
                    _LOGGER.info("Discovery done")
                return  # ignore timeouts on discover
            except Exception as ex:
                _LOGGER.warning("error while reading discover results: %s", ex)
                break

    def get_properties(
        self,
        parameters: Any = None,
        retry_count: int = 1,
        timeout: int = 3
    ) -> Any:
        return self.send("get_properties", parameters, retry_count, timeout)

    def set_property(
        self,
        siid: int,
        piid: int,
        value: Any = None,
        retry_count: int = 0,
        timeout: int = 2
    ) -> Any:
        return self.set_properties([
            {
                "did": f'{siid}.{piid}',
                "siid": siid,
                "piid": piid,
                "value": value,
            }
        ], retry_count, timeout)

    def set_properties(
        self,
        parameters: Any = None,
        retry_count: int = 1,
        timeout: int = 3
    ) -> Any:
        return self.send("set_properties", parameters, retry_count, timeout)

    def action(
        self,
        siid: int,
        aiid: int,
        parameters=[],
        retry_count: int = 1,
        timeout: int = 3
    ) -> Any:
        if parameters is None:
            parameters = []

        return self.send(
            "action",
            {
                "did": f'{siid}.{aiid}',
                "siid": siid,
                "aiid": aiid,
                "in": parameters,
            },
        )

    def send(
        self,
        command: str,
        parameters: Any = None,
        retry_count: int = 1,
        timeout: int = 3,
        *,
        extra_parameters: Dict = None,
    ) -> Any:
        """Build and send the given command. Note that this will implicitly call
        :func:`send_handshake` to do a handshake, and will re-try in case of errors
        while incrementing the `_id` by 100."""

        try:
            if not self.lazy_discover or not self._discovered:
                self.send_handshake()

            request = self._create_request(
                command, parameters, extra_parameters)

            send_ts = self._device_ts + timedelta(seconds=1)
            header = {
                "length": 0,
                "unknown": 0x00000000,
                "device_id": self._device_id,
                "ts": send_ts,
            }

            msg = {
                "data": {"value": request},
                "header": {"value": header},
                "checksum": 0,
            }
            m = Message.build(msg, token=self.token)
            _LOGGER.debug("%s:%s >>: %s", self.ip, self.port, request)

            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(timeout)

            s.sendto(m, (self.ip, self.port))
        except OSError as ex:
            _LOGGER.error("failed to send msg: %s", ex)
            return None
            # raise DeviceException from ex

        try:
            data, addr = s.recvfrom(4096)
            m = Message.parse(data, token=self.token)

            header = m.header.value
            payload = m.data.value

            self.__id = payload["id"]
            # type: ignore # ts uses timeadapter
            self._device_ts = header["ts"]

            _LOGGER.debug(
                "%s:%s (ts: %s, id: %s) << %s",
                self.ip,
                self.port,
                header["ts"],
                payload["id"],
                payload,
            )
            if "error" in payload:
                raise DeviceException(
                    "Device returned error: %s" % payload["error"])
            try:
                return payload["result"]
            except KeyError:
                return payload
        except core.ChecksumError as ex:
            raise DeviceException(
                "Got checksum error which indicates use of an invalid token. Please check your token!"
            ) from ex
        except OSError as ex:
            if retry_count > 0:
                _LOGGER.debug(
                    "Retrying with incremented id, retries left: %s", retry_count
                )
                self.__id += 100
                self._discovered = False
                return self.send(
                    command,
                    parameters,
                    retry_count - 1,
                    extra_parameters=extra_parameters,
                )

            _LOGGER.error("Got error when receiving: %s", ex)
            raise DeviceException("No response from the device") from ex
        except Exception as ex:
            if retry_count > 0:
                _LOGGER.debug(
                    "Retrying to send failed command, retries left: %s", retry_count
                )
                return self.send(
                    command,
                    parameters,
                    retry_count - 1,
                    extra_parameters=extra_parameters,
                )

            _LOGGER.error("Got error when receiving: %s", ex)
            raise DeviceException("Unable to recover failed command") from ex

    @property
    def _id(self) -> int:
        """Increment and return the sequence id."""
        self.__id += random.randint(1, 1000)
        if self.__id >= 9999:
            self.__id = 1
        return self.__id

    @property
    def raw_id(self) -> int:
        return self.__id

    @property
    def connected(self) -> bool:
        return self._discovered

    def _create_request(
        self, command: str, parameters: Any, extra_parameters: Dict = None
    ):
        """Create request payload."""
        request = {"id": self._id, "method": command}

        if parameters is not None:
            request["params"] = parameters
        else:
            request["params"] = []

        if extra_parameters is not None:
            request = {**request, **extra_parameters}

        return request


class MiIOCloudProtocol:
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
        self._useragent = f"Android-7.1.1-1.0.0-ONEPLUS A3010-136-{MiIOCloudProtocol.get_random_agent_id()} APP/xiaomi.smarthome APPV/62830"
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
        self._device_id = MiIOCloudProtocol.generate_device_id()
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
        params["rc4_hash__"] = MiIOCloudProtocol.generate_enc_signature(
            url, method, signed_nonce, params
        )
        for k, v in params.items():
            params[k] = MiIOCloudProtocol.encrypt_rc4(signed_nonce, v)
        params.update(
            {
                "signature": MiIOCloudProtocol.generate_enc_signature(
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
