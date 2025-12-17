"""
Tests for edf_parser.py module
"""

import pytest
import struct
import gzip
from pathlib import Path
from datetime import datetime
from cpap_py.edf_parser import EDFParser, EDFHeader, EDFSignal, Annotation


class TestEDFHeader:
    """Tests for EDFHeader dataclass"""
    
    def test_edf_header_defaults(self):
        """Test EDFHeader default values"""
        header = EDFHeader()
        assert header.version == 0
        assert header.patient_ident == ""
        assert header.recording_ident == ""
        assert header.start_date is None
        assert header.num_header_bytes == 0
        assert header.reserved == ""
        assert header.num_data_records == 0
        assert header.duration_seconds == 0.0
        assert header.num_signals == 0
    
    def test_edf_header_initialization(self):
        """Test EDFHeader with custom values"""
        dt = datetime(2024, 12, 15, 12, 30, 0)
        header = EDFHeader(
            version=0,
            patient_ident="Test Patient",
            recording_ident="Test Recording",
            start_date=dt,
            num_header_bytes=512,
            num_data_records=100,
            duration_seconds=1.0,
            num_signals=2
        )
        assert header.version == 0
        assert header.patient_ident == "Test Patient"
        assert header.start_date == dt
        assert header.num_signals == 2


class TestEDFSignal:
    """Tests for EDFSignal dataclass"""
    
    def test_edf_signal_defaults(self):
        """Test EDFSignal default values"""
        signal = EDFSignal()
        assert signal.label == ""
        assert signal.transducer_type == ""
        assert signal.physical_dimension == ""
        assert signal.physical_minimum == 0.0
        assert signal.physical_maximum == 0.0
        assert signal.digital_minimum == 0
        assert signal.digital_maximum == 0
        assert signal.gain == 1.0
        assert signal.offset == 0.0
        assert signal.prefiltering == ""
        assert signal.sample_count == 0
        assert signal.reserved == ""
        assert signal.data == []
    
    def test_edf_signal_gain_offset_calculation(self):
        """Test automatic gain and offset calculation"""
        signal = EDFSignal(
            physical_minimum=-100.0,
            physical_maximum=100.0,
            digital_minimum=-32768,
            digital_maximum=32767
        )
        # gain = (100 - (-100)) / (32767 - (-32768)) = 200 / 65535
        expected_gain = 200.0 / 65535.0
        # offset = 100 - gain * 32767
        expected_offset = 100.0 - expected_gain * 32767
        
        assert abs(signal.gain - expected_gain) < 1e-6
        assert abs(signal.offset - expected_offset) < 1e-6
    
    def test_edf_signal_zero_range(self):
        """Test signal with zero digital range"""
        signal = EDFSignal(
            physical_minimum=0.0,
            physical_maximum=100.0,
            digital_minimum=0,
            digital_maximum=0
        )
        # Should not divide by zero
        assert signal.gain == 1.0
        assert signal.offset == 0.0


class TestAnnotation:
    """Tests for Annotation dataclass"""
    
    def test_annotation_defaults(self):
        """Test Annotation default values"""
        anno = Annotation()
        assert anno.offset == 0.0
        assert anno.duration == -1.0
        assert anno.text == ""
    
    def test_annotation_initialization(self):
        """Test Annotation with custom values"""
        anno = Annotation(offset=10.5, duration=2.0, text="Test Event")
        assert anno.offset == 10.5
        assert anno.duration == 2.0
        assert anno.text == "Test Event"


class TestEDFParser:
    """Tests for EDFParser"""
    
    def test_parser_initialization(self, temp_dir):
        """Test parser initialization"""
        filepath = temp_dir / "test.edf"
        parser = EDFParser(str(filepath))
        assert parser.filepath == filepath
        assert parser.header.version == 0
        assert parser.signals == []
        assert parser.annotations == []
        assert parser._data is None
    
    def test_open_regular_edf(self, sample_edf_file):
        """Test opening regular EDF file"""
        parser = EDFParser(str(sample_edf_file))
        assert parser.open() is True
        assert parser._data is not None
        assert len(parser._data) >= 256
    
    def test_open_gzipped_edf(self, temp_dir):
        """Test opening gzipped EDF file"""
        # Create a simple EDF and compress it
        edf_data = b'0       ' + b' ' * 248
        gz_path = temp_dir / "test.edf.gz"
        with gzip.open(gz_path, 'wb') as f:
            f.write(edf_data)
        
        parser = EDFParser(str(gz_path))
        assert parser.open() is True
        assert parser._data == edf_data
    
    def test_open_nonexistent_file(self, temp_dir):
        """Test opening nonexistent file"""
        parser = EDFParser(str(temp_dir / "nonexistent.edf"))
        assert parser.open() is False
    
    def test_open_too_short_file(self, temp_dir):
        """Test opening file that's too short"""
        filepath = temp_dir / "short.edf"
        filepath.write_bytes(b'short')
        
        parser = EDFParser(str(filepath))
        assert parser.open() is False
    
    def test_parse_header(self, sample_edf_file):
        """Test parsing EDF header"""
        parser = EDFParser(str(sample_edf_file))
        assert parser.open() is True
        assert parser.parse_header() is True
        
        assert parser.header.version == 0
        assert parser.header.num_signals == 2
        assert parser.header.num_data_records == 1
        assert parser.header.duration_seconds == 1.0
        assert parser.header.num_header_bytes == 768
    
    def test_parse_header_without_open(self):
        """Test parsing header without opening file first"""
        parser = EDFParser("/nonexistent/file.edf")
        assert parser.parse_header() is False
    
    def test_parse_date_2000s(self, sample_edf_file):
        """Test parsing date in 2000s"""
        parser = EDFParser(str(sample_edf_file))
        parser.open()
        parser.parse_header()
        
        # Date should be parsed correctly (15.12.24 -> 2024)
        assert parser.header.start_date is not None
        assert parser.header.start_date.year == 2024
        assert parser.header.start_date.month == 12
        assert parser.header.start_date.day == 15
        assert parser.header.start_date.hour == 12
        assert parser.header.start_date.minute == 30
        assert parser.header.start_date.second == 0
    
    def test_parse_date_1900s(self, temp_dir):
        """Test parsing date in 1900s (year >= 85)"""
        # Create EDF with date in 1999
        header = bytearray(256)
        header[0:8] = b'0       '
        header[8:88] = b' ' * 80
        header[88:168] = b' ' * 80
        header[168:184] = b'15.12.9912.30.00'  # 99 -> 1999
        header[184:192] = b'256     '
        header[192:236] = b' ' * 44
        header[236:244] = b'0       '
        header[244:252] = b'1       '
        header[252:256] = b'0   '
        
        filepath = temp_dir / "old.edf"
        filepath.write_bytes(header)
        
        parser = EDFParser(str(filepath))
        parser.open()
        parser.parse_header()
        
        assert parser.header.start_date.year == 1999
    
    def test_parse_signal_headers(self, sample_edf_file):
        """Test parsing signal headers"""
        parser = EDFParser(str(sample_edf_file))
        parser.open()
        parser.parse_header()
        assert parser.parse_signal_headers() is True
        
        assert len(parser.signals) == 2
        
        # Check first signal (Flow)
        assert parser.signals[0].label == "Flow"
        assert parser.signals[0].physical_dimension == "L/min"
        assert parser.signals[0].physical_minimum == -100.0
        assert parser.signals[0].physical_maximum == 100.0
        assert parser.signals[0].digital_minimum == -32768
        assert parser.signals[0].digital_maximum == 32767
        assert parser.signals[0].sample_count == 25
        
        # Check second signal (Pressure)
        assert parser.signals[1].label == "Pressure"
        assert parser.signals[1].physical_dimension == "cmH2O"
        assert parser.signals[1].physical_minimum == 0.0
        assert parser.signals[1].physical_maximum == 30.0
    
    def test_parse_signal_headers_without_parse_header(self, sample_edf_file):
        """Test parsing signal headers without parsing main header first"""
        parser = EDFParser(str(sample_edf_file))
        parser.open()
        assert parser.parse_signal_headers() is False
    
    def test_parse_data(self, sample_edf_file):
        """Test parsing signal data"""
        parser = EDFParser(str(sample_edf_file))
        parser.open()
        parser.parse_header()
        parser.parse_signal_headers()
        assert parser.parse_data() is True
        
        # Check data was read
        assert len(parser.signals[0].data) == 25  # 1 record * 25 samples
        assert len(parser.signals[1].data) == 25
        
        # Check some data values
        assert parser.signals[0].data[0] == 0
        assert parser.signals[1].data[0] == 10000
    
    def test_parse_full(self, sample_edf_file):
        """Test full parse method"""
        parser = EDFParser(str(sample_edf_file))
        assert parser.parse() is True
        
        assert parser.header.num_signals == 2
        assert len(parser.signals) == 2
        assert len(parser.signals[0].data) > 0
    
    def test_get_signal_by_label(self, sample_edf_file):
        """Test getting signal by label"""
        parser = EDFParser(str(sample_edf_file))
        parser.parse()
        
        flow_signal = parser.get_signal("Flow")
        assert flow_signal is not None
        assert flow_signal.label == "Flow"
        
        pressure_signal = parser.get_signal("Pressure")
        assert pressure_signal is not None
        assert pressure_signal.label == "Pressure"
        
        nonexistent = parser.get_signal("NonExistent")
        assert nonexistent is None
    
    def test_get_signal_with_index(self, sample_edf_file):
        """Test getting signal by label with index"""
        parser = EDFParser(str(sample_edf_file))
        parser.parse()
        
        # Get first Flow signal (index 0)
        signal = parser.get_signal("Flow", 0)
        assert signal is not None
        
        # Try to get second Flow signal (doesn't exist)
        signal = parser.get_signal("Flow", 1)
        assert signal is None
    
    def test_get_physical_values(self, sample_edf_file):
        """Test converting digital to physical values"""
        parser = EDFParser(str(sample_edf_file))
        parser.parse()
        
        flow_signal = parser.get_signal("Flow")
        physical_values = parser.get_physical_values(flow_signal)
        
        assert len(physical_values) == len(flow_signal.data)
        
        # Check conversion formula: physical = digital * gain + offset
        for i, digital in enumerate(flow_signal.data):
            expected = digital * flow_signal.gain + flow_signal.offset
            assert abs(physical_values[i] - expected) < 1e-6
    
    def test_parse_corrupted_header(self, temp_dir):
        """Test parsing corrupted header"""
        # Create file with invalid data
        header = bytearray(256)
        header[0:8] = b'INVALID '
        
        filepath = temp_dir / "corrupt.edf"
        filepath.write_bytes(header)
        
        parser = EDFParser(str(filepath))
        parser.open()
        # Should handle gracefully
        result = parser.parse_header()
        # May fail or succeed depending on how forgiving the parser is
        # but should not crash
    
    def test_parse_data_truncated(self, temp_dir):
        """Test parsing data when file is truncated"""
        # Create EDF with header but insufficient data
        header = bytearray(256)
        header[0:8] = b'0       '
        header[8:88] = b' ' * 80
        header[88:168] = b' ' * 80
        header[168:184] = b'15.12.2412.30.00'
        header[184:192] = b'512     '  # Header size for 1 signal
        header[192:236] = b' ' * 44
        header[236:244] = b'10      '  # 10 data records
        header[244:252] = b'1       '
        header[252:256] = b'1   '
        
        # Signal header
        signal_header = bytearray(256)
        signal_header[0:16] = b'Test            '
        signal_header[96:104] = b'unit    '
        signal_header[104:112] = b'0       '
        signal_header[112:120] = b'100     '
        signal_header[120:128] = b'-32768  '
        signal_header[128:136] = b'32767   '
        signal_header[216:224] = b'10      '  # 10 samples per record
        
        # Only partial data (not enough for 10 records)
        data = b'\x00\x00' * 5  # Only 5 samples instead of 100
        
        filepath = temp_dir / "truncated.edf"
        filepath.write_bytes(header + signal_header + data)
        
        parser = EDFParser(str(filepath))
        parser.open()
        parser.parse_header()
        parser.parse_signal_headers()
        
        # Should fail gracefully
        assert parser.parse_data() is False
    
    def test_anno_constants(self):
        """Test annotation constants are defined"""
        assert EDFParser.ANNO_SEP == b'\x14'
        assert EDFParser.ANNO_DUR_MARK == b'\x15'
        assert EDFParser.ANNO_END == b'\x00'
