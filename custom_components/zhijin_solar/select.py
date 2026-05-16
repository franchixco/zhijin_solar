"""Select platform for ZhiJin Solar Controller configuration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import ZhiJinConfigEntry
from .const import DOMAIN
from .coordinator import ZhiJinCoordinator
from .protocol import DeviceType, FuncCode, build_frame

_LOGGER = logging.getLogger(__name__)

BATTERY_TYPE_OPTIONS = {
    1: "Lithium",
    2: "Gel",
    3: "Lead-acid",
}

OUTPUT_MODE_OPTIONS = {
    0: "Manual",
    1: "Auto",
    2: "Timer",
    3: "Straight-through",
}

VOLTAGE_MONITOR_OPTIONS = {
    0: "Auto",
    1: "12V",
    2: "24V",
    3: "36V",
    4: "48V",
    5: "60V",
    6: "72V",
    7: "84V",
}


class ZhiJinSelectEntity(CoordinatorEntity[ZhiJinCoordinator], SelectEntity):
    def __init__(
        self,
        coordinator: ZhiJinCoordinator,
        description: SelectEntityDescription,
        options_map: dict[int, str],
        write_payload_fn: Any,
        device_type: int,
        read_key: str | None = None,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._options_map = options_map
        self._reverse_map = {v: k for k, v in options_map.items()}
        self._write_payload_fn = write_payload_fn
        self._device_type = device_type
        self._read_key = read_key
        self._attr_unique_id = f"{coordinator._address}_{description.key}"
        self._attr_device_info = coordinator.device_info
        self._attr_options = list(options_map.values())
        self._attr_current_option = None

    @property
    def current_option(self) -> str | None:
        if self._read_key and self.coordinator.data:
            settings = self.coordinator.data.get("settings", {})
            raw = settings.get(self._read_key)
            if raw is not None and raw in self._options_map:
                return self._options_map[raw]
        return self._attr_current_option

    async def async_select_option(self, option: str) -> None:
        raw_value = self._reverse_map.get(option)
        if raw_value is None:
            return

        payload = self._write_payload_fn(raw_value)
        cmd = build_frame(self._device_type, FuncCode.WRITE, payload)
        result = await self.coordinator._send_command(cmd)

        if result:
            self._attr_current_option = option
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ZhiJinConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    device_type = coordinator._device_type

    entities: list[ZhiJinSelectEntity] = []

    if device_type == DeviceType.STANDARD:
        entities.append(
            ZhiJinSelectEntity(
                coordinator,
                SelectEntityDescription(
                    key="battery_type",
                    translation_key="battery_type",
                ),
                BATTERY_TYPE_OPTIONS,
                lambda v: [0x10, 0x01, 0x00, 0x01, 0x02, 0x00, v & 0xFF],
                DeviceType.STANDARD,
                read_key="battery_type",
            )
        )
        entities.append(
            ZhiJinSelectEntity(
                coordinator,
                SelectEntityDescription(
                    key="output_mode",
                    translation_key="output_mode",
                ),
                OUTPUT_MODE_OPTIONS,
                lambda v: [0x10, 0x05, 0x00, 0x01, 0x02, 0x00, v & 0xFF],
                DeviceType.STANDARD,
                read_key="output_mode",
            )
        )
        entities.append(
            ZhiJinSelectEntity(
                coordinator,
                SelectEntityDescription(
                    key="voltage_monitor",
                    translation_key="voltage_monitor",
                ),
                VOLTAGE_MONITOR_OPTIONS,
                lambda v: [0x10, 0x08, 0x00, 0x01, 0x02, 0x00, v & 0xFF],
                DeviceType.STANDARD,
                read_key="voltage_monitor",
            )
        )

    async_add_entities(entities)
