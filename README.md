# cpap-py

A lightweight Python library for parsing ResMed CPAP (Continuous Positive Airway Pressure) device data files. This library provides complete access to all data stored on CPAP devices including device identification, summary statistics, detailed waveform data, and configuration changes.

## Features

- **Zero Dependencies**: Pure Python implementation using only the standard library
- **Complete Data Extraction**: Parses all available CPAP data including pressure settings, delivered pressures, leak rates, respiratory metrics, and event indices
- **Device Identification**: Parse both `.tgt` (text) and `.json` format identification files
- **Summary Data**: Extract daily statistics from `STR.edf` files including AHI, leak, pressure, respiratory rate
- **Session Data**: Parse detailed waveform data from `DATALOG` EDF files (BRP, PLD, SAD, EVE, CSL, AEV)
- **Settings & Configuration**: Extract device settings including pressure ranges (min/max), comfort settings, humidification
- **Pure Python EDF Parser**: Full implementation of European Data Format (EDF/EDF+) parser
- **Multiple Device Support**: Works with ResMed S9, AirSense 10, AirSense 11, and AirCurve series
- **BiLevel Support**: Full support for BiLevel therapy modes (S, ST, T, PAC, ASV)
- **Comprehensive Testing**: 97% code coverage with 188 automated tests
- **Python 3.9+**: Supports Python 3.9, 3.10, 3.11, and 3.12

## Installation

```bash
pip install cpap-py
```

For development installation with test dependencies:

```bash
git clone https://github.com/dynacylabs/cpap-py.git
cd cpap-py
pip install -e ".[dev]"
```

See [INSTALL.md](INSTALL.md) for detailed installation instructions.

## Quick Start

### Load All CPAP Data

```python
from cpap_py import CPAPLoader

# Load all data from a CPAP data directory
loader = CPAPLoader("path/to/cpap/data")
data = loader.load_all()

# Access device information
print(f"Device: {data.machine_info.model}")
print(f"Serial: {data.machine_info.serial}")
print(f"Model Series: {data.machine_info.series}")

# Access daily summary records
for record in data.summary_records:
    print(f"Date: {record.date}")
    print(f"  AHI: {record.ahi:.1f} events/hour")
    print(f"  Duration: {record.mask_duration/3600:.1f} hours")
    print(f"  Leak (median): {record.leak_50:.1f} L/min")
    print(f"  Pressure (95th): {record.mp_95:.1f} cmH2O")

# Access detailed session data
for session in data.sessions:
    print(f"Session: {session.start_time}")
    print(f"  Duration: {session.duration/3600:.1f} hours")
    print(f"  Flow rate samples: {len(session.flow_rate)}")
    print(f"  Pressure samples: {len(session.pressure)}")
    print(f"  Events recorded: {len(session.events)}")
    print(f"  File type: {session.file_type}")
```

## Usage Examples

### Parse Device Identification

```python
from cpap_py import IdentificationParser

parser = IdentificationParser("path/to/data")
info = parser.parse()

if info:
    print(f"Model: {info.model}")
    print(f"Serial: {info.serial}")
    print(f"Series: {info.series}")
    print(f"Model Number: {info.model_number}")
```

### Parse Summary Data (STR.edf)

```python
from cpap_py import STRParser

parser = STRParser("path/to/STR.edf")
if parser.parse():
    for record in parser.records:
        if record.date:
            print(f"{record.date}: AHI={record.ahi:.1f}, Hours={record.mask_duration/3600:.1f}")
            print(f"  Leak (median/95th): {record.leak_50:.1f}/{record.leak_95:.1f} L/min")
            print(f"  Pressure (median/95th): {record.mp_50:.1f}/{record.mp_95:.1f} cmH2O")
            
    # Filter by date range
    from datetime import date
    filtered = parser.get_records_by_date_range(
        date(2025, 12, 1),
        date(2025, 12, 15)
    )
```

### Parse Session Data (DATALOG)

```python
from cpap_py import DatalogParser

parser = DatalogParser("path/to/DATALOG")

# Parse all sessions
sessions = parser.parse_all_sessions()

for session in sessions:
    print(f"{session.date} - {session.file_type}")
    print(f"  Start: {session.start_time}")
    print(f"  Duration: {session.duration/3600:.2f} hours")
    print(f"  Sample rate: {session.sample_rate} Hz")
    
    # Access waveform data
    if session.flow_rate:
        print(f"  Flow rate: {len(session.flow_rate)} samples")
    if session.pressure:
        print(f"  Pressure: {len(session.pressure)} samples")
    if session.spo2:
        print(f"  SpO2: {len(session.spo2)} samples")
        
    # Access events
    for event in session.events:
        print(f"  Event: {event.event_type} at {event.timestamp}s")

# Get sessions for specific date
from datetime import date
date_sessions = parser.get_sessions_by_date(date(2025, 12, 15))
```

### Parse Settings Files

```python
from cpap_py import SettingsParser

parser = SettingsParser("path/to/SETTINGS")
changes = parser.parse_all()

for change in changes:
    print(f"{change.timestamp}: {change.setting} = {change.value}")
```

### Parse Individual EDF Files

```python
from cpap_py import EDFParser

edf = EDFParser("path/to/file.edf")
if edf.parse():
    # Access header information
    print(f"Recording date: {edf.header.start_date}")
    print(f"Duration: {edf.header.duration} seconds")
    print(f"Signals: {len(edf.signals)}")
    
    # Access signals
    for signal in edf.signals:
        print(f"  {signal.label}: {len(signal.data)} samples")
        print(f"    Unit: {signal.physical_dimension}")
        print(f"    Range: {signal.physical_min} to {signal.physical_max}")
        
    # Find specific signal
    flow_signal = edf.get_signal("Flow")
    if flow_signal:
        # Get physical (scaled) values
        physical_values = edf.get_physical_values(flow_signal)
        print(f"Flow range: {min(physical_values):.1f} to {max(physical_values):.1f} L/min")
```

## Data Directory Structure

The library expects data in the ResMed CPAP format:

```
data_directory/
├── Identification.tgt     # or Identification.json
├── STR.edf               # Daily summary data
├── DATALOG/
│   ├── 20251126/        # Date folders (YYYYMMDD)
│   │   ├── BRP00001.edf # Breathing data
│   │   ├── PLD00001.edf # Pressure/leak data
│   │   └── EVE00001.edf # Events
│   └── 20251127/
└── SETTINGS/
    ├── CGL.tgt          # Clinical settings
    └── UGL.tgt          # User settings
```

## File Types

### Identification Files
- `.tgt`: Text format with `#KEY value` pairs
- `.json`: JSON format (AirSense 11)

### EDF Files
- `STR.edf`: Daily summary statistics
- `BRP.edf`: Breathing waveforms (flow, tidal volume, etc.)
- `PLD.edf`: Pressure and leak data
- `SAD.edf`: Summary/advanced data
- `EVE.edf`: Event markers (apneas, hypopneas)
- `CSL.edf`: Clinical settings log
- `AEV.edf`: Advanced events

## API Reference

### CPAPLoader

High-level interface for loading all CPAP data.

```python
loader = CPAPLoader(data_path: str)
```

**Methods:**
- `load_all()` → `CPAPData`: Load all data (identification, summary, sessions, settings)
- `load_identification_only()` → `MachineInfo | None`: Load only device identification
- `load_summary_only()` → `List[STRRecord]`: Load only STR.edf summary data
- `load_sessions_for_date(date)` → `List[SessionData]`: Load sessions for specific date
- `get_date_range()` → `tuple[date, date] | None`: Get (start_date, end_date) of available data

### IdentificationParser

Parse device identification files (.tgt or .json).

```python
parser = IdentificationParser(data_path: str)
```

**Methods:**
- `parse()` → `MachineInfo | None`: Parse identification file and return device info

**Supported Files:**
- `Identification.tgt` - Text format with `#KEY value` pairs
- `Identification.json` - JSON format (AirSense 11)

### STRParser

Parse STR.edf daily summary files.

```python
parser = STRParser(filepath: str, serial_number: str = None)
```

**Methods:**
- `parse()` → `bool`: Parse file and populate records list
- `get_records_by_date_range(start: date, end: date)` → `List[STRRecord]`: Filter records by date

**Mode Constants:**
- `MODE_UNKNOWN = 0`
- `MODE_CPAP = 1`
- `MODE_APAP = 2`
- `MODE_BILEVEL_FIXED = 3`
- `MODE_BILEVEL_AUTO = 4`
- `MODE_BILEVEL_S = 5`
- `MODE_BILEVEL_ST = 6`
- `MODE_BILEVEL_T = 7`
- `MODE_BILEVEL_PAC = 8`
- `MODE_ASV = 9`

### DatalogParser

Parse DATALOG session files (BRP, PLD, SAD, EVE, CSL, AEV).

```python
parser = DatalogParser(datalog_path: str)
```

**Methods:**
- `scan_files()` → `Dict[date, List[Path]]`: Scan directory and return files by date
- `parse_session_file(filepath: str)` → `SessionData | None`: Parse single session file
- `parse_all_sessions()` → `List[SessionData]`: Parse all session files in directory
- `get_sessions_by_date(target_date: date)` → `List[SessionData]`: Get sessions for specific date
- `get_sessions_by_date_range(start: date, end: date)` → `List[SessionData]`: Get sessions in range

**File Types:**
- `BRP` - Breathing waveforms (flow, tidal volume, minute ventilation, respiratory rate)
- `PLD` - Pressure and leak data
- `SAD` - Summary/advanced data
- `EVE` - Event markers (apneas, hypopneas, flow limitations)
- `CSL` - Clinical settings log
- `AEV` - Advanced events

### SettingsParser

Parse SETTINGS files (.tgt format).

```python
parser = SettingsParser(settings_path: str)
```

**Methods:**
- `parse_all()` → `List[SettingChange]`: Parse all settings files
- `parse_file(filepath: str)` → `List[SettingChange]`: Parse single settings file

### EDFParser

Low-level European Data Format (EDF/EDF+) parser.

```python
parser = EDFParser(filepath: str)
```

**Methods:**
- `open()` → `bool`: Open EDF file
- `close()`: Close file
- `parse()` → `bool`: Parse entire file (header + signals + data)
- `parse_header()` → `bool`: Parse only file header
- `parse_signal_headers()` → `bool`: Parse signal definitions
- `parse_data()` → `bool`: Parse signal data
- `get_signal(label: str, index: int = 0)` → `EDFSignal | None`: Find signal by label
- `get_physical_values(signal: EDFSignal)` → `List[float]`: Convert digital to physical values

## Data Classes

### CPAPData

Complete CPAP data container.

**Fields:**
- `machine_info: MachineInfo | None` - Device information
- `summary_records: List[STRRecord]` - Daily summary statistics
- `sessions: List[SessionData]` - Detailed session waveform data
- `settings_changes: List[SettingChange]` - Configuration changes

### MachineInfo

Device identification information.

**Fields:**
- `serial: str` - Device serial number
- `model: str` - Model name (e.g., \"AirSense 10 AutoSet\")
- `model_number: str` - Model number
- `series: str` - Device series (e.g., \"AirSense 11\", \"AirSense 10\", \"S9\")
- `properties: Dict[str, str]` - Additional device properties

### STRRecord

Daily summary record from STR.edf.

**Key Fields:**
- `date: date` - Record date
- `ahi: float` - Apnea-Hypopnea Index (events/hour)
- `ai: float` - Apnea Index
- `hi: float` - Hypopnea Index
- `cai: float` - Central Apnea Index
- `oai: float` - Obstructive Apnea Index
- `mask_duration: float` - Therapy duration (seconds)
- `mask_on: List[int]` - Mask-on timestamps
- `mask_off: List[int]` - Mask-off timestamps
- `leak_50: float` - Median leak (L/min)
- `leak_95: float` - 95th percentile leak (L/min)
- `mp_50: float` - Median mask pressure (cmH2O)
- `mp_95: float` - 95th percentile mask pressure (cmH2O)
- `mode: int` - Therapy mode
- `min_pressure: float` - Minimum pressure setting
- `max_pressure: float` - Maximum pressure setting
- `ipap: float` - IPAP setting (BiLevel)
- `epap: float` - EPAP setting (BiLevel)
- `epr: int` - EPR setting
- And 70+ more statistics fields...

### SessionData

Detailed session data from DATALOG files.

**Fields:**
- `date: date` - Session date
- `start_time: datetime` - Session start timestamp
- `duration: float` - Session duration (seconds)
- `file_type: str` - File type (BRP, PLD, SAD, EVE, etc.)
- `sample_rate: float` - Sample rate (Hz)
- `flow_rate: List[float]` - Flow rate waveform (L/min)
- `pressure: List[float]` - Pressure waveform (cmH2O)
- `mask_pressure: List[float]` - Mask pressure (cmH2O)
- `leak: List[float]` - Leak rate (L/min)
- `tidal_volume: List[float]` - Tidal volume (mL)
- `minute_vent: List[float]` - Minute ventilation (L/min)
- `resp_rate: List[float]` - Respiratory rate (breaths/min)
- `target_ipap: List[float]` - Target IPAP (cmH2O)
- `target_epap: List[float]` - Target EPAP (cmH2O)
- `spo2: List[float]` - SpO2 (%)
- `pulse: List[float]` - Pulse rate (bpm)
- `events: List[SessionEvent]` - Respiratory events

### SessionEvent

Event recorded during CPAP session.

**Fields:**
- `timestamp: float` - Time since session start (seconds)
- `event_type: str` - Event type (e.g., \"Obstructive Apnea\", \"Hypopnea\")
- `duration: float` - Event duration (seconds)
- `data: Dict[str, float]` - Additional event data

### SettingChange

Device setting change record.

**Fields:**
- `timestamp: datetime` - When setting was changed
- `setting: str` - Setting name
- `value: str` - New value
- `source: str` - Source file

### EDFHeader

EDF file header information.

**Fields:**
- `version: str` - EDF version
- `patient_id: str` - Patient identifier
- `recording_id: str` - Recording identifier
- `start_date: datetime` - Recording start date/time
- `header_bytes: int` - Header size
- `reserved: str` - Reserved field (may contain \"EDF+C\" for EDF+)
- `num_records: int` - Number of data records
- `duration: float` - Duration of data record (seconds)
- `num_signals: int` - Number of signals

### EDFSignal

EDF signal descriptor.

**Fields:**
- `label: str` - Signal label
- `transducer_type: str` - Transducer type
- `physical_dimension: str` - Physical unit (e.g., \"L/min\", \"cmH2O\")
- `physical_min: float` - Physical minimum
- `physical_max: float` - Physical maximum
- `digital_min: int` - Digital minimum
- `digital_max: int` - Digital maximum
- `prefiltering: str` - Prefiltering info
- `sample_count: int` - Samples per data record
- `reserved: str` - Reserved field
- `data: List[int]` - Raw digital samples
- `gain: float` - Calculated gain for conversion
- `offset: float` - Calculated offset for conversion

## Project Structure

```
cpap-py/
├── src/
│   └── cpap_py/                    # Main library package
│       ├── __init__.py             # Package initialization and exports
│       ├── edf_parser.py           # EDF/EDF+ file parser (pure Python)
│       ├── identification.py       # Device identification parser
│       ├── str_parser.py           # STR.edf summary data parser
│       ├── datalog_parser.py       # DATALOG session data parser
│       ├── settings_parser.py      # Settings file parser
│       ├── loader.py               # High-level data loader
│       └── utils.py                # Utility functions
├── tests/                          # Comprehensive test suite (97% coverage)
│   ├── conftest.py                 # Pytest fixtures
│   ├── test_init.py                # Package initialization tests
│   ├── test_identification.py      # ID parser tests
│   ├── test_edf_parser.py          # EDF parser tests
│   ├── test_utils.py               # Utility function tests
│   ├── test_parser_core.py         # Core parser functionality
│   ├── test_integration.py         # Integration tests
│   ├── test_mock_scenarios.py      # Mock-based tests
│   ├── test_realistic_edf_data.py  # Realistic EDF data tests
│   ├── test_signal_combinations.py # Signal combination tests
│   ├── test_bilevel_modes.py       # BiLevel mode tests
│   ├── test_settings_alternative_signals.py  # Alternative signal tests
│   └── test_optional_signals_errors.py       # Error handling tests
├── setup.py                        # Setup configuration
├── pyproject.toml                  # Project metadata and build config
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── INSTALL.md                      # Installation guide
├── USAGE.md                        # Detailed usage guide
├── DEVELOPMENT.md                  # Development guide
├── CONTRIBUTING.md                 # Contribution guidelines
├── TEST_SUITE.md                   # Test suite documentation
├── TESTING_COMPLETE.md             # Test coverage report
└── LICENSE                         # MIT License
```

## Utility Functions

The `utils` module provides helper functions for CPAP data analysis:

```python
from cpap_py.utils import (
    split_sessions_by_noon,
    format_duration,
    calculate_ahi,
    therapy_mode_name,
    downsample_signal,
    calculate_percentile
)

# Split session timestamps by noon boundary
sessions = split_sessions_by_noon(timestamps)

# Format duration as HH:MM:SS
duration_str = format_duration(seconds)

# Calculate AHI from event counts and hours
ahi = calculate_ahi(apneas=10, hypopneas=5, hours=7.5)

# Get therapy mode name from mode code
mode_name = therapy_mode_name(mode_code)  # "CPAP", "APAP", "BiLevel S", etc.

# Downsample signal data
downsampled = downsample_signal(data, factor=10)

# Calculate percentile (50th, 95th, etc.)
p95 = calculate_percentile(data, 95)
```

## Testing

The library includes a comprehensive test suite with **97% code coverage** and **188 automated tests**.

### Run Tests

```bash
# Run all tests with coverage
./run_tests.sh

# Run specific test file
pytest tests/test_identification.py -v

# Run with detailed coverage
pytest tests/ --cov=cpap_py --cov-report=term-missing
```

See [TEST_SUITE.md](TEST_SUITE.md) for detailed testing documentation.

## Documentation

- **[README.md](README.md)** - This file - Quick start and API reference
- **[INSTALL.md](INSTALL.md)** - Detailed installation instructions
- **[USAGE.md](USAGE.md)** - Comprehensive usage guide with examples
- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Development setup and workflows
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - How to contribute to the project
- **[TEST_SUITE.md](TEST_SUITE.md)** - Test suite documentation
- **[TESTING_COMPLETE.md](TESTING_COMPLETE.md)** - Test coverage report

## Requirements

- **Python**: 3.9 or higher
- **Dependencies**: None (pure Python standard library implementation)
- **Development Dependencies** (optional):
  - pytest >= 7.0.0
  - pytest-cov >= 4.0.0
  - pytest-mock >= 3.10.0
  - coverage >= 7.0.0
  - black >= 23.0.0 (code formatting)
  - ruff >= 0.1.0 (linting)

## Supported Devices

- **ResMed AirSense 11** - Latest generation with JSON identification
- **ResMed AirSense 10** - AutoSet, Elite, CPAP, For Her
- **ResMed AirCurve 10** - S, ST, VAuto, ASV
- **ResMed S9** - AutoSet, Elite, CPAP, VPAP series
- Other ResMed devices using EDF format

## Supported Data Files

### Identification Files
- `Identification.tgt` - Text format (#KEY value)
- `Identification.json` - JSON format (AirSense 11)

### Summary Files
- `STR.edf` - Daily summary statistics (AHI, leak, pressure, etc.)

### Session Data Files (DATALOG/)
- `BRP*.edf` - Breathing waveforms (flow rate, tidal volume, minute ventilation, respiratory rate)
- `PLD*.edf` - Pressure and leak data
- `SAD*.edf` - Summary/advanced data
- `EVE*.edf` - Respiratory events (apneas, hypopneas, flow limitations)
- `CSL*.edf` - Clinical settings log
- `AEV*.edf` - Advanced events

### Settings Files (SETTINGS/)
- `*.tgt` - Settings files (CGL, UGL, etc.)

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Run the test suite (`./run_tests.sh`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

This library is based on the file format specifications from [OSCAR](https://www.sleepfiles.com/OSCAR/) (Open Source CPAP Analysis Reporter), an excellent open-source CPAP data analysis application.

Special thanks to the OSCAR development team for their comprehensive documentation of ResMed file formats.

## Support

- **Issues**: [GitHub Issues](https://github.com/dynacylabs/cpap-py/issues)
- **Documentation**: [GitHub Repository](https://github.com/dynacylabs/cpap-py)
- **Repository**: [https://github.com/dynacylabs/cpap-py](https://github.com/dynacylabs/cpap-py)

## Related Projects

- **[OSCAR](https://www.sleepfiles.com/OSCAR/)** - Open Source CPAP Analysis Reporter (Qt/C++ desktop application)
- **[SleepHQ](https://sleephq.com/)** - Online CPAP data analysis platform
- **[pyedflib](https://github.com/holgern/pyedflib)** - Python library for reading/writing EDF files

## Changelog

### Version 0.1.0 (Current)

- Initial release
- Complete EDF/EDF+ parser (pure Python)
- Support for all ResMed device generations (S9, AirSense 10, AirSense 11)
- Parse identification files (.tgt, .json)
- Parse STR.edf summary data
- Parse DATALOG session data (BRP, PLD, SAD, EVE, CSL, AEV)
- Parse SETTINGS files
- High-level CPAPLoader interface
- Comprehensive test suite (97% coverage, 188 tests)
- Zero external dependencies
- Python 3.9+ support
