"""Config flow for Dremae Vacuum."""
from __future__ import annotations
from typing import Any, Final
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from collections.abc import Mapping
import logging
from homeassistant import config_entries
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
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    OptionsFlow,
)

from .dreame import DreameVacuumDeviceProtocol, DreameVacuumCloudProtocol, MAP_COLOR_SCHEME_LIST

from .const import (
    DOMAIN,
    CONF_NOTIFY,
    CONF_COLOR_SCHEME,
    CONF_COUNTRY,
    CONF_TYPE,
    CONF_MAC,
    CONF_MAP_OBJECTS,
    NOTIFICATION,
    MAP_OBJECTS
)

SUPPORTED_MODELS = [
    ## Dreame Lidar Robots
    "dreame.vacuum.p2009",
    "dreame.vacuum.p2027",
    "dreame.vacuum.p2028",
    "dreame.vacuum.p2028a",
    "dreame.vacuum.p2029",
    "dreame.vacuum.r2104",
    "dreame.vacuum.p2114",
    "dreame.vacuum.p2114o",
    "dreame.vacuum.p2114a",
    "dreame.vacuum.p2114b",
    "dreame.vacuum.p2150o",
    "dreame.vacuum.p2150a",
    "dreame.vacuum.p2150b",
    "dreame.vacuum.p2149o",
    "dreame.vacuum.p2157",
    "dreame.vacuum.p2187",
    "dreame.vacuum.r2205",
    "dreame.vacuum.p2259",
    "dreame.vacuum.r2228o",
    "dreame.vacuum.r2215o",
    "dreame.vacuum.r2233",
    "dreame.vacuum.r2228",

    ## Dreame Vslam Robots
    #"dreame.vacuum.p2140q",
    #"dreame.vacuum.p2140p",
    #"dreame.vacuum.p2140o",
    #"dreame.vacuum.p2140a",
    #"dreame.vacuum.p2140",
    #"dreame.vacuum.p2148o",
    #"dreame.vacuum.p2156o",
    #"dreame.vacuum.p2041o",
    #"dreame.vacuum.p2041",
    #"dreame.vacuum.p2008",
]

WITH_MAP: Final = "With map (Automatic)"
WITHOUT_MAP: Final = "Without map (Manual)"


class DreameVacuumOptionsFlowHandler(OptionsFlow):
    """Handle Dreame Vacuum options."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize Dreame Vacuum options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage Dreame Vacuum options."""
        errors = {}
        data = self.config_entry.data
        options = self.config_entry.options

        if user_input is not None:
            return self.async_create_entry(title="", data={**options, **user_input})
        
        notify = options[CONF_NOTIFY]
        if isinstance(notify, bool):
            if notify is True:
                notify = list(NOTIFICATION.keys())
            else:
                notify = []

        data_schema = vol.Schema(
            {vol.Required(CONF_NOTIFY, default=notify): cv.multi_select(NOTIFICATION)}
        )
        if data[CONF_USERNAME]:
            data_schema = data_schema.extend(
                {
                    vol.Required(CONF_COLOR_SCHEME, default=options[CONF_COLOR_SCHEME]): vol.In(list(MAP_COLOR_SCHEME_LIST.keys())),
                    vol.Required(CONF_MAP_OBJECTS, default=options.get(CONF_MAP_OBJECTS, list(MAP_OBJECTS.keys()))): cv.multi_select(MAP_OBJECTS),
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
        self.country: str = None
        self.with_map: bool = True
        self.devices: dict[str, dict[str, Any]] = {}

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> DreameVacuumOptionsFlowHandler:
        """Get the options flow for this handler."""
        return DreameVacuumOptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initialized by the user."""
        if user_input is not None:
            with_map = user_input.get(CONF_TYPE, WITH_MAP)
            self.with_map = True if with_map == WITH_MAP else False
            if self.with_map:
                self.country = "cn"
                return await self.async_step_with_map()
            return await self.async_step_without_map()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_TYPE, default=WITH_MAP): vol.In(
                        [WITH_MAP, WITHOUT_MAP]
                    )
                }
            ),
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
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Dialog that informs the user that reauth is required."""
        if user_input is not None:
            return await self.async_step_cloud()
        return self.async_show_form(step_id="reauth_confirm")

    async def async_step_connect(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Connect to a Dreame Vacuum device."""
        errors: dict[str, str] = {}
        if len(self.token) == 32:
            try:
                protocol = DreameVacuumDeviceProtocol(self.host, self.token)
                info = await self.hass.async_add_executor_job(protocol.connect, 2)
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
                        }
                    )

                if self.model in SUPPORTED_MODELS:
                    if self.name is None:
                        self.name = self.model
                    return await self.async_step_options()
                else:
                    errors["base"] = "unsupported"
        else:
            errors["base"] = "wrong_token"

        return await self.async_step_without_map(errors=errors)

    async def async_step_without_map(
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
            step_id="without_map",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=self.host): str,
                    vol.Required(CONF_TOKEN, default=self.token): str,
                }
            ),
            errors=errors,
        )

    async def async_step_with_map(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configure a dreame vacuum device through the Miio Cloud."""
        errors = {}
        if user_input is not None:
            username = user_input.get(CONF_USERNAME)
            password = user_input.get(CONF_PASSWORD)
            country = user_input.get(CONF_COUNTRY)

            if username and password and country:
                self.username = username
                self.password = password
                self.country = country

                protocol = DreameVacuumCloudProtocol(
                    self.username, self.password, self.country)
                await self.hass.async_add_executor_job(protocol.login)

                if protocol._logged_in is None:
                    errors["base"] = "2fa_required"
                elif protocol._logged_in is False:
                    errors["base"] = "login_error"
                elif protocol._logged_in:
                    devices = await self.hass.async_add_executor_job(
                        protocol.get_devices
                    )
                    if devices:
                        found = list(
                            filter(
                                lambda d: not d.get("parent_id")
                                and str(d["model"]) in SUPPORTED_MODELS,
                                devices["result"]["list"],
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
                                self.extract_info(
                                    list(self.devices.values())[0])
                                return await self.async_step_connect()
                            return await self.async_step_devices()

                    errors["base"] = "no_devices"
            else:
                errors["base"] = "credentials_incomplete"
        return self.async_show_form(
            step_id="with_map",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME, default=self.username): str,
                    vol.Required(CONF_PASSWORD, default=self.password): str,
                    vol.Required(CONF_COUNTRY, default=self.country): vol.In(
                        ["cn", "de", "us", "ru", "tw", "sg", "in", "i2"]
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_devices(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle multiple Dreame Vacuum devices found."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self.extract_info(self.devices[user_input["devices"]])
            return await self.async_step_connect()

        return self.async_show_form(
            step_id="devices",
            data_schema=vol.Schema(
                {vol.Required("devices"): vol.In(list(self.devices))}
            ),
            errors=errors,
        )

    async def async_step_options(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
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
                },
                options={
                    CONF_NOTIFY: user_input[CONF_NOTIFY],
                    CONF_COLOR_SCHEME: user_input.get(CONF_COLOR_SCHEME),
                    CONF_MAP_OBJECTS: user_input.get(CONF_MAP_OBJECTS),
                },
            )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=self.name): str,
                vol.Required(CONF_NOTIFY, default=list(NOTIFICATION.keys())): cv.multi_select(NOTIFICATION),
            }
        )

        if self.with_map:
            data_schema = data_schema.extend(
                {
                    vol.Required(CONF_COLOR_SCHEME, default="Dreame Light"): vol.In(list(MAP_COLOR_SCHEME_LIST.keys())),
                    vol.Required(CONF_MAP_OBJECTS, default=list(MAP_OBJECTS.keys())): cv.multi_select(MAP_OBJECTS),
                }
            )

        return self.async_show_form(
            step_id="options", data_schema=data_schema, errors=errors
        )

    def extract_info(self, device_info: dict[str, Any]) -> None:
        """Extract the device info."""
        if self.host is None:
            self.host = device_info["localip"]
        if self.mac is None:
            self.mac = device_info["mac"]
        if self.model is None:
            self.model = device_info["model"]
        if self.name is None:
            self.name = device_info["name"]
        self.token = device_info["token"]
