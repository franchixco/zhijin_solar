# ZhiJin Solar Controller

Home Assistant custom integration for ZhiJin solar charge controllers via Bluetooth Low Energy (BLE).

## Supported Controllers

ZhiJin (枝晋) BLE-enabled solar controllers, including models like ZJBE-2412 series.

## Features

- **Sensor readings**: Battery voltage, charging/discharge current, temperature, total energy, battery SOC (State of Charge)
- **Configuration**: Battery type (Gel/LiFePO4/Lead-Acid/Custom), output mode, voltage monitor mode
- **Battery protection**: Full voltage, cutoff voltage, restore discharge voltage — critical settings to prevent battery damage
- **Switch control**: Load output on/off
- **Firmware**: Displays controller firmware version

## Installation

### HACS (recommended)

1. Add this repository as a custom repository in HACS:
   - Go to HACS → Integrations → ⋮ → Custom repositories
   - Paste: `https://github.com/franchixco/zhijin_solar`
   - Category: Integration
2. Click Install
3. Restart Home Assistant
4. Add the integration: Settings → Devices & Services → Add Integration → search "ZhiJin"

### Manual

1. Copy the `custom_components/zhijin_solar/` directory to your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant
3. Add the integration: Settings → Devices & Services → Add Integration → search "ZhiJin"

## Configuration

The integration is configured via the UI. You need:

- **Bluetooth address** of your ZhiJin controller (shown in your phone's Bluetooth settings or the ZhiJin app)

If Home Assistant has a Bluetooth adapter, nearby controllers will be discovered automatically. Otherwise, enter the MAC address manually.

### Requirements

- Home Assistant 2024.1.0 or newer
- A working Bluetooth adapter connected to Home Assistant (HAOS built-in Bluetooth, or a Bluetooth proxy)
- ZhiJin controller within Bluetooth range

## Battery Protection

This integration exposes cutoff voltage, full voltage, and restore discharge voltage settings. These are critical for battery health:

- **Gel batteries**: Typical cutoff ~10.5V (12V system), full ~13.8V
- **LiFePO4**: Typical cutoff ~10.0V (12V system), full ~14.4V
- **Lead-Acid**: Typical cutoff ~10.5V (12V system), full ~14.4V

Incorrect voltage settings can permanently damage batteries. Always verify values against your battery manufacturer's specifications.

## Entities

### Sensors
| Entity | Description |
|--------|-------------|
| Battery voltage | Current battery voltage (V) |
| Charging current | Solar charging current (A) |
| Discharge current | Load discharge current (A) |
| Temperature | Controller temperature (°C) |
| Total energy | Cumulative energy generated (kWh) |
| Battery SOC | State of charge (%) |
| Firmware version | Controller firmware |

### Selects
| Entity | Options |
|--------|---------|
| Battery type | Gel, LiFePO4, Lead-Acid, Custom |
| Output mode | Multiple output modes |
| Voltage monitor mode | Voltage monitoring modes |

### Numbers
| Entity | Range |
|--------|-------|
| Full voltage | Configurable |
| Cutoff voltage | Configurable |
| Restore discharge voltage | Configurable |

### Switches
| Entity | Description |
|--------|-------------|
| Load output | Toggle load output on/off |

## Troubleshooting

- **"Unknown" values**: Ensure the controller is powered on and within Bluetooth range
- **Integration not found**: Make sure Bluetooth is enabled in Home Assistant
- **Wrong entity types**: Delete the integration entry, restart HA, and re-add it

## License

MIT
