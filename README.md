# cpap-py

A comprehensive Python library for parsing and analyzing ResMed CPAP (AirSense 10/11) machine data from SD card exports.

## Features

- 📊 Parse all ResMed EDF file types (BRP, PLD, SAD, EVE, CSL, STR)
- ⚙️ Read and parse device settings (TGT files)
- ✅ CRC verification with configurable validation modes
- 🔍 Session discovery and grouping by device
- 📈 Time-series data access (pressure, flow, SpO2, flow limitation, snore)
- 🏥 Clinical metrics and therapy statistics
- 🤖 MCP (Model Context Protocol) ready
- 🐍 Type-safe with Pydantic models
- 📦 Zero GUI dependencies - pure Python library

## Installation

```bash
pip install cpap-py
```

For development:
```bash
git clone <repository>
cd cpap-py
pip install -e ".[dev]"
```

## Quick Start

```python
from cpap_py import CPAPReader

# Load data from SD card directory
reader = CPAPReader("/path/to/sdcard")

# Get all devices found on card
devices = reader.get_devices()

# Get sessions for a specific device
sessions = reader.get_sessions(device_id=devices[0].serial_number)

# Access session details
for session in sessions:
    print(f"Session on {session.date}")
    print(f"Duration: {session.duration_hours:.2f} hours")
    print(f"AHI: {session.summary.ahi:.1f}")
    
    # Get waveform data
    pressure = session.get_pressure_data()  # Returns pandas DataFrame
    flow = session.get_flow_data()
    spo2 = session.get_spo2_data()
    
    # Get events
    events = session.get_events()  # Returns list of Event objects
```

## Architecture

```
cpap-py/
├── src/cpap_py/
│   ├── __init__.py
│   ├── reader.py           # Main CPAPReader API
│   ├── models.py           # Pydantic data models
│   ├── settings.py         # Settings models and proposals
│   ├── parsers/
│   │   ├── edf_parser.py   # EDF file parser
│   │   ├── str_parser.py   # Custom STR.edf parser
│   │   ├── tgt_parser.py   # Settings file parser
│   │   └── crc_parser.py   # CRC verification
│   └── utils/
│       ├── constants.py    # Channel IDs, event types
│       └── validation.py   # Data validation utilities
├── tests/                  # Comprehensive test suite
│   └── README.md           # Test documentation
├── docs/                   # Additional documentation
└── data/                   # Sample CPAP data
```

## File Types

ResMed SD cards contain several file types:

- **BRP**: Breathing/Respiratory/Pressure waveform data
- **PLD**: Detailed pressure measurements (high resolution)
- **SAD**: SpO2/oximetry data (blood oxygen saturation)
- **EVE**: Events (apneas, hypopneas, flow limitations)
- **CSL**: Clinical session summaries with Cheyne-Stokes events
- **STR.edf**: Summary statistics with mask on/off times
- **TGT**: Device settings (plain text key-value format)
- **CRC**: Checksums for data integrity verification

## API Reference

### CPAPReader

Main entry point for reading SD card data.

```python
CPAPReader(
    sdcard_path: str,
    crc_validation: CRCValidationMode = CRCValidationMode.PERMISSIVE,
    lazy_load: bool = True
)
```

**Key Methods:**
- `get_devices() -> List[Device]` - Get all devices found on card
- `get_sessions(...) -> List[Session]` - Get therapy sessions with optional filters
- `get_summary_statistics(days=30) -> Dict` - Get aggregate statistics
- `export_to_dict() -> Dict` - Export all data as JSON-serializable dict

### Session

Represents a therapy session.

**Properties:**
- `date: date` - Session date
- `start_time: datetime` - Session start time
- `end_time: datetime` - Session end time
- `summary: SessionSummary` - Summary statistics (AHI, pressure, leak, SpO2)
- `settings: DeviceSettings` - Device configuration
- `has_pressure_data: bool` - Pressure waveform available
- `has_flow_data: bool` - Flow waveform available
- `has_spo2_data: bool` - SpO2 data available

**Methods:**
- `get_events(event_type=None) -> List[Event]` - Get respiratory events
- `get_pressure_data() -> pd.DataFrame` - Get pressure waveform
- `get_flow_data() -> pd.DataFrame` - Get flow waveform
- `get_spo2_data() -> pd.DataFrame` - Get SpO2 waveform
- `get_flow_limitation_data() -> pd.DataFrame` - Get flow limitation signal
- `get_snore_data() -> pd.DataFrame` - Get snore detection signal

### SessionSummary

Summary statistics for a therapy session.

**Key Properties:**
- `duration_hours: float` - Session duration
- `ahi: float` - Apnea-Hypopnea Index
- `ai: float` - Apnea Index
- `hi: float` - Hypopnea Index
- `obstructive_apneas: int` - Count of obstructive apneas
- `central_apneas: int` - Count of central apneas
- `hypopneas: int` - Count of hypopneas
- `pressure_median: float` - Median pressure (cmH2O)
- `pressure_95th: float` - 95th percentile pressure
- `leak_median: float` - Median leak rate (L/min)
- `leak_95th: float` - 95th percentile leak
- `spo2_median: float` - Median SpO2 (%)
- `spo2_min: float` - Minimum SpO2

### Settings Proposals

Enables AI to propose changes without writing files:

```python
from cpap_py.settings import create_pressure_adjustment_proposal

proposal = create_pressure_adjustment_proposal(
    device_serial="ABC123",
    current_settings=session.settings,
    target_pressure=14.0,
    reason="Elevated AHI",
    ahi=8.5
)

print(proposal.to_summary())
if proposal.all_changes_safe:
    new_settings = proposal.apply_to_settings(session.settings)
```

## Common Workflows

### Analyze Last 7 Days
```python
from datetime import date, timedelta

recent = reader.get_sessions(
    start_date=date.today() - timedelta(days=7)
)

total_ahi = sum(s.summary.ahi for s in recent if s.summary.ahi)
avg_ahi = total_ahi / len(recent)
```

### Find Problem Sessions
```python
high_ahi = [s for s in sessions if s.summary.ahi > 10]
high_leak = [s for s in sessions if s.summary.leak_95th > 24]
```

### Export for Analysis
```python
import pandas as pd

data = []
for s in sessions:
    data.append({
        'date': s.date,
        'ahi': s.summary.ahi,
        'hours': s.summary.duration_hours,
        'leak': s.summary.leak_95th,
    })

df = pd.DataFrame(data)
df.to_csv('therapy_summary.csv')
```

## Signal Extraction

The library extracts all critical clinical signals:

### Core Signals
- **Mask Pressure** (40ms or 2s resolution)
- **Flow Rate** (40ms or 2s resolution)
- **Leak Rate**
- **Respiratory Rate**
- **Tidal Volume**

### Advanced Signals
- **Flow Limitation** (0.0-1.0 index, 0.5 Hz) - Indicates upper airway restriction
- **Snore Detection** (0.0-1.0 index, 0.5 Hz) - Vibratory snore indication
- **EPAP** (BiLevel machines) - Expiratory pressure
- **Target Ventilation** (ASV/iVAPS) - Target minute ventilation

### Oximetry (if available)
- **SpO2** - Blood oxygen saturation (%)
- **Pulse Rate** - Heart rate (BPM)

### Event Types
- `OA` - Obstructive Apnea
- `CA` - Central Apnea
- `H` - Hypopnea
- `FL` - Flow Limitation
- `RE` - RERA
- `VS` - Vibratory Snore
- `LL` - Large Leak
- `CSR` - Cheyne-Stokes Respiration

## STR.edf Parser

The library includes a custom parser for ResMed's non-standard STR.edf files:

- Handles empty/invalid physical dimension fields
- Extracts device serial number
- Reads all 81 signal channels
- Parses mask on/off times (session boundaries)
- Captures daily summary statistics
- Matches DATALOG sessions to STR session times
- Populates SessionSummary with accurate statistics
- Supports multi-session days

## MCP Integration

All data structures are JSON-serializable for Model Context Protocol:

```python
# Export data for MCP server
data = reader.export_to_dict()

# All Pydantic models have to_dict() methods
session_dict = session.to_dict()
proposal_dict = proposal.to_dict()

import json
json_output = json.dumps(data, default=str)
```

See USAGE.md for more detailed examples and integration patterns.

## Performance Considerations

- **Lazy Loading**: Waveform data is only loaded when requested
- **Filtering**: Use filters in `get_sessions()` to reduce memory usage
- **CRC Validation**: Disable if performance is critical and data integrity is assured

## Safety Features

1. **Validation**: Settings proposals checked against clinical limits
2. **Approval Flags**: Major changes flagged for clinical review
3. **Read-Only**: Never writes to SD card
4. **Error Tracking**: All parsing errors collected and reported
5. **CRC Verification**: Optional data integrity checking

## Dependencies

### Core
- `pyedflib>=0.1.30` - EDF file parsing
- `numpy>=1.20.0` - Array operations
- `pandas>=1.3.0` - DataFrame support
- `pydantic>=2.0.0` - Data validation & serialization
- `python-dateutil>=2.8.0` - Date handling

### Development
- `pytest>=7.0.0` - Testing
- `black>=23.0.0` - Code formatting
- `ruff>=0.1.0` - Linting
- `mypy>=1.0.0` - Type checking

## Changelog

### [Unreleased] - 2025-12-01

**Added:**
- STR session matching algorithm connecting DATALOG files with STR.edf boundaries
- Summary statistics integration with real STR.edf data
- Multi-session day support with proper session indexing
- Flow limitation and snore signal extraction
- High-resolution signal prioritization
- Cheyne-Stokes Respiration (CSR) event extraction
- EPAP and target ventilation signal support

**Enhanced:**
- Comprehensive signal name standardization (40+ mappings)
- Unit conversion (L/s → L/min for flow and leak)
- CSL file parsing for clinical events

### [0.1.0] - 2025-11-27 (Initial Implementation)

**Added:**
- Complete Python library for parsing ResMed CPAP data
- EDF file parsers (BRP, PLD, SAD, EVE, CSL)
- Custom STR.edf parser handling non-compliant format
- TGT settings file parser
- CRC validation with configurable modes
- Pydantic data models for type safety
- Settings proposal system with safety validation
- MCP-ready JSON serialization

## License

MIT License - see LICENSE file for details

## Contributing

Contributions welcome! Please ensure:
- Code follows black formatting
- Type hints are included
- Tests pass
- Documentation is updated

## Acknowledgments

Based on research from:
- [OSCAR project](https://www.sleepfiles.com/OSCAR/) - Open-source CPAP analysis
- ResMed file format documentation
- EDF+ standard specifications

## Support

For issues, questions, or contributions, please use the GitHub issue tracker.
