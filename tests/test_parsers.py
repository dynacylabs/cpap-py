"""
Tests for str_parser.py, datalog_parser.py, settings_parser.py, and loader.py modules
"""

import pytest
from datetime import date, datetime
from pathlib import Path
from cpap_py.str_parser import STRParser, STRRecord
from cpap_py.datalog_parser import DatalogParser, SessionData, SessionEvent
from cpap_py.settings_parser import SettingsParser, SettingChange
from cpap_py.loader import CPAPLoader, CPAPData


# Tests for STRRecord
class TestSTRRecord:
    """Tests for STRRecord dataclass"""
    
    def test_str_record_defaults(self):
        """Test STRRecord default values"""
        record = STRRecord()
        assert record.date is None
        assert record.mask_on == []
        assert record.mask_off == []
        assert record.mask_events == 0
        assert record.mask_duration == 0.0
        assert record.ahi == 0.0
        assert record.leak_50 == 0.0


# Tests for STRParser
class TestSTRParser:
    """Tests for STRParser"""
    
    def test_mode_constants(self):
        """Test mode constants are defined"""
        assert STRParser.MODE_UNKNOWN == 0
        assert STRParser.MODE_CPAP == 1
        assert STRParser.MODE_APAP == 2
        assert STRParser.MODE_BILEVEL_FIXED == 3
    
    def test_parser_initialization(self, temp_dir):
        """Test parser initialization"""
        filepath = temp_dir / "STR.edf"
        filepath.touch()
        parser = STRParser(str(filepath), "12345678")
        assert parser.serial_number == "12345678"
        assert parser.records == []


# Tests for SessionEvent
class TestSessionEvent:
    """Tests for SessionEvent dataclass"""
    
    def test_session_event_defaults(self):
        """Test SessionEvent default values"""
        event = SessionEvent(timestamp=10.5, event_type="Apnea")
        assert event.timestamp == 10.5
        assert event.event_type == "Apnea"
        assert event.duration == 0.0
        assert event.data == {}
    
    def test_session_event_with_data(self):
        """Test SessionEvent with custom data"""
        event = SessionEvent(
            timestamp=10.5,
            event_type="Hypopnea",
            duration=15.0,
            data={"severity": "moderate"}
        )
        assert event.duration == 15.0
        assert event.data["severity"] == "moderate"


# Tests for SessionData
class TestSessionData:
    """Tests for SessionData dataclass"""
    
    def test_session_data_defaults(self):
        """Test SessionData default values"""
        session = SessionData()
        assert session.date is None
        assert session.start_time is None
        assert session.duration == 0.0
        assert session.flow_rate == []
        assert session.pressure == []
        assert session.events == []
        assert session.sample_rate == 0.0
        assert session.filepath == ""


# Tests for DatalogParser
class TestDatalogParser:
    """Tests for DatalogParser"""
    
    def test_file_types_defined(self):
        """Test file type constants"""
        assert "BRP" in DatalogParser.FILE_TYPES
        assert "PLD" in DatalogParser.FILE_TYPES
        assert "EVE" in DatalogParser.FILE_TYPES
        assert DatalogParser.FILE_TYPES["BRP"] == "Breathing Data"
    
    def test_signal_aliases_defined(self):
        """Test signal aliases are defined"""
        assert "Flow" in DatalogParser.SIGNAL_ALIASES
        assert "Pressure" in DatalogParser.SIGNAL_ALIASES
        assert "Leak" in DatalogParser.SIGNAL_ALIASES
    
    def test_parser_initialization(self, temp_dir):
        """Test parser initialization"""
        datalog_dir = temp_dir / "DATALOG"
        datalog_dir.mkdir()
        parser = DatalogParser(str(datalog_dir))
        assert parser.datalog_path == datalog_dir
        assert parser.sessions == []
    
    def test_scan_files_empty(self, temp_dir):
        """Test scanning empty DATALOG directory"""
        datalog_dir = temp_dir / "DATALOG"
        datalog_dir.mkdir()
        parser = DatalogParser(str(datalog_dir))
        files = parser.scan_files()
        assert files == {}
    
    def test_scan_files_with_date_dirs(self, temp_dir):
        """Test scanning DATALOG with date directories"""
        datalog_dir = temp_dir / "DATALOG"
        datalog_dir.mkdir()
        
        # Create valid date directory
        day_dir = datalog_dir / "20241215"
        day_dir.mkdir()
        
        # Create invalid directory
        invalid_dir = datalog_dir / "invalid"
        invalid_dir.mkdir()
        
        # Create a test file
        (day_dir / "test.edf").touch()
        
        parser = DatalogParser(str(datalog_dir))
        files = parser.scan_files()
        
        assert date(2024, 12, 15) in files
        assert len(files[date(2024, 12, 15)]) == 1
    
    def test_get_sessions_by_date_empty(self, temp_dir):
        """Test getting sessions when none exist"""
        datalog_dir = temp_dir / "DATALOG"
        datalog_dir.mkdir()
        parser = DatalogParser(str(datalog_dir))
        
        sessions = parser.get_sessions_by_date(date(2024, 12, 15))
        assert sessions == []


# Tests for SettingChange
class TestSettingChange:
    """Tests for SettingChange dataclass"""
    
    def test_setting_change_defaults(self):
        """Test SettingChange default values"""
        change = SettingChange()
        assert change.timestamp is None
        assert change.setting_name == ""
        assert change.old_value is None
        assert change.new_value is None
        assert change.category == ""
        assert change.properties == {}
    
    def test_setting_change_initialization(self):
        """Test SettingChange with values"""
        dt = datetime(2024, 12, 15, 12, 0, 0)
        change = SettingChange(
            timestamp=dt,
            setting_name="MinPressure",
            old_value="4.0",
            new_value="5.0",
            category="PressureSettings"
        )
        assert change.timestamp == dt
        assert change.setting_name == "MinPressure"
        assert change.new_value == "5.0"


# Tests for SettingsParser
class TestSettingsParser:
    """Tests for SettingsParser"""
    
    def test_settings_prefixes_defined(self):
        """Test settings prefixes are defined"""
        assert "CGL" in SettingsParser.SETTINGS_PREFIXES
        assert "UGL" in SettingsParser.SETTINGS_PREFIXES
    
    def test_parser_initialization(self, temp_dir):
        """Test parser initialization"""
        settings_dir = temp_dir / "SETTINGS"
        settings_dir.mkdir()
        parser = SettingsParser(str(settings_dir))
        assert parser.settings_path == settings_dir
        assert parser.changes == []
    
    def test_parse_all_empty(self, temp_dir):
        """Test parsing empty settings directory"""
        settings_dir = temp_dir / "SETTINGS"
        settings_dir.mkdir()
        parser = SettingsParser(str(settings_dir))
        changes = parser.parse_all()
        assert changes == []
    
    def test_parse_file_tgt_format(self, temp_dir):
        """Test parsing TGT format settings file"""
        settings_dir = temp_dir / "SETTINGS"
        settings_dir.mkdir()
        
        content = """#TIM 20241215120000
#SET MinPressure
#OLD 4.0
#NEW 5.0

"""
        filepath = settings_dir / "CGL_12345.tgt"
        filepath.write_text(content)
        
        parser = SettingsParser(str(settings_dir))
        changes = parser.parse_file(filepath)
        
        assert len(changes) == 1
        assert changes[0].setting_name == "MinPressure"
        assert changes[0].old_value == "4.0"
        assert changes[0].new_value == "5.0"
    
    def test_get_changes_by_setting(self, temp_dir):
        """Test filtering changes by setting name"""
        settings_dir = temp_dir / "SETTINGS"
        settings_dir.mkdir()
        parser = SettingsParser(str(settings_dir))
        
        parser.changes = [
            SettingChange(setting_name="MinPressure", new_value="5.0"),
            SettingChange(setting_name="MaxPressure", new_value="15.0"),
            SettingChange(setting_name="MinPressure", new_value="6.0"),
        ]
        
        min_pressure_changes = parser.get_changes_by_setting("MinPressure")
        assert len(min_pressure_changes) == 2


# Tests for CPAPData
class TestCPAPData:
    """Tests for CPAPData dataclass"""
    
    def test_cpap_data_defaults(self):
        """Test CPAPData default values"""
        data = CPAPData()
        assert data.machine_info is None
        assert data.summary_records == []
        assert data.sessions == []
        assert data.settings_changes == []
    
    def test_cpap_data_initialization(self):
        """Test CPAPData with values"""
        from cpap_py.identification import MachineInfo
        
        info = MachineInfo(serial="12345678")
        data = CPAPData(machine_info=info)
        assert data.machine_info.serial == "12345678"


# Tests for CPAPLoader
class TestCPAPLoader:
    """Tests for CPAPLoader"""
    
    def test_loader_initialization(self, temp_dir):
        """Test loader initialization"""
        loader = CPAPLoader(str(temp_dir))
        assert loader.data_path == temp_dir
    
    def test_load_identification_only(self, sample_tgt_identification, temp_dir):
        """Test loading only identification"""
        loader = CPAPLoader(str(temp_dir))
        info = loader.load_identification_only()
        
        assert info is not None
        assert info.serial == "12345678"
        assert "AirSense 10" in info.model
    
    def test_load_identification_only_missing(self, temp_dir):
        """Test loading identification when file doesn't exist"""
        loader = CPAPLoader(str(temp_dir))
        info = loader.load_identification_only()
        assert info is None
    
    def test_load_summary_only_missing(self, temp_dir):
        """Test loading summary when STR.edf doesn't exist"""
        loader = CPAPLoader(str(temp_dir))
        records = loader.load_summary_only()
        assert records == []
    
    def test_load_sessions_for_date_missing(self, temp_dir):
        """Test loading sessions when DATALOG doesn't exist"""
        loader = CPAPLoader(str(temp_dir))
        sessions = loader.load_sessions_for_date(date(2024, 12, 15))
        assert sessions == []
    
    def test_get_date_range_missing(self, temp_dir):
        """Test getting date range when STR.edf doesn't exist"""
        loader = CPAPLoader(str(temp_dir))
        date_range = loader.get_date_range()
        assert date_range is None
    
    def test_load_all_complete(self, sample_cpap_directory):
        """Test loading complete CPAP directory"""
        loader = CPAPLoader(str(sample_cpap_directory))
        data = loader.load_all()
        
        # Should have machine info from identification
        assert data.machine_info is not None
        assert data.machine_info.serial == "12345678"
        
        # Others may be empty but should not be None
        assert isinstance(data.summary_records, list)
        assert isinstance(data.sessions, list)
        assert isinstance(data.settings_changes, list)
