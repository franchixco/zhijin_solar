"""Sensor platform for ZhiJin Solar Controller."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import ZhiJinConfigEntry
from .const import DOMAIN
from .coordinator import ZhiJinCoordinator
from .protocol import DeviceType


@dataclass(frozen=True, kw_only=True)
class ZhiJinSensorEntityDescription(SensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], Any]
    device_type_filter: set[int] | None = None


def _calc_soc(data: dict) -> float | None:
    """Calculate State of Charge using controller's own voltage settings.

    Uses full_voltage as 100% reference and cutoff_voltage as 0% reference.
    The IPA hardcodes per-chemistry voltages (11.8/12.2V for lithium) which
    are too conservative for real 3S Li-ion (should be ~12.6V). Using the
    controller's configurable settings lets the user calibrate SOC by
    adjusting full_voltage and cutoff_voltage on the controller or via HA.
    """
    std = data.get("standard", {})
    settings = data.get("settings", {})
    voltage = std.get("battery_voltage")
    if voltage is None:
        return None

    full_v = settings.get("full_voltage", 12.6)
    cutoff_v = settings.get("cutoff_voltage", 9.0)

    if full_v <= cutoff_v:
        return None

    soc = (voltage - cutoff_v) / (full_v - cutoff_v) * 100.0
    return round(max(0.0, min(100.0, soc)), 1)


STANDARD_SENSORS = (
    ZhiJinSensorEntityDescription(
        key="battery_voltage",
        translation_key="battery_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        value_fn=lambda d: d.get("standard", {}).get("battery_voltage"),
        device_type_filter={DeviceType.STANDARD},
    ),
    ZhiJinSensorEntityDescription(
        key="charging_current",
        translation_key="charging_current",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        value_fn=lambda d: d.get("standard", {}).get("charging_current"),
        device_type_filter={DeviceType.STANDARD},
    ),
    ZhiJinSensorEntityDescription(
        key="discharge_current",
        translation_key="discharge_current",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        value_fn=lambda d: d.get("standard", {}).get("discharge_current"),
        device_type_filter={DeviceType.STANDARD},
    ),
    ZhiJinSensorEntityDescription(
        key="temperature",
        translation_key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda d: d.get("standard", {}).get("temperature"),
        device_type_filter={DeviceType.STANDARD},
    ),
    ZhiJinSensorEntityDescription(
        key="total_power",
        translation_key="total_power",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=lambda d: d.get("standard", {}).get("total_power"),
        device_type_filter={DeviceType.STANDARD},
    ),
    ZhiJinSensorEntityDescription(
        key="battery_soc",
        translation_key="battery_soc",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda d: _calc_soc(d),
        device_type_filter={DeviceType.STANDARD},
    ),
)

BINGWANG_SENSORS = (
    ZhiJinSensorEntityDescription(
        key="bw_pv_voltage",
        translation_key="pv_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        value_fn=lambda d: d.get("bingwang", {}).get("pv_voltage"),
        device_type_filter={DeviceType.BINGWANG},
    ),
    ZhiJinSensorEntityDescription(
        key="bw_pv_current",
        translation_key="pv_current",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        value_fn=lambda d: d.get("bingwang", {}).get("pv_current"),
        device_type_filter={DeviceType.BINGWANG},
    ),
    ZhiJinSensorEntityDescription(
        key="bw_mains_voltage",
        translation_key="mains_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        value_fn=lambda d: d.get("bingwang", {}).get("mains_voltage"),
        device_type_filter={DeviceType.BINGWANG},
    ),
    ZhiJinSensorEntityDescription(
        key="bw_mains_frequency",
        translation_key="mains_frequency",
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        value_fn=lambda d: d.get("bingwang", {}).get("mains_frequency"),
        device_type_filter={DeviceType.BINGWANG},
    ),
    ZhiJinSensorEntityDescription(
        key="bw_realtime_power",
        translation_key="realtime_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=lambda d: d.get("bingwang", {}).get("realtime_power"),
        device_type_filter={DeviceType.BINGWANG},
    ),
    ZhiJinSensorEntityDescription(
        key="bw_accumulated_power",
        translation_key="accumulated_power",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=lambda d: d.get("bingwang", {}).get("accumulated_power"),
        device_type_filter={DeviceType.BINGWANG},
    ),
    ZhiJinSensorEntityDescription(
        key="bw_temperature",
        translation_key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda d: d.get("bingwang", {}).get("temperature"),
        device_type_filter={DeviceType.BINGWANG},
    ),
)

LIWANG_SENSORS = (
    ZhiJinSensorEntityDescription(
        key="lw_battery_voltage",
        translation_key="battery_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        value_fn=lambda d: d.get("liwang", {}).get("battery_voltage"),
        device_type_filter={DeviceType.LIWANG},
    ),
    ZhiJinSensorEntityDescription(
        key="lw_dc_current",
        translation_key="dc_current",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        value_fn=lambda d: d.get("liwang", {}).get("dc_current"),
        device_type_filter={DeviceType.LIWANG},
    ),
    ZhiJinSensorEntityDescription(
        key="lw_output_voltage",
        translation_key="output_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        value_fn=lambda d: d.get("liwang", {}).get("output_voltage"),
        device_type_filter={DeviceType.LIWANG},
    ),
    ZhiJinSensorEntityDescription(
        key="lw_output_frequency",
        translation_key="output_frequency",
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        value_fn=lambda d: d.get("liwang", {}).get("output_frequency"),
        device_type_filter={DeviceType.LIWANG},
    ),
    ZhiJinSensorEntityDescription(
        key="lw_realtime_power",
        translation_key="realtime_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=lambda d: d.get("liwang", {}).get("realtime_power"),
        device_type_filter={DeviceType.LIWANG},
    ),
    ZhiJinSensorEntityDescription(
        key="lw_accumulated_power",
        translation_key="accumulated_power",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=lambda d: d.get("liwang", {}).get("accumulated_power"),
        device_type_filter={DeviceType.LIWANG},
    ),
    ZhiJinSensorEntityDescription(
        key="lw_temperature",
        translation_key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda d: d.get("liwang", {}).get("temperature"),
        device_type_filter={DeviceType.LIWANG},
    ),
)

COMMON_SENSORS = (
    ZhiJinSensorEntityDescription(
        key="firmware_version",
        translation_key="firmware_version",
        value_fn=lambda d: d.get("module_info", {}).get(
            "firmware_string",
            str(d.get("module_info", {}).get("firmware_version", "unknown")),
        ),
        device_type_filter=None,
    ),
)

ALL_SENSORS = STANDARD_SENSORS + BINGWANG_SENSORS + LIWANG_SENSORS + COMMON_SENSORS


class ZhiJinSensorEntity(CoordinatorEntity[ZhiJinCoordinator], SensorEntity):
    entity_description: ZhiJinSensorEntityDescription

    def __init__(
        self,
        coordinator: ZhiJinCoordinator,
        description: ZhiJinSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator._address}_{description.key}"
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.coordinator.data or {})


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ZhiJinConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    device_type = coordinator._device_type

    entities = []
    for description in ALL_SENSORS:
        if description.device_type_filter is None or device_type in description.device_type_filter:
            entities.append(ZhiJinSensorEntity(coordinator, description))

    async_add_entities(entities)
