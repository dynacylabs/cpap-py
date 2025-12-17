"""
Final coverage boost tests targeting specific uncovered lines
"""

import pytest
import struct
from pathlib import Path
from datetime import datetime, date
from cpap_py.str_parser import STRParser, STRRecord
from cpap_py.datalog_parser import DatalogParser
from cpap_py.loader import CPAPLoader
from cpap_py.edf_parser import EDFParser


def create_str_with_bilevel_modes(filepath, mode=2):
    """Create STR.edf with BiLevel mode settings for coverage"""
    header = bytearray(256)
    header[0:8] = b'0       '
    header[8:88] = b'12345678' + b' ' * 72
    header[88:168] = b'Startdate 01.01.24 ResMed' + b' ' * 55
    header[168:184] = b'01.01.2400.00.00'
    
    # Signals including BiLevel-specific ones
    signal_names = [
        'Mask On', 'Mask Off', 'Mask Events',
        'Mode', 'IPAP', 'EPAP', 'PS',
        'S.EasyBreathe', 'S.RiseEnable', 'S.RiseTime',
        'S.Cycle', 'S.Trigger', 'S.TiMax', 'S.TiMin'
    ]
    
    num_signals = len(signal_names)
    header_bytes = 256 + (256 * num_signals)
    header[184:192] = f'{header_bytes:<8}'.encode()
    header[192:236] = b' ' * 44
    header[236:244] = b'1       '
    header[244:252] = b'86400   '
    header[252:256] = f'{num_signals:<4}'.encode()
    
    # Build signal headers
    signal_header = bytearray(256 * num_signals)
    offset = 0
    
    # Labels
    for name in signal_names:
        signal_header[offset:offset+16] = f'{name:<16}'.encode()[:16]
        offset += 16
    
    # Transducer type
    for _ in range(num_signals):
        signal_header[offset:offset+80] = b' ' * 80
        offset += 80
    
    # Physical dimension
    for _ in range(num_signals):
        signal_header[offset:offset+8] = b'        '
        offset += 8
    
    # Physical min/max
    for _ in range(num_signals):
        signal_header[offset:offset+8] = b'0       '
        offset += 8
    for _ in range(num_signals):
        signal_header[offset:offset+8] = b'100     '
        offset += 8
    
    # Digital min/max
    for _ in range(num_signals):
        signal_header[offset:offset+8] = b'-32768  '
        offset += 8
    for _ in range(num_signals):
        signal_header[offset:offset+8] = b'32767   '
        offset += 8
    
    # Prefiltering
    for _ in range(num_signals):
        signal_header[offset:offset+80] = b' ' * 80
        offset += 80
    
    # Number of samples
    for i, name in enumerate(signal_names):
        samples = 10 if 'Mask O' in name else 1
        signal_header[offset:offset+8] = f'{samples:<8}'.encode()
        offset += 8
    
    # Reserved
    for _ in range(num_signals):
        signal_header[offset:offset+32] = b' ' * 32
        offset += 32
    
    # Data for 1 day
    data = bytearray()
    
    # Mask On (10 samples)
    for i in range(10):
        val = 720 + (i * 30) if i < 3 else 0
        data.extend(struct.pack('<h', val))
    
    # Mask Off (10 samples)
    for i in range(10):
        val = 1200 + (i * 30) if i < 3 else 0
        data.extend(struct.pack('<h', val))
    
    # Mask Events
    data.extend(struct.pack('<h', 2))
    
    # Mode (BiLevel mode 2, 3, 4, or 5)
    data.extend(struct.pack('<h', mode))
    
    # IPAP, EPAP, PS
    data.extend(struct.pack('<h', 12000))
    data.extend(struct.pack('<h', 8000))
    data.extend(struct.pack('<h', 4000))
    
    # BiLevel settings (values depend on mode)
    data.extend(struct.pack('<h', 1))  # S.EasyBreathe
    data.extend(struct.pack('<h', 1))  # S.RiseEnable
    data.extend(struct.pack('<h', 300))  # S.RiseTime
    data.extend(struct.pack('<h', 50))  # S.Cycle
    data.extend(struct.pack('<h', 20))  # S.Trigger
    data.extend(struct.pack('<h', 2500))  # S.TiMax
    data.extend(struct.pack('<h', 800))  # S.TiMin
    
    filepath.write_bytes(header + signal_header + data)


def create_str_missing_signals(filepath):
    """Create STR without required signals for error path"""
    header = bytearray(256)
    header[0:8] = b'0       '
    header[8:88] = b'12345678' + b' ' * 72
    header[88:168] = b'Startdate 01.01.24' + b' ' * 62
    header[168:184] = b'01.01.2400.00.00'
    header[184:192] = b'512     '  # 256 + 256*1
    header[192:236] = b' ' * 44
    header[236:244] = b'1       '
    header[244:252] = b'1       '
    header[252:256] = b'1   '
    
    # Only one signal (not Mask On/Off/Events)
    signal_header = bytearray(256)
    signal_header[0:16] = b'Other           '
    signal_header[16:96] = b' ' * 80
    signal_header[96:104] = b'        '
    signal_header[104:112] = b'0       '
    signal_header[112:120] = b'100     '
    signal_header[120:128] = b'-32768  '
    signal_header[128:136] = b'32767   '
    signal_header[136:216] = b' ' * 80
    signal_header[216:224] = b'1       '
    signal_header[224:256] = b' ' * 32
    
    data = struct.pack('<h', 0)
    filepath.write_bytes(header + signal_header + data)


def create_str_no_start_date(filepath):
    """Create STR with missing start date"""
    header = bytearray(256)
    header[0:8] = b'0       '
    header[8:88] = b' ' * 80
    header[88:168] = b' ' * 80
    header[168:184] = b'                '  # Empty date
    header[184:192] = b'256     '
    header[192:236] = b' ' * 44
    header[236:244] = b'0       '
    header[244:252] = b'1       '
    header[252:256] = b'0   '
    
    filepath.write_bytes(header)


def create_str_invalid_day(filepath):
    """Create STR where all mask events are 0 (invalid day)"""
    header = bytearray(256)
    header[0:8] = b'0       '
    header[8:88] = b'12345678' + b' ' * 72
    header[88:168] = b'Startdate 01.01.24' + b' ' * 62
    header[168:184] = b'01.01.2400.00.00'
    
    signal_names = ['Mask On', 'Mask Off', 'Mask Events']
    num_signals = 3
    header_bytes = 256 + (256 * num_signals)
    header[184:192] = f'{header_bytes:<8}'.encode()
    header[192:236] = b' ' * 44
    header[236:244] = b'1       '
    header[244:252] = b'86400   '
    header[252:256] = f'{num_signals:<4}'.encode()
    
    signal_header = bytearray(256 * num_signals)
    offset = 0
    
    # Labels
    for name in signal_names:
        signal_header[offset:offset+16] = f'{name:<16}'.encode()[:16]
        offset += 16
    
    # Transducer
    for _ in range(num_signals):
        signal_header[offset:offset+80] = b' ' * 80
        offset += 80
    
    # Dimensions and ranges
    for _ in range(num_signals):
        signal_header[offset:offset+8] = b'        '
        offset += 8
    for _ in range(num_signals):
        signal_header[offset:offset+8] = b'0       '
        offset += 8
    for _ in range(num_signals):
        signal_header[offset:offset+8] = b'100     '
        offset += 8
    for _ in range(num_signals):
        signal_header[offset:offset+8] = b'-32768  '
        offset += 8
    for _ in range(num_signals):
        signal_header[offset:offset+8] = b'32767   '
        offset += 8
    
    # Prefilter
    for _ in range(num_signals):
        signal_header[offset:offset+80] = b' ' * 80
        offset += 80
    
    # Samples
    for name in signal_names:
        samples = 10 if 'Mask O' in name else 1
        signal_header[offset:offset+8] = f'{samples:<8}'.encode()
        offset += 8
    
    # Reserved
    for _ in range(num_signals):
        signal_header[offset:offset+32] = b' ' * 32
        offset += 32
    
    # Data - all zeros (no mask events)
    data = bytearray()
    for _ in range(10):  # Mask On
        data.extend(struct.pack('<h', 0))
    for _ in range(10):  # Mask Off
        data.extend(struct.pack('<h', 0))
    data.extend(struct.pack('<h', 0))  # Mask Events = 0
    
    filepath.write_bytes(header + signal_header + data)


class TestSTRParserBiLevelModes:
    """Test STR parser with different BiLevel modes for complete coverage"""
    
    def test_parse_bilevel_mode_2(self, temp_dir):
        """Test BiLevel mode 2 settings"""
        str_file = temp_dir / "STR_mode2.edf"
        create_str_with_bilevel_modes(str_file, mode=2)
        
        parser = STRParser(str(str_file))
        result = parser.parse()
        
        assert result is True
        assert len(parser.records) == 1
        # Mode value will be transformed by gain/offset, just verify parsing worked
    
    def test_parse_bilevel_mode_3_s(self, temp_dir):
        """Test BiLevel mode 3 (S mode) with EasyBreathe"""
        str_file = temp_dir / "STR_mode3.edf"
        create_str_with_bilevel_modes(str_file, mode=3)
        
        parser = STRParser(str(str_file))
        result = parser.parse()
        
        assert result is True
        assert len(parser.records) == 1
        # Mode 3 should trigger S.Cycle, S.Trigger, S.EasyBreathe parsing
    
    def test_parse_bilevel_mode_4_st(self, temp_dir):
        """Test BiLevel mode 4 (ST mode) with TiMax/TiMin"""
        str_file = temp_dir / "STR_mode4.edf"
        create_str_with_bilevel_modes(str_file, mode=4)
        
        parser = STRParser(str(str_file))
        result = parser.parse()
        
        assert result is True
        assert len(parser.records) == 1
        # Mode 4 should trigger both S/ST settings and ST/T settings parsing
    
    def test_parse_bilevel_mode_5_t(self, temp_dir):
        """Test BiLevel mode 5 (T mode)"""
        str_file = temp_dir / "STR_mode5.edf"
        create_str_with_bilevel_modes(str_file, mode=5)
        
        parser = STRParser(str(str_file))
        result = parser.parse()
        
        assert result is True
        assert len(parser.records) == 1
        # Mode 5 should trigger T mode settings parsing


class TestSTRParserErrorPaths:
    """Test STR parser error handling paths"""
    
    def test_parse_missing_required_signals(self, temp_dir):
        """Test parsing STR without Mask On/Off/Events signals"""
        str_file = temp_dir / "STR_missing.edf"
        create_str_missing_signals(str_file)
        
        parser = STRParser(str(str_file))
        result = parser.parse()
        
        assert result is False
    
    def test_parse_no_start_date(self, temp_dir):
        """Test parsing STR with no start date"""
        str_file = temp_dir / "STR_nodate.edf"
        create_str_no_start_date(str_file)
        
        parser = STRParser(str(str_file))
        result = parser.parse()
        
        assert result is False
    
    def test_parse_invalid_day(self, temp_dir):
        """Test parsing STR where day has no mask events (should skip)"""
        str_file = temp_dir / "STR_invalid.edf"
        create_str_invalid_day(str_file)
        
        parser = STRParser(str(str_file))
        result = parser.parse()
        
        # Parser succeeds but returns empty records list
        assert result is True
        assert len(parser.records) == 0


class TestLoaderEdgeCases:
    """Test CPAP loader edge cases for coverage"""
    
    def test_load_summary_no_str_file(self, temp_dir):
        """Test load_summary when STR.edf doesn't exist"""
        loader = CPAPLoader(str(temp_dir))
        records = loader.load_summary_only()
        
        assert records == []
    
    def test_load_summary_str_parse_fails(self, temp_dir):
        """Test load_summary when STR.edf parsing fails"""
        str_file = temp_dir / "STR.edf"
        create_str_missing_signals(str_file)
        
        loader = CPAPLoader(str(temp_dir))
        records = loader.load_summary_only()
        
        assert records == []
    
    def test_load_sessions_no_datalog_dir(self, temp_dir):
        """Test load_sessions_for_date when DATALOG doesn't exist"""
        loader = CPAPLoader(str(temp_dir))
        sessions = loader.load_sessions_for_date(date(2024, 1, 1))
        
        assert sessions == []
    
    def test_load_sessions_no_files_for_date(self, temp_dir):
        """Test load_sessions_for_date when no files exist for date"""
        datalog_dir = temp_dir / "DATALOG"
        datalog_dir.mkdir()
        
        loader = CPAPLoader(str(temp_dir))
        sessions = loader.load_sessions_for_date(date(2024, 1, 1))
        
        assert sessions == []
    
    def test_get_date_range_no_str(self, temp_dir):
        """Test get_date_range when STR.edf doesn't exist"""
        loader = CPAPLoader(str(temp_dir))
        date_range = loader.get_date_range()
        
        assert date_range is None
    
    def test_get_date_range_parse_fails(self, temp_dir):
        """Test get_date_range when STR parsing fails"""
        str_file = temp_dir / "STR.edf"
        create_str_missing_signals(str_file)
        
        loader = CPAPLoader(str(temp_dir))
        date_range = loader.get_date_range()
        
        assert date_range is None
    
    def test_get_date_range_no_records(self, temp_dir):
        """Test get_date_range when STR has no valid records"""
        str_file = temp_dir / "STR.edf"
        create_str_invalid_day(str_file)
        
        loader = CPAPLoader(str(temp_dir))
        date_range = loader.get_date_range()
        
        assert date_range is None


class TestDatalogParserCoverage:
    """Test datalog parser for missing coverage"""
    
    def test_scan_files_nested_directories(self, temp_dir):
        """Test scanning with nested date directories"""
        datalog_dir = temp_dir / "DATALOG"
        datalog_dir.mkdir()
        
        # Create nested directory structure
        date_dir = datalog_dir / "20240101"
        date_dir.mkdir()
        (date_dir / "test.edf").write_bytes(b'x' * 256)
        
        parser = DatalogParser(str(datalog_dir))
        files = parser.scan_files()
        
        assert date(2024, 1, 1) in files
        assert len(files[date(2024, 1, 1)]) == 1
    
    def test_get_sessions_for_nonexistent_date(self, temp_dir):
        """Test getting sessions for a date with no files"""
        datalog_dir = temp_dir / "DATALOG"
        datalog_dir.mkdir()
        
        parser = DatalogParser(str(datalog_dir))
        sessions = parser.get_sessions_by_date(date(2024, 12, 25))
        
        assert sessions == []


class TestEDFParserEdgeCases:
    """Test EDF parser edge cases"""
    
    def test_parse_with_gain_offset_calculation(self, temp_dir):
        """Test EDF parsing with proper gain/offset"""
        filepath = temp_dir / "test.edf"
        
        # Create minimal valid EDF
        header = bytearray(256)
        header[0:8] = b'0       '
        header[8:88] = b' ' * 80
        header[88:168] = b' ' * 80
        header[168:184] = b'01.01.2400.00.00'
        header[184:192] = b'512     '
        header[192:236] = b' ' * 44
        header[236:244] = b'1       '
        header[244:252] = b'1       '
        header[252:256] = b'1   '
        
        # Signal header with non-zero gain/offset
        signal_header = bytearray(256)
        signal_header[0:16] = b'Test            '
        signal_header[16:96] = b' ' * 80
        signal_header[96:104] = b'mbar    '
        signal_header[104:112] = b'5.0     '  # phys min
        signal_header[112:120] = b'25.0    '  # phys max
        signal_header[120:128] = b'-1000   '  # digital min
        signal_header[128:136] = b'1000    '  # digital max
        signal_header[136:216] = b' ' * 80
        signal_header[216:224] = b'1       '
        signal_header[224:256] = b' ' * 32
        
        data = struct.pack('<h', 0)  # One sample
        
        filepath.write_bytes(header + signal_header + data)
        
        parser = EDFParser(str(filepath))
        result = parser.parse()
        
        assert result is True
        assert len(parser.signals) == 1
        signal = parser.signals[0]
        # Gain = (25-5)/(1000--1000) = 20/2000 = 0.01
        # Offset = 25 - 0.01*1000 = 15
        assert abs(signal.gain - 0.01) < 0.001
        assert abs(signal.offset - 15.0) < 0.001
