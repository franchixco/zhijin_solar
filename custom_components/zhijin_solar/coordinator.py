"""ZhiJin Solar Controller - BLE Data Coordinator."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from bleak import BleakClient, BleakError
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DEFAULT_POLL_INTERVAL,
    DOMAIN,
    MANUFACTURER,
    MODEL,
    NUS_NOTIFY_CHAR_UUID,
    NUS_SERVICE_UUID,
    NUS_WRITE_CHAR_UUID,
)
from .protocol import (
    DEVICE_TYPE_NAMES,
    DeviceType,
    FuncCode,
    StandardDetail,
    cmd_read_bingwang_config,
    cmd_read_bingwang_main,
    cmd_read_liwang_config,
    cmd_read_liwang_main,
    cmd_read_module,
    cmd_read_standard_detail,
    cmd_read_standard_main,
    parse_response,
)

_LOGGER = logging.getLogger(__name__)

# Device Information Service (DIS) UUIDs
DIS_SERVICE_UUID = "0000180a-0000-1000-8000-00805f9b34fb"
DIS_MANUFACTURER_CHAR = "00002a29-0000-1000-8000-00805f9b34fb"
DIS_FIRMWARE_CHAR = "00002a26-0000-1000-8000-00805f9b34fb"
DIS_MODEL_CHAR = "00002a24-0000-1000-8000-00805f9b34fb"


class ZhiJinCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for ZhiJin Solar Controller BLE communication."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self._address: str = entry.data[CONF_ADDRESS]
        self._poll_interval: int = entry.data.get(
            "poll_interval", DEFAULT_POLL_INTERVAL
        )
        self._client: BleakClient | None = None
        self._response_queue: asyncio.Queue[bytes] = asyncio.Queue()
        self._device_type: int | None = None
        self._device_type_name: str = ""
        self._write_char: str = NUS_WRITE_CHAR_UUID
        self._notify_char: str = NUS_NOTIFY_CHAR_UUID
        self._dis_info: dict[str, str] = {}

        super().__init__(
            hass,
            _LOGGER,
            name=f"ZhiJin Solar {self._address}",
            update_interval=timedelta(seconds=self._poll_interval),
        )

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info dict for HA device registry."""
        info: dict[str, Any] = {
            "identifiers": {(DOMAIN, self._address)},
            "name": "ZhiJin Solar Controller",
            "manufacturer": self._dis_info.get("manufacturer", MANUFACTURER),
            "model": MODEL,
        }
        if self._device_type_name:
            info["model"] = f"{MODEL} ({self._device_type_name})"
        if "firmware" in self._dis_info:
            info["sw_version"] = self._dis_info["firmware"]
        elif self.data and "module_info" in self.data:
            fw = self.data["module_info"].get("firmware_version")
            if fw is not None:
                info["sw_version"] = str(fw)
        if "model" in self._dis_info:
            info["hw_version"] = self._dis_info["model"]
        return info

    async def shutdown(self) -> None:
        """Disconnect BLE client on integration unload."""
        if self._client and self._client.is_connected:
            try:
                await self._client.stop_notify(self._notify_char)
            except BleakError:
                pass
            try:
                await self._client.disconnect()
            except BleakError:
                _LOGGER.debug("Error disconnecting during shutdown")
        self._client = None

    async def _ensure_connected(self) -> None:
        """Ensure BLE client is connected and NUS notifications are subscribed."""
        if self._client and self._client.is_connected:
            return

        # Clean up stale client before reconnecting
        if self._client is not None:
            try:
                if self._client.is_connected:
                    await self._client.stop_notify(self._notify_char)
            except BleakError:
                pass
            try:
                await self._client.disconnect()
            except BleakError:
                pass
            self._client = None

        _LOGGER.debug("Connecting to %s", self._address)
        self._client = BleakClient(self._address, timeout=15.0)
        await self._client.connect()

        # Resolve NUS characteristics from GATT services
        self._write_char = NUS_WRITE_CHAR_UUID
        self._notify_char = NUS_NOTIFY_CHAR_UUID

        for service in self._client.services:
            if service.uuid.upper() == NUS_SERVICE_UUID:
                for char in service.characteristics:
                    props = char.properties
                    if "write" in props or "write-without-response" in props:
                        self._write_char = char.uuid
                    if "notify" in props:
                        self._notify_char = char.uuid

        # Clean up any stale notification subscription
        try:
            await self._client.stop_notify(self._notify_char)
        except Exception:
            pass

        await self._client.start_notify(
            self._notify_char, self._notification_handler
        )
        await asyncio.sleep(0.3)

        # Read Device Information Service for manufacturer/firmware
        await self._read_dis()

        _LOGGER.info(
            "Connected to ZhiJin controller at %s (type=%s)",
            self._address,
            self._device_type_name or "unknown",
        )

    async def _read_dis(self) -> None:
        """Read Device Information Service (0x180A) for device metadata."""
        if not self._client or not self._client.is_connected:
            return
        try:
            for service in self._client.services:
                if service.uuid.lower() == DIS_SERVICE_UUID:
                    for char in service.characteristics:
                        char_lower = char.uuid.lower()
                        try:
                            if char_lower == DIS_MANUFACTURER_CHAR:
                                val = await self._client.read_gatt_char(char)
                                self._dis_info["manufacturer"] = (
                                    val.decode("utf-8", errors="replace")
                                    .rstrip("\x00")
                                )
                            elif char_lower == DIS_FIRMWARE_CHAR:
                                val = await self._client.read_gatt_char(char)
                                self._dis_info["firmware"] = (
                                    val.decode("utf-8", errors="replace")
                                    .rstrip("\x00")
                                )
                            elif char_lower == DIS_MODEL_CHAR:
                                val = await self._client.read_gatt_char(char)
                                self._dis_info["model"] = (
                                    val.decode("utf-8", errors="replace")
                                    .rstrip("\x00")
                                )
                        except BleakError:
                            _LOGGER.debug("Could not read DIS char %s", char.uuid)
                    break
        except BleakError as err:
            _LOGGER.debug("Could not read DIS: %s", err)

    def _notification_handler(self, _sender: Any, data: bytearray) -> None:
        """Handle NUS notification callbacks from BLE device."""
        self._response_queue.put_nowait(bytes(data))

    async def _send_command(self, cmd: bytes, timeout: float = 5.0) -> bytes | None:
        """Send a BLE command and wait for response via NUS notification."""
        if not self._client or not self._client.is_connected:
            return None

        # Drain stale responses from previous commands
        while not self._response_queue.empty():
            self._response_queue.get_nowait()

        await self._client.write_gatt_char(self._write_char, cmd, response=False)

        try:
            return await asyncio.wait_for(
                self._response_queue.get(), timeout=timeout
            )
        except asyncio.TimeoutError:
            _LOGGER.warning("Timeout waiting for BLE response")
            return None

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the BLE device."""
        try:
            await self._ensure_connected()
        except BleakError as err:
            self._client = None
            raise UpdateFailed(f"BLE connection failed: {err}") from err

        result: dict[str, Any] = {"address": self._address}

        try:
            # Always read MODULE_INFO first to detect/confirm device type
            response = await self._send_command(cmd_read_module())
            if response:
                _LOGGER.debug(
                    "MODULE response raw: %s (len=%d)",
                    response.hex(),
                    len(response),
                )
                parsed = parse_response(response)
                if "data" in parsed:
                    info = parsed["data"]
                    self._device_type = info.device_type_raw
                    self._device_type_name = info.device_type_name
                    result["module_info"] = {
                        "device_type": info.device_type_raw,
                        "device_type_name": info.device_type_name,
                        "firmware_version": info.firmware_version,
                        "firmware_string": self._dis_info.get(
                            "firmware", str(info.firmware_version)
                        ),
                    }
                elif len(response) >= 3:
                    self._device_type = response[0]
                    self._device_type_name = DEVICE_TYPE_NAMES.get(
                        DeviceType(response[0]), f"Unknown({response[0]})"
                    )
                    _LOGGER.info(
                        "MODULE parse fallback: using frame[0]=%s as device_type",
                        response[0],
                    )

            await asyncio.sleep(0.3)

            # Read device-type-specific data
            if self._device_type == DeviceType.STANDARD:
                await self._read_standard(result)
            elif self._device_type == DeviceType.BINGWANG:
                await self._read_bingwang(result)
            elif self._device_type == DeviceType.LIWANG:
                await self._read_liwang(result)
            else:
                _LOGGER.warning(
                    "Unknown device type %s, attempting standard reads",
                    self._device_type,
                )
                await self._read_standard(result)

        except BleakError as err:
            self._client = None
            raise UpdateFailed(f"BLE communication failed: {err}") from err

        return result

    async def _read_standard(self, result: dict[str, Any]) -> None:
        """Read Standard controller main + detail data."""
        response = await self._send_command(cmd_read_standard_main())
        if response:
            parsed = parse_response(response)
            if "data" in parsed:
                d = parsed["data"]
                result["standard"] = {
                    "battery_voltage": d.battery_voltage,
                    "charging_current": d.charging_current,
                    "discharge_current": d.discharge_current,
                    "temperature": d.temperature,
                    "solar_status": d.solar_status,
                    "total_power": d.total_power,
                }

        await asyncio.sleep(0.3)

        response = await self._send_command(cmd_read_standard_detail())
        if response:
            parsed = parse_response(response)
            if "data" in parsed and isinstance(parsed["data"], StandardDetail):
                d = parsed["data"]
                result["settings"] = {
                    "battery_type": d.battery_type,
                    "full_voltage": d.full_voltage,
                    "cutoff_voltage": d.cutoff_voltage,
                    "output_mode": d.output_mode,
                    "load_output": d.load_output,
                    "voltage_monitor": d.voltage_monitor,
                    "restore_discharge_voltage": d.restore_discharge_voltage,
                    "timing_hour": d.timing_hour,
                    "timing_min": d.timing_min,
                }
            else:
                result["standard_detail_raw"] = parsed

    async def _read_bingwang(self, result: dict[str, Any]) -> None:
        """Read Bingwang controller main + config data."""
        response = await self._send_command(cmd_read_bingwang_main())
        if response:
            parsed = parse_response(response)
            if "data" in parsed:
                d = parsed["data"]
                result["bingwang"] = {
                    "pv_voltage": d.pv_voltage,
                    "pv_current": d.pv_current,
                    "mains_voltage": d.mains_voltage,
                    "mains_frequency": d.mains_frequency,
                    "realtime_power": d.realtime_power,
                    "accumulated_power": d.accumulated_power,
                    "temperature": d.temperature,
                    "warnings": d.warnings,
                }

        await asyncio.sleep(0.3)

        response = await self._send_command(cmd_read_bingwang_config())
        if response:
            parsed = parse_response(response)
            if "data" in parsed:
                d = parsed["data"]
                result["bingwang_config"] = {
                    "max_power": d.max_power,
                    "interval_generation_switch": d.interval_generation_switch,
                }

    async def _read_liwang(self, result: dict[str, Any]) -> None:
        """Read Liwang controller main + config data."""
        response = await self._send_command(cmd_read_liwang_main())
        if response:
            parsed = parse_response(response)
            if "data" in parsed:
                d = parsed["data"]
                result["liwang"] = {
                    "battery_voltage": d.battery_voltage,
                    "dc_current": d.dc_current,
                    "output_voltage": d.output_voltage,
                    "output_frequency": d.output_frequency,
                    "realtime_power": d.realtime_power,
                    "accumulated_power": d.accumulated_power,
                    "temperature": d.temperature,
                }

        await asyncio.sleep(0.3)

        response = await self._send_command(cmd_read_liwang_config())
        if response:
            parsed = parse_response(response)
            result["liwang_config_raw"] = parsed

    async def async_write_command(
        self, device_type: int, payload: list[int]
    ) -> dict[str, Any] | None:
        """Send a WRITE command and return parsed response."""
        from .protocol import build_frame, FuncCode

        cmd = build_frame(device_type, FuncCode.WRITE, payload)
        response = await self._send_command(cmd)
        if response:
            return parse_response(response)
        return None
