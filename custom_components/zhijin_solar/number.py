"""Number platform for ZhiJin Solar Controller numeric settings."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import ZhiJinConfigEntry
from .const import DOMAIN
from .coordinator import ZhiJinCoordinator
from .protocol import DeviceType, FuncCode, build_frame

_LOGGER = logging.getLogger(__name__)


class ZhiJinNumberEntity(CoordinatorEntity[ZhiJinCoordinator], NumberEntity):
    def __init__(
        self,
        coordinator: ZhiJinCoordinator,
        description: NumberEntityDescription,
        write_payload_fn: Any,
        device_type: int,
        read_key: str | None = None,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._write_payload_fn = write_payload_fn
        self._device_type = device_type
        self._read_key = read_key
        self._attr_unique_id = f"{coordinator._address}_{description.key}"
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self) -> float | None:
        if self._read_key and self.coordinator.data:
            settings = self.coordinator.data.get("settings", {})
            return settings.get(self._read_key)
        return self._attr_native_value

    async def async_set_native_value(self, value: float) -> None:
        raw = int(value)
        payload = self._write_payload_fn(raw)
        cmd = build_frame(self._device_type, FuncCode.WRITE, payload)
        result = await self.coordinator._send_command(cmd)

        if result:
            self._attr_native_value = value
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ZhiJinConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    device_type = coordinator._device_type

    entities: list[ZhiJinNumberEntity] = []

    if device_type == DeviceType.STANDARD:
        entities.extend([
            ZhiJinNumberEntity(
                coordinator,
                NumberEntityDescription(
                    key="full_voltage",
                    translation_key="full_voltage",
                    native_min_value=0,
                    native_max_value=60,
                    native_step=0.1,
                    mode="box",
                ),
                lambda v: [0x10, 0x04, 0x00, 0x01, 0x02, (int(v * 10) >> 8) & 0xFF, int(v * 10) & 0xFF],
                DeviceType.STANDARD,
                read_key="full_voltage",
            ),
            ZhiJinNumberEntity(
                coordinator,
                NumberEntityDescription(
                    key="cutoff_voltage",
                    translation_key="cutoff_voltage",
                    native_min_value=0,
                    native_max_value=60,
                    native_step=0.1,
                    mode="box",
                ),
                lambda v: [0x10, 0x06, 0x00, 0x01, 0x02, (int(v * 10) >> 8) & 0xFF, int(v * 10) & 0xFF],
                DeviceType.STANDARD,
                read_key="cutoff_voltage",
            ),
            ZhiJinNumberEntity(
                coordinator,
                NumberEntityDescription(
                    key="restore_discharge_voltage",
                    translation_key="restore_discharge_voltage",
                    native_min_value=0,
                    native_max_value=60,
                    native_step=0.1,
                    mode="box",
                ),
                lambda v: [0x10, 0x09, 0x00, 0x01, 0x02, (int(v * 10) >> 8) & 0xFF, int(v * 10) & 0xFF],
                DeviceType.STANDARD,
                read_key="restore_discharge_voltage",
            ),
        ])

    if device_type == DeviceType.BINGWANG:
        entities.extend([
            ZhiJinNumberEntity(
                coordinator,
                NumberEntityDescription(
                    key="max_power",
                    translation_key="max_power",
                    native_min_value=0,
                    native_max_value=10000,
                    native_step=100,
                    mode="slider",
                ),
                lambda v: [4, 1, 0, 0, (v >> 8) & 0xFF, v & 0xFF],
                DeviceType.BINGWANG,
            ),
        ])

    async_add_entities(entities)
