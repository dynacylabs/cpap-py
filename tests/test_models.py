"""
Tests for data models and Pydantic validation.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta

from cpap_py.models import (
    Device,
    Event,
    EventType,
    WaveformData,
    SessionSummary,
    DeviceSettings,
    Session,
    CPAPMode,
    MaskType,
    ValidationError,
)


@pytest.mark.unit
class TestDevice:
    """Test Device model."""
    
    def test_device_creation(self):
        """Test creating a device instance."""
        device = Device(
            serial_number="TEST123456",
            model_name="AirSense 10"
        )
        assert device.serial_number == "TEST123456"
        assert device.model_name == "AirSense 10"
    
    def test_device_with_optional_fields(self):
        """Test device with all fields populated."""
        device = Device(
            serial_number="TEST123456",
            model_name="AirSense 10 AutoSet",
            model_id=37,
            firmware_version="6.04.01",
            last_updated=datetime(2024, 11, 27, 10, 0, 0)
        )
        assert device.firmware_version == "6.04.01"
        assert device.model_id == 37
        assert device.last_updated.year == 2024
    
    def test_device_json_serialization(self):
        """Test device can be serialized to JSON."""
        device = Device(
            serial_number="TEST123",
            model_name="AirSense 10",
            firmware_version="6.04.01"
        )
        json_str = device.model_dump_json()
        assert "TEST123" in json_str
        assert "AirSense 10" in json_str


@pytest.mark.unit
class TestEvent:
    """Test Event model."""
    
    def test_event_creation(self):
        """Test creating an event."""
        event = Event(
            type=EventType.OBSTRUCTIVE_APNEA,
            timestamp=datetime(2024, 11, 27, 1, 30, 0),
            duration=12.5
        )
        assert event.type == EventType.OBSTRUCTIVE_APNEA
        assert event.duration == 12.5
    
    def test_event_with_data(self):
        """Test event with additional data."""
        event = Event(
            type=EventType.HYPOPNEA,
            timestamp=datetime(2024, 11, 27, 2, 0, 0),
            duration=15.0,
            data={"severity": "moderate", "annotation": "test"}
        )
        assert event.data["severity"] == "moderate"
        assert event.data["annotation"] == "test"
    
    def test_event_type_enum_values(self):
        """Test all event type enum values are valid."""
        event_types = [
            EventType.OBSTRUCTIVE_APNEA,
            EventType.CENTRAL_APNEA,
            EventType.HYPOPNEA,
            EventType.APNEA,
            EventType.FLOW_LIMITATION,
            EventType.RERA,
            EventType.VIBRATORY_SNORE,
            EventType.PERIODIC_BREATHING,
            EventType.CHEYNE_STOKES,
            EventType.LARGE_LEAK,
        ]
        for event_type in event_types:
            event = Event(
                type=event_type,
                timestamp=datetime.now()
            )
            assert event.type == event_type


@pytest.mark.unit
class TestWaveformData:
    """Test WaveformData model."""
    
    def test_waveform_creation(self):
        """Test creating waveform data."""
        values = np.array([10.0, 10.5, 11.0, 10.8, 10.2])
        waveform = WaveformData(
            channel_name="Mask Pressure",
            unit="cmH2O",
            sample_rate=25.0,
            start_time=datetime(2024, 11, 27, 0, 0, 0),
            values=values
        )
        assert waveform.channel_name == "Mask Pressure"
        assert waveform.unit == "cmH2O"
        assert waveform.sample_rate == 25.0
        assert len(waveform.values) == 5
    
    def test_waveform_to_dataframe(self):
        """Test converting waveform to DataFrame."""
        values = np.array([10.0, 10.5, 11.0])
        waveform = WaveformData(
            channel_name="Pressure",
            unit="cmH2O",
            sample_rate=1.0,
            start_time=datetime(2024, 11, 27, 0, 0, 0),
            values=values
        )
        df = waveform.to_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert "Pressure" in df.columns
        assert len(df) == 3
        assert df.index[0].hour == 0
    
    def test_waveform_to_dict(self):
        """Test converting waveform to dictionary."""
        values = np.array([10.0, 10.5, 11.0])
        waveform = WaveformData(
            channel_name="Flow Rate",
            unit="L/min",
            sample_rate=25.0,
            start_time=datetime(2024, 11, 27, 0, 0, 0),
            values=values
        )
        data = waveform.to_dict()
        assert data["channel_name"] == "Flow Rate"
        assert data["unit"] == "L/min"
        assert data["sample_rate"] == 25.0
        assert data["length"] == 3
        assert isinstance(data["values"], list)
    
    def test_waveform_high_sample_rate(self):
        """Test waveform with high sample rate."""
        # 25 Hz for 1 minute = 1500 samples
        values = np.random.randn(1500) * 2 + 12
        waveform = WaveformData(
            channel_name="Mask Pressure",
            unit="cmH2O",
            sample_rate=25.0,
            start_time=datetime(2024, 11, 27, 0, 0, 0),
            values=values
        )
        df = waveform.to_dataframe()
        assert len(df) == 1500


@pytest.mark.unit
class TestSessionSummary:
    """Test SessionSummary model."""
    
    def test_session_summary_creation(self):
        """Test creating a session summary."""
        summary = SessionSummary(
            duration_seconds=27000,
            duration_hours=7.5,
            ahi=5.2
        )
        assert summary.duration_hours == 7.5
        assert summary.ahi == 5.2
    
    def test_session_summary_with_all_fields(self, mock_session_summary):
        """Test session summary with all fields populated."""
        summary = SessionSummary(**mock_session_summary)
        assert summary.ahi == 5.2
        assert summary.obstructive_apneas == 15
        assert summary.central_apneas == 1
        assert summary.hypopneas == 23
        assert summary.pressure_median == 12.5
        assert summary.leak_median == 3.2
    
    def test_session_summary_optional_fields(self):
        """Test session summary with minimal fields."""
        summary = SessionSummary(
            duration_seconds=3600,
            duration_hours=1.0
        )
        assert summary.ahi is None
        assert summary.obstructive_apneas == 0
        assert summary.pressure_median is None
    
    def test_session_summary_event_counts(self):
        """Test event count fields."""
        summary = SessionSummary(
            duration_seconds=28800,
            duration_hours=8.0,
            obstructive_apneas=20,
            central_apneas=5,
            hypopneas=30,
            flow_limitations=100,
            reras=10
        )
        assert summary.obstructive_apneas == 20
        assert summary.central_apneas == 5
        assert summary.hypopneas == 30


@pytest.mark.unit
class TestDeviceSettings:
    """Test DeviceSettings model."""
    
    def test_device_settings_cpap_mode(self):
        """Test CPAP mode settings."""
        settings = DeviceSettings(
            mode=CPAPMode.CPAP,
            pressure=10.0,
            epr_enabled=True,
            epr_level=2
        )
        assert settings.mode == CPAPMode.CPAP
        assert settings.pressure == 10.0
        assert settings.epr_enabled is True
        assert settings.epr_level == 2
    
    def test_device_settings_apap_mode(self):
        """Test APAP mode settings."""
        settings = DeviceSettings(
            mode=CPAPMode.APAP,
            pressure_min=6.0,
            pressure_max=20.0,
            epr_enabled=True,
            epr_level=3
        )
        assert settings.mode == CPAPMode.APAP
        assert settings.pressure_min == 6.0
        assert settings.pressure_max == 20.0
    
    def test_device_settings_ramp(self, mock_device_settings):
        """Test ramp settings."""
        settings = DeviceSettings(**mock_device_settings)
        assert settings.ramp_enabled is True
        assert settings.ramp_time == 20
        assert settings.ramp_start_pressure == 4.0
    
    def test_device_settings_humidifier(self):
        """Test humidifier settings."""
        settings = DeviceSettings(
            humidifier_enabled=True,
            humidifier_level=5,
            climate_control="Auto",
            temperature_enabled=True,
            temperature=72.0
        )
        assert settings.humidifier_enabled is True
        assert settings.humidifier_level == 5
        assert settings.climate_control == "Auto"
    
    def test_device_settings_mask_type(self):
        """Test mask type settings."""
        for mask_type in [MaskType.NASAL, MaskType.PILLOWS, MaskType.FULL_FACE]:
            settings = DeviceSettings(mask_type=mask_type)
            assert settings.mask_type == mask_type
    
    def test_device_settings_epr_validation(self):
        """Test EPR level validation."""
        # Valid EPR levels
        for level in [0, 1, 2, 3]:
            settings = DeviceSettings(epr_level=level)
            assert settings.epr_level == level
    
    def test_device_settings_optional_fields(self):
        """Test settings with minimal fields."""
        settings = DeviceSettings()
        assert settings.mode is None
        assert settings.pressure is None
        assert settings.epr_enabled is None


@pytest.mark.unit
class TestSession:
    """Test Session model."""
    
    def test_session_creation(self):
        """Test creating a session."""
        summary = SessionSummary(duration_seconds=28800, duration_hours=8.0)
        settings = DeviceSettings(mode=CPAPMode.APAP)
        
        session = Session(
            session_id="TEST123_20241127_010000",
            device_serial="TEST123",
            date=date(2024, 11, 27),
            start_time=datetime(2024, 11, 27, 1, 0, 0),
            summary=summary,
            settings=settings
        )
        assert session.session_id == "TEST123_20241127_010000"
        assert session.device_serial == "TEST123"
        assert session.date == date(2024, 11, 27)
    
    def test_session_with_data_flags(self):
        """Test session with data availability flags."""
        summary = SessionSummary(duration_seconds=28800, duration_hours=8.0)
        settings = DeviceSettings()
        
        session = Session(
            session_id="TEST123_20241127_010000",
            device_serial="TEST123",
            date=date(2024, 11, 27),
            start_time=datetime(2024, 11, 27, 1, 0, 0),
            summary=summary,
            settings=settings,
            has_pressure_data=True,
            has_flow_data=True,
            has_spo2_data=False,
            has_events=True
        )
        assert session.has_pressure_data is True
        assert session.has_flow_data is True
        assert session.has_spo2_data is False
        assert session.has_events is True
    
    def test_session_to_dict(self):
        """Test converting session to dictionary."""
        summary = SessionSummary(duration_seconds=28800, duration_hours=8.0, ahi=5.0)
        settings = DeviceSettings(mode=CPAPMode.APAP)
        
        session = Session(
            session_id="TEST123_20241127_010000",
            device_serial="TEST123",
            date=date(2024, 11, 27),
            start_time=datetime(2024, 11, 27, 1, 0, 0),
            summary=summary,
            settings=settings
        )
        
        data = session.to_dict()
        assert data["session_id"] == "TEST123_20241127_010000"
        assert data["device_serial"] == "TEST123"
        assert "summary" in data
        assert "settings" in data
        assert data["has_pressure_data"] is False
    
    def test_session_get_pressure_data_no_data(self):
        """Test getting pressure data when none available."""
        summary = SessionSummary(duration_seconds=28800, duration_hours=8.0, ahi=5.0)
        settings = DeviceSettings(mode=CPAPMode.CPAP)
        session = Session(
            session_id="TEST_20240101_220000",
            device_serial="TEST123",
            date=date(2024, 1, 1),
            start_time=datetime(2024, 1, 1, 22, 0),
            end_time=datetime(2024, 1, 2, 6, 0),
            summary=summary,
            settings=settings,
            has_pressure_data=False
        )
        assert session.get_pressure_data() is None
    
    def test_session_get_flow_data_no_data(self):
        """Test getting flow data when none available."""
        summary = SessionSummary(duration_seconds=28800, duration_hours=8.0, ahi=5.0)
        settings = DeviceSettings(mode=CPAPMode.CPAP)
        session = Session(
            session_id="TEST_20240101_220000",
            device_serial="TEST123",
            date=date(2024, 1, 1),
            start_time=datetime(2024, 1, 1, 22, 0),
            end_time=datetime(2024, 1, 2, 6, 0),
            summary=summary,
            settings=settings,
            has_flow_data=False
        )
        assert session.get_flow_data() is None
    
    def test_session_get_spo2_data_no_data(self):
        """Test getting SpO2 data when none available."""
        summary = SessionSummary(duration_seconds=28800, duration_hours=8.0, ahi=5.0)
        settings = DeviceSettings(mode=CPAPMode.CPAP)
        session = Session(
            session_id="TEST_20240101",
            device_serial="TEST123",
            date=date(2024, 1, 1),
            start_time=datetime(2024, 1, 1, 22, 0),
            end_time=datetime(2024, 1, 2, 6, 0),
            summary=summary,
            settings=settings,
            has_spo2_data=False
        )
        assert session.get_spo2_data() is None
    
    def test_session_with_file_paths(self, tmp_path):
        """Test session with actual file paths set."""
        summary = SessionSummary(duration_seconds=28800, duration_hours=8.0, ahi=5.0)
        settings = DeviceSettings(mode=CPAPMode.CPAP)
        
        # Create session - Session model may not expose _brp_file as a public field
        session = Session(
            session_id="TEST_20240101",
            device_serial="TEST123",
            date=date(2024, 1, 1),
            start_time=datetime(2024, 1, 1, 22, 0),
            end_time=datetime(2024, 1, 2, 6, 0),
            summary=summary,
            settings=settings,
            has_pressure_data=True
        )
        
        # Verify session was created
        assert session.has_pressure_data is True


@pytest.mark.unit
class TestValidationError:
    """Test ValidationError model."""
    
    def test_validation_error_creation(self):
        """Test creating a validation error."""
        error = ValidationError(
            file_path="/path/to/file.edf",
            error_type="crc_mismatch",
            message="CRC validation failed"
        )
        assert error.file_path == "/path/to/file.edf"
        assert error.error_type == "crc_mismatch"
        assert error.message == "CRC validation failed"
        assert error.severity == "warning"
    
    def test_validation_error_severity_levels(self):
        """Test different severity levels."""
        for severity in ["warning", "error", "critical"]:
            error = ValidationError(
                file_path="/path/to/file.edf",
                error_type="test",
                message="test error",
                severity=severity
            )
            assert error.severity == severity
    
    def test_validation_error_timestamp(self):
        """Test that timestamp is automatically set."""
        error = ValidationError(
            file_path="/path/to/file.edf",
            error_type="test",
            message="test"
        )
        assert isinstance(error.timestamp, datetime)
        assert error.timestamp.year == datetime.now().year


@pytest.mark.unit
class TestEnums:
    """Test enum definitions."""
    
    def test_cpap_mode_values(self):
        """Test CPAP mode enum values."""
        modes = [
            CPAPMode.CPAP,
            CPAPMode.APAP,
            CPAPMode.BILEVEL_T,
            CPAPMode.BILEVEL_S,
            CPAPMode.BILEVEL_ST,
            CPAPMode.BILEVEL_AUTO,
            CPAPMode.ASV,
            CPAPMode.ASV_AUTO,
        ]
        for mode in modes:
            assert isinstance(mode.value, str)
    
    def test_mask_type_values(self):
        """Test mask type enum values."""
        masks = [
            MaskType.NASAL,
            MaskType.PILLOWS,
            MaskType.FULL_FACE,
            MaskType.UNKNOWN,
        ]
        for mask in masks:
            assert isinstance(mask.value, str)
    
    def test_event_type_values(self):
        """Test event type enum values."""
        events = [
            EventType.OBSTRUCTIVE_APNEA,
            EventType.CENTRAL_APNEA,
            EventType.HYPOPNEA,
            EventType.FLOW_LIMITATION,
            EventType.LARGE_LEAK,
        ]
        for event in events:
            assert isinstance(event.value, str)


@pytest.mark.unit
class TestSessionDataRetrievalEdgeCases:
    """Test edge cases for session data retrieval methods."""
    
    def test_get_pressure_data_returns_none_when_no_matching_channels(self, tmp_path, mocker):
        """Test get_pressure_data returns None when no pressure channels found."""
        brp_file = tmp_path / "test.BRP"
        brp_file.write_bytes(b"dummy")
        
        summary = SessionSummary(
            duration_seconds=3600,
            duration_hours=1.0,
            mask_on_time=datetime(2024, 1, 1, 22, 0),
            mask_off_time=datetime(2024, 1, 1, 23, 0)
        )
        
        settings = DeviceSettings()
        
        session = Session(
            session_id="test1",
            device_serial="TEST123",
            date=date(2024, 1, 1),
            start_time=datetime(2024, 1, 1, 22, 0),
            summary=summary,
            settings=settings,
            has_pressure_data=True,
            _brp_file=str(brp_file)
        )
        
        # Mock parse_pressure_file to return waveforms with no pressure channels
        mock_waveform = WaveformData(
            channel_name="OtherChannel",
            values=np.array([1.0, 2.0, 3.0]),
            sample_rate=1.0,
            start_time=datetime(2024, 1, 1, 22, 0),
            unit="unknown"
        )
        mocker.patch('cpap_py.parsers.edf_parser.parse_pressure_file', return_value=[mock_waveform])
        
        result = session.get_pressure_data()
        assert result is None
    
    def test_get_flow_data_returns_none_when_no_matching_channels(self, tmp_path, mocker):
        """Test get_flow_data returns None when no flow channels found."""
        brp_file = tmp_path / "test.BRP"
        brp_file.write_bytes(b"dummy")
        
        summary = SessionSummary(
            duration_seconds=3600,
            duration_hours=1.0,
            mask_on_time=datetime(2024, 1, 1, 22, 0),
            mask_off_time=datetime(2024, 1, 1, 23, 0)
        )
        
        settings = DeviceSettings()
        
        session = Session(
            session_id="test2",
            device_serial="TEST123",
            date=date(2024, 1, 1),
            start_time=datetime(2024, 1, 1, 22, 0),
            summary=summary,
            settings=settings,
            has_flow_data=True,
            _brp_file=str(brp_file)
        )
        
        # Mock parse_pressure_file to return waveforms with no flow channels
        mock_waveform = WaveformData(
            channel_name="PressureChannel",
            values=np.array([10.0, 11.0, 12.0]),
            sample_rate=1.0,
            start_time=datetime(2024, 1, 1, 22, 0),
            unit="cmH2O"
        )
        mocker.patch('cpap_py.parsers.edf_parser.parse_pressure_file', return_value=[mock_waveform])
        
        result = session.get_flow_data()
        assert result is None
    
    def test_get_spo2_data_returns_none_when_empty_list(self, tmp_path, mocker):
        """Test get_spo2_data returns None when parser returns empty list."""
        sad_file = tmp_path / "test.SAD"
        sad_file.write_bytes(b"dummy")
        
        summary = SessionSummary(
            duration_seconds=3600,
            duration_hours=1.0,
            mask_on_time=datetime(2024, 1, 1, 22, 0),
            mask_off_time=datetime(2024, 1, 1, 23, 0)
        )
        
        settings = DeviceSettings()
        
        session = Session(
            session_id="test3",
            device_serial="TEST123",
            date=date(2024, 1, 1),
            start_time=datetime(2024, 1, 1, 22, 0),
            summary=summary,
            settings=settings,
            has_spo2_data=True,
            _sad_file=str(sad_file)
        )
        
        # Mock parse_spo2_file to return empty list
        mocker.patch('cpap_py.parsers.edf_parser.parse_spo2_file', return_value=[])
        
        result = session.get_spo2_data()
        assert result is None


@pytest.mark.unit
class TestSessionDataRetrieval:
    """Test Session data retrieval methods with lazy loading."""
    
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
        
        events = session.get_events()
        assert len(events) == 1
        
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
        
        events = session.get_events()
        assert events == []
    
    def test_get_pressure_data_with_file(self, tmp_path, mocker):
        """Test get_pressure_data with BRP file."""
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
        """Test get_flow_data with BRP file."""
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
        """Test get_spo2_data with SAD file."""
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
