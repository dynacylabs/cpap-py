# Usage Guide

This guide provides comprehensive examples for using cpap-py to parse and analyze ResMed CPAP machine data.

## Table of Contents

- [Quick Start](#quick-start)
- [Reading CPAP Data](#reading-cpap-data)
- [Working with Summary Data](#working-with-summary-data)
- [Working with Session Data](#working-with-session-data)
- [Device Settings](#device-settings)
- [Advanced Usage](#advanced-usage)
- [API Reference](#api-reference)

## Quick Start

### Basic Data Loading

The simplest way to use the library:

```python
from cpap_py import CPAPLoader

# Load all data from CPAP data directory
loader = CPAPLoader("/path/to/cpap/data")
data = loader.load_all()

# Access device information
print(f"Device: {data.machine_info.model}")
print(f"Serial: {data.machine_info.serial}")

# Get summary statistics
print(f"Found {len(data.summary_records)} days of data")
print(f"Found {len(data.sessions)} sessions")
```

### Quick Session Analysis

```python
from cpap_py import CPAPLoader

loader = CPAPLoader("/path/to/cpap/data")
data = loader.load_all()

# Analyze recent session
if data.summary_records:
    recent = data.summary_records[-1]
    print(f"Session on {recent.date}")
    print(f"Duration: {recent.mask_duration/3600:.2f} hours")
    print(f"AHI: {recent.ahi:.1f} events/hour")
    print(f"Median Pressure: {recent.mp_50:.1f} cmH2O")
    print(f"95th Percentile Leak: {recent.leak_95:.1f} L/min")
```

## Reading CPAP Data

### Initialize the Loader

```python
from cpap_py import CPAPLoader

# Standard loading
loader = CPAPLoader("/path/to/cpap/data")

# Load all data
data = loader.load_all()
```

### Load Specific Data Types

```python
# Load only device identification
machine_info = loader.load_identification_only()
print(f"Model: {machine_info.model}")
print(f"Serial: {machine_info.serial}")

# Load only summary data
summary_records = loader.load_summary_only()
for record in summary_records:
    print(f"{record.date}: AHI={record.ahi:.1f}")

# Load sessions for a specific date
from datetime import date
sessions = loader.load_sessions_for_date(date(2025, 12, 15))

# Get date range of available data
date_range = loader.get_date_range()
if date_range:
    start, end = date_range
    print(f"Data available from {start} to {end}")
```

## Working with Summary Data

### Parse STR.edf Files

```python
from cpap_py import STRParser
from datetime import date

# Parse summary file
parser = STRParser("/path/to/STR.edf")
if parser.parse():
    print(f"Loaded {len(parser.records)} daily records")
    
    # Access individual records
    for record in parser.records:
        if record.date:
            print(f"\nDate: {record.date}")
            print(f"  Usage: {record.mask_duration/3600:.1f} hours")
            print(f"  AHI: {record.ahi:.1f}")
            print(f"  Median Leak: {record.leak_50:.1f} L/min")
            print(f"  Median Pressure: {record.mp_50:.1f} cmH2O")
            print(f"  Therapy Mode: {record.mode}")

# Filter by date range
start_date = date(2025, 12, 1)
end_date = date(2025, 12, 15)
filtered = parser.get_records_by_date_range(start_date, end_date)
print(f"Found {len(filtered)} records in date range}")
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

## Working with Session Data

### Parse DATALOG Files

```python
from cpap_py import DatalogParser

# Initialize parser
parser = DatalogParser("/path/to/DATALOG")

# Scan for available session files
files_by_date = parser.scan_files()
print(f"Found data for {len(files_by_date)} days")

# Parse all sessions
sessions = parser.parse_all_sessions()
print(f"Loaded {len(sessions)} total sessions")

# Parse specific session file
from pathlib import Path
session_file = Path("/path/to/DATALOG/20251215/BRP00001.edf")
session = parser.parse_session_file(session_file)
```

### Access Waveform Data

```python
# Access detailed waveform data
session = sessions[0]

print(f"Session: {session.start_time}")
print(f"Duration: {session.duration/3600:.2f} hours")
print(f"Sample rate: {session.sample_rate} Hz")

# Flow rate (L/min)
if session.flow_rate:
    print(f"Flow rate samples: {len(session.flow_rate)}")
    print(f"  Min: {min(session.flow_rate):.1f}")
    print(f"  Max: {max(session.flow_rate):.1f}")

# Pressure (cmH2O)
if session.pressure:
    print(f"Pressure samples: {len(session.pressure)}")
    
# Leak (L/min)
if session.leak:
    print(f"Leak samples: {len(session.leak)}")

# Respiratory metrics
if session.tidal_volume:
    print(f"Tidal volume samples: {len(session.tidal_volume)}")
if session.minute_vent:
    print(f"Minute ventilation samples: {len(session.minute_vent)}")
if session.resp_rate:
    print(f"Respiratory rate samples: {len(session.resp_rate)}")
```

### Access Events

```python
# Parse events from session
for event in session.events:
    print(f"Event: {event.event_type}")
    print(f"  Time: {event.timestamp:.1f}s")
    print(f"  Duration: {event.duration:.1f}s")
```

### Filter Sessions by Date

```python
from datetime import date

# Get sessions for specific date
target_date = date(2025, 12, 15)
day_sessions = parser.get_sessions_by_date(target_date)

# Get sessions in date range
start = date(2025, 12, 1)
end = date(2025, 12, 15)
range_sessions = parser.get_sessions_by_date_range(start, end)
```

## Device Settings

### Parse Settings Files

```python
from cpap_py import SettingsParser

# Initialize parser
parser = SettingsParser("/path/to/SETTINGS")

# Parse all settings files
changes = parser.parse_all()
print(f"Found {len(changes)} setting changes")

# View changes
for change in changes:
    print(f"{change.timestamp}: {change.setting}")
    print(f"  Value: {change.value}")
## Device Settings

### Parse Settings Files

```python
from cpap_py import SettingsParser

# Initialize parser
parser = SettingsParser("/path/to/SETTINGS")

# Parse all settings files
changes = parser.parse_all()
print(f"Found {len(changes)} setting changes")

# View changes
for change in changes:
    print(f"{change.timestamp}: {change.setting_name}")
    print(f"  Category: {change.category}")
    print(f"  Old: {change.old_value}")
    print(f"  New: {change.new_value}")
```

### Filter Settings Changes

```python
from datetime import datetime

# Get changes for specific setting
pressure_changes = parser.get_changes_by_setting("MaxPressure")

# Get changes in date range
start = datetime(2025, 12, 1)
end = datetime(2025, 12, 15)
recent_changes = parser.get_changes_by_date_range(start, end)
```

## Advanced Usage

### Low-Level EDF Parsing

```python
from cpap_py import EDFParser

# Parse any EDF file
edf = EDFParser("/path/to/file.edf")
if edf.parse():
    # Access header
    print(f"Patient ID: {edf.header.patient_ident}")
    print(f"Start time: {edf.header.start_date}")
    print(f"Duration: {edf.header.duration_seconds}s")
    print(f"Number of signals: {edf.header.num_signals}")
    
    # Access signals
    for signal in edf.signals:
        print(f"\nSignal: {signal.label}")
        print(f"  Dimension: {signal.physical_dimension}")
        print(f"  Samples: {len(signal.data)}")
        print(f"  Range: {signal.physical_minimum} - {signal.physical_maximum}")
        
        # Get physical values
        values = edf.get_physical_values(signal)
        print(f"  Mean value: {sum(values)/len(values):.2f}")
```

### Device Identification

```python
from cpap_py import IdentificationParser

# Parse identification file
parser = IdentificationParser("/path/to/data")
info = parser.parse()

if info:
    print(f"Serial: {info.serial}")
    print(f"Model: {info.model}")
    print(f"Model Number: {info.model_number}")
    print(f"Series: {info.series}")
    print(f"Loader: {info.loader_name}")
    
    # Access all properties
    for key, value in info.properties.items():
        print(f"  {key}: {value}")
```

### Utility Functions

```python
from cpap_py import utils

# Split timestamps by noon (ResMed convention)
timestamps = [...]  # Unix timestamps
sessions = utils.split_sessions_by_noon(timestamps)
for session_date, session_stamps in sessions:
    print(f"{session_date}: {len(session_stamps)} timestamps")

# Format duration
seconds = 25200  # 7 hours
formatted = utils.format_duration(seconds)  # "07:00:00"

# Calculate AHI
ahi = utils.calculate_ahi(apneas=10, hypopneas=15, hours=7.0)
print(f"AHI: {ahi:.1f}")

# Get therapy mode name
from cpap_py.str_parser import STRParser
mode_name = utils.therapy_mode_name(STRParser.MODE_APAP)
print(f"Mode: {mode_name}")  # "APAP"

# Downsample signal
data = [1, 2, 3, 4, 5, 6, 7, 8]
downsampled = utils.downsample_signal(data, factor=2)  # [1.5, 3.5, 5.5, 7.5]

# Calculate percentile
values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
median = utils.calculate_percentile(values, 50)  # 5.5
p95 = utils.calculate_percentile(values, 95)  # 9.5
```

## API Reference

See the main [README](README.md) for complete API documentation, including:

- CPAPLoader methods
- IdentificationParser
- STRParser and STRRecord fields
- DatalogParser and SessionData fields  
- SettingsParser and SettingChange fields
- EDFParser for low-level EDF access
- Utility functions

## Examples

For more examples, check the project repository or create an issue if you need help with a specific use case.
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
## Working with Summary Data

### Parse STR.edf Files

```python
from cpap_py import STRParser
from datetime import date

# Parse summary file
parser = STRParser("/path/to/STR.edf")
if parser.parse():
    print(f"Loaded {len(parser.records)} daily records")
    
    # Access individual records
    for record in parser.records:
        if record.date:
            print(f"\nDate: {record.date}")
            print(f"  Usage: {record.mask_duration/3600:.1f} hours")
            print(f"  AHI: {record.ahi:.1f}")
            print(f"  Median Leak: {record.leak_50:.1f} L/min")
            print(f"  Median Pressure: {record.mp_50:.1f} cmH2O")
            print(f"  Therapy Mode: {record.mode}")

# Filter by date range
start_date = date(2025, 12, 1)
end_date = date(2025, 12, 15)
filtered = parser.get_records_by_date_range(start_date, end_date)
print(f"Found {len(filtered)} records in date range")
```

### Access Detailed Statistics

```python
# Each STRRecord contains comprehensive statistics
record = parser.records[0]

# Event indices
print(f"AHI: {record.ahi}")
print(f"AI (Apnea Index): {record.ai}")
print(f"HI (Hypopnea Index): {record.hi}")
print(f"CAI (Central Apnea): {record.cai}")
print(f"OAI (Obstructive Apnea): {record.oai}")

# Leak statistics (L/min)
print(f"Leak 50th percentile: {record.leak_50}")
print(f"Leak 95th percentile: {record.leak_95}")
print(f"Leak maximum: {record.leak_max}")

# Pressure statistics (cmH2O)
print(f"Pressure 50th percentile: {record.mp_50}")
print(f"Pressure 95th percentile: {record.mp_95}")

# Respiratory rate (breaths/min)
print(f"RR 50th percentile: {record.rr_50}")

# Device settings
print(f"Min Pressure: {record.min_pressure}")
print(f"Max Pressure: {record.max_pressure}")
print(f"EPR: {record.epr}")
```

## Working with Session Data

### Parse DATALOG Files

```python
from cpap_py import DatalogParser

# Initialize parser
parser = DatalogParser("/path/to/DATALOG")

# Scan for available session files
files_by_date = parser.scan_files()
print(f"Found data for {len(files_by_date)} days")

# Parse all sessions
sessions = parser.parse_all_sessions()
print(f"Loaded {len(sessions)} total sessions")

# Parse specific session file
from pathlib import Path
session_file = Path("/path/to/DATALOG/20251215/BRP00001.edf")
session = parser.parse_session_file(session_file)
```

### Access Waveform Data

```python
# Access detailed waveform data
session = sessions[0]

print(f"Session: {session.start_time}")
print(f"Duration: {session.duration/3600:.2f} hours")
print(f"Sample rate: {session.sample_rate} Hz")

# Flow rate (L/min)
if session.flow_rate:
    print(f"Flow rate samples: {len(session.flow_rate)}")
    print(f"  Min: {min(session.flow_rate):.1f}")
    print(f"  Max: {max(session.flow_rate):.1f}")

# Pressure (cmH2O)
if session.pressure:
    print(f"Pressure samples: {len(session.pressure)}")
    
# Leak (L/min)
if session.leak:
    print(f"Leak samples: {len(session.leak)}")

# Respiratory metrics
if session.tidal_volume:
    print(f"Tidal volume samples: {len(session.tidal_volume)}")
if session.minute_vent:
    print(f"Minute ventilation samples: {len(session.minute_vent)}")
if session.resp_rate:
    print(f"Respiratory rate samples: {len(session.resp_rate)}")
```

### Access Events

```python
# Parse events from session
for event in session.events:
    print(f"Event: {event.event_type}")
    print(f"  Time: {event.timestamp:.1f}s")
    print(f"  Duration: {event.duration:.1f}s")
```

### Filter Sessions by Date

```python
from datetime import date

# Get sessions for specific date
target_date = date(2025, 12, 15)
day_sessions = parser.get_sessions_by_date(target_date)

# Get sessions in date range
start = date(2025, 12, 1)
end = date(2025, 12, 15)
range_sessions = parser.get_sessions_by_date_range(start, end)
```
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

See the main [README.md](README.md#api-reference) for complete API documentation, including:

- CPAPLoader methods
- IdentificationParser
- STRParser and STRRecord fields
- DatalogParser and SessionData fields  
- SettingsParser and SettingChange fields
- EDFParser for low-level EDF access
- Utility functions

## Best Practices

1. **Use CPAPLoader for simplicity**: The high-level interface handles all the complexity
2. **Check for None**: Not all fields are present in all files
3. **Handle missing data**: Some signals may not be present in all sessions
4. **Respect data privacy**: CPAP data contains health information
5. **Validate data**: Always check return values before using data

## Additional Resources

For more information:
- **Installation**: See [INSTALL.md](INSTALL.md)
- **Development**: See [DEVELOPMENT.md](DEVELOPMENT.md)
- **Contributing**: See [CONTRIBUTING.md](CONTRIBUTING.md)
- **API Reference**: See [README.md](README.md#api-reference)
- **Test Documentation**: See [TEST_SUITE.md](TEST_SUITE.md)

