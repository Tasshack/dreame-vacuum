"""Config flow for Dremae Vacuum."""

from __future__ import annotations
from typing import Any, Final
import re
import zlib
import base64
import json
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from collections.abc import Mapping
from homeassistant.const import (
    CONF_NAME,
    CONF_HOST,
    CONF_TOKEN,
    CONF_PASSWORD,
    CONF_USERNAME,
)
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult, AbortFlow
from homeassistant.helpers.device_registry import format_mac
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    OptionsFlow,
)

from .dreame import DreameVacuumProtocol, MAP_COLOR_SCHEME_LIST, MAP_ICON_SET_LIST, DEVICE_INFO, VERSION

from .const import (
    DOMAIN,
    CONF_NOTIFY,
    CONF_COLOR_SCHEME,
    CONF_ICON_SET,
    CONF_COUNTRY,
    CONF_TYPE,
    CONF_ACCOUNT_TYPE,
    CONF_MAC,
    CONF_DID,
    CONF_AUTH_KEY,
    CONF_HIDDEN_MAP_OBJECTS,
    CONF_PREFER_CLOUD,
    CONF_LOW_RESOLUTION,
    CONF_SQUARE,
    CONF_DONATED,
    CONF_VERSION,
    NOTIFICATION,
    MAP_OBJECTS,
    SPONSOR,
)


ACCOUNT_TYPE_DREAME = "dreame"
ACCOUNT_TYPE_MOVA = "mova"
ACCOUNT_TYPE_MI = "mi"
ACCOUNT_TYPE_TROUVER = "trouver"
ACCOUNT_TYPE_LOCAL = "local"

ACCOUNT_TYPE: Final = {
    "Dreamehome Account": ACCOUNT_TYPE_DREAME,
    "Xiaomi Home Account": ACCOUNT_TYPE_MI,
    "Movahome Account": ACCOUNT_TYPE_MOVA,
    "Trouver Account": ACCOUNT_TYPE_TROUVER,
    "Manual Connection (Without map)": ACCOUNT_TYPE_LOCAL,
}


class DreameVacuumOptionsFlowHandler(OptionsFlow):
    """Handle Dreame Vacuum options."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize Dreame Vacuum options flow."""
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Manage Dreame Vacuum options."""
        errors = {}
        if user_input is not None:
            return self.async_create_entry(title="", data={**self._config_entry.options, **user_input})

        notify = self._config_entry.options[CONF_NOTIFY]
        if isinstance(notify, bool):
            if notify is True:
                notify = list(NOTIFICATION.keys())
            else:
                notify = []

        data_schema = vol.Schema({vol.Required(CONF_NOTIFY, default=notify): cv.multi_select(NOTIFICATION)})
        if self._config_entry.data[CONF_USERNAME]:
            data_schema = data_schema.extend(
                {
                    vol.Required(CONF_COLOR_SCHEME, default=self._config_entry.options[CONF_COLOR_SCHEME]): vol.In(
                        list(MAP_COLOR_SCHEME_LIST.keys())
                    ),
                    vol.Required(
                        CONF_ICON_SET,
                        default=self._config_entry.options.get(CONF_ICON_SET, next(iter(MAP_ICON_SET_LIST))),
                    ): vol.In(list(MAP_ICON_SET_LIST.keys())),
                    vol.Required(
                        CONF_HIDDEN_MAP_OBJECTS,
                        default=self._config_entry.options.get(CONF_HIDDEN_MAP_OBJECTS, []),
                    ): cv.multi_select(MAP_OBJECTS),
                    vol.Required(CONF_SQUARE, default=self._config_entry.options.get(CONF_SQUARE, False)): bool,
                    vol.Required(
                        CONF_LOW_RESOLUTION,
                        default=self._config_entry.options.get(CONF_LOW_RESOLUTION, False),
                    ): bool,
                }
            )
            if self._config_entry.data.get(CONF_ACCOUNT_TYPE, ACCOUNT_TYPE_MI) == ACCOUNT_TYPE_MI:
                data_schema = data_schema.extend(
                    {
                        vol.Required(
                            CONF_PREFER_CLOUD,
                            default=self._config_entry.options.get(CONF_PREFER_CLOUD, False),
                        ): bool,
                    }
                )

            data_schema = data_schema.extend(
                {
                    vol.Required(
                        CONF_DONATED,
                        default=self._config_entry.options.get(CONF_DONATED, False),
                    ): bool
                }
            )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            errors=errors,
        )


class DreameVacuumFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle config flow for an Dreame Vacuum device."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize."""
        self.entry: ConfigEntry | None = None
        self.mac: str | None = None
        self.model = None
        self.host: str | None = None
        self.token: str | None = None
        self.name: str | None = None
        self.username: str | None = None
        self.password: str | None = None
        self.country: str = "eu"
        self.account_type: str = ACCOUNT_TYPE_MI
        self.device_id: int | None = None
        self.prefer_cloud: bool = True
        self.low_resolution: bool = False
        self.square: bool = False
        self.options: dict[str, dict[str, Any]] = {}
        self.protocol: DreameVacuumProtocol | None = None
        self.models: dict[str, int] = None
        self.devices: dict[str, Any] = None
        self.unsupported_devices: dict[str, Any] = None
        self.reauth: bool = False

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> DreameVacuumOptionsFlowHandler:
        """Get the options flow for this handler."""
        return DreameVacuumOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle a flow initialized by the user."""
        if self._async_in_progress():
            return self.async_abort(reason="already_in_progress")

        account_type = list(ACCOUNT_TYPE.keys())

        if user_input is not None:
            self.account_type = ACCOUNT_TYPE[user_input.get(CONF_TYPE, account_type[0])]
            return await self.async_step_login()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_TYPE, default=account_type[0]): vol.In(account_type)}),
            errors={},
        )

    async def async_step_reauth(self, user_input: Mapping[str, Any]) -> FlowResult:
        """Perform reauth upon an authentication error or missing cloud credentials."""
        self.name = user_input[CONF_NAME]
        self.host = user_input[CONF_HOST]
        self.token = user_input[CONF_TOKEN]
        self.username = user_input[CONF_USERNAME]
        self.password = user_input[CONF_PASSWORD]
        self.country = user_input[CONF_COUNTRY]
        self.account_type = user_input.get(CONF_ACCOUNT_TYPE, ACCOUNT_TYPE_MI)
        self.device_id = user_input.get(CONF_DID)
        self.mac = user_input.get(CONF_MAC)
        self.prefer_cloud = True  # Only for reauth
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Dialog that informs the user that reauth is required."""
        if user_input is not None:
            self.reauth = True
            return await self.async_step_login()
        return self.async_show_form(step_id="reauth_confirm")

    async def async_step_connect(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Connect to a Dreame Vacuum device."""
        error = None
        if self.prefer_cloud or (self.token and len(self.token) == 32):
            try:
                if (
                    self.account_type != ACCOUNT_TYPE_DREAME
                    and self.account_type != ACCOUNT_TYPE_MOVA
                    and self.account_type != ACCOUNT_TYPE_TROUVER
                ):
                    if self.protocol is not None:
                        self.protocol.disconnect()

                    self.protocol = DreameVacuumProtocol(
                        self.host,
                        self.token,
                        self.username,
                        self.password,
                        self.country,
                        self.prefer_cloud,
                        self.account_type,
                        self.device_id,
                        self.protocol.cloud.auth_key if self.protocol and self.protocol.cloud else None,
                    )

                    info = await self.hass.async_add_executor_job(self.protocol.connect, None, None, 3)
                    if info:
                        self.mac = info["mac"]
                        self.model = info["model"]

                    self.protocol.disconnect()
            except:
                error = "cannot_connect"
            else:
                if self.reauth:
                    return self.async_update_reload_and_abort(
                        self._get_reauth_entry(),
                        data_updates={
                            CONF_USERNAME: self.username,
                            CONF_PASSWORD: self.password,
                            CONF_HOST: self.host,
                            CONF_TOKEN: self.token,
                            CONF_AUTH_KEY: (
                                self.protocol.cloud.auth_key if self.protocol and self.protocol.cloud else None
                            ),
                        },
                    )

                if self.mac:
                    await self.async_set_unique_id(format_mac(self.mac))
                    self._abort_if_unique_id_configured(
                        updates={
                            CONF_HOST: self.host,
                            CONF_TOKEN: self.token,
                            CONF_MAC: self.mac,
                            CONF_DID: self.device_id,
                        }
                    )

                self.load_devices()
                if self.model in self.models:
                    if self.name is None:
                        self.name = self.model
                    return await self.async_step_options()
                else:
                    error = "unsupported"

            if self.username and self.password:
                return await self.async_step_login(error=error)
        else:
            error = "wrong_token"
        return await self.async_step_local(error=error)

    async def async_step_local(
        self,
        user_input: dict[str, Any] | None = None,
        errors: dict[str, Any] | None = {},
        error: str | None = None,
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is not None:
            self._async_abort_entries_match(user_input)

            self.host = user_input[CONF_HOST]
            self.token = user_input[CONF_TOKEN]
            self.mac = None
            return await self.async_step_connect()
        elif error:
            errors["base"] = error
        else:
            errors = {}

        return self.async_show_form(
            step_id=ACCOUNT_TYPE_LOCAL,
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=self.host): str,
                    vol.Required(CONF_TOKEN, default=self.token): str,
                }
            ),
            errors=errors,
        )

    async def async_step_login(self, error=None):
        if self.account_type == ACCOUNT_TYPE_MI:
            return await self.async_step_mi(error=error)
        if self.account_type == ACCOUNT_TYPE_DREAME:
            return await self.async_step_dreame(error=error)
        if self.account_type == ACCOUNT_TYPE_MOVA:
            return await self.async_step_mova(error=error)
        if self.account_type == ACCOUNT_TYPE_TROUVER:
            return await self.async_step_trouver(error=error)
        return await self.async_step_local(error=error)

    async def async_step_mi(
        self, user_input: dict[str, Any] | None = None, errors: dict[str, Any] | None = {}, error: str | None = None
    ) -> FlowResult:
        """Configure a dreame vacuum device through the Miio Cloud."""

        description_placeholders = {}
        if user_input is not None:
            username = user_input.get(CONF_USERNAME)
            password = user_input.get(CONF_PASSWORD)
            country = user_input.get(CONF_COUNTRY, self.country)

            if username and password and country:
                self.username = username
                self.password = password
                self.country = country
                self.prefer_cloud = user_input.get(CONF_PREFER_CLOUD, self.prefer_cloud)

                if self.protocol is not None:
                    self.protocol.disconnect()

                self.protocol = DreameVacuumProtocol(
                    username=self.username,
                    password=self.password,
                    country=self.country,
                    prefer_cloud=self.prefer_cloud,
                    account_type=self.account_type,
                )

                await self.hass.async_add_executor_job(self.protocol.cloud.login)

                if self.protocol.cloud.captcha_img is not None:
                    return await self.async_step_captcha()
                elif self.protocol.cloud.verification_url is not None:
                    return await self.async_step_2fa()
                elif self.protocol.cloud.logged_in is False:
                    errors["base"] = "login_error"
                elif self.protocol.cloud.logged_in:
                    return await self.async_step_devices()
            else:
                errors["base"] = "credentials_incomplete"
        elif error:
            errors["base"] = error
            devices = ""
            if error == "no_devices" and self.unsupported_devices:
                for device in self.unsupported_devices:
                    devices = f"{devices} ({device.get("model", "unknown")})"

            description_placeholders = {"devices": devices}
        else:
            errors = {}

        return self.async_show_form(
            step_id=self.account_type,
            data_schema=self.login_schema,
            description_placeholders=description_placeholders,
            errors=errors,
        )

    async def async_step_2fa(self, user_input: dict[str, Any] | None = None, errors: dict[str, Any] | None = {}):
        if self.protocol.cloud.verification_url is None and not self.protocol.cloud.logged_in:
            return await self.async_step_mi()

        if user_input is not None:
            verification_code = user_input.get("verification_code")
            result = await self.hass.async_add_executor_job(self.protocol.cloud.verify_code, verification_code)
            if result:
                if not self.protocol.cloud.logged_in:
                    return await self.async_step_mi(user_input=None, error="login_error")
                return await self.async_step_devices()
            else:
                errors["base"] = "2fa_failed"
        else:
            errors = {}

        return self.async_show_form(
            step_id="2fa",
            data_schema=vol.Schema(
                {
                    vol.Required("verification_code"): str,
                }
            ),
            description_placeholders={"url": self.protocol.cloud.verification_url},
            errors=errors,
        )

    async def async_step_captcha(self, user_input: dict[str, Any] | None = None, errors: dict[str, Any] | None = {}):
        if self.protocol.cloud.captcha_img is None and not self.protocol.cloud.logged_in:
            return await self.async_step_mi()

        if user_input is not None:
            code = user_input.get("code")
            result = await self.hass.async_add_executor_job(self.protocol.cloud.verify_captcha, code)
            if result:
                if not self.protocol.cloud.logged_in:
                    if self.protocol.cloud.verification_url is not None:
                        return await self.async_step_2fa()
                    return await self.async_step_mi(user_input=None, error="login_error")
                return await self.async_step_devices()
            else:
                errors["base"] = "wrong_captcha"
        else:
            errors = {}

        return self.async_show_form(
            step_id="captcha",
            data_schema=vol.Schema(
                {
                    vol.Required("code"): str,
                }
            ),
            description_placeholders={"img": self.protocol.cloud.captcha_img},
            errors=errors,
        )

    async def async_step_dreame(
        self,
        user_input: dict[str, Any] | None = None,
        errors: dict[str, Any] | None = {},
        error: str | None = None,
    ) -> FlowResult:
        """Configure a dreame vacuum device through the Dreame Cloud."""

        description_placeholders = {}
        if user_input is not None:
            username = user_input.get(CONF_USERNAME)
            password = user_input.get(CONF_PASSWORD)
            country = user_input.get(CONF_COUNTRY, self.country)

            if username and password and country:
                self.username = username
                self.password = password
                self.country = country
                self.prefer_cloud = True

                if self.protocol is not None:
                    self.protocol.disconnect()

                self.protocol = DreameVacuumProtocol(
                    username=self.username,
                    password=self.password,
                    country=self.country,
                    prefer_cloud=self.prefer_cloud,
                    account_type=self.account_type,
                )
                await self.hass.async_add_executor_job(self.protocol.cloud.login)

                if self.protocol.cloud.logged_in is False:
                    errors["base"] = "login_error"
                elif self.protocol.cloud.logged_in:
                    return await self.async_step_devices()
            else:
                errors["base"] = "credentials_incomplete"
        elif error:
            errors["base"] = error
            devices = ""
            if error == "no_devices" and self.unsupported_devices:
                for device in self.unsupported_devices:
                    devices = f"{devices} ({device.get("model", "unknown")})"

            description_placeholders = {"devices": devices}
        else:
            errors = {}

        return self.async_show_form(
            step_id=self.account_type,
            data_schema=self.login_schema,
            description_placeholders=description_placeholders,
            errors=errors,
        )

    async def async_step_mova(
        self,
        user_input: dict[str, Any] | None = None,
        errors: dict[str, Any] | None = {},
        error: str | None = None,
    ) -> FlowResult:
        """Configure a dreame vacuum device through the Mova Cloud."""

        return await self.async_step_dreame(user_input, errors, error)

    async def async_step_trouver(
        self,
        user_input: dict[str, Any] | None = None,
        errors: dict[str, Any] | None = {},
        error: str | None = None,
    ) -> FlowResult:
        """Configure a dreame vacuum device through the Trouver Cloud."""

        return await self.async_step_dreame(user_input, errors, error)

    async def async_step_devices(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle Dreame Vacuum devices found."""

        if user_input is None:
            if not self.devices:
                self.load_devices()
                supported_devices, self.unsupported_devices = await self.hass.async_add_executor_job(
                    self.protocol.cloud.get_supported_devices, self.models, self.host, self.mac
                )
                if not supported_devices:
                    return await self.async_step_login(error="no_devices")

                self.devices = {}
                for device in supported_devices:
                    if self.reauth or not self.hass.config_entries.async_entry_for_domain_unique_id(
                        self.handler, format_mac(device["mac"])
                    ):
                        self.devices[f"{device.get("name", device["model"])} - {device["mac"]}"] = device

                if not self.devices:
                    if self.unsupported_devices:
                        return await self.async_step_login(error="no_devices")
                    raise AbortFlow("already_configured")

                if len(self.devices) == 1:
                    user_input = {"devices": list(self.devices.keys())[0]}

        if user_input is not None:
            self.extract_info(self.devices[user_input["devices"]])
            return await self.async_step_connect()

        return self.async_show_form(
            step_id="devices",
            data_schema=vol.Schema({vol.Required("devices"): vol.In(list(self.devices))}),
            errors={},
        )

    async def async_step_options(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle Dreame Vacuum options step."""

        if user_input is not None:
            self.name = user_input[CONF_NAME]
            self.options = {
                CONF_NOTIFY: user_input[CONF_NOTIFY],
                CONF_COLOR_SCHEME: user_input.get(CONF_COLOR_SCHEME),
                CONF_ICON_SET: user_input.get(CONF_ICON_SET),
                CONF_HIDDEN_MAP_OBJECTS: user_input.get(CONF_HIDDEN_MAP_OBJECTS),
                CONF_SQUARE: user_input.get(CONF_SQUARE),
                CONF_LOW_RESOLUTION: user_input.get(CONF_LOW_RESOLUTION),
                CONF_PREFER_CLOUD: self.prefer_cloud,
            }

            return await self.async_step_donation()

        data_schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=self.name): str,
                vol.Required(CONF_NOTIFY, default=list(NOTIFICATION.keys())): cv.multi_select(NOTIFICATION),
            }
        )

        self.load_devices()
        hidden_map_objects = []
        if self.models[self.model] == 1:
            default_color_scheme = "Mijia Light"
            default_icon_set = "Mijia"
            hidden_map_objects.append("name_background")
            hidden_map_objects.append("icon")
        else:
            default_color_scheme = "Dreame Light"
            default_icon_set = "Dreame"
            model = re.sub(r"[^0-9]", "", self.model)
            if (not (model.isnumeric() and int(model) >= 2215)) or self.models[self.model] == 3:
                hidden_map_objects.append("name_background")
                hidden_map_objects.append("name")

        if self.account_type != ACCOUNT_TYPE_LOCAL:
            data_schema = data_schema.extend(
                {
                    vol.Required(CONF_COLOR_SCHEME, default=default_color_scheme): vol.In(
                        list(MAP_COLOR_SCHEME_LIST.keys())
                    ),
                    vol.Required(CONF_ICON_SET, default=default_icon_set): vol.In(list(MAP_ICON_SET_LIST.keys())),
                    vol.Required(CONF_HIDDEN_MAP_OBJECTS, default=hidden_map_objects): cv.multi_select(MAP_OBJECTS),
                    vol.Required(CONF_SQUARE, default=False): bool,
                    vol.Required(CONF_LOW_RESOLUTION, default=False): bool,
                }
            )

        return self.async_show_form(step_id="options", data_schema=data_schema, errors={})

    async def async_step_donation(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            self.options = self.options | {CONF_DONATED: user_input.get(CONF_DONATED, False), CONF_VERSION: VERSION}

            return self.async_create_entry(
                title=self.name,
                data={
                    CONF_NAME: self.name,
                    CONF_HOST: self.host,
                    CONF_TOKEN: self.token,
                    CONF_USERNAME: self.username,
                    CONF_PASSWORD: self.password,
                    CONF_COUNTRY: self.country,
                    CONF_MAC: self.mac,
                    CONF_DID: self.device_id,
                    CONF_AUTH_KEY: self.protocol.cloud.auth_key if self.protocol and self.protocol.cloud else None,
                    CONF_ACCOUNT_TYPE: self.account_type,
                },
                options=self.options,
            )

        return self.async_show_form(
            step_id="donation",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_DONATED,
                        default=False,
                    ): bool
                }
            ),
            description_placeholders={"text": SPONSOR},
            errors={},
        )

    def extract_info(self, device_info: dict[str, Any]) -> None:
        """Extract the device info."""

        if self.account_type == ACCOUNT_TYPE_MI:
            if self.host is None:
                self.host = device_info["localip"]
            if self.mac is None:
                self.mac = device_info["mac"]
            if self.model is None:
                self.model = device_info["model"]
            if self.name is None:
                self.name = device_info["name"]
            self.token = device_info["token"]
            self.device_id = device_info["did"]
        elif (
            self.account_type == ACCOUNT_TYPE_DREAME
            or self.account_type == ACCOUNT_TYPE_MOVA
            or self.account_type == ACCOUNT_TYPE_TROUVER
        ):
            if self.token is None:
                self.token = " "
            if self.host is None:
                self.host = device_info["bindDomain"]
            if self.mac is None:
                self.mac = device_info["mac"]
            if self.model is None:
                self.model = device_info["model"]
            if self.name is None:
                self.name = (
                    device_info["customName"]
                    if device_info["customName"] and len(device_info["customName"]) > 0
                    else device_info["deviceInfo"]["displayName"]
                )
            self.device_id = device_info["did"]

    def load_devices(self):
        if self.models is None:
            self.models = {}
            device_info = json.loads(zlib.decompress(base64.b64decode(DEVICE_INFO), zlib.MAX_WBITS | 32))
            for k in device_info[3]:
                info = device_info[0][device_info[3][k]]
                if info:
                    self.models[
                        f"{"xiaomi" if info[0] == 1 else ACCOUNT_TYPE_MOVA if info[0] == 2 else ACCOUNT_TYPE_TROUVER if info[0] == 3 else ACCOUNT_TYPE_DREAME}.vacuum.{k}"
                    ] = info[1]

    @property
    def login_schema(self):
        if self.reauth:
            return vol.Schema(
                {
                    vol.Required(CONF_USERNAME, default=self.username): str,
                    vol.Required(CONF_PASSWORD, default=self.password): str,
                }
            )

        if self.account_type == ACCOUNT_TYPE_MI:
            return vol.Schema(
                {
                    vol.Required(CONF_USERNAME, default=self.username): str,
                    vol.Required(CONF_PASSWORD, default=self.password): str,
                    vol.Required(CONF_COUNTRY, default=("de" if self.country == "eu" else self.country)): vol.In(
                        ["de", "cn", "us", "ru", "tw", "sg", "in", "i2"]
                    ),
                    vol.Optional(CONF_PREFER_CLOUD, default=self.prefer_cloud): bool,
                }
            )

        country_list = ["eu", "cn", "us", "ru", "sg"]
        if self.account_type == ACCOUNT_TYPE_MOVA:
            country_list.pop(2)
        elif self.account_type == ACCOUNT_TYPE_TROUVER:
            country_list.pop(1)

        return vol.Schema(
            {
                vol.Required(CONF_USERNAME, default=self.username): str,
                vol.Required(CONF_PASSWORD, default=self.password): str,
                vol.Required(CONF_COUNTRY, default=self.country): vol.In(country_list),
            }
        )
