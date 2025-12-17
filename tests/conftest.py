"""
Pytest configuration and shared fixtures for cpap-py tests
"""

import pytest
import tempfile
import json
import gzip
import struct
from pathlib import Path
from datetime import datetime, date


@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory for test files"""
    return tmp_path


@pytest.fixture
def sample_tgt_identification(temp_dir):
    """Create a sample .tgt identification file"""
    content = """#SRN 12345678
#PNA AirSense 10 AutoSet
#PCD 37207
#MID AS10-AUTOSET
#CID 12345
#SID V10.3.0
"""
    filepath = temp_dir / "Identification.tgt"
    filepath.write_text(content)
    return filepath


@pytest.fixture
def sample_json_identification(temp_dir):
    """Create a sample .json identification file"""
    data = {
        "FlowGenerator": {
            "IdentificationProfiles": {
                "Product": {
                    "SerialNumber": "87654321",
                    "ProductCode": "38000",
                    "ProductName": "AirSense 11 AutoSet"
                }
            }
        }
    }
    filepath = temp_dir / "Identification.json"
    filepath.write_text(json.dumps(data, indent=2))
    return filepath


@pytest.fixture
def sample_edf_file(temp_dir):
    """Create a minimal valid EDF file"""
    # EDF header is 256 bytes + signal headers
    header = bytearray(256)
    
    # Version (8 bytes)
    header[0:8] = b'0       '
    
    # Patient ID (80 bytes)
    header[8:88] = b'X X X X                                                                         '
    
    # Recording ID (80 bytes)
    header[88:168] = b'Startdate X X X X                                                               '
    
    # Start date/time (16 bytes) - dd.MM.yyHH.mm.ss
    header[168:184] = b'15.12.2412.30.00'
    
    # Number of bytes in header (8 bytes) - 256 + (256 * num_signals)
    # For 2 signals: 256 + 512 = 768
    header[184:192] = b'768     '
    
    # Reserved (44 bytes)
    header[192:236] = b'EDF+C                                       '
    
    # Number of data records (8 bytes)
    header[236:244] = b'1       '
    
    # Duration of a data record (8 bytes)
    header[244:252] = b'1       '
    
    # Number of signals (4 bytes)
    header[252:256] = b'2   '
    
    # Signal headers - EDF format requires all signals for each field sequentially
    num_signals = 2
    signal_header = bytearray(256 * num_signals)
    
    offset = 0
    # Labels (16 bytes * num_signals)
    signal_header[offset:offset+16] = b'Flow            '
    signal_header[offset+16:offset+32] = b'Pressure        '
    offset += 16 * num_signals
    
    # Transducer types (80 bytes * num_signals)
    signal_header[offset:offset+80] = b' ' * 80
    signal_header[offset+80:offset+160] = b' ' * 80
    offset += 80 * num_signals
    
    # Physical dimensions (8 bytes * num_signals)
    signal_header[offset:offset+8] = b'L/min   '
    signal_header[offset+8:offset+16] = b'cmH2O   '
    offset += 8 * num_signals
    
    # Physical minimums (8 bytes * num_signals)
    signal_header[offset:offset+8] = b'-100    '
    signal_header[offset+8:offset+16] = b'0       '
    offset += 8 * num_signals
    
    # Physical maximums (8 bytes * num_signals)
    signal_header[offset:offset+8] = b'100     '
    signal_header[offset+8:offset+16] = b'30      '
    offset += 8 * num_signals
    
    # Digital minimums (8 bytes * num_signals)
    signal_header[offset:offset+8] = b'-32768  '
    signal_header[offset+8:offset+16] = b'-32768  '
    offset += 8 * num_signals
    
    # Digital maximums (8 bytes * num_signals)
    signal_header[offset:offset+8] = b'32767   '
    signal_header[offset+8:offset+16] = b'32767   '
    offset += 8 * num_signals
    
    # Prefiltering (80 bytes * num_signals)
    signal_header[offset:offset+80] = b' ' * 80
    signal_header[offset+80:offset+160] = b' ' * 80
    offset += 80 * num_signals
    
    # Number of samples (8 bytes * num_signals)
    signal_header[offset:offset+8] = b'25      '
    signal_header[offset+8:offset+16] = b'25      '
    offset += 8 * num_signals
    
    # Reserved (32 bytes * num_signals)
    signal_header[offset:offset+32] = b' ' * 32
    signal_header[offset+32:offset+64] = b' ' * 32
    
    # Data records (25 samples * 2 bytes * 2 signals = 100 bytes)
    data = bytearray(100)
    for i in range(25):
        # Flow signal
        data[i*2:i*2+2] = struct.pack('<h', i * 1000)
        # Pressure signal
        data[50 + i*2:50 + i*2+2] = struct.pack('<h', 10000 + i * 100)
    
    filepath = temp_dir / "test.edf"
    with open(filepath, 'wb') as f:
        f.write(header)
        f.write(signal_header)
        f.write(data)
    
    return filepath


@pytest.fixture
def sample_str_edf(temp_dir):
    """Create a minimal STR.edf file with basic structure"""
    # This is a simplified version - real STR files are more complex
    # For testing, we'll create a minimal EDF structure
    header = bytearray(256)
    
    header[0:8] = b'0       '
    header[8:88] = b'12345678                                                                        '
    header[88:168] = b'Startdate 01.01.24 ResMed                                                       '
    header[168:184] = b'01.01.2400.00.00'
    header[184:192] = b'512     '  # 256 + 256 for 1 signal
    header[192:236] = b' ' * 44
    header[236:244] = b'1       '
    header[244:252] = b'86400   '  # 1 day duration
    header[252:256] = b'1   '
    
    # Single signal header
    signal_header = bytearray(256)
    signal_header[0:16] = b'Summary         '
    signal_header[16:96] = b' ' * 80
    signal_header[96:104] = b'        '
    signal_header[104:112] = b'0       '
    signal_header[112:120] = b'1       '
    signal_header[120:128] = b'0       '
    signal_header[128:136] = b'1       '
    signal_header[136:216] = b' ' * 80
    signal_header[216:224] = b'1       '
    signal_header[224:256] = b' ' * 32
    
    # Minimal data
    data = struct.pack('<h', 0)
    
    filepath = temp_dir / "STR.edf"
    with open(filepath, 'wb') as f:
        f.write(header)
        f.write(signal_header)
        f.write(data)
    
    return filepath


@pytest.fixture
def sample_cpap_directory(temp_dir, sample_tgt_identification):
    """Create a complete sample CPAP data directory structure"""
    # Create subdirectories
    datalog_dir = temp_dir / "DATALOG"
    datalog_dir.mkdir()
    
    settings_dir = temp_dir / "SETTINGS"
    settings_dir.mkdir()
    
    # Create a sample day directory in DATALOG
    day_dir = datalog_dir / "20241215"
    day_dir.mkdir()
    
    # Create a sample settings file
    settings_file = settings_dir / "CGL_12345.tgt"
    settings_file.write_text("#TS 2024-12-15T12:00:00\n#SET MinPressure 4.0\n")
    
    return temp_dir


@pytest.fixture
def mock_datetime():
    """Fixture for mocking datetime"""
    return datetime(2024, 12, 15, 12, 30, 0)


@pytest.fixture
def mock_date():
    """Fixture for mocking date"""
    return date(2024, 12, 15)
