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
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.device_registry import format_mac
from homeassistant.components import persistent_notification
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    OptionsFlow,
)

from .dreame import DreameVacuumProtocol, MAP_COLOR_SCHEME_LIST, MAP_ICON_SET_LIST

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
    CONF_MAP_OBJECTS,
    CONF_PREFER_CLOUD,
    CONF_LOW_RESOLUTION,
    CONF_SQUARE,
    NOTIFICATION,
    MAP_OBJECTS,
    NOTIFICATION_ID_2FA_LOGIN,
    NOTIFICATION_2FA_LOGIN,
    SUPPORTED_MODELS
)

MIHOME: Final = "Xiaomi Home Account"
DREAMEHOME: Final = "Dreamehome Account"
LOCAL: Final = "Manual Connection (Without map)"

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
                        CONF_MAP_OBJECTS,
                        default=self._config_entry.options.get(CONF_MAP_OBJECTS, list(MAP_OBJECTS.keys())),
                    ): cv.multi_select(MAP_OBJECTS),
                    vol.Required(CONF_SQUARE, default=self._config_entry.options.get(CONF_SQUARE, False)): bool,
                    vol.Required(
                        CONF_LOW_RESOLUTION,
                        default=self._config_entry.options.get(CONF_LOW_RESOLUTION, False),
                    ): bool,
                }
            )
            if self._config_entry.data.get(CONF_ACCOUNT_TYPE, "mi") == "mi":
                data_schema = data_schema.extend(
                    {
                        vol.Required(
                            CONF_PREFER_CLOUD,
                            default=self._config_entry.options.get(CONF_PREFER_CLOUD, False),
                        ): bool,
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
        self.country: str = "cn"
        self.account_type: str = "local"
        self.device_id: int | None = None
        self.prefer_cloud: bool = False
        self.low_resolution: bool = False
        self.square: bool = False
        self.devices: dict[str, dict[str, Any]] = {}
        self.protocol: DreameVacuumProtocol | None = None
        self.models = json.loads(zlib.decompress(base64.b64decode(SUPPORTED_MODELS), zlib.MAX_WBITS | 32))

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> DreameVacuumOptionsFlowHandler:
        """Get the options flow for this handler."""
        return DreameVacuumOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle a flow initialized by the user."""
        if user_input is not None:
            config_type = user_input.get(CONF_TYPE, MIHOME)
            if config_type == MIHOME:
                return await self.async_step_mi()
            if config_type == DREAMEHOME:
                return await self.async_step_dreame()
            return await self.async_step_local()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_TYPE, default=MIHOME): vol.In([MIHOME, DREAMEHOME, LOCAL])}),
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
        self.prefer_cloud = user_input[CONF_PREFER_CLOUD]
        self.account_type = user_input.get(CONF_ACCOUNT_TYPE, MIHOME)
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Dialog that informs the user that reauth is required."""
        if user_input is not None:
            return await self.async_step_cloud()
        return self.async_show_form(step_id="reauth_confirm")

    async def async_step_connect(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Connect to a Dreame Vacuum device."""
        errors: dict[str, str] = {}
        if self.prefer_cloud or (self.token and len(self.token) == 32):
            try:
                if self.protocol is None:
                    self.protocol = DreameVacuumProtocol(
                        self.host,
                        self.token,
                        self.username,
                        self.password,
                        self.country,
                        self.prefer_cloud,
                        self.account_type,
                    )
                else:
                    self.protocol.set_credentials(self.host, self.token, account_type=self.account_type)

                if self.protocol.device_cloud:
                    self.protocol.device_cloud._did = self.device_id

                if self.account_type != "dreame" or self.mac is None or self.model is None:
                    info = await self.hass.async_add_executor_job(self.protocol.connect, 5)
                    if info:
                        self.mac = info["mac"]
                        self.model = info["model"]
            except:
                errors["base"] = "cannot_connect"
            else:
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

                if self.model in self.models["dreame"] or self.model in self.models["mijia"]:
                    if self.name is None:
                        self.name = self.model
                    return await self.async_step_options()
                else:
                    errors["base"] = "unsupported"

            if self.username and self.password:
                if self.account_type == "mi":
                    return await self.async_step_mi(errors=errors)
                else:
                    return await self.async_step_dreame(errors=errors)
        else:
            errors["base"] = "wrong_token"
        return await self.async_step_local(errors=errors)

    async def async_step_local(
        self,
        user_input: dict[str, Any] | None = None,
        errors: dict[str, Any] | None = {},
    ) -> FlowResult:
        """Handle the initial step."""

        if user_input is not None:
            self._async_abort_entries_match(user_input)

            self.host = user_input[CONF_HOST]
            self.token = user_input[CONF_TOKEN]
            self.mac = None
            return await self.async_step_connect()

        return self.async_show_form(
            step_id="local",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=self.host): str,
                    vol.Required(CONF_TOKEN, default=self.token): str,
                }
            ),
            errors=errors,
        )

    async def async_step_mi(
        self,
        user_input: dict[str, Any] | None = None,
        errors: dict[str, Any] | None = {},
    ) -> FlowResult:
        """Configure a dreame vacuum device through the Miio Cloud."""
        placeholders = {}
        if user_input is not None:
            self.account_type = "mi"
            username = user_input.get(CONF_USERNAME)
            password = user_input.get(CONF_PASSWORD)
            country = user_input.get(CONF_COUNTRY)

            if username and password and country:
                self.username = username
                self.password = password
                self.country = country
                self.prefer_cloud = user_input.get(CONF_PREFER_CLOUD, False)

                self.protocol = DreameVacuumProtocol(
                    username=self.username,
                    password=self.password,
                    country=self.country,
                    prefer_cloud=self.prefer_cloud,
                    account_type="mi",
                )
                await self.hass.async_add_executor_job(self.protocol.cloud.login)

                if self.protocol.cloud.two_factor_url is not None:
                    errors["base"] = "2fa_required"
                    persistent_notification.create(
                        self.hass,
                        f"{NOTIFICATION_2FA_LOGIN}[{self.protocol.cloud.two_factor_url}]({self.protocol.cloud.two_factor_url})",
                        f"Login to Dreame Vacuum: {self.username}",
                        f"{DOMAIN}_{NOTIFICATION_ID_2FA_LOGIN}",
                    )
                    placeholders = {"url": self.protocol.cloud.two_factor_url}
                elif self.protocol.cloud.logged_in is False:
                    errors["base"] = "login_error"
                elif self.protocol.cloud.logged_in:
                    persistent_notification.dismiss(self.hass, f"{DOMAIN}_{NOTIFICATION_ID_2FA_LOGIN}")

                    devices = await self.hass.async_add_executor_job(self.protocol.cloud.get_devices)
                    if devices:
                        found = list(
                            filter(
                                lambda d: not d.get("parent_id")
                                and (str(d["model"]) in self.models["dreame"] or str(d["model"]) in self.models["mijia"]),
                                devices,
                            )
                        )

                        self.devices = {}
                        for device in found:
                            name = device["name"]
                            model = device["model"]
                            list_name = f"{name} - {model}"
                            self.devices[list_name] = device

                        if self.host is not None:
                            for device in self.devices.values():
                                host = device.get("localip")
                                if host == self.host:
                                    self.extract_info(device)
                                    return await self.async_step_connect()

                        if self.devices:
                            if len(self.devices) == 1:
                                self.extract_info(list(self.devices.values())[0])
                                return await self.async_step_connect()
                            return await self.async_step_devices()

                    errors["base"] = "no_devices"
            else:
                errors["base"] = "credentials_incomplete"

        return self.async_show_form(
            step_id="mi",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME, default=self.username): str,
                    vol.Required(CONF_PASSWORD, default=self.password): str,
                    vol.Required(CONF_COUNTRY, default=self.country): vol.In(
                        ["cn", "de", "us", "ru", "tw", "sg", "in", "i2"]
                    ),
                    vol.Required(CONF_PREFER_CLOUD, default=self.prefer_cloud): bool,
                }
            ),
            description_placeholders=placeholders,
            errors=errors,
        )

    async def async_step_dreame(
        self,
        user_input: dict[str, Any] | None = None,
        errors: dict[str, Any] | None = {},
    ) -> FlowResult:
        """Configure a dreame vacuum device through the Miio Cloud."""
        placeholders = {}
        if user_input is not None:
            self.account_type = "dreame"
            username = user_input.get(CONF_USERNAME)
            password = user_input.get(CONF_PASSWORD)
            country = user_input.get(CONF_COUNTRY)

            if username and password and country:
                self.username = username
                self.password = password
                self.country = country
                self.prefer_cloud = True

                self.protocol = DreameVacuumProtocol(
                    username=self.username,
                    password=self.password,
                    country=self.country,
                    prefer_cloud=self.prefer_cloud,
                    account_type="dreame",
                )
                await self.hass.async_add_executor_job(self.protocol.cloud.login)

                if self.protocol.cloud.logged_in is False:
                    errors["base"] = "login_error"
                elif self.protocol.cloud.logged_in:
                    persistent_notification.dismiss(self.hass, f"{DOMAIN}_{NOTIFICATION_ID_2FA_LOGIN}")

                    devices = await self.hass.async_add_executor_job(self.protocol.cloud.get_devices)
                    if devices:
                        found = list(
                            filter(
                                lambda d: str(d["model"]) in self.models["dreame"] or str(d["model"]) in self.models["mijia"],
                                devices["page"]["records"],
                            )
                        )

                        self.devices = {}
                        for device in found:
                            name = (
                                device["customName"]
                                if device["customName"] and len(device["customName"]) > 0
                                else device["deviceInfo"]["displayName"]
                            )
                            model = device["model"]
                            list_name = f"{name} - {model}"
                            self.devices[list_name] = device

                        if self.devices:
                            if len(self.devices) == 1:
                                self.extract_info(list(self.devices.values())[0])
                                return await self.async_step_connect()
                            return await self.async_step_devices()

                    errors["base"] = "no_devices"
            else:
                errors["base"] = "credentials_incomplete"

        return self.async_show_form(
            step_id="dreame",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME, default=self.username): str,
                    vol.Required(CONF_PASSWORD, default=self.password): str,
                    vol.Required(CONF_COUNTRY, default=self.country): vol.In(["cn", "eu", "us", "ru", "sg"]),
                }
            ),
            description_placeholders=placeholders,
            errors=errors,
        )

    async def async_step_devices(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle multiple Dreame Vacuum devices found."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self.extract_info(self.devices[user_input["devices"]])
            return await self.async_step_connect()

        return self.async_show_form(
            step_id="devices",
            data_schema=vol.Schema({vol.Required("devices"): vol.In(list(self.devices))}),
            errors=errors,
        )

    async def async_step_options(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle Dreame Vacuum options step."""
        errors = {}

        if user_input is not None:
            self.name = user_input[CONF_NAME]

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
                    CONF_ACCOUNT_TYPE: self.account_type,
                },
                options={
                    CONF_NOTIFY: user_input[CONF_NOTIFY],
                    CONF_COLOR_SCHEME: user_input.get(CONF_COLOR_SCHEME),
                    CONF_ICON_SET: user_input.get(CONF_ICON_SET),
                    CONF_MAP_OBJECTS: user_input.get(CONF_MAP_OBJECTS),
                    CONF_SQUARE: user_input.get(CONF_SQUARE),
                    CONF_LOW_RESOLUTION: user_input.get(CONF_LOW_RESOLUTION),
                    CONF_PREFER_CLOUD: self.prefer_cloud,
                },
            )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=self.name): str,
                vol.Required(CONF_NOTIFY, default=list(NOTIFICATION.keys())): cv.multi_select(NOTIFICATION),
            }
        )

        mijia = bool(self.model in self.models["mijia"])
        default_objects = list(MAP_OBJECTS.keys())
        if mijia:
            default_color_scheme = "Mijia Light"
            default_icon_set = "Mijia"
            default_objects.pop(3)  # Room Name Background
            default_objects.pop(1)  # Room icons
        else:
            default_color_scheme = "Dreame Light"
            default_icon_set = "Dreame"
            model = re.sub(r"[^0-9]", "", self.model)
            if not (model.isnumeric() and int(model) >= 2215):
                default_objects.pop(3)  # Room Name Background
                default_objects.pop(2)  # Room Names

        if self.account_type != "local":
            data_schema = data_schema.extend(
                {
                    vol.Required(CONF_COLOR_SCHEME, default=default_color_scheme): vol.In(
                        list(MAP_COLOR_SCHEME_LIST.keys())
                    ),
                    vol.Required(CONF_ICON_SET, default=default_icon_set): vol.In(list(MAP_ICON_SET_LIST.keys())),
                    vol.Required(CONF_MAP_OBJECTS, default=default_objects): cv.multi_select(MAP_OBJECTS),
                    vol.Required(CONF_SQUARE, default=False): bool,
                    vol.Required(CONF_LOW_RESOLUTION, default=False): bool,
                }
            )

        return self.async_show_form(step_id="options", data_schema=data_schema, errors=errors)

    def extract_info(self, device_info: dict[str, Any]) -> None:
        """Extract the device info."""
        if self.account_type == "mi":
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
        elif self.account_type == "dreame":
            if self.token is None:
                self.token = " "  # device_info["token"]
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
