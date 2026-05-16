"""Binary sensor platform for ZhiJin Solar Controller warnings."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import ZhiJinConfigEntry
from .const import DOMAIN
from .coordinator import ZhiJinCoordinator
from .protocol import DeviceType, WARNING_NAMES_BINGWANG


@dataclass(frozen=True, kw_only=True)
class ZhiJinWarningEntityDescription(BinarySensorEntityDescription):
    warning_key: str
    device_type_filter: set[int]


WARNING_DESCRIPTIONS = tuple(
    ZhiJinWarningEntityDescription(
        key=f"warning_{name}",
        translation_key=f"warning_{name}",
        warning_key=name,
        device_class=None,
        device_type_filter={DeviceType.BINGWANG},
    )
    for name in WARNING_NAMES_BINGWANG
)


class ZhiJinWarningEntity(CoordinatorEntity[ZhiJinCoordinator], BinarySensorEntity):
    _attr_has_entity_name = True
    entity_description: ZhiJinWarningEntityDescription

    def __init__(
        self,
        coordinator: ZhiJinCoordinator,
        description: ZhiJinWarningEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator._address}_{description.key}"
        self._attr_device_info = coordinator.device_info

    @property
    def is_on(self) -> bool:
        warnings: list[str] = (
            self.coordinator.data.get("bingwang", {}).get("warnings", [])
            if self.coordinator.data
            else []
        )
        return self.entity_description.warning_key in warnings


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ZhiJinConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    device_type = coordinator._device_type

    entities = []
    for description in WARNING_DESCRIPTIONS:
        if device_type in description.device_type_filter:
            entities.append(ZhiJinWarningEntity(coordinator, description))

    async_add_entities(entities)
