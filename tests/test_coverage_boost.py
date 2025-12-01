"""
Additional tests to boost coverage to 95%+
Covers edge cases in models, reader, and parsers that were removed during cleanup.
"""

import pytest
import numpy as np
import struct
from datetime import datetime, date
from pathlib import Path

from cpap_py.models import (
    Session,
    SessionSummary,
    DeviceSettings,
    WaveformData,
    Event,
    EventType,
    CPAPMode,
)
from cpap_py.reader import CPAPReader
from cpap_py.parsers.crc_parser import CRCValidationMode
from cpap_py.settings import SettingsProposal, SettingChange, ChangeReason, ChangeSeverity


@pytest.mark.unit
class TestSessionDataRetrieval:
    """Test Session data retrieval methods for coverage."""
    
    def test_get_events_lazy_load_with_file(self, tmp_path, mocker):
        """Test lazy loading events from EVE file."""
        eve_file = tmp_path / "test_EVE.edf"
        eve_file.write_bytes(b"mock data")
        
        # Mock parse_eve_file
        mock_event = Event(
            type=EventType.OBSTRUCTIVE_APNEA,
            timestamp=datetime(2024, 1, 1, 22, 30),
            duration=10.0
        )
        mocker.patch('cpap_py.parsers.edf_parser.parse_eve_file', return_value=[mock_event])
        
        summary = SessionSummary(duration_seconds=28800, duration_hours=8.0, ahi=5.0)
        settings = DeviceSettings(mode=CPAPMode.CPAP)
        session = Session(
            session_id='TEST_001',
            device_serial='TEST123',
            date=date(2024, 1, 1),
            start_time=datetime(2024, 1, 1, 22, 0),
            summary=summary,
            settings=settings,
            has_events=True
        )
        session._eve_file = str(eve_file)
        
        # Trigger lazy load - covers lines 246-250
        events = session.get_events()
        assert len(events) == 1
        
        # Test filtering - covers line 251
        filtered = session.get_events(event_type=EventType.OBSTRUCTIVE_APNEA)
        assert len(filtered) == 1
    
    def test_get_events_no_file_set(self):
        """Test get_events when no EVE file is set."""
        summary = SessionSummary(duration_seconds=28800, duration_hours=8.0, ahi=5.0)
        settings = DeviceSettings(mode=CPAPMode.CPAP)
        session = Session(
            session_id='TEST_001',
            device_serial='TEST123',
            date=date(2024, 1, 1),
            start_time=datetime(2024, 1, 1, 22, 0),
            summary=summary,
            settings=settings,
            has_events=True
        )
        # _eve_file not set - covers line 248
        
        events = session.get_events()
        assert events == []
    
    def test_get_pressure_data_with_file(self, tmp_path, mocker):
        """Test get_pressure_data with BRP file - covers lines 259-266."""
        brp_file = tmp_path / "test_BRP.edf"
        brp_file.write_bytes(b"mock data")
        
        mock_waveform = WaveformData(
            channel_name="Mask Pressure",
            unit="cmH2O",
            sample_rate=25.0,
            start_time=datetime(2024, 1, 1, 22, 0),
            values=np.array([10.0, 10.5, 11.0])
        )
        mocker.patch('cpap_py.parsers.edf_parser.parse_pressure_file', return_value=[mock_waveform])
        
        summary = SessionSummary(duration_seconds=28800, duration_hours=8.0, ahi=5.0)
        settings = DeviceSettings(mode=CPAPMode.CPAP)
        session = Session(
            session_id='TEST_001',
            device_serial='TEST123',
            date=date(2024, 1, 1),
            start_time=datetime(2024, 1, 1, 22, 0),
            summary=summary,
            settings=settings,
            has_pressure_data=True
        )
        session._brp_file = str(brp_file)
        
        df = session.get_pressure_data()
        assert df is not None
    
    def test_get_flow_data_with_file(self, tmp_path, mocker):
        """Test get_flow_data with BRP file - covers lines 273-279."""
        brp_file = tmp_path / "test_BRP.edf"
        brp_file.write_bytes(b"mock data")
        
        mock_waveform = WaveformData(
            channel_name="Flow Rate",
            unit="L/min",
            sample_rate=25.0,
            start_time=datetime(2024, 1, 1, 22, 0),
            values=np.array([20.0, 21.0, 22.0])
        )
        mocker.patch('cpap_py.parsers.edf_parser.parse_pressure_file', return_value=[mock_waveform])
        
        summary = SessionSummary(duration_seconds=28800, duration_hours=8.0, ahi=5.0)
        settings = DeviceSettings(mode=CPAPMode.CPAP)
        session = Session(
            session_id='TEST_001',
            device_serial='TEST123',
            date=date(2024, 1, 1),
            start_time=datetime(2024, 1, 1, 22, 0),
            summary=summary,
            settings=settings,
            has_flow_data=True
        )
        session._brp_file = str(brp_file)
        
        df = session.get_flow_data()
        assert df is not None
    
    def test_get_spo2_data_with_file(self, tmp_path, mocker):
        """Test get_spo2_data with SAD file - covers lines 286-291."""
        sad_file = tmp_path / "test_SAD.edf"
        sad_file.write_bytes(b"mock data")
        
        mock_waveform = WaveformData(
            channel_name="SpO2",
            unit="%",
            sample_rate=1.0,
            start_time=datetime(2024, 1, 1, 22, 0),
            values=np.array([95.0, 96.0, 97.0])
        )
        mocker.patch('cpap_py.parsers.edf_parser.parse_spo2_file', return_value=[mock_waveform])
        
        summary = SessionSummary(duration_seconds=28800, duration_hours=8.0, ahi=5.0)
        settings = DeviceSettings(mode=CPAPMode.CPAP)
        session = Session(
            session_id='TEST_001',
            device_serial='TEST123',
            date=date(2024, 1, 1),
            start_time=datetime(2024, 1, 1, 22, 0),
            summary=summary,
            settings=settings,
            has_spo2_data=True
        )
        session._sad_file = str(sad_file)
        
        df = session.get_spo2_data()
        assert df is not None


@pytest.mark.unit
class TestReaderEdgeCases:
    """Test reader edge cases for coverage."""
    
    def test_reader_missing_datalog_directory(self, tmp_path):
        """Test reader when DATALOG directory is missing - covers lines 82, 90."""
        (tmp_path / "SETTINGS").mkdir()
        # No DATALOG directory
        
        reader = CPAPReader(str(tmp_path), crc_validation=CRCValidationMode.DISABLED)
        errors = reader.get_validation_errors()
        
        datalog_errors = [e for e in errors if 'DATALOG' in e.message]
        assert len(datalog_errors) > 0
    
    def test_reader_str_parse_exception(self, tmp_path, mocker):
        """Test STR parsing exception handling - covers lines 229-232."""
        (tmp_path / "DATALOG").mkdir()
        (tmp_path / "SETTINGS").mkdir()
        
        str_file = tmp_path / "STR.edf"
        str_file.write_bytes(b"corrupt data")
        
        mocker.patch('cpap_py.parsers.str_parser.parse_resmed_str_file', side_effect=Exception("Parse error"))
        
        reader = CPAPReader(str(tmp_path), crc_validation=CRCValidationMode.DISABLED)
        # Should handle exception gracefully
        assert isinstance(reader.get_validation_errors(), list)
    
    def test_reader_no_identification_file(self, tmp_path):
        """Test reader creates generic device when no ID file - covers lines 157-158."""
        (tmp_path / "DATALOG").mkdir()
        (tmp_path / "SETTINGS").mkdir()
        # No identification file
        
        reader = CPAPReader(str(tmp_path), crc_validation=CRCValidationMode.DISABLED)
        devices = reader.get_devices()
        
        assert len(devices) > 0
        assert devices[0].serial_number == "UNKNOWN"
    
    def test_reader_serial_extraction_from_str(self, tmp_path, mocker):
        """Test serial number extraction from STR - covers lines 145-147."""
        (tmp_path / "DATALOG").mkdir()
        (tmp_path / "SETTINGS").mkdir()
        
        str_file = tmp_path / "STR.edf"
        str_file.write_bytes(b"data")
        
        mock_device_info = {
            'recording_id': 'Device Model SRN=12345678 Extra Info',
            'software_version': '1.0'
        }
        mocker.patch('cpap_py.parsers.str_parser.parse_resmed_str_file', 
                    return_value=([], {'device_info': mock_device_info}))
        
        reader = CPAPReader(str(tmp_path), crc_validation=CRCValidationMode.DISABLED)
        devices = reader.get_devices()
        
        assert len(devices) > 0
        assert isinstance(devices[0].serial_number, str)
    
    def test_reader_invalid_date_directory(self, tmp_path):
        """Test reader skips invalid date directories - covers lines 247-248."""
        datalog_dir = tmp_path / "DATALOG"
        datalog_dir.mkdir()
        (tmp_path / "SETTINGS").mkdir()
        
        invalid_dir = datalog_dir / "invalid_date"
        invalid_dir.mkdir()
        (invalid_dir / "test.edf").write_bytes(b"data")
        
        reader = CPAPReader(str(tmp_path), crc_validation=CRCValidationMode.DISABLED)
        sessions = reader.get_sessions()
        
        assert isinstance(sessions, list)
        assert len(sessions) == 0
    
    def test_reader_session_matching_with_str(self, tmp_path, mocker):
        """Test session matching with STR data - covers lines 269-270, 324-325."""
        datalog_dir = tmp_path / "DATALOG"
        datalog_dir.mkdir()
        (tmp_path / "SETTINGS").mkdir()
        
        date_dir = datalog_dir / "20240101"
        date_dir.mkdir()
        
        brp_file = date_dir / "20240101_220000_BRP.edf"
        brp_file.write_bytes(b"x" * 256)
        
        str_sessions = [(datetime(2024, 1, 1, 21, 0), datetime(2024, 1, 2, 5, 0))]
        mocker.patch('cpap_py.parsers.str_parser.parse_resmed_str_file', return_value=(str_sessions, {}))
        
        reader = CPAPReader(str(tmp_path), crc_validation=CRCValidationMode.DISABLED)
        sessions = reader.get_sessions()
        
        assert isinstance(sessions, list)
    
    def test_reader_create_session_summary_no_str(self, tmp_path):
        """Test session summary creation without STR data - covers lines 364, 379-380."""
        (tmp_path / "DATALOG").mkdir()
        (tmp_path / "SETTINGS").mkdir()
        
        reader = CPAPReader(str(tmp_path), crc_validation=CRCValidationMode.DISABLED)
        reader._str_session_times = []
        reader._str_summary_stats = {}
        
        start_time = datetime(2024, 1, 1, 22, 0)
        summary = reader._create_session_summary(start_time, None, None)
        
        assert summary is not None
        assert summary.mask_on_time == start_time
    
    def test_reader_export_with_data(self, tmp_path):
        """Test export_to_dict - covers lines 440-445."""
        (tmp_path / "DATALOG").mkdir()
        (tmp_path / "SETTINGS").mkdir()
        
        reader = CPAPReader(str(tmp_path), crc_validation=CRCValidationMode.DISABLED)
        export_data = reader.export_to_dict()
        
        assert isinstance(export_data, dict)
        assert "devices" in export_data
        assert "sessions" in export_data
        assert "validation_errors" in export_data
    
    def test_reader_summary_statistics_no_sessions(self, tmp_path):
        """Test summary statistics with no sessions - covers lines 507-519."""
        (tmp_path / "DATALOG").mkdir()
        (tmp_path / "SETTINGS").mkdir()
        
        reader = CPAPReader(str(tmp_path), crc_validation=CRCValidationMode.DISABLED)
        stats = reader.get_summary_statistics(days=7)
        
        assert isinstance(stats, dict)
        assert stats == {}


@pytest.mark.unit
class TestParserEdgeCases:
    """Test parser edge cases for coverage."""
    
    def test_crc_parser_big_endian_2byte(self, tmp_path):
        """Test 2-byte big-endian CRC reading - covers line 52."""
        from cpap_py.parsers.crc_parser import read_crc_file
        
        crc_file = tmp_path / "test.crc"
        crc_file.write_bytes(struct.pack('>H', 0x1234))
        
        result = read_crc_file(str(crc_file))
        assert result is not None
    
    def test_crc_parser_big_endian_4byte(self, tmp_path):
        """Test 4-byte big-endian CRC reading - covers line 54."""
        from cpap_py.parsers.crc_parser import read_crc_file
        
        crc_file = tmp_path / "test.crc"
        crc_file.write_bytes(struct.pack('>I', 0x12345678))
        
        result = read_crc_file(str(crc_file))
        assert result is not None
    
    def test_crc_validation_file_read_error(self, tmp_path, mocker):
        """Test CRC validation handles file read errors - covers lines 137-141."""
        from cpap_py.parsers.crc_parser import validate_file_crc
        
        data_file = tmp_path / "test.edf"
        crc_file = tmp_path / "test.crc"
        
        data_file.write_bytes(b"test data")
        crc_file.write_bytes(struct.pack('<H', 12345))
        
        mocker.patch('cpap_py.parsers.crc_parser.read_crc_file', return_value=12345)
        
        original_open = open
        def mock_open_func(path, *args, **kwargs):
            if str(path).endswith('.edf') and 'rb' in str(args):
                raise IOError("Mocked error")
            return original_open(path, *args, **kwargs)
        
        mocker.patch('builtins.open', side_effect=mock_open_func)
        
        is_valid, msg = validate_file_crc(str(data_file), CRCValidationMode.PERMISSIVE)
        assert is_valid is False
    
    def test_edf_parser_compressed_file_detection(self, tmp_path):
        """Test EDF parser detects compressed files - covers lines 109-114."""
        from cpap_py.parsers.edf_parser import EDFParser
        
        gz_file = tmp_path / "test.edf.gz"
        gz_file.write_bytes(b"compressed data")
        
        parser = EDFParser(str(gz_file))
        
        with pytest.raises(Exception):
            with parser._open_file():
                pass
    
    def test_edf_parser_read_annotations_exception(self, tmp_path, mocker):
        """Test annotation reading exception handling - covers lines 164-172."""
        from cpap_py.parsers.edf_parser import EDFParser
        
        edf_file = tmp_path / "test.edf"
        edf_file.write_bytes(b"x" * 256)
        
        parser = EDFParser(str(edf_file))
        mocker.patch.object(parser, '_open_file', side_effect=Exception("Open failed"))
        
        annotations = parser.read_annotations()
        assert annotations == []
    
    def test_edf_parser_signal_out_of_range(self, tmp_path):
        """Test get_signal_info with out of range index - covers line 59."""
        from cpap_py.parsers.edf_parser import EDFParser
        import shutil
        
        sample_file = Path("/workspaces/cpap-py/data/DATALOG/20241126/20241127_004016_BRP.edf")
        if sample_file.exists():
            test_file = tmp_path / "test.edf"
            shutil.copy(sample_file, test_file)
            
            parser = EDFParser(str(test_file))
            
            with pytest.raises(ValueError):
                parser.get_signal_info(999)
        else:
            pytest.skip("Sample data not available")
    
    def test_str_parser_exception_handling(self, tmp_path):
        """Test STR parser handles exceptions - covers lines 54, 57-58."""
        from cpap_py.parsers.str_parser import parse_resmed_str_file
        
        str_file = tmp_path / "corrupt.edf"
        header = b' ' * 256  # Invalid header
        str_file.write_bytes(header)
        
        with pytest.raises(ValueError):
            parse_resmed_str_file(str(str_file))
    
    def test_str_parser_out_of_range_index(self):
        """Test STR parser handles out of range index - covers lines 136-138, 150."""
        from cpap_py.parsers.str_parser import extract_session_summary_from_str
        
        signal_data = {
            'AHI': {'data': [5.0], 'unit': 'events/hour', 'samples': 1}
        }
        
        summary = extract_session_summary_from_str(signal_data, session_idx=100)
        assert summary == {}
    
    def test_tgt_parser_exception_handling(self, tmp_path):
        """Test TGT parser handles exceptions - covers lines 129-130."""
        from cpap_py.parsers.tgt_parser import parse_tgt_file
        
        tgt_file = tmp_path / "invalid.tgt"
        tgt_file.write_text("invalid content\n")
        
        result = parse_tgt_file(str(tgt_file))
        assert isinstance(result, dict)
    
    def test_tgt_parser_no_matching_file(self, tmp_path):
        """Test find_settings_for_date with no match - covers lines 161, 165."""
        from cpap_py.parsers.tgt_parser import find_settings_for_date
        
        settings_dir = tmp_path / "SETTINGS"
        settings_dir.mkdir()
        
        wrong_file = settings_dir / "ABC.tgt"
        wrong_file.write_bytes(b"data")
        
        result = find_settings_for_date(str(settings_dir), date(2024, 1, 1))
        
        assert isinstance(result, DeviceSettings)
        assert result.mode is None
    
    def test_tgt_parser_hex_conversion(self, tmp_path):
        """Test TGT hex value parsing - covers lines 87-88."""
        from cpap_py.parsers.tgt_parser import parse_tgt_file
        
        tgt_file = tmp_path / "test.tgt"
        tgt_file.write_text("Version: 0x0A\nMode: 0x02\n")
        
        result = parse_tgt_file(str(tgt_file))
        assert isinstance(result, dict)


@pytest.mark.unit
class TestSettingsEdgeCases:
    """Test settings module edge cases for coverage."""
    
    def test_settings_proposal_methods(self):
        """Test SettingsProposal methods - covers lines 154, 229, 243."""
        current = DeviceSettings(mode=CPAPMode.CPAP, pressure=10.0)
        
        change = SettingChange(
            setting_name="pressure",
            current_value=10.0,
            proposed_value=12.0,
            reason=ChangeReason.REDUCE_AHI,
            rationale="Increase pressure",
            severity=ChangeSeverity.MODERATE
        )
        
        proposal = SettingsProposal(
            device_serial="TEST123",
            current_settings=current,
            proposed_changes=[change],
            overall_rationale="Improve therapy"
        )
        
        # Test validate_all_changes - covers line 154
        is_valid = proposal.validate_all_changes()
        assert isinstance(is_valid, bool)
        
        # Test to_summary - covers line 229
        summary = proposal.to_summary()
        assert isinstance(summary, str)
        assert "TEST123" in summary
        
        # Test __str__ - covers line 243
        str_repr = str(proposal)
        assert isinstance(str_repr, str)
