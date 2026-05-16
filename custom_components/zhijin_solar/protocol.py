"""ZhiJin Solar Controller BLE Protocol Library.

Reverse-engineered from ZhiJinPower v1.3.5 (UniApp/DCloud).
Protocol: Custom binary over Nordic UART Service (NUS).
Frame: [device_type][func_code][payload...][CRC16_lo][CRC16_hi]
CRC16: Modbus-like, polynomial 0xA001, init 0xFFFF.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any

NUS_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
NUS_WRITE_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"
NUS_NOTIFY_CHAR_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"


class DeviceType(IntEnum):
    MODULE = 0x00
    STANDARD = 0x01
    BINGWANG = 0x02
    LIWANG = 0x03


class FuncCode(IntEnum):
    READ = 0x03
    WRITE = 0x10


DEVICE_TYPE_NAMES = {
    DeviceType.MODULE: "Module",
    DeviceType.STANDARD: "Standard Controller",
    DeviceType.BINGWANG: "Bingwang (Grid-tied)",
    DeviceType.LIWANG: "Liwang (Off-grid)",
}

WARNING_NAMES_BINGWANG = [
    "battery_undervoltage",
    "battery_overvoltage",
    "overheat_protection",
    "overload_protection",
    "dc_undervoltage",
    "dc_overvoltage",
    "ac_undervoltage",
    "ac_overvoltage",
    "under_frequency",
    "over_frequency",
    "islanding_protection",
    "pv_undervoltage",
    "pv_overvoltage",
    "grid_undervoltage",
    "grid_overvoltage",
]


def crc16(data: bytes) -> tuple[int, int]:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return (crc & 0xFF, (crc >> 8) & 0xFF)


def build_frame(device_type: int, func_code: int, payload: list[int]) -> bytes:
    data = bytes([device_type, func_code] + payload)
    c = crc16(data)
    return data + bytes(c)


def verify_crc(frame: bytes) -> bool:
    if len(frame) < 3:
        return False
    return (frame[-2], frame[-1]) == crc16(frame[:-2])


def u16_be(data: bytes, offset: int) -> int:
    return (data[offset] << 8) | data[offset + 1]


def u32_be(data: bytes, offset: int) -> int:
    return (data[offset] << 24) | (data[offset + 1] << 16) | (data[offset + 2] << 8) | data[offset + 3]


# --- Command builders ---

def cmd_read_module() -> bytes:
    return build_frame(DeviceType.MODULE, FuncCode.READ, [0x00, 0x01, 0x00, 0x05])

def cmd_read_standard_main() -> bytes:
    return build_frame(DeviceType.STANDARD, FuncCode.READ, [0x00, 0x01, 0x00, 0x10])

def cmd_read_standard_detail() -> bytes:
    return build_frame(DeviceType.STANDARD, FuncCode.READ, [0x10, 0x01, 0x00, 0x0F])

def cmd_read_bingwang_main() -> bytes:
    return build_frame(DeviceType.BINGWANG, FuncCode.READ, [0x00, 0x01, 0x00, 0x10])

def cmd_read_bingwang_config() -> bytes:
    return build_frame(DeviceType.BINGWANG, FuncCode.READ, [0x00, 0x01, 0x00, 0x0D])

def cmd_read_bingwang_extended() -> bytes:
    return build_frame(DeviceType.BINGWANG, FuncCode.READ, [0x10, 0x01, 0x00, 0x02])

def cmd_read_liwang_main() -> bytes:
    return build_frame(DeviceType.LIWANG, FuncCode.READ, [0x00, 0x01, 0x00, 0x10])

def cmd_read_liwang_config() -> bytes:
    return build_frame(DeviceType.LIWANG, FuncCode.READ, [0x10, 0x01, 0x00, 0x01])


# --- Parsed data containers ---

@dataclass
class ModuleInfo:
    device_type_raw: int = 0
    device_type_name: str = ""
    firmware_version: int = 0

@dataclass
class StandardData:
    battery_voltage: float = 0.0
    charging_current: float = 0.0
    discharge_current: float = 0.0
    temperature: float = 0.0
    solar_status: str = ""
    work_status: int = 0
    power_status: int = 0
    total_power: float = 0.0

@dataclass
class StandardDetail:
    battery_type: int = 0
    timing_hour: int = 0
    timing_min: int = 0
    full_voltage: float = 0.0
    output_mode: int = 0
    cutoff_voltage: float = 0.0
    load_output: int = 0
    voltage_monitor: int = 0
    restore_discharge_voltage: float = 0.0

@dataclass
class BingwangData:
    pv_voltage: float = 0.0
    pv_current: float = 0.0
    mains_voltage: float = 0.0
    mains_frequency: float = 0.0
    realtime_power: float = 0.0
    accumulated_power: float = 0.0
    temperature: float = 0.0
    warnings: list[str] = field(default_factory=list)

@dataclass
class BingwangConfig:
    max_power: int = 0
    interval_generation_switch: int = 0

@dataclass
class LiwangData:
    battery_voltage: float = 0.0
    dc_current: float = 0.0
    output_voltage: float = 0.0
    output_frequency: float = 0.0
    realtime_power: float = 0.0
    accumulated_power: float = 0.0
    temperature: float = 0.0

@dataclass
class ControllerReading:
    module_info: ModuleInfo | None = None
    standard_data: StandardData | None = None
    bingwang_data: BingwangData | None = None
    bingwang_config: BingwangConfig | None = None
    liwang_data: LiwangData | None = None
    raw_frame: str = ""


# --- Response parsers ---

def parse_module_info(frame: bytes) -> ModuleInfo:
    if len(frame) >= 6:
        raw = u16_be(frame, 4)
    else:
        raw = frame[0]
    firmware = u16_be(frame, 7) if len(frame) > 8 else 0
    return ModuleInfo(
        device_type_raw=raw,
        device_type_name=DEVICE_TYPE_NAMES.get(DeviceType(raw), f"Unknown({raw})"),
        firmware_version=firmware,
    )

def parse_standard_main(frame: bytes) -> StandardData:
    return StandardData(
        battery_voltage=u16_be(frame, 5) / 10.0,
        charging_current=u16_be(frame, 7) / 10.0,
        discharge_current=u16_be(frame, 9) / 10.0,
        temperature=u16_be(frame, 11) / 100.0,
        solar_status="Day" if u16_be(frame, 13) == 1 else "Night",
        work_status=u16_be(frame, 15),
        power_status=u16_be(frame, 17),
        total_power=(u16_be(frame, 21) * 1000 + u16_be(frame, 19)) / 10.0,
    )

def parse_standard_detail(frame: bytes) -> StandardDetail:
    return StandardDetail(
        battery_type=u16_be(frame, 3),
        timing_hour=u16_be(frame, 5),
        timing_min=u16_be(frame, 7),
        full_voltage=u16_be(frame, 9) / 10.0,
        output_mode=u16_be(frame, 11),
        cutoff_voltage=u16_be(frame, 13) / 10.0,
        load_output=u16_be(frame, 15),
        voltage_monitor=u16_be(frame, 17),
        restore_discharge_voltage=u16_be(frame, 19) / 10.0,
    )

def parse_bingwang_main(frame: bytes) -> BingwangData:
    warnings: list[str] = []
    if len(frame) > 22:
        raw = u16_be(frame, 21)
        bits = format(raw, "016b")
        for i, name in enumerate(WARNING_NAMES_BINGWANG):
            if i < len(bits) and bits[-(i + 1)] == "1":
                warnings.append(name)
    return BingwangData(
        pv_voltage=u16_be(frame, 3) / 10.0,
        pv_current=u16_be(frame, 5) / 10.0,
        mains_voltage=u16_be(frame, 7) / 10.0,
        mains_frequency=u16_be(frame, 9) / 100.0,
        realtime_power=u16_be(frame, 11) / 10.0,
        accumulated_power=u32_be(frame, 13) / 10.0,
        temperature=u16_be(frame, 27) / 100.0 if len(frame) > 28 else 0.0,
        warnings=warnings,
    )

def parse_bingwang_config(frame: bytes) -> BingwangConfig:
    return BingwangConfig(
        max_power=u16_be(frame, 3),
        interval_generation_switch=u16_be(frame, 5),
    )

def parse_liwang_main(frame: bytes) -> LiwangData:
    return LiwangData(
        battery_voltage=u16_be(frame, 3) / 10.0,
        dc_current=u16_be(frame, 5) / 10.0,
        output_voltage=u16_be(frame, 7) / 10.0,
        output_frequency=u16_be(frame, 9) / 100.0,
        realtime_power=u16_be(frame, 11) / 10.0,
        accumulated_power=u32_be(frame, 13) / 10.0,
        temperature=u16_be(frame, 21) / 100.0 if len(frame) > 22 else 0.0,
    )


def parse_response(frame: bytes) -> dict[str, Any]:
    if not verify_crc(frame):
        return {"error": "CRC mismatch", "raw": frame.hex()}

    device_type = frame[0]
    func_code = frame[1]
    sub_code = frame[2] if len(frame) > 2 else -1

    result: dict[str, Any] = {
        "device_type": device_type,
        "device_type_name": DEVICE_TYPE_NAMES.get(DeviceType(device_type), f"Unknown({device_type})"),
        "func_code": func_code,
        "sub_code": sub_code,
    }

    try:
        is_module_response = func_code == FuncCode.READ and sub_code == 0x00
        if device_type == DeviceType.MODULE or is_module_response:
            result["data"] = parse_module_info(frame)
        elif device_type == DeviceType.STANDARD and sub_code == 0x14:
            result["data"] = parse_standard_main(frame)
        elif device_type == DeviceType.STANDARD and sub_code == 0x12:
            result["data"] = parse_standard_detail(frame)
        elif device_type == DeviceType.BINGWANG and sub_code == 0x1A:
            result["data"] = parse_bingwang_main(frame)
        elif device_type == DeviceType.BINGWANG and sub_code == 0x04:
            result["data"] = parse_bingwang_config(frame)
        elif device_type == DeviceType.LIWANG and sub_code == 0x14:
            result["data"] = parse_liwang_main(frame)
        else:
            result["raw"] = frame.hex()
    except IndexError:
        result["error"] = "Frame too short"
        result["raw"] = frame.hex()

    return result
