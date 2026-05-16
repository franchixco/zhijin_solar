"""Switch platform for ZhiJin Solar Controller."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import ZhiJinConfigEntry
from .const import DOMAIN
from .coordinator import ZhiJinCoordinator
from .protocol import DeviceType, FuncCode, build_frame

_LOGGER = logging.getLogger(__name__)


class ZhiJinSwitchEntity(CoordinatorEntity[ZhiJinCoordinator], SwitchEntity):
    _attr_has_entity_name = True
    def __init__(
        self,
        coordinator: ZhiJinCoordinator,
        description: SwitchEntityDescription,
        on_payload: list[int],
        off_payload: list[int],
        device_type: int,
        read_key: str | None = None,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._on_payload = on_payload
        self._off_payload = off_payload
        self._device_type = device_type
        self._read_key = read_key
        self._attr_unique_id = f"{coordinator._address}_{description.key}"
        self._attr_device_info = coordinator.device_info
        self._is_on = False

    @property
    def is_on(self) -> bool:
        if self._read_key and self.coordinator.data:
            settings = self.coordinator.data.get("settings", {})
            return bool(settings.get(self._read_key, 0))
        return self._is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        cmd = build_frame(self._device_type, FuncCode.WRITE, self._on_payload)
        result = await self.coordinator._send_command(cmd)
        if result:
            self._is_on = True
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        cmd = build_frame(self._device_type, FuncCode.WRITE, self._off_payload)
        result = await self.coordinator._send_command(cmd)
        if result:
            self._is_on = False
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ZhiJinConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    device_type = coordinator._device_type

    entities: list[ZhiJinSwitchEntity] = []

    if device_type == DeviceType.STANDARD:
        entities.append(
            ZhiJinSwitchEntity(
                coordinator,
                SwitchEntityDescription(
                    key="load_output",
                    name="Load output",
                    translation_key="load_output",
                ),
                on_payload=[0x10, 0x07, 0x00, 0x01, 0x02, 0x00, 0x01],
                off_payload=[0x10, 0x07, 0x00, 0x01, 0x02, 0x00, 0x00],
                device_type=DeviceType.STANDARD,
                read_key="load_output",
            )
        )

    if device_type == DeviceType.BINGWANG:
        entities.append(
            ZhiJinSwitchEntity(
                coordinator,
                SwitchEntityDescription(
                    key="inverter_switch",
                    name="Inverter switch",
                    translation_key="inverter_switch",
                ),
                on_payload=[2, 1, 0, 0, 0, 1],
                off_payload=[2, 1, 0, 0, 0, 0],
                device_type=DeviceType.BINGWANG,
            )
        )

    if device_type == DeviceType.LIWANG:
        entities.append(
            ZhiJinSwitchEntity(
                coordinator,
                SwitchEntityDescription(
                    key="inverter_switch",
                    name="Inverter switch",
                    translation_key="inverter_switch",
                ),
                on_payload=[2, 1, 0, 0, 0, 1],
                off_payload=[2, 1, 0, 0, 0, 0],
                device_type=DeviceType.LIWANG,
            )
        )

    async_add_entities(entities)
