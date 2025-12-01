# Usage Guide

This guide provides comprehensive examples for using cpap-py to parse and analyze ResMed CPAP machine data.

## Table of Contents

- [Quick Start](#quick-start)
- [Reading CPAP Data](#reading-cpap-data)
- [Working with Sessions](#working-with-sessions)
- [Accessing Waveform Data](#accessing-waveform-data)
- [Device Settings](#device-settings)
- [Settings Proposals](#settings-proposals)
- [Advanced Usage](#advanced-usage)
- [API Reference](#api-reference)

## Quick Start

### Basic Data Loading

The simplest way to use the library:

```python
from cpap_py import CPAPReader

# Load data from SD card directory
reader = CPAPReader("/path/to/sdcard")

# Get all devices found on card
devices = reader.get_devices()
print(f"Found {len(devices)} device(s)")

# Get sessions for a specific device
sessions = reader.get_sessions(device_id=devices[0].serial_number)
print(f"Found {len(sessions)} session(s)")
```

### Quick Session Analysis

```python
from cpap_py import CPAPReader

reader = CPAPReader("/path/to/sdcard")
sessions = reader.get_sessions()

# Analyze recent session
recent = sessions[-1]
print(f"Session on {recent.date}")
print(f"Duration: {recent.summary.duration_hours:.2f} hours")
print(f"AHI: {recent.summary.ahi:.1f} events/hour")
print(f"Median Pressure: {recent.summary.pressure_median:.1f} cmH2O")
print(f"95th Percentile Leak: {recent.summary.leak_95th:.1f} L/min")
```

## Reading CPAP Data

### Initialize the Reader

```python
from cpap_py import CPAPReader
from cpap_py.utils import CRCValidationMode

# Standard mode (default)
reader = CPAPReader("/path/to/sdcard")

# Strict CRC validation
reader = CPAPReader(
    "/path/to/sdcard",
    crc_validation=CRCValidationMode.STRICT
)

# Disabled CRC validation (fastest)
reader = CPAPReader(
    "/path/to/sdcard",
    crc_validation=CRCValidationMode.DISABLED
)

# Eager loading (load all waveforms immediately)
reader = CPAPReader(
    "/path/to/sdcard",
    lazy_load=False
)
```

### Discover Devices

```python
# Get all devices
devices = reader.get_devices()

for device in devices:
    print(f"Serial Number: {device.serial_number}")
    print(f"Model: {device.model}")
    print(f"Mode: {device.mode}")
    print(f"Firmware: {device.firmware_version}")
```

### Filter Sessions

```python
from datetime import date, timedelta

# Get all sessions
all_sessions = reader.get_sessions()

# Get sessions for specific device
device_sessions = reader.get_sessions(
    device_id="1234567890"
)

# Get sessions in date range
recent = reader.get_sessions(
    start_date=date.today() - timedelta(days=7),
    end_date=date.today()
)

# Get sessions with minimum duration
long_sessions = reader.get_sessions(
    min_duration_hours=4.0
)

# Combine filters
filtered = reader.get_sessions(
    device_id="1234567890",
    start_date=date(2025, 11, 1),
    min_duration_hours=4.0
)
```

## Working with Sessions

### Session Properties

```python
session = sessions[0]

# Basic info
print(f"Date: {session.date}")
print(f"Start: {session.start_time}")
print(f"End: {session.end_time}")

# Duration
print(f"Hours: {session.summary.duration_hours:.2f}")

# Check data availability
if session.has_pressure_data:
    print("Pressure waveform available")
if session.has_flow_data:
    print("Flow waveform available")
if session.has_spo2_data:
    print("SpO2 data available")
```

### Session Summary Statistics

```python
summary = session.summary

# Respiratory events
print(f"AHI: {summary.ahi:.1f}")
print(f"Apnea Index: {summary.ai:.1f}")
print(f"Hypopnea Index: {summary.hi:.1f}")
print(f"Obstructive Apneas: {summary.obstructive_apneas}")
print(f"Central Apneas: {summary.central_apneas}")
print(f"Hypopneas: {summary.hypopneas}")

# Pressure statistics
print(f"Median Pressure: {summary.pressure_median:.1f} cmH2O")
print(f"95th Percentile: {summary.pressure_95th:.1f} cmH2O")

# Leak statistics
print(f"Median Leak: {summary.leak_median:.1f} L/min")
print(f"95th Percentile Leak: {summary.leak_95th:.1f} L/min")

# SpO2 (if available)
if summary.spo2_median:
    print(f"Median SpO2: {summary.spo2_median:.1f}%")
    print(f"Minimum SpO2: {summary.spo2_min:.1f}%")
```

### Respiratory Events

```python
# Get all events
events = session.get_events()
print(f"Total events: {len(events)}")

# Filter by event type
from cpap_py.utils.constants import EventType

obstructive = session.get_events(event_type=EventType.OBSTRUCTIVE_APNEA)
central = session.get_events(event_type=EventType.CENTRAL_APNEA)
hypopneas = session.get_events(event_type=EventType.HYPOPNEA)

# Event details
for event in events[:5]:  # First 5 events
    print(f"{event.type}: {event.start_time} - {event.duration:.1f}s")
```

## Accessing Waveform Data

### Pressure Data

```python
# Get pressure waveform (returns pandas DataFrame)
pressure_df = session.get_pressure_data()

print(f"Data points: {len(pressure_df)}")
print(f"Time range: {pressure_df['time'].min()} to {pressure_df['time'].max()}")
print(f"Pressure range: {pressure_df['pressure'].min():.1f} - {pressure_df['pressure'].max():.1f} cmH2O")

# Access values
times = pressure_df['time']
pressures = pressure_df['pressure']

# Calculate statistics
mean_pressure = pressure_df['pressure'].mean()
std_pressure = pressure_df['pressure'].std()
```

### Flow Data

```python
# Get flow waveform
flow_df = session.get_flow_data()

# Flow is in L/min
print(f"Flow range: {flow_df['flow'].min():.1f} - {flow_df['flow'].max():.1f} L/min")

# Identify inhalation vs exhalation
inhalation = flow_df[flow_df['flow'] > 0]
exhalation = flow_df[flow_df['flow'] < 0]
```

### SpO2 Data

```python
# Get SpO2 data (if available)
if session.has_spo2_data:
    spo2_df = session.get_spo2_data()
    
    print(f"SpO2 range: {spo2_df['spo2'].min():.1f}% - {spo2_df['spo2'].max():.1f}%")
    
    # Also includes pulse rate
    if 'pulse' in spo2_df.columns:
        print(f"Pulse range: {spo2_df['pulse'].min():.0f} - {spo2_df['pulse'].max():.0f} BPM")
    
    # Identify desaturations (SpO2 < 90%)
    desats = spo2_df[spo2_df['spo2'] < 90]
    print(f"Time with SpO2 < 90%: {len(desats)} data points")
```

### Flow Limitation and Snore

```python
# Flow limitation (0.0-1.0, higher = more limited)
fl_df = session.get_flow_limitation_data()
high_fl = fl_df[fl_df['flow_limitation'] > 0.5]
print(f"Time with high flow limitation: {len(high_fl)} data points")

# Snore detection (0.0-1.0, higher = more snoring)
snore_df = session.get_snore_data()
snoring = snore_df[snore_df['snore'] > 0.3]
print(f"Time with snoring: {len(snoring)} data points")
```

## Device Settings

### Reading Current Settings

```python
settings = session.settings

# Basic settings
print(f"Mode: {settings.mode}")
print(f"Min Pressure: {settings.min_pressure} cmH2O")
print(f"Max Pressure: {settings.max_pressure} cmH2O")

# Advanced settings (if available)
if settings.ramp_time:
    print(f"Ramp Time: {settings.ramp_time} minutes")
if settings.ramp_start_pressure:
    print(f"Ramp Start: {settings.ramp_start_pressure} cmH2O")

# Comfort settings
print(f"EPR: {settings.epr}")
print(f"EPR Type: {settings.epr_type}")
```

### Export Settings

```python
# Export to dictionary
settings_dict = settings.to_dict()

# Export to JSON
import json
json_str = json.dumps(settings_dict, indent=2)
print(json_str)
```

## Settings Proposals

### Create Pressure Adjustment Proposal

```python
from cpap_py.settings import create_pressure_adjustment_proposal

# Propose pressure increase for high AHI
proposal = create_pressure_adjustment_proposal(
    device_serial=device.serial_number,
    current_settings=session.settings,
    target_pressure=14.0,
    reason="Elevated AHI indicating inadequate pressure",
    ahi=12.5
)

# Review proposal
print(proposal.to_summary())
print(f"Safe to apply: {proposal.all_changes_safe}")

# Apply if safe
if proposal.all_changes_safe:
    new_settings = proposal.apply_to_settings(session.settings)
    print(f"New max pressure: {new_settings.max_pressure} cmH2O")
```

### Create Custom Proposal

```python
from cpap_py.settings import SettingsProposal, SettingsChange

# Create manual proposal
proposal = SettingsProposal(
    device_serial=device.serial_number,
    proposed_changes=[
        SettingsChange(
            parameter="min_pressure",
            current_value=6.0,
            proposed_value=8.0,
            reason="Increase minimum pressure to reduce central apneas",
            requires_clinical_approval=False,
            safety_validated=True
        ),
        SettingsChange(
            parameter="epr",
            current_value=3,
            proposed_value=2,
            reason="Reduce EPR to improve therapy effectiveness",
            requires_clinical_approval=False,
            safety_validated=True
        )
    ]
)

# Check proposal
if proposal.all_changes_safe:
    print("All changes are safe to apply")
else:
    print("Clinical approval required")
```

## Advanced Usage

### Batch Analysis

```python
from datetime import date, timedelta
import pandas as pd

# Analyze last 30 days
sessions = reader.get_sessions(
    start_date=date.today() - timedelta(days=30)
)

# Create summary DataFrame
data = []
for session in sessions:
    data.append({
        'date': session.date,
        'hours': session.summary.duration_hours,
        'ahi': session.summary.ahi,
        'pressure_median': session.summary.pressure_median,
        'pressure_95th': session.summary.pressure_95th,
        'leak_95th': session.summary.leak_95th,
        'obstructive': session.summary.obstructive_apneas,
        'central': session.summary.central_apneas,
        'hypopneas': session.summary.hypopneas,
    })

df = pd.DataFrame(data)

# Calculate trends
print(f"Average AHI: {df['ahi'].mean():.1f}")
print(f"Average hours: {df['hours'].mean():.1f}")
print(f"Days with good therapy (AHI < 5): {len(df[df['ahi'] < 5])}")
```

### Identify Problem Sessions

```python
# High AHI sessions
high_ahi = [s for s in sessions if s.summary.ahi > 10]
print(f"Sessions with AHI > 10: {len(high_ahi)}")

# High leak sessions
high_leak = [s for s in sessions if s.summary.leak_95th > 24]
print(f"Sessions with leak > 24 L/min: {len(high_leak)}")

# Short sessions
short = [s for s in sessions if s.summary.duration_hours < 4]
print(f"Sessions under 4 hours: {len(short)}")

# Central vs obstructive apneas
for session in sessions:
    total = session.summary.obstructive_apneas + session.summary.central_apneas
    if total > 0:
        central_pct = session.summary.central_apneas / total * 100
        if central_pct > 50:
            print(f"{session.date}: {central_pct:.0f}% central apneas")
```

### Export for External Analysis

```python
# Export all data
data = reader.export_to_dict()

# Save to JSON
import json
with open('cpap_data.json', 'w') as f:
    json.dump(data, f, indent=2, default=str)

# Export specific session with waveforms
session = sessions[0]
session_data = {
    'summary': session.summary.to_dict(),
    'events': [e.to_dict() for e in session.get_events()],
    'pressure': session.get_pressure_data().to_dict('records'),
    'flow': session.get_flow_data().to_dict('records'),
}

with open(f'session_{session.date}.json', 'w') as f:
    json.dump(session_data, f, indent=2, default=str)
```

### MCP Integration

```python
# All data is JSON-serializable for Model Context Protocol
import json

# Export reader data
mcp_data = reader.export_to_dict()
json_output = json.dumps(mcp_data, default=str)

# Individual models
session_dict = session.to_dict()
proposal_dict = proposal.to_dict()
settings_dict = settings.to_dict()

# Use in MCP server
def get_cpap_data(path: str):
    """MCP tool to read CPAP data."""
    reader = CPAPReader(path)
    return reader.export_to_dict()
```

## API Reference

See the main [README.md](README.md#api-reference) for complete API documentation.

### Key Classes

- **CPAPReader**: Main entry point for reading data
- **Device**: CPAP device information
- **Session**: Therapy session with data and events
- **SessionSummary**: Summary statistics for a session
- **DeviceSettings**: Device configuration
- **SettingsProposal**: Proposed settings changes
- **Event**: Respiratory event (apnea, hypopnea, etc.)
- **WaveformData**: Time-series signal data

### Common Workflows

1. **Load and explore**: `CPAPReader` → `get_devices()` → `get_sessions()`
2. **Analyze session**: `session.summary` → `session.get_events()`
3. **Get waveforms**: `get_pressure_data()`, `get_flow_data()`, `get_spo2_data()`
4. **Review settings**: `session.settings`
5. **Propose changes**: `create_pressure_adjustment_proposal()`

## Best Practices

1. **Use lazy loading**: Default behavior loads waveforms only when needed
2. **Filter sessions**: Use date ranges and filters to reduce memory usage
3. **Check data availability**: Use `has_pressure_data` etc. before requesting
4. **Handle missing data**: Not all sessions have all signal types
5. **Validate proposals**: Always check `all_changes_safe` before applying
6. **Export for analysis**: Use pandas DataFrames for statistical analysis
7. **CRC validation**: Use PERMISSIVE mode unless data integrity is critical

## Additional Resources

For more information:
- **Installation**: See [INSTALL.md](INSTALL.md)
- **Development**: See [DEVELOPMENT.md](DEVELOPMENT.md)
- **Contributing**: See [CONTRIBUTING.md](CONTRIBUTING.md)
- **API Reference**: See [README.md](README.md#api-reference)
- **Test Documentation**: See [tests/README.md](tests/README.md)
