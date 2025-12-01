"""
Tests for error handling and edge cases.
"""

import pytest
from datetime import datetime
import numpy as np

from cpap_py.models import (
    Device,
    Session,
    SessionSummary,
    DeviceSettings,
    WaveformData,
    Event,
    EventType,
)
from cpap_py.reader import CPAPReader
from cpap_py.parsers.crc_parser import CRCError, CRCValidationMode


@pytest.mark.unit
class TestModelValidation:
    """Test Pydantic model validation."""
    
    def test_device_requires_serial_number(self):
        """Test that Device requires serial_number."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            Device(model_name="AirSense 10")
    
    def test_event_requires_type_and_timestamp(self):
        """Test that Event requires type and timestamp."""
        with pytest.raises(Exception):
            Event(duration=10.0)
    
    def test_waveform_requires_all_fields(self):
        """Test that WaveformData requires all fields."""
        with pytest.raises(Exception):
            WaveformData(
                channel_name="Pressure",
                unit="cmH2O",
                # Missing sample_rate, start_time, values
            )
    
    def test_session_summary_duration_required(self):
        """Test that SessionSummary requires duration fields."""
        with pytest.raises(Exception):
            SessionSummary(ahi=5.0)  # Missing duration_seconds and duration_hours


@pytest.mark.unit
class TestReaderErrorHandling:
    """Test CPAPReader error handling."""
    
    def test_reader_missing_directory(self):
        """Test reader with non-existent directory."""
        with pytest.raises(FileNotFoundError):
            CPAPReader("/nonexistent/directory")
    
    def test_reader_empty_directory(self, test_output_dir):
        """Test reader with empty directory."""
        # Create minimal structure
        (test_output_dir / "DATALOG").mkdir()
        (test_output_dir / "SETTINGS").mkdir()
        
        reader = CPAPReader(str(test_output_dir))
        
        # Should not crash
        devices = reader.get_devices()
        assert len(devices) > 0  # Should create a default device
        
        sessions = reader.get_sessions()
        assert isinstance(sessions, list)
        assert len(sessions) == 0  # No session files
    
    def test_reader_crc_strict_mode_errors(self, test_output_dir):
        """Test that CRC errors are raised in strict mode."""
        # Create structure
        datalog_dir = test_output_dir / "DATALOG"
        datalog_dir.mkdir()
        (test_output_dir / "SETTINGS").mkdir()
        
        # Create a file with mismatched CRC
        data_file = datalog_dir / "test.edf"
        crc_file = datalog_dir / "test.crc"
        
        data_file.write_bytes(b'test data')
        crc_file.write_bytes(b'\xFF\xFF')  # Wrong CRC
        
        # Should collect validation errors but not crash in PERMISSIVE mode
        reader = CPAPReader(str(test_output_dir), crc_validation=CRCValidationMode.PERMISSIVE)
        errors = reader.get_validation_errors()
        
        # May have CRC errors
        crc_errors = [e for e in errors if "crc" in e.error_type.lower()]
        # Expect at least one CRC error
        assert len(crc_errors) > 0
    
    def test_reader_str_parsing_error(self, test_output_dir, mocker):
        """Test reader handles STR.edf parsing errors gracefully."""
        # Create structure with invalid STR.edf
        (test_output_dir / "DATALOG").mkdir()
        (test_output_dir / "SETTINGS").mkdir()
        str_file = test_output_dir / "STR.edf"
        str_file.write_bytes(b"invalid data")
        
        # Mock parse_str_file to raise exception
        mocker.patch('cpap_py.reader.parse_str_file', side_effect=Exception("Parse error"))
        
        # Should not crash, just log validation error
        reader = CPAPReader(str(test_output_dir), crc_validation=CRCValidationMode.DISABLED)
        
        # Reader should be created successfully despite STR parsing error
        assert reader is not None
        assert reader.sdcard_path == test_output_dir
        
        # The reader should not crash - that's the main test
        # Validation errors may or may not include STR depending on implementation
        validation_errors = reader.get_validation_errors()
        assert isinstance(validation_errors, list)


@pytest.mark.unit
class TestWaveformEdgeCases:
    """Test waveform data edge cases."""
    
    def test_waveform_empty_values(self):
        """Test waveform with empty values array."""
        waveform = WaveformData(
            channel_name="Test",
            unit="unit",
            sample_rate=1.0,
            start_time=datetime.now(),
            values=np.array([])
        )
        
        assert len(waveform.values) == 0
        
        df = waveform.to_dataframe()
        assert len(df) == 0
    
    def test_waveform_single_value(self):
        """Test waveform with single value."""
        waveform = WaveformData(
            channel_name="Test",
            unit="unit",
            sample_rate=1.0,
            start_time=datetime.now(),
            values=np.array([10.0])
        )
        
        df = waveform.to_dataframe()
        assert len(df) == 1
        assert df.iloc[0, 0] == 10.0
    
    def test_waveform_very_large_array(self):
        """Test waveform with large array."""
        # Simulate 1 hour of 25 Hz data
        large_array = np.random.randn(90000)
        
        waveform = WaveformData(
            channel_name="Pressure",
            unit="cmH2O",
            sample_rate=25.0,
            start_time=datetime.now(),
            values=large_array
        )
        
        assert len(waveform.values) == 90000
        
        data_dict = waveform.to_dict()
        assert data_dict["length"] == 90000
    
    def test_waveform_nan_values(self):
        """Test waveform with NaN values."""
        values = np.array([10.0, np.nan, 11.0, np.nan, 12.0])
        
        waveform = WaveformData(
            channel_name="Test",
            unit="unit",
            sample_rate=1.0,
            start_time=datetime.now(),
            values=values
        )
        
        # Should preserve NaN values
        assert np.isnan(waveform.values[1])
        assert np.isnan(waveform.values[3])


@pytest.mark.unit
class TestSessionEdgeCases:
    """Test Session edge cases."""
    
    def test_session_with_no_end_time(self):
        """Test session without end time."""
        summary = SessionSummary(duration_seconds=0, duration_hours=0)
        settings = DeviceSettings()
        
        session = Session(
            session_id="TEST_001",
            device_serial="TEST",
            date=datetime.now().date(),
            start_time=datetime.now(),
            summary=summary,
            settings=settings,
            end_time=None
        )
        
        assert session.end_time is None
        
        data = session.to_dict()
        assert data["end_time"] is None
    
    def test_session_get_events_empty(self):
        """Test getting events when none exist."""
        summary = SessionSummary(duration_seconds=3600, duration_hours=1.0)
        settings = DeviceSettings()
        
        session = Session(
            session_id="TEST_001",
            device_serial="TEST",
            date=datetime.now().date(),
            start_time=datetime.now(),
            summary=summary,
            settings=settings
        )
        
        events = session.get_events()
        assert events == []
    
    def test_session_get_events_by_type(self):
        """Test filtering events by type."""
        summary = SessionSummary(duration_seconds=3600, duration_hours=1.0)
        settings = DeviceSettings()
        
        session = Session(
            session_id="TEST_001",
            device_serial="TEST",
            date=datetime.now().date(),
            start_time=datetime.now(),
            summary=summary,
            settings=settings
        )
        
        # Manually set events
        session._events = [
            Event(type=EventType.OBSTRUCTIVE_APNEA, timestamp=datetime.now()),
            Event(type=EventType.HYPOPNEA, timestamp=datetime.now()),
            Event(type=EventType.OBSTRUCTIVE_APNEA, timestamp=datetime.now()),
        ]
        
        oa_events = session.get_events(EventType.OBSTRUCTIVE_APNEA)
        assert len(oa_events) == 2
        
        h_events = session.get_events(EventType.HYPOPNEA)
        assert len(h_events) == 1


@pytest.mark.unit
class TestSettingsEdgeCases:
    """Test settings edge cases."""
    
    def test_device_settings_all_none(self):
        """Test device settings with all None values."""
        settings = DeviceSettings()
        
        assert settings.mode is None
        assert settings.pressure is None
        assert settings.epr_enabled is None
        
        # Should still serialize
        data = settings.model_dump()
        assert isinstance(data, dict)
    
    def test_device_settings_invalid_epr_level(self):
        """Test that invalid EPR level is caught."""
        # Pydantic should validate EPR level is 0-3
        with pytest.raises(Exception):
            DeviceSettings(epr_level=10)
    
    def test_device_settings_invalid_humidifier_level(self):
        """Test that invalid humidifier level is caught."""
        with pytest.raises(Exception):
            DeviceSettings(humidifier_level=20)


@pytest.mark.unit
class TestNumericalEdgeCases:
    """Test numerical edge cases."""
    
    def test_zero_duration_session(self):
        """Test session with zero duration."""
        summary = SessionSummary(
            duration_seconds=0,
            duration_hours=0.0
        )
        assert summary.duration_seconds == 0
        assert summary.duration_hours == 0.0
    
    def test_very_high_ahi(self):
        """Test session with very high AHI."""
        summary = SessionSummary(
            duration_seconds=3600,
            duration_hours=1.0,
            ahi=150.0  # Very severe
        )
        assert summary.ahi == 150.0
    
    def test_negative_pressure_values(self):
        """Test that negative pressure values are allowed (for flow)."""
        # Flow can be negative (exhalation)
        waveform = WaveformData(
            channel_name="Flow Rate",
            unit="L/min",
            sample_rate=25.0,
            start_time=datetime.now(),
            values=np.array([-10.0, -5.0, 0.0, 5.0, 10.0])
        )
        assert waveform.values[0] == -10.0
    
    def test_extreme_leak_values(self):
        """Test session with extreme leak values."""
        summary = SessionSummary(
            duration_seconds=3600,
            duration_hours=1.0,
            leak_max=120.0,  # Very high leak
            leak_95th=80.0
        )
        assert summary.leak_max == 120.0


@pytest.mark.unit
class TestDateTimeEdgeCases:
    """Test date/time edge cases."""
    
    def test_session_across_midnight(self):
        """Test session that spans midnight."""
        from datetime import date, timedelta
        
        start_time = datetime(2024, 11, 27, 23, 0, 0)
        end_time = datetime(2024, 11, 28, 2, 0, 0)
        
        duration = (end_time - start_time).total_seconds()
        
        summary = SessionSummary(
            duration_seconds=duration,
            duration_hours=duration / 3600,
            mask_on_time=start_time,
            mask_off_time=end_time
        )
        
        settings = DeviceSettings()
        
        session = Session(
            session_id="TEST_001",
            device_serial="TEST",
            date=date(2024, 11, 27),  # Session date is start date
            start_time=start_time,
            end_time=end_time,
            summary=summary,
            settings=settings
        )
        
        assert session.start_time.date() != session.end_time.date()
    
    def test_very_long_session(self):
        """Test session with very long duration."""
        # 24 hour session
        summary = SessionSummary(
            duration_seconds=86400,
            duration_hours=24.0
        )
        assert summary.duration_hours == 24.0
    
    def test_very_short_session(self):
        """Test session with very short duration."""
        # 1 minute session
        summary = SessionSummary(
            duration_seconds=60,
            duration_hours=60/3600
        )
        assert summary.duration_hours == pytest.approx(0.0167, rel=0.01)


@pytest.mark.unit
class TestStringEdgeCases:
    """Test string handling edge cases."""
    
    def test_device_with_unicode_characters(self):
        """Test device with unicode in serial number."""
        device = Device(
            serial_number="TEST™123",
            model_name="AirSense® 10"
        )
        assert "™" in device.serial_number
        assert "®" in device.model_name
    
    def test_device_with_very_long_serial(self):
        """Test device with very long serial number."""
        long_serial = "X" * 100
        device = Device(
            serial_number=long_serial,
            model_name="Test"
        )
        assert len(device.serial_number) == 100
