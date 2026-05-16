# ZhiJin Solar Controller

![HACS Default](https://img.shields.io/badge/HACS-Default-41BDF5?style=for-the-badge&logo=home-assistant)
![GitHub release](https://img.shields.io/github/v/release/franchixco/zhijin_solar?style=for-the-badge)
![License MIT](https://img.shields.io/badge/license-MIT-blue?style=for-the-badge)
![Last commit](https://img.shields.io/github/last-commit/franchixco/zhijin_solar?style=for-the-badge)

Home Assistant custom integration for ZhiJin solar charge controllers via Bluetooth Low Energy (BLE). Provides real-time monitoring and configuration for ZJBE-2412 series and compatible controllers.

<!-- TODO: Add screenshot of device page showing all entities -->

## Supported Controllers

| Controller Type | Status |
|----------------|--------|
| Standard (ZJBE-2412 series) | ![Tested](https://img.shields.io/badge/Tested-green) |
| Bingwang (Grid-tied) | ![Untested](https://img.shields.io/badge/Untested-orange) |
| Liwang (Off-grid) | ![Untested](https://img.shields.io/badge/Untested-orange) |

The Standard controller is actively tested. Bingwang and Liwang variants are implemented based on protocol analysis but lack hardware validation.

## Features

- Real-time sensor readings: battery voltage, charging/discharging current, temperature, total energy
- Battery SOC (State of Charge) calculated from voltage using configurable full/cutoff settings
- Configuration options: battery type, output mode, voltage monitor mode
- Battery protection settings: full voltage, cutoff voltage, restore discharge voltage
- Load output control (Standard) or inverter switch (Bingwang/Liwang)
- Warning detection for grid-tied inverters (Bingwang)
- Firmware version display
- Configurable poll interval (default 10 seconds)

## Requirements

- Home Assistant 2024.1.0 or newer
- Bluetooth adapter connected to Home Assistant (HAOS built-in, or Bluetooth proxy)
- ZhiJin controller within Bluetooth range
- Nordic UART Service (NUS) compatible BLE adapter

## Installation

### HACS (recommended)

1. Add this repository to HACS:
   - Navigate to HACS → Integrations → ⋮ → Custom repositories
   - Add repository: `https://github.com/franchixco/zhijin_solar`
   - Category: Integration
   - Click Add
2. Install the integration
3. Restart Home Assistant
4. Add integration: Settings → Devices & Services → Add Integration → search "ZhiJin Solar Controller"

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=zhijin_solar)

<details>
<summary>Manual installation</summary>

1. Copy the `custom_components/zhijin_solar/` directory to your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant
3. Add integration: Settings → Devices & Services → Add Integration → search "ZhiJin Solar Controller"

</details>

## Configuration

The integration uses Home Assistant's config flow for setup.

1. During setup, select your ZhiJin controller from discovered BLE devices, or enter the MAC address manually
2. MAC address format: `24:12:00:00:XX:XX` (check your phone's Bluetooth settings or ZhiJin app)
3. Configure poll interval (default 10 seconds, adjustable in integration options)
4. The controller automatically identifies its device type (Standard, Bingwang, or Liwang)

### Bluetooth Service UUID

The integration uses the Nordic UART Service (NUS):
- Service UUID: `6E400001-B5A3-F393-E0A9-E50E24DCCA9E`
- Write Characteristic: `6E400003-B5A3-F393-E0A9-E50E24DCCA9E`
- Notify Characteristic: `6E400002-B5A3-F393-E0A9-E50E24DCCA9E`

## Entities

### Sensors

#### Standard Controller

| Entity | Unit | Device Class | State Class | Notes |
|--------|------|--------------|-------------|-------|
| Battery voltage | V | voltage | measurement | Current battery voltage |
| Solar charging current | A | current | measurement | Solar panel input current |
| Load discharge current | A | current | measurement | Load output current |
| Temperature | °C | temperature | measurement | Controller temperature |
| Total energy generated | kWh | energy | total_increasing | Cumulative energy, read-only |
| Battery SOC | % | battery | measurement | Calculated from voltage |
| Firmware version | - | - | - | Controller firmware |

#### Bingwang Controller (⚠️ Untested)

| Entity | Unit | Device Class | State Class | Notes |
|--------|------|--------------|-------------|-------|
| PV voltage | V | voltage | measurement | Solar panel voltage |
| PV current | A | current | measurement | Solar panel current |
| Mains voltage | V | voltage | measurement | Grid voltage |
| Mains frequency | Hz | frequency | measurement | Grid frequency |
| Real-time power | W | power | measurement | Current output power |
| Accumulated energy | kWh | energy | total_increasing | Cumulative energy, read-only |
| Temperature | °C | temperature | measurement | Controller temperature |
| Firmware version | - | - | - | Controller firmware |

#### Liwang Controller (⚠️ Untested)

| Entity | Unit | Device Class | State Class | Notes |
|--------|------|--------------|-------------|-------|
| Battery voltage | V | voltage | measurement | Current battery voltage |
| DC current | A | current | measurement | DC input current |
| Output voltage | V | voltage | measurement | Inverter output voltage |
| Output frequency | Hz | frequency | measurement | Inverter output frequency |
| Real-time power | W | power | measurement | Current output power |
| Accumulated energy | kWh | energy | total_increasing | Cumulative energy, read-only |
| Temperature | °C | temperature | measurement | Controller temperature |
| Firmware version | - | - | - | Controller firmware |

### Selects

#### Standard Controller

| Entity | Options |
|--------|---------|
| Battery type | Lithium, Gel, Lead-acid |
| Output mode | Manual, Auto, Timer, Straight-through |
| Voltage monitor mode | Auto, 12V, 24V, 36V, 48V, 60V, 72V, 84V |

### Numbers

#### Standard Controller

| Entity | Range | Step | Notes |
|--------|-------|------|-------|
| Full voltage | 0-60 V | 0.1 | Voltage at 100% SOC |
| Cutoff voltage | 0-60 V | 0.1 | Minimum battery voltage |
| Restore discharge voltage | 0-60 V | 0.1 | Voltage to restore load |

#### Bingwang Controller (⚠️ Untested)

| Entity | Range | Step | Notes |
|--------|-------|------|-------|
| Max power | 0-10000 W | 100 | Maximum power output |

### Switches

| Entity | Device Type | Notes |
|--------|-------------|-------|
| Load output | Standard | Toggle load output on/off |
| Inverter switch | Bingwang, Liwang | Toggle inverter on/off (⚠️ Untested) |

### Binary Sensors

#### Bingwang Controller (⚠️ Untested)

| Entity | Notes |
|--------|-------|
| Battery undervoltage | Battery voltage below threshold |
| Battery overvoltage | Battery voltage above threshold |
| Overheat protection | Controller overheated |
| Overload protection | Output overload detected |
| DC undervoltage | DC voltage below threshold |
| DC overvoltage | DC voltage above threshold |
| AC undervoltage | AC voltage below threshold |
| AC overvoltage | AC voltage above threshold |
| Under frequency | AC frequency below threshold |
| Over frequency | AC frequency above threshold |
| Islanding protection | Grid islanding detected |
| PV undervoltage | PV voltage below threshold |
| PV overvoltage | PV voltage above threshold |
| Grid undervoltage | Grid voltage below threshold |
| Grid overvoltage | Grid voltage above threshold |

## Battery SOC

State of Charge (SOC) is calculated by the integration using the battery voltage and the controller's configured settings:

- 100% SOC = Full voltage setting
- 0% SOC = Cutoff voltage setting
- Current SOC = Linear interpolation between these two points

For accurate SOC readings, calibrate the full and cutoff voltage settings:

1. Fully charge your battery using the controller
2. Set the full voltage to match your fully charged voltage
3. Set the cutoff voltage to your battery manufacturer's recommended minimum voltage
4. SOC will now be calculated based on your battery's actual characteristics

The ZhiJin app uses hardcoded voltages per battery chemistry which may not match your specific battery. Using the configurable settings allows for accurate calibration.

## Battery Protection

⚠️ WARNING: Incorrect battery voltage settings can permanently damage batteries.

The integration exposes three critical voltage settings for battery protection:

### Recommended Settings for 12V Systems

| Battery Type | Cutoff Voltage | Full Voltage | Restore Voltage |
|--------------|----------------|--------------|-----------------|
| LiFePO4 | 10.0 V | 14.4 V | 11.0 V |
| Gel | 10.5 V | 13.8 V | 11.5 V |
| Lead-Acid | 10.5 V | 14.4 V | 11.5 V |

Always verify values against your battery manufacturer's specifications. Settings for 24V, 36V, 48V, and higher systems should be scaled accordingly.

### How it works

- **Cutoff voltage**: Minimum voltage before load is disconnected to protect the battery from deep discharge
- **Full voltage**: Voltage at which the battery is considered fully charged (used for SOC calculation)
- **Restore voltage**: Voltage at which the load is re-enabled after cutoff

The controller automatically disconnects the load when battery voltage falls below the cutoff voltage and reconnects when it rises above the restore voltage.

## Energy Tracking

The total energy generated sensor shows the cumulative energy processed by the controller.

- **Storage**: Energy data is stored in the controller's internal memory
- **Read-only**: This value cannot be reset via Home Assistant
- **Reset method**: Long press the UP key on the physical controller to reset the counter
- **Post-reset**: After resetting, you may want to adjust your Home Assistant energy statistics to match the new baseline

The energy counter persists across power cycles and only resets when manually triggered via the controller's hardware interface.

## Troubleshooting

### Bluetooth Connection Issues

1. **Device not discovered**
   - Ensure the controller is powered on
   - Check Bluetooth range (typically 10-30 meters without obstructions)
   - Verify your Bluetooth adapter is working in Home Assistant
   - Try restarting Home Assistant

2. **Connection drops frequently**
   - Increase the poll interval in integration options (default 10 seconds)
   - Check for Bluetooth interference from other devices
   - Move your Bluetooth adapter closer to the controller
   - Consider using a dedicated Bluetooth adapter with external antenna

3. **Failed to connect**
   - Verify the MAC address is correct
   - Check if another device is connected to the controller (BLE allows only one active connection)
   - Disconnect from the ZhiJin app before setting up in Home Assistant

### Data Issues

4. **Entities showing "Unknown" or "Unavailable"**
   - Wait for the next poll cycle (check poll interval setting)
   - Check the controller is powered on and functioning
   - Review integration logs for errors
   - Try restarting the integration

5. **Incorrect values**
   - Verify your battery type and voltage settings match your actual system
   - Check for sensor calibration issues
   - Compare readings with the ZhiJin app

6. **SOC not updating or showing incorrect values**
   - Ensure full voltage and cutoff voltage are set correctly
   - Verify battery type is set correctly
   - Check that the battery is in the expected voltage range

### Configuration Issues

7. **Settings not applying**
   - Verify the write operation completed successfully
   - Check integration logs for write errors
   - Some settings may only take effect after a controller restart
   - Ensure the controller is not in a locked state

8. **Device type mismatch**
   - The integration auto-detects device type during initial connection
   - If incorrect, remove and re-add the integration
   - Check the device label on your physical controller

### Performance Issues

9. **High battery drain**
   - Reduce the poll interval in integration options
   - Consider using a Bluetooth proxy to reduce HA's Bluetooth adapter usage
   - Check for unnecessary automations triggering frequent reads

10. **Slow updates**
    - Adjust poll interval to a lower value for more frequent updates
    - Check network latency if using a Bluetooth proxy
    - Review Home Assistant system performance

### Debug Logging

Enable debug logging to troubleshoot issues:

```yaml
logger:
  default: info
  logs:
    custom_components.zhijin_solar: debug
    bleak: debug
```

Restart Home Assistant after adding this configuration. Logs will appear in Home Assistant → System → Logs.

## Protocol Details

<details>
<summary>Technical protocol documentation</summary>

### Overview

The ZhiJin Solar Controller uses a custom binary protocol over the Nordic UART Service (BLE NUS).

### Frame Format

```
[device_type][func_code][payload...][CRC16_lo][CRC16_hi]
```

- **device_type**: 1 byte (0x01=Standard, 0x02=Bingwang, 0x03=Liwang)
- **func_code**: 1 byte (0x03=Read, 0x10=Write)
- **payload**: Variable length data
- **CRC16**: 2 bytes (little-endian order, polynomial 0xA001, init 0xFFFF)

### Register Banks

- **Read-only**: 0x0001-0x0010 (sensor data)
- **Read/Write**: 0x1001-0x100F (configuration settings)

### Device Types

| Type | Value | Name |
|------|-------|------|
| MODULE | 0x00 | Module |
| STANDARD | 0x01 | Standard Controller |
| BINGWANG | 0x02 | Bingwang (Grid-tied) |
| LIWANG | 0x03 | Liwang (Off-grid) |

### Function Codes

| Code | Value | Description |
|------|-------|-------------|
| READ | 0x03 | Read registers |
| WRITE | 0x10 | Write registers |

### CRC16 Calculation

Modbus-like CRC16 with polynomial 0xA001 and initial value 0xFFFF. The CRC is appended to the frame in little-endian order (low byte first).

### Data Encoding

- Voltage: 16-bit unsigned integer, divide by 10 (e.g., 125 = 12.5V)
- Current: 16-bit unsigned integer, divide by 10 (e.g., 52 = 5.2A)
- Temperature: 16-bit unsigned integer, divide by 100 (e.g., 2450 = 24.50°C)
- Frequency: 16-bit unsigned integer, divide by 100 (e.g., 5000 = 50.00Hz)
- Power: 16-bit unsigned integer, divide by 10 (e.g., 1234 = 123.4W)
- Energy: 32-bit unsigned integer, divide by 10 (e.g., 12345 = 1234.5kWh)

</details>

## Known Limitations

- BLE allows only one active connection per device. Disconnect from the ZhiJin app before using this integration.
- Energy counters are stored in the controller and cannot be reset via Home Assistant.
- Battery SOC is a linear approximation based on voltage; actual SOC may vary with battery age, temperature, and load.
- Bingwang and Liwang controller types are untested; entity support is based on protocol analysis only.
- Some configuration changes may not take effect immediately or may require a controller restart.
- Bluetooth range is limited; use a Bluetooth proxy if your controller is far from Home Assistant.

## Contributing

Contributions are welcome. Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

If you have a Bingwang or Liwang controller, testing and feedback would be particularly valuable.

## License

MIT License - see LICENSE file for details.

## Support

- **Issues**: https://github.com/franchixco/zhijin_solar/issues
- **Documentation**: https://github.com/franchixco/zhijin_solar
- **HACS**: https://github.com/franchixco/zhijin_solar

---

Manufacturer: ZhiJin Energy (枝晋)
Model: Solar Controller (ZJBE-2412 series)
BLE Version: 5.x
Firmware: 11.0.2+