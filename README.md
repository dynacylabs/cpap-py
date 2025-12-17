# CPAP Data Parser Library

A Python library for parsing ResMed CPAP (Continuous Positive Airway Pressure) device data files. This library supports parsing all information stored in CPAP data files including device identification, summary statistics, detailed waveform data, and configuration changes.

## Features

- **Complete Data Extraction**: Parses all available CPAP data including pressure settings, delivered pressures, leak rates, respiratory metrics, and event indices
- **Device Identification**: Parse both `.tgt` (text) and `.json` format identification files
- **Summary Data**: Extract daily statistics from `STR.edf` files including AHI, leak, pressure, respiratory rate
- **Session Data**: Parse detailed waveform data from `DATALOG` EDF files
- **Settings & Configuration**: Extract device settings including pressure ranges (min/max), comfort settings, humidification
- **EDF/EDF+ Support**: Full parser for European Data Format files used by medical devices
- **Multiple Device Support**: Works with ResMed S9, AirSense 10, AirSense 11, and AirCurve series
- **JSON Export**: Complete data export to JSON for analysis

## Installation

```bash
pip install -e .
```

## Quick Start

### Generate Complete JSON Output

```bash
# Export all CPAP data to JSON
python dump_cpap_data.py data/set_1/ > output.json
```

The output.json file contains:
- Device identification and firmware info
- Current device configuration (pressure ranges, comfort settings, humidification)
- Daily summary records with AHI, leak stats, pressure stats, respiratory metrics
- Detailed session data organized by date
- Settings change history

See [DATA_GUIDE.md](DATA_GUIDE.md) for complete details on the JSON output format.

### Use the Library Programmatically

```python
from cpap_parser import CPAPLoader

# Load all data from a CPAP data directory
loader = CPAPLoader("path/to/cpap/data")
data = loader.load_all()

# Access device information
print(f"Device: {data.machine_info.model}")
print(f"Serial: {data.machine_info.serial}")

# Access daily summary records
for record in data.summary_records:
    print(f"Date: {record.date}")
    print(f"  AHI: {record.ahi:.1f}")
    print(f"  Duration: {record.mask_duration/3600:.1f} hours")
    print(f"  Leak (median): {record.leak_50:.1f} L/min")

# Access detailed session data
for session in data.sessions:
    print(f"Session: {session.start_time}")
    print(f"  Flow rate samples: {len(session.flow_rate)}")
    print(f"  Pressure samples: {len(session.pressure)}")
    print(f"  Events: {len(session.events)}")
```

## Usage Examples

### Load Only Identification

```python
from cpap_parser import IdentificationParser

parser = IdentificationParser("path/to/data")
info = parser.parse()
print(f"{info.model} (S/N: {info.serial})")
```

### Load Summary Data

```python
from cpap_parser import STRParser

parser = STRParser("path/to/STR.edf")
if parser.parse():
    for record in parser.records:
        if record.date:
            print(f"{record.date}: AHI={record.ahi:.1f}, Hours={record.mask_duration/3600:.1f}")
```

### Load Session Data

```python
from cpap_parser import DatalogParser

parser = DatalogParser("path/to/DATALOG")
sessions = parser.parse_all_sessions()

for session in sessions:
    print(f"{session.date} - {session.file_type}")
    print(f"  Sample rate: {session.sample_rate} Hz")
    print(f"  Duration: {session.duration/3600:.2f} hours")
```

### Parse Individual EDF Files

```python
from cpap_parser import EDFParser

edf = EDFParser("path/to/file.edf")
if edf.parse():
    print(f"Signals: {len(edf.signals)}")
    for signal in edf.signals:
        print(f"  {signal.label}: {len(signal.data)} samples")
        # Get physical (scaled) values
        values = edf.get_physical_values(signal)
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
Main high-level interface for loading CPAP data.

**Methods:**
- `load_all()`: Load all data (identification, summary, sessions, settings)
- `load_identification_only()`: Load only device info
- `load_summary_only()`: Load only STR.edf
- `load_sessions_for_date(date)`: Load sessions for specific date
- `get_date_range()`: Get (start_date, end_date) of available data

### IdentificationParser
Parse device identification files.

**Methods:**
- `parse()`: Parse and return MachineInfo object

### STRParser
Parse STR.edf summary files.

**Methods:**
- `parse()`: Parse file and populate records list
- `get_records_by_date_range(start, end)`: Filter records by date

### DatalogParser
Parse DATALOG session files.

**Methods:**
- `scan_files()`: Scan DATALOG directory and return files by date
- `parse_session_file(path)`: Parse single session file
- `parse_all_sessions()`: Parse all sessions
- `get_sessions_by_date(date)`: Get sessions for specific date
- `get_sessions_by_date_range(start, end)`: Get sessions in date range

### EDFParser
Low-level EDF/EDF+ file parser.

**Methods:**
- `parse()`: Parse entire file
- `parse_header()`: Parse only header
- `parse_signal_headers()`: Parse signal definitions
- `parse_data()`: Parse signal data
- `get_signal(label, index=0)`: Find signal by label
- `get_physical_values(signal)`: Convert digital to physical values

## Data Classes

### MachineInfo
Device identification information.

**Fields:** `serial`, `model`, `model_number`, `series`, `properties`

### STRRecord
Daily summary record.

**Fields:** `date`, `ahi`, `leak_50`, `leak_95`, `mask_duration`, `mode`, `min_pressure`, `max_pressure`, and many more...

### SessionData
Detailed session data.

**Fields:** `date`, `start_time`, `duration`, `flow_rate`, `pressure`, `leak`, `events`, and more waveform data...

### EDFSignal
EDF signal descriptor.

**Fields:** `label`, `physical_dimension`, `sample_count`, `gain`, `offset`, `data`

## Example Scripts

See the [examples/](examples/) directory for useful scripts:

- **show_one_day.py**: Display all data for a specific date
- **list_str_signals.py**: List all available signals in STR.edf
- **show_settings.py**: View device settings from .tgt files

## Documentation

- **[DATA_GUIDE.md](DATA_GUIDE.md)**: Complete guide to available CPAP data and clinical assessment
- **[examples/README.md](examples/README.md)**: Example script usage

## Development

### Repository Cleanup

To remove temporary files and clean up the repository:

```bash
# Linux/Mac
bash cleanup.sh

# Or use Python (cross-platform)
python cleanup.py
```

This removes:
- Old debug scripts (now in `examples/`)
- Generated output files (`output.json`)
- Python cache files (`__pycache__/`, `*.pyc`)

### Running Tests
```bash
python -m pytest tests/
```

### Project Structure
```
cpap_analysis/
├── cpap_parser/          # Main library package
│   ├── edf_parser.py     # EDF/EDF+ file parser
│   ├── identification.py # Device ID parser
│   ├── str_parser.py     # Summary data parser
│   ├── datalog_parser.py # Session data parser
│   ├── settings_parser.py# Settings parser
│   ├── loader.py         # High-level loader
│   └── utils.py          # Helper functions
├── examples/             # Example scripts
├── data/                 # CPAP data files (not in git)
├── dump_cpap_data.py     # JSON export script
└── setup.py             # Package setup

```

## License

See LICENSE file for details.

## Contributing

Contributions welcome! Please open an issue or pull request.

## Acknowledgments

Based on the excellent [OSCAR](https://gitlab.com/CrimsonNape/OSCAR-code) CPAP analysis software.

## Utilities

The `utils` module provides helper functions:

- `split_sessions_by_noon(timestamps)`: Split timestamps by noon boundary
- `format_duration(seconds)`: Format duration as HH:MM:SS
- `calculate_ahi(apneas, hypopneas, hours)`: Calculate AHI
- `therapy_mode_name(mode)`: Get mode name string
- `downsample_signal(data, factor)`: Downsample signal data
- `calculate_percentile(data, percentile)`: Calculate percentile

## Based On

This library is based on the file format specifications from [OSCAR](https://www.sleepfiles.com/OSCAR/) (Open Source CPAP Analysis Reporter), an open-source CPAP data analysis application.

## License

MIT License - see LICENSE file for details
