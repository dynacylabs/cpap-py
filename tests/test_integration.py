"""
Additional integration and edge case tests for comprehensive coverage
"""

import pytest
import struct
from pathlib import Path
from datetime import datetime, date, time, timedelta
from cpap_py.identification import IdentificationParser, MachineInfo
from cpap_py.edf_parser import EDFParser, EDFSignal
from cpap_py.str_parser import STRParser
from cpap_py.loader import CPAPLoader
from cpap_py.utils import split_sessions_by_noon


class TestEDFParserIntegration:
    """Integration tests for EDF parser with realistic scenarios"""
    
    def test_parse_edf_with_multiple_data_records(self, temp_dir):
        """Test parsing EDF with multiple data records"""
        # Create EDF with 3 data records
        header = bytearray(256)
        header[0:8] = b'0       '
        header[8:88] = b' ' * 80
        header[88:168] = b' ' * 80
        header[168:184] = b'15.12.2412.30.00'
        header[184:192] = b'512     '
        header[192:236] = b' ' * 44
        header[236:244] = b'3       '  # 3 data records
        header[244:252] = b'1       '
        header[252:256] = b'1   '
        
        # Signal header
        signal_header = bytearray(256)
        signal_header[0:16] = b'TestSignal      '
        signal_header[96:104] = b'unit    '
        signal_header[104:112] = b'0       '
        signal_header[112:120] = b'100     '
        signal_header[120:128] = b'-32768  '
        signal_header[128:136] = b'32767   '
        signal_header[216:224] = b'5       '  # 5 samples per record
        
        # Data: 3 records * 5 samples * 2 bytes = 30 bytes
        data = bytearray(30)
        for i in range(15):
            data[i*2:i*2+2] = struct.pack('<h', i * 1000)
        
        filepath = temp_dir / "multi_record.edf"
        filepath.write_bytes(header + signal_header + data)
        
        parser = EDFParser(str(filepath))
        assert parser.parse() is True
        assert len(parser.signals[0].data) == 15  # 3 records * 5 samples
    
    def test_get_signal_multiple_same_label(self, temp_dir):
        """Test getting signal when multiple have the same label"""
        # Create EDF with 2 signals with same label
        header = bytearray(256)
        header[0:8] = b'0       '
        header[8:88] = b' ' * 80
        header[88:168] = b' ' * 80
        header[168:184] = b'15.12.2412.30.00'
        header[184:192] = b'768     '  # 256 + 512 for 2 signals
        header[192:236] = b' ' * 44
        header[236:244] = b'1       '
        header[244:252] = b'1       '
        header[252:256] = b'2   '  # 2 signals
        
        # Two signal headers with same label - proper EDF format
        signal_header = bytearray(512)
        offset = 0
        
        # Labels (16 bytes * 2)
        signal_header[offset:offset+16] = b'Flow            '
        signal_header[offset+16:offset+32] = b'Flow            '  # Same label
        offset += 16 * 2
        
        # Transducer types (80 bytes * 2)
        signal_header[offset:offset+80] = b' ' * 80
        signal_header[offset+80:offset+160] = b' ' * 80
        offset += 80 * 2
        
        # Physical dimensions (8 bytes * 2)
        signal_header[offset:offset+8] = b'L/min   '
        signal_header[offset+8:offset+16] = b'L/min   '
        offset += 8 * 2
        
        # Physical min (8 bytes * 2)
        signal_header[offset:offset+8] = b'0       '
        signal_header[offset+8:offset+16] = b'0       '
        offset += 8 * 2
        
        # Physical max (8 bytes * 2)
        signal_header[offset:offset+8] = b'100     '
        signal_header[offset+8:offset+16] = b'100     '
        offset += 8 * 2
        
        # Digital min (8 bytes * 2)
        signal_header[offset:offset+8] = b'-32768  '
        signal_header[offset+8:offset+16] = b'-32768  '
        offset += 8 * 2
        
        # Digital max (8 bytes * 2)
        signal_header[offset:offset+8] = b'32767   '
        signal_header[offset+8:offset+16] = b'32767   '
        offset += 8 * 2
        
        # Prefiltering (80 bytes * 2)
        signal_header[offset:offset+80] = b' ' * 80
        signal_header[offset+80:offset+160] = b' ' * 80
        offset += 80 * 2
        
        # Samples per record (8 bytes * 2)
        signal_header[offset:offset+8] = b'5       '
        signal_header[offset+8:offset+16] = b'5       '
        offset += 8 * 2
        
        # Reserved (32 bytes * 2)
        signal_header[offset:offset+32] = b' ' * 32
        signal_header[offset+32:offset+64] = b' ' * 32
        
        # Data
        data = bytearray(20)  # 2 signals * 5 samples * 2 bytes
        
        filepath = temp_dir / "duplicate_labels.edf"
        filepath.write_bytes(header + signal_header + data)
        
        parser = EDFParser(str(filepath))
        parser.parse()
        
        # Get first Flow signal
        signal0 = parser.get_signal("Flow", 0)
        assert signal0 is not None
        
        # Get second Flow signal
        signal1 = parser.get_signal("Flow", 1)
        assert signal1 is not None
        
        # Try to get third (doesn't exist)
        signal2 = parser.get_signal("Flow", 2)
        assert signal2 is None


class TestIdentificationEdgeCases:
    """Edge case tests for identification parser"""
    
    def test_tgt_with_unicode_characters(self, temp_dir):
        """Test parsing TGT with unicode characters"""
        content = "#SRN 12345678\n#PNA AirSense™ 10\n#PCD 37207\n"
        filepath = temp_dir / "Identification.tgt"
        filepath.write_text(content, encoding='utf-8')
        
        parser = IdentificationParser(str(temp_dir))
        info = parser.parse()
        
        assert info is not None
        assert info.serial == "12345678"
    
    def test_json_with_nested_empty_objects(self, temp_dir):
        """Test parsing JSON with nested empty objects"""
        import json
        data = {
            "FlowGenerator": {
                "IdentificationProfiles": {}
            }
        }
        filepath = temp_dir / "Identification.json"
        filepath.write_text(json.dumps(data))
        
        parser = IdentificationParser(str(temp_dir))
        info = parser.parse()
        assert info is None  # Should return None when no product info


class TestSessionSplitting:
    """Tests for session splitting logic"""
    
    def test_session_spanning_multiple_days(self):
        """Test session that spans multiple calendar days"""
        # Start at 10 PM Dec 15
        dt1 = datetime(2024, 12, 15, 22, 0, 0)
        # Continue at 1 AM Dec 16
        dt2 = datetime(2024, 12, 16, 1, 0, 0)
        # Continue at 6 AM Dec 16
        dt3 = datetime(2024, 12, 16, 6, 0, 0)
        # Continue at 11 AM Dec 16 (still before noon)
        dt4 = datetime(2024, 12, 16, 11, 0, 0)
        
        timestamps = [int(dt.timestamp()) for dt in [dt1, dt2, dt3, dt4]]
        
        result = split_sessions_by_noon(timestamps)
        # All should belong to Dec 15 session (before noon on Dec 16)
        assert len(result) == 1
        assert result[0][0] == date(2024, 12, 15)
        assert len(result[0][1]) == 4
    
    def test_back_to_back_sessions(self):
        """Test consecutive sessions on different days"""
        # Session 1: Dec 15, 11 PM
        dt1 = datetime(2024, 12, 15, 23, 0, 0)
        # Session 1 ends: Dec 16, 8 AM
        dt2 = datetime(2024, 12, 16, 8, 0, 0)
        # Session 2 starts: Dec 16, 1 PM
        dt3 = datetime(2024, 12, 16, 13, 0, 0)
        # Session 2 continues: Dec 16, 3 PM
        dt4 = datetime(2024, 12, 16, 15, 0, 0)
        
        timestamps = [int(dt.timestamp()) for dt in [dt1, dt2, dt3, dt4]]
        
        result = split_sessions_by_noon(timestamps)
        # Should be 2 sessions
        assert len(result) == 2
        assert result[0][0] == date(2024, 12, 15)
        assert result[1][0] == date(2024, 12, 16)


class TestLoaderEdgeCases:
    """Edge case tests for CPAPLoader"""
    
    def test_load_all_with_minimal_data(self, temp_dir):
        """Test loading when only identification exists"""
        # Create minimal identification
        content = "#SRN 12345678\n#PNA AirSense 10\n"
        (temp_dir / "Identification.tgt").write_text(content)
        
        loader = CPAPLoader(str(temp_dir))
        data = loader.load_all()
        
        assert data.machine_info is not None
        assert data.machine_info.serial == "12345678"
        assert data.summary_records == []
        assert data.sessions == []
        assert data.settings_changes == []
    
    def test_load_all_with_empty_directories(self, temp_dir):
        """Test loading with empty DATALOG and SETTINGS directories"""
        # Create identification
        content = "#SRN 12345678\n#PNA AirSense 10\n"
        (temp_dir / "Identification.tgt").write_text(content)
        
        # Create empty directories
        (temp_dir / "DATALOG").mkdir()
        (temp_dir / "SETTINGS").mkdir()
        
        loader = CPAPLoader(str(temp_dir))
        data = loader.load_all()
        
        assert data.machine_info is not None
        assert data.sessions == []
        assert data.settings_changes == []


class TestSTRParserModes:
    """Tests for STR parser mode mapping"""
    
    def test_mode_mapping(self):
        """Test ResMed mode to standard mode mapping"""
        parser = STRParser.__new__(STRParser)  # Create instance without __init__
        
        assert parser._map_mode(0) == STRParser.MODE_CPAP
        assert parser._map_mode(1) == STRParser.MODE_APAP
        assert parser._map_mode(2) == STRParser.MODE_BILEVEL_FIXED
        assert parser._map_mode(6) == STRParser.MODE_BILEVEL_AUTO_FIXED_PS
        assert parser._map_mode(7) == STRParser.MODE_ASV
        assert parser._map_mode(11) == STRParser.MODE_APAP
        assert parser._map_mode(999) == STRParser.MODE_UNKNOWN


class TestUtilsEdgeCases:
    """Edge case tests for utility functions"""
    
    def test_minutes_since_noon_across_dst(self):
        """Test minutes since noon calculation"""
        from cpap_py.utils import minutes_since_noon
        
        # Test at exactly 11:59:00 AM (1 minute before noon)
        dt = datetime(2024, 12, 15, 11, 59, 0)
        result = minutes_since_noon(dt)
        assert result == -1  # Should be -1 minute
    
    def test_format_duration_very_long(self):
        """Test formatting very long duration"""
        from cpap_py.utils import format_duration
        
        # 100 hours
        result = format_duration(360000)
        assert result == "100:00:00"
    
    def test_downsample_signal_empty(self):
        """Test downsampling empty signal"""
        from cpap_py.utils import downsample_signal
        
        result = downsample_signal([], 2)
        assert result == []
    
    def test_calculate_percentile_single_value(self):
        """Test percentile with single value"""
        from cpap_py.utils import calculate_percentile
        
        result = calculate_percentile([5.0], 50)
        assert result == 5.0
    
    def test_calculate_percentile_boundary(self):
        """Test percentile at boundaries"""
        from cpap_py.utils import calculate_percentile
        
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        
        # 0th percentile should be minimum
        result = calculate_percentile(data, 0)
        assert result == 1.0
        
        # 100th percentile should be maximum
        result = calculate_percentile(data, 100)
        assert result == 5.0


class TestCPAPDataPostInit:
    """Test CPAPData post-initialization"""
    
    def test_cpap_data_none_values(self):
        """Test that None values are converted to empty lists"""
        from cpap_py.loader import CPAPData
        
        # Create with all None
        data = CPAPData(
            machine_info=None,
            summary_records=None,
            sessions=None,
            settings_changes=None
        )
        
        # Post-init should convert None to empty lists
        assert data.summary_records == []
        assert data.sessions == []
        assert data.settings_changes == []


class TestDatalogParserSignalAliases:
    """Test signal alias resolution in datalog parser"""
    
    def test_find_signal_with_alias(self, sample_edf_file):
        """Test finding signal using alias"""
        from cpap_py.datalog_parser import DatalogParser
        
        parser_instance = DatalogParser("/tmp")
        edf = EDFParser(str(sample_edf_file))
        edf.parse()
        
        # Try to find Flow signal
        signal = parser_instance._find_signal(edf, "Flow")
        assert signal is not None
        assert signal.label == "Flow"
    
    def test_find_nonexistent_signal(self, sample_edf_file):
        """Test finding signal that doesn't exist"""
        from cpap_py.datalog_parser import DatalogParser
        
        parser_instance = DatalogParser("/tmp")
        edf = EDFParser(str(sample_edf_file))
        edf.parse()
        
        signal = parser_instance._find_signal(edf, "NonExistent")
        assert signal is None
