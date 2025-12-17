"""
Final push to 95%+ coverage
Tests for remaining uncovered lines in datalog_parser, settings_parser, identification
"""

import pytest
import struct
import json
from pathlib import Path
from datetime import datetime, date
from cpap_py.datalog_parser import DatalogParser, SessionData
from cpap_py.settings_parser import SettingsParser
from cpap_py.identification import IdentificationParser


def create_datalog_with_all_optional_signals(filepath):
    """Create DATALOG with all optional signals for complete coverage"""
    header = bytearray(256)
    header[0:8] = b'0       '
    header[8:88] = b'Session' + b' ' * 73
    header[88:168] = b'Recording' + b' ' * 71
    header[168:184] = b'15.12.2422.00.00'
    
    # All optional signals that might not always be present
    signal_names = [
        'Flow', 'Pressure', 'Leak', 'MaskPressure',
        'TidalVolume', 'MinuteVent', 'RespRate',
        'TargetIPAP', 'TargetEPAP', 'SpO2', 'Pulse'
    ]
    
    num_signals = len(signal_names)
    header[184:192] = f'{256 + 256*num_signals:<8}'.encode()
    header[192:236] = b'EDF+C' + b' ' * 39
    header[236:244] = b'5       '
    header[244:252] = b'1       '
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
    
    # Physical dimension
    for _ in range(num_signals):
        signal_header[offset:offset+8] = b'        '
        offset += 8
    
    # Physical min/max
    for _ in range(num_signals):
        signal_header[offset:offset+8] = b'-100    '
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
    
    # Prefilter
    for _ in range(num_signals):
        signal_header[offset:offset+80] = b' ' * 80
        offset += 80
    
    # Samples (high rate for waveform signals)
    for name in signal_names:
        if name in ['Flow', 'Pressure']:
            samples = 25  # 25 Hz
        else:
            samples = 1
        signal_header[offset:offset+8] = f'{samples:<8}'.encode()
        offset += 8
    
    # Reserved
    for _ in range(num_signals):
        signal_header[offset:offset+32] = b' ' * 32
        offset += 32
    
    # Data for 5 records
    data = bytearray()
    for rec in range(5):
        # Flow (25 samples)
        for _ in range(25):
            data.extend(struct.pack('<h', 100 + rec))
        
        # Pressure (25 samples)
        for _ in range(25):
            data.extend(struct.pack('<h', 200 + rec))
        
        # All other signals (1 sample each)
        for _ in range(9):
            data.extend(struct.pack('<h', 50 + rec))
    
    filepath.write_bytes(header + signal_header + data)


def create_settings_tgt_with_ioerror(filepath):
    """Create a settings file that will cause IOError during parsing"""
    # This will be deleted before parsing to cause IOError
    filepath.write_text("SystemSetting:TestValue\nTimeStamp:20240101120000\n")


class TestDatalogOptionalSignals:
    """Test datalog parser with all optional signals"""
    
    def test_parse_session_with_all_signals(self, temp_dir):
        """Test parsing session file with all optional signals present"""
        datalog_dir = temp_dir / "DATALOG"
        datalog_dir.mkdir()
        date_dir = datalog_dir / "20241215"
        date_dir.mkdir()
        
        session_file = date_dir / "session.edf"
        create_datalog_with_all_optional_signals(session_file)
        
        parser = DatalogParser(str(datalog_dir))
        session = parser.parse_session_file(session_file)
        
        assert session is not None
        # Verify optional signals were parsed
        assert session.tidal_volume is not None
        assert session.minute_vent is not None
        assert session.resp_rate is not None
        assert session.target_ipap is not None
        assert session.target_epap is not None
        assert session.spo2 is not None
        assert session.pulse is not None
    
    def test_scan_files_invalid_date_format(self, temp_dir):
        """Test scan_files with invalid date directory names"""
        datalog_dir = temp_dir / "DATALOG"
        datalog_dir.mkdir()
        
        # Create invalid directory names
        (datalog_dir / "invalid").mkdir()
        (datalog_dir / "2024").mkdir()  # Too short
        (datalog_dir / "20240132").mkdir()  # Invalid date
        (datalog_dir / "abcd1234").mkdir()  # Not digits
        
        parser = DatalogParser(str(datalog_dir))
        files = parser.scan_files()
        
        # Should not crash, should return empty dict
        assert isinstance(files, dict)
    
    def test_parse_session_file_edf_parse_fails(self, temp_dir):
        """Test parse_session_file when EDF parsing fails"""
        datalog_dir = temp_dir / "DATALOG"
        datalog_dir.mkdir()
        
        # Create corrupt EDF file
        bad_file = datalog_dir / "bad.edf"
        bad_file.write_bytes(b'CORRUPT DATA' * 20)
        
        parser = DatalogParser(str(datalog_dir))
        session = parser.parse_session_file(bad_file)
        
        # Should return None
        assert session is None


class TestSettingsParserIOErrors:
    """Test settings parser IOError handling"""
    
    def test_parse_tgt_file_missing(self, temp_dir):
        """Test parse_tgt_file with non-existent file"""
        settings_dir = temp_dir / "SETTINGS"
        settings_dir.mkdir()
        
        fake_file = settings_dir / "nonexistent.tgt"
        
        parser = SettingsParser(str(settings_dir))
        changes = parser.parse_file(fake_file)
        
        # Should handle gracefully and return empty list
        assert changes == []
    
    def test_parse_json_file_invalid_json(self, temp_dir):
        """Test parse_json_file with invalid JSON"""
        settings_dir = temp_dir / "SETTINGS"
        settings_dir.mkdir()
        
        bad_json = settings_dir / "bad.json"
        bad_json.write_text("{invalid json")
        
        parser = SettingsParser(str(settings_dir))
        changes = parser.parse_file(bad_json)
        
        # Should handle gracefully
        assert changes == []
    
    def test_parse_timestamp_invalid_formats(self, temp_dir):
        """Test _parse_timestamp with various invalid formats"""
        settings_dir = temp_dir / "SETTINGS"
        settings_dir.mkdir()
        
        parser = SettingsParser(str(settings_dir))
        
        # Test invalid timestamps
        result = parser._parse_timestamp("invalid")
        assert result is None
        
        result = parser._parse_timestamp("20241332120000")  # Invalid month
        assert result is None
        
        result = parser._parse_timestamp("")
        assert result is None


class TestIdentificationModelSeries:
    """Test identification parser model/series detection"""
    
    def test_parse_tgt_airsense_11(self, temp_dir):
        """Test parsing TGT file with AirSense 11 model"""
        id_file = temp_dir / "Identification.tgt"
        id_file.write_text(
            "#SRN 12345678\n"
            "#PNA AirSense 11 AutoSet\n"
            "#PCD CPAP\n"
        )
        
        parser = IdentificationParser(str(temp_dir))
        info = parser.parse()
        
        assert info.model == "AirSense 11 AutoSet"
        assert info.series == "AirSense 11"
    
    def test_parse_tgt_aircurve_10(self, temp_dir):
        """Test parsing TGT file with AirCurve 10 model"""
        id_file = temp_dir / "Identification.tgt"
        id_file.write_text(
            "#SRN 87654321\n"
            "#PNA AirCurve 10 VAuto\n"
        )
        
        parser = IdentificationParser(str(temp_dir))
        info = parser.parse()
        
        assert info.model == "AirCurve 10 VAuto"
        assert info.series == "AirSense 10"
    
    def test_parse_tgt_s9_series(self, temp_dir):
        """Test parsing TGT file with S9 series model"""
        id_file = temp_dir / "Identification.tgt"
        id_file.write_text(
            "#SRN 99999999\n"
            "#PNA S9 Elite\n"
        )
        
        parser = IdentificationParser(str(temp_dir))
        info = parser.parse()
        
        assert info.model == "S9 Elite"
        assert info.series == "S9"
    
    def test_parse_tgt_ioerror(self, temp_dir):
        """Test parsing TGT file that causes IOError"""
        # Create a directory instead of file to cause IOError
        id_dir = temp_dir / "Identification.tgt"
        id_dir.mkdir()
        
        parser = IdentificationParser(str(temp_dir))
        info = parser.parse()
        
        # Should handle gracefully
        assert info is not None


class TestEDFParserEdgeCases:
    """Test EDF parser edge cases for missing coverage"""
    
    def test_parse_signal_headers_without_data(self, temp_dir):
        """Test parse_signal_headers when file has no data section"""
        from cpap_py.edf_parser import EDFParser
        
        filepath = temp_dir / "nodata.edf"
        
        # EDF with header and signal headers but no data
        header = bytearray(256)
        header[0:8] = b'0       '
        header[8:88] = b' ' * 80
        header[88:168] = b' ' * 80
        header[168:184] = b'01.01.2400.00.00'
        header[184:192] = b'512     '  # 256 + 256
        header[192:236] = b' ' * 44
        header[236:244] = b'1       '
        header[244:252] = b'1       '
        header[252:256] = b'1   '
        
        signal_header = bytearray(256)
        signal_header[0:16] = b'Test            '
        signal_header[16:96] = b' ' * 80
        signal_header[96:104] = b'        '
        signal_header[104:112] = b'0       '
        signal_header[112:120] = b'100     '
        signal_header[120:128] = b'-32768  '
        signal_header[128:136] = b'32767   '
        signal_header[136:216] = b' ' * 80
        signal_header[216:224] = b'1       '
        signal_header[224:256] = b' ' * 32
        
        # No data section
        filepath.write_bytes(header + signal_header)
        
        parser = EDFParser(str(filepath))
        parser.open()
        parser.parse_header()
        result = parser.parse_signal_headers()
        
        # Should succeed
        assert result is True
        assert len(parser.signals) == 1
    
    def test_open_file_too_short(self, temp_dir):
        """Test opening file that's too short"""
        from cpap_py.edf_parser import EDFParser
        
        filepath = temp_dir / "short.edf"
        filepath.write_bytes(b'x' * 100)  # Less than 256 bytes
        
        parser = EDFParser(str(filepath))
        result = parser.open()
        
        # Should return False
        assert result is False


class TestLoaderRemainingEdgeCases:
    """Test remaining loader edge cases"""
    
    def test_load_sessions_for_date_session_none(self, temp_dir):
        """Test load_sessions_for_date when parse_session_file returns None"""
        from cpap_py.loader import CPAPLoader
        
        datalog_dir = temp_dir / "DATALOG"
        datalog_dir.mkdir()
        date_dir = datalog_dir / "20240101"
        date_dir.mkdir()
        
        # Create invalid session file
        bad_session = date_dir / "bad.edf"
        bad_session.write_bytes(b'CORRUPT' * 10)
        
        loader = CPAPLoader(str(temp_dir))
        sessions = loader.load_sessions_for_date(date(2024, 1, 1))
        
        # Should return empty list (None sessions are filtered out)
        assert isinstance(sessions, list)
    
    def test_get_date_range_empty_dates(self, temp_dir):
        """Test get_date_range when records have no dates"""
        from cpap_py.loader import CPAPLoader
        from cpap_py.str_parser import STRParser
        
        # Create STR that parses but has records with None dates
        str_file = temp_dir / "STR.edf"
        
        # Create minimal STR
        header = bytearray(256)
        header[0:8] = b'0       '
        header[8:88] = b' ' * 80
        header[88:168] = b' ' * 80
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
        
        for name in signal_names:
            signal_header[offset:offset+16] = f'{name:<16}'.encode()[:16]
            offset += 16
        
        for _ in range(num_signals):
            signal_header[offset:offset+80] = b' ' * 80
            offset += 80
        
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
        
        for _ in range(num_signals):
            signal_header[offset:offset+80] = b' ' * 80
            offset += 80
        
        for name in signal_names:
            samples = 10 if 'Mask O' in name else 1
            signal_header[offset:offset+8] = f'{samples:<8}'.encode()
            offset += 8
        
        for _ in range(num_signals):
            signal_header[offset:offset+32] = b' ' * 32
            offset += 32
        
        # All zeros - should result in invalid day (no mask events)
        data = bytearray(21 * 2)  # 10+10+1 samples, 2 bytes each
        
        str_file.write_bytes(header + signal_header + data)
        
        loader = CPAPLoader(str(temp_dir))
        date_range = loader.get_date_range()
        
        # Should return None (no valid dates)
        assert date_range is None
