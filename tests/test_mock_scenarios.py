"""
Mock-based tests for higher coverage of parsers
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime, date
from cpap_py.str_parser import STRParser, STRRecord
from cpap_py.datalog_parser import DatalogParser, SessionData
from cpap_py.settings_parser import SettingsParser, SettingChange
from cpap_py.loader import CPAPLoader
from cpap_py.edf_parser import EDFParser, EDFSignal, EDFHeader


class TestSTRParserWithMocks:
    """Tests for STRParser using mocks to increase coverage"""
    
    def test_get_records_by_date_range(self):
        """Test filtering records by date range"""
        parser = STRParser.__new__(STRParser)
        parser.records = [
            STRRecord(date=date(2024, 12, 10)),
            STRRecord(date=date(2024, 12, 15)),
            STRRecord(date=date(2024, 12, 20)),
            STRRecord(date=date(2024, 12, 25)),
        ]
        
        results = parser.get_records_by_date_range(
            date(2024, 12, 12),
            date(2024, 12, 22)
        )
        
        assert len(results) == 2
        assert results[0].date == date(2024, 12, 15)
        assert results[1].date == date(2024, 12, 20)


class TestDatalogParserWithMocks:
    """Tests for DatalogParser using mocks"""
    
    def test_get_sessions_by_date(self):
        """Test getting sessions by specific date"""
        parser = DatalogParser("/tmp")
        parser.sessions = [
            SessionData(date=date(2024, 12, 10)),
            SessionData(date=date(2024, 12, 15)),
            SessionData(date=date(2024, 12, 15)),
            SessionData(date=date(2024, 12, 20)),
        ]
        
        results = parser.get_sessions_by_date(date(2024, 12, 15))
        assert len(results) == 2
    
    def test_get_sessions_by_date_range(self):
        """Test getting sessions by date range"""
        parser = DatalogParser("/tmp")
        parser.sessions = [
            SessionData(date=date(2024, 12, 10)),
            SessionData(date=date(2024, 12, 15)),
            SessionData(date=date(2024, 12, 20)),
            SessionData(date=date(2024, 12, 25)),
        ]
        
        results = parser.get_sessions_by_date_range(
            date(2024, 12, 12),
            date(2024, 12, 22)
        )
        
        assert len(results) == 2


class TestSettingsParserWithMocks:
    """Tests for SettingsParser using mocks"""
    
    def test_get_changes_by_setting(self):
        """Test filtering changes by setting name"""
        parser = SettingsParser.__new__(SettingsParser)
        parser.changes = [
            SettingChange(setting_name="MinPressure", new_value="4.0"),
            SettingChange(setting_name="MaxPressure", new_value="15.0"),
            SettingChange(setting_name="MinPressure", new_value="5.0"),
        ]
        
        results = parser.get_changes_by_setting("MinPressure")
        assert len(results) == 2
    
    def test_get_changes_by_date_range(self):
        """Test filtering changes by date range"""
        parser = SettingsParser.__new__(SettingsParser)
        parser.changes = [
            SettingChange(timestamp=datetime(2024, 12, 10, 12, 0), setting_name="A"),
            SettingChange(timestamp=datetime(2024, 12, 15, 12, 0), setting_name="B"),
            SettingChange(timestamp=datetime(2024, 12, 20, 12, 0), setting_name="C"),
            SettingChange(timestamp=None, setting_name="D"),  # No timestamp
        ]
        
        results = parser.get_changes_by_date_range(
            datetime(2024, 12, 12),
            datetime(2024, 12, 18)
        )
        
        assert len(results) == 1
        assert results[0].setting_name == "B"
    
    def test_parse_timestamp_formats(self, temp_dir):
        """Test parsing various timestamp formats"""
        parser = SettingsParser(str(temp_dir))
        
        # 14-digit format
        ts = parser._parse_timestamp("20241215123045")
        assert ts == datetime(2024, 12, 15, 12, 30, 45)
        
        # ISO format
        ts = parser._parse_timestamp("2024-12-15 12:30:45")
        assert ts == datetime(2024, 12, 15, 12, 30, 45)
        
        # Slash format
        ts = parser._parse_timestamp("2024/12/15 12:30:45")
        assert ts == datetime(2024, 12, 15, 12, 30, 45)
        
        # Invalid format
        ts = parser._parse_timestamp("invalid")
        assert ts is None
        
        # Non-digit 14-char string
        ts = parser._parse_timestamp("abcd1234567890")
        assert ts is None


class TestLoaderIntegration:
    """Integration tests for loader with mocked components"""
    
    @patch('cpap_py.loader.SettingsParser')
    @patch('cpap_py.loader.DatalogParser')
    @patch('cpap_py.loader.STRParser')
    @patch('cpap_py.loader.IdentificationParser')
    def test_load_all_integration(self, mock_ident, mock_str, mock_datalog, mock_settings, temp_dir):
        """Test complete load_all workflow with mocks"""
        # Setup mocks
        from cpap_py.identification import MachineInfo
        
        mock_info = MachineInfo(serial="12345", model="Test Device")
        mock_ident.return_value.parse.return_value = mock_info
        
        mock_str_instance = Mock()
        mock_str_instance.parse.return_value = True
        mock_str_instance.records = [STRRecord(date=date(2024, 12, 15))]
        mock_str.return_value = mock_str_instance
        
        mock_datalog_instance = Mock()
        mock_datalog_instance.parse_all_sessions.return_value = []
        mock_datalog.return_value = mock_datalog_instance
        
        mock_settings_instance = Mock()
        mock_settings_instance.parse_all.return_value = []
        mock_settings.return_value = mock_settings_instance
        
        # Create directories and files
        (temp_dir / "STR.edf").touch()
        (temp_dir / "DATALOG").mkdir()
        (temp_dir / "SETTINGS").mkdir()
        
        loader = CPAPLoader(str(temp_dir))
        data = loader.load_all()
        
        assert data.machine_info == mock_info
        assert len(data.summary_records) == 1
