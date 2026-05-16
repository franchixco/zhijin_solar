"""Config flow for ZhiJin Solar Controller."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.const import CONF_ADDRESS
from homeassistant.data_entry_flow import FlowResult

from .const import CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL, DOMAIN, NUS_SERVICE_UUID

_LOGGER = logging.getLogger(__name__)


class ZhiJinFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._discovered_devices: dict[str, str] = {}
        self._address: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()

            self._address = address
            return await self.async_step_configure()

        discovered = async_discovered_service_info(self.hass)
        for info in discovered:
            if info.address in self._discovered_devices:
                continue
            for service_uuid in info.service_uuids:
                if service_uuid.upper() == NUS_SERVICE_UUID:
                    name = info.name or info.address
                    self._discovered_devices[info.address] = name
                    break

        if self._discovered_devices:
            addresses = {
                addr: f"{name} ({addr})"
                for addr, name in self._discovered_devices.items()
            }
            schema = vol.Schema({vol.Required(CONF_ADDRESS): vol.In(addresses)})
        else:
            schema = vol.Schema({vol.Required(CONF_ADDRESS): str})

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_configure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            poll_interval = user_input.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL)
            return self.async_create_entry(
                title=f"ZhiJin Solar ({self._address})",
                data={
                    CONF_ADDRESS: self._address,
                    CONF_POLL_INTERVAL: poll_interval,
                },
            )

        return self.async_show_form(
            step_id="configure",
            data_schema=vol.Schema({
                vol.Optional(CONF_POLL_INTERVAL, default=DEFAULT_POLL_INTERVAL): vol.All(
                    int, vol.Range(min=5, max=300)
                ),
            }),
            errors=errors,
        )

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> FlowResult:
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        self._address = discovery_info.address
        self._discovered_devices[discovery_info.address] = (
            discovery_info.name or discovery_info.address
        )

        return await self.async_step_configure()
