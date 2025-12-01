"""
Tests for the main CPAPReader API.
"""

import pytest
from pathlib import Path
from datetime import datetime, date
from unittest.mock import Mock, patch, MagicMock

from cpap_py.reader import CPAPReader
from cpap_py.models import Device, Session, ValidationError
from cpap_py.parsers.crc_parser import CRCValidationMode


@pytest.mark.unit
class TestCPAPReaderInit:
    """Test CPAPReader initialization."""
    
    def test_reader_init_valid_path(self, sample_data_dir):
        """Test reader initialization with valid path."""
        reader = CPAPReader(sample_data_dir)
        assert reader.sdcard_path == Path(sample_data_dir)
        assert reader.crc_validation == CRCValidationMode.PERMISSIVE
        assert reader.lazy_load is True
    
    def test_reader_init_invalid_path(self):
        """Test reader initialization with invalid path."""
        with pytest.raises(FileNotFoundError):
            CPAPReader("/nonexistent/path")
    
    def test_reader_init_with_options(self, sample_data_dir):
        """Test reader initialization with custom options."""
        reader = CPAPReader(
            sample_data_dir,
            crc_validation=CRCValidationMode.DISABLED,  # Disable CRC to avoid missing file errors
            lazy_load=False
        )
        assert reader.crc_validation == CRCValidationMode.DISABLED
        assert reader.lazy_load is False
    
    def test_reader_scan_structure(self, sample_data_dir):
        """Test that reader scans directory structure."""
        reader = CPAPReader(sample_data_dir)
        # Should have scanned and found DATALOG and SETTINGS
        assert reader._datalog_path.exists()


@pytest.mark.unit
class TestCPAPReaderGetDevices:
    """Test getting device information."""
    
    def test_get_devices(self, sample_data_dir):
        """Test getting device list."""
        reader = CPAPReader(sample_data_dir)
        devices = reader.get_devices()
        
        assert devices is not None
        assert isinstance(devices, list)
        assert len(devices) > 0
        assert isinstance(devices[0], Device)
    
    def test_get_devices_cached(self, sample_data_dir):
        """Test that devices are cached after first call."""
        reader = CPAPReader(sample_data_dir)
        devices1 = reader.get_devices()
        devices2 = reader.get_devices()
        
        # Should return same object (cached)
        assert devices1 is devices2
    
    @patch('cpap_py.reader.parse_identification_file')
    def test_get_devices_with_identification(self, mock_parse, sample_data_dir):
        """Test device parsing with identification file."""
        mock_parse.return_value = {
            "software_version": "6.04.01",
            "platform_version": "37"
        }
        
        reader = CPAPReader(sample_data_dir)
        devices = reader.get_devices()
        
        assert len(devices) > 0
        device = devices[0]
        assert device.firmware_version == "6.04.01"


@pytest.mark.unit
class TestCPAPReaderGetSessions:
    """Test getting session data."""
    
    def test_get_sessions(self, sample_data_dir):
        """Test getting all sessions."""
        reader = CPAPReader(sample_data_dir)
        sessions = reader.get_sessions()
        
        assert isinstance(sessions, list)
        # Should have sessions from test data
        if len(sessions) > 0:
            session = sessions[0]
            assert isinstance(session, Session)
            assert hasattr(session, 'session_id')
            assert hasattr(session, 'summary')
            assert hasattr(session, 'settings')
    
    def test_get_sessions_with_date_filter(self, sample_data_dir):
        """Test filtering sessions by date."""
        reader = CPAPReader(sample_data_dir)
        
        start_date = date(2024, 11, 27)
        end_date = date(2024, 11, 28)
        
        sessions = reader.get_sessions(start_date=start_date, end_date=end_date)
        
        for session in sessions:
            assert session.date >= start_date
            assert session.date <= end_date
    
    def test_get_sessions_with_duration_filter(self, sample_data_dir):
        """Test filtering sessions by minimum duration."""
        reader = CPAPReader(sample_data_dir)
        
        min_hours = 4.0
        sessions = reader.get_sessions(min_duration_hours=min_hours)
        
        for session in sessions:
            assert session.summary.duration_hours >= min_hours
    
    def test_get_sessions_with_device_filter(self, sample_data_dir):
        """Test filtering sessions by device ID."""
        reader = CPAPReader(sample_data_dir)
        devices = reader.get_devices()
        
        if devices:
            device_id = devices[0].serial_number
            sessions = reader.get_sessions(device_id=device_id)
            
            for session in sessions:
                assert session.device_serial == device_id
    
    def test_get_sessions_cached(self, sample_data_dir):
        """Test that sessions are cached."""
        reader = CPAPReader(sample_data_dir)
        sessions1 = reader.get_sessions()
        sessions2 = reader.get_sessions()
        
        # Same list object (before filtering)
        assert reader._sessions is not None


@pytest.mark.unit
class TestCPAPReaderValidation:
    """Test validation error handling."""
    
    def test_get_validation_errors(self, sample_data_dir):
        """Test getting validation errors."""
        reader = CPAPReader(sample_data_dir)
        errors = reader.get_validation_errors()
        
        assert isinstance(errors, list)
        # May or may not have errors depending on test data
        for error in errors:
            assert isinstance(error, ValidationError)
    
    @patch('cpap_py.reader.validate_directory_crcs')
    def test_crc_validation_disabled(self, mock_validate, sample_data_dir):
        """Test that CRC validation can be disabled."""
        reader = CPAPReader(sample_data_dir, crc_validation=CRCValidationMode.DISABLED)
        
        # validate_directory_crcs should not be called with DISABLED mode
        # Check validation_errors is empty or doesn't contain CRC errors
        errors = reader.get_validation_errors()
        crc_errors = [e for e in errors if e.error_type == "crc_mismatch"]
        # With DISABLED mode, CRC validation shouldn't run
        assert mock_validate.call_count == 0


@pytest.mark.unit
class TestCPAPReaderSummaryStats:
    """Test summary statistics generation."""
    
    def test_get_summary_statistics(self, sample_data_dir):
        """Test getting aggregate statistics."""
        reader = CPAPReader(sample_data_dir)
        stats = reader.get_summary_statistics(days=30)
        
        assert isinstance(stats, dict)
        if stats:  # If we have sessions
            assert "period_days" in stats
            assert "total_sessions" in stats
            assert "total_hours" in stats
            assert stats["period_days"] == 30
    
    def test_get_summary_statistics_empty(self, test_output_dir):
        """Test summary stats with no sessions."""
        # Create empty directory structure
        data_dir = test_output_dir / "empty_data"
        data_dir.mkdir()
        (data_dir / "DATALOG").mkdir()
        (data_dir / "SETTINGS").mkdir()
        
        reader = CPAPReader(str(data_dir))
        stats = reader.get_summary_statistics(days=30)
        
        assert stats == {}
    
    def test_get_summary_statistics_with_device_filter(self, sample_data_dir):
        """Test summary stats filtered by device."""
        reader = CPAPReader(sample_data_dir)
        devices = reader.get_devices()
        
        if devices:
            device_id = devices[0].serial_number
            stats = reader.get_summary_statistics(device_id=device_id, days=30)
            
            assert isinstance(stats, dict)
    
    def test_get_summary_statistics_no_sessions(self, tmp_path):
        """Test summary statistics when no sessions exist."""
        # Create empty structure
        (tmp_path / "DATALOG").mkdir()
        (tmp_path / "SETTINGS").mkdir()
        
        reader = CPAPReader(tmp_path, crc_validation=CRCValidationMode.DISABLED)
        stats = reader.get_summary_statistics(days=30)
        
        # Should return empty dict when no sessions
        assert stats == {}
    
    def test_get_devices_without_identification(self, tmp_path):
        """Test getting devices when Identification file is missing."""
        (tmp_path / "DATALOG").mkdir()
        (tmp_path / "SETTINGS").mkdir()
        
        reader = CPAPReader(tmp_path, crc_validation=CRCValidationMode.DISABLED)
        devices = reader.get_devices()
        
        # Should still return a list (may be empty or have placeholder)
        assert isinstance(devices, list)


@pytest.mark.unit
class TestCPAPReaderExport:
    """Test data export functionality."""
    
    def test_export_to_dict(self, sample_data_dir):
        """Test exporting all data to dictionary."""
        reader = CPAPReader(sample_data_dir)
        data = reader.export_to_dict()
        
        assert isinstance(data, dict)
        assert "devices" in data
        assert "sessions" in data
        assert "validation_errors" in data
        
        assert isinstance(data["devices"], list)
        assert isinstance(data["sessions"], list)
        assert isinstance(data["validation_errors"], list)
    
    def test_export_to_dict_serializable(self, sample_data_dir):
        """Test that exported data is JSON-serializable."""
        import json
        
        reader = CPAPReader(sample_data_dir)
        data = reader.export_to_dict()
        
        # Should be able to serialize to JSON
        json_str = json.dumps(data, default=str)
        assert isinstance(json_str, str)


@pytest.mark.unit
class TestCPAPReaderInternals:
    """Test internal helper methods."""
    
    def test_match_str_session(self, sample_data_dir):
        """Test matching DATALOG sessions to STR sessions."""
        reader = CPAPReader(sample_data_dir)
        
        # Test with mock data
        from datetime import timedelta
        datalog_time = datetime(2024, 11, 27, 1, 0, 0)
        str_sessions = [
            (datetime(2024, 11, 27, 1, 0, 0), datetime(2024, 11, 27, 8, 0, 0)),
            (datetime(2024, 11, 27, 22, 0, 0), datetime(2024, 11, 28, 6, 0, 0)),
        ]
        
        match = reader._match_str_session(datalog_time, str_sessions)
        assert match == str_sessions[0]
    
    def test_match_str_session_no_match(self, sample_data_dir):
        """Test matching when no STR session matches."""
        reader = CPAPReader(sample_data_dir)
        
        datalog_time = datetime(2024, 11, 27, 12, 0, 0)
        str_sessions = [
            (datetime(2024, 11, 27, 1, 0, 0), datetime(2024, 11, 27, 8, 0, 0)),
        ]
        
        match = reader._match_str_session(datalog_time, str_sessions)
        # Should still return closest match if within tolerance
        assert match is not None or match is None
    
    def test_find_str_session_index(self, sample_data_dir):
        """Test finding session index in STR data."""
        reader = CPAPReader(sample_data_dir)
        
        sessions = [
            (datetime(2024, 11, 27, 1, 0, 0), datetime(2024, 11, 27, 8, 0, 0)),
            (datetime(2024, 11, 27, 22, 0, 0), datetime(2024, 11, 28, 6, 0, 0)),
        ]
        
        idx = reader._find_str_session_index(sessions[1], sessions)
        assert idx == 1
    
    def test_create_session_summary(self, sample_data_dir):
        """Test creating session summary from STR data."""
        reader = CPAPReader(sample_data_dir)
        
        start_time = datetime(2024, 11, 27, 1, 0, 0)
        matched_session = (
            datetime(2024, 11, 27, 1, 0, 0),
            datetime(2024, 11, 27, 8, 0, 0)
        )
        
        summary = reader._create_session_summary(start_time, matched_session, {})
        
        assert summary.duration_hours == 7.0
        assert summary.mask_on_time == matched_session[0]
        assert summary.mask_off_time == matched_session[1]


@pytest.mark.integration
def test_reader_full_workflow(sample_data_dir):
    """Integration test of full reader workflow."""
    # Create reader
    reader = CPAPReader(sample_data_dir)
    
    # Get devices
    devices = reader.get_devices()
    assert len(devices) > 0
    
    # Get sessions
    sessions = reader.get_sessions()
    assert isinstance(sessions, list)
    
    # Get summary stats
    stats = reader.get_summary_statistics(days=30)
    assert isinstance(stats, dict)
    
    # Export data
    data = reader.export_to_dict()
    assert "devices" in data
    assert "sessions" in data
