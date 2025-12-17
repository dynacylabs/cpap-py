"""
High-level CPAP data loader.

Provides a unified interface for loading and accessing all CPAP data
from a ResMed device data directory.
"""

import sys
from pathlib import Path
from datetime import date, datetime
from typing import Optional, List, Dict
from dataclasses import dataclass

from .identification import IdentificationParser, MachineInfo
from .str_parser import STRParser, STRRecord
from .datalog_parser import DatalogParser, SessionData
from .settings_parser import SettingsParser, SettingChange


@dataclass
class CPAPData:
    """Complete CPAP data for a device"""
    machine_info: Optional[MachineInfo] = None
    summary_records: List[STRRecord] = None
    sessions: List[SessionData] = None
    settings_changes: List[SettingChange] = None
    
    def __post_init__(self):
        if self.summary_records is None:
            self.summary_records = []
        if self.sessions is None:
            self.sessions = []
        if self.settings_changes is None:
            self.settings_changes = []


class CPAPLoader:
    """High-level loader for CPAP data"""
    
    def __init__(self, data_path: str):
        """
        Initialize CPAP loader.
        
        Args:
            data_path: Path to CPAP data directory (contains Identification,
                      STR.edf, DATALOG/, SETTINGS/)
        """
        self.data_path = Path(data_path)
        
    def load_all(self) -> CPAPData:
        """
        Load all CPAP data from directory.
        
        Returns:
            CPAPData object with all parsed data
        """
        data = CPAPData()
        
        # Load identification
        print("Loading device identification...", file=sys.stderr)
        ident_parser = IdentificationParser(str(self.data_path))
        data.machine_info = ident_parser.parse()
        
        if data.machine_info:
            print(f"  Device: {data.machine_info.model}", file=sys.stderr)
            print(f"  Serial: {data.machine_info.serial}", file=sys.stderr)
        
        # Load STR.edf (summary data)
        str_path = self.data_path / "STR.edf"
        if str_path.exists():
            print("Loading summary data (STR.edf)...", file=sys.stderr)
            str_parser = STRParser(
                str(str_path),
                data.machine_info.serial if data.machine_info else None
            )
            if str_parser.parse():
                data.summary_records = str_parser.records
                print(f"  Loaded {len(data.summary_records)} daily records", file=sys.stderr)
        
        # Load DATALOG (session data)
        datalog_path = self.data_path / "DATALOG"
        if datalog_path.exists() and datalog_path.is_dir():
            print("Loading session data (DATALOG)...", file=sys.stderr)
            datalog_parser = DatalogParser(str(datalog_path))
            data.sessions = datalog_parser.parse_all_sessions()
            print(f"  Loaded {len(data.sessions)} sessions", file=sys.stderr)
        
        # Load SETTINGS
        settings_path = self.data_path / "SETTINGS"
        if settings_path.exists() and settings_path.is_dir():
            print("Loading settings changes...", file=sys.stderr)
            settings_parser = SettingsParser(str(settings_path))
            data.settings_changes = settings_parser.parse_all()
            print(f"  Loaded {len(data.settings_changes)} setting changes", file=sys.stderr)
        
        return data
    
    def load_identification_only(self) -> Optional[MachineInfo]:
        """Load only device identification"""
        ident_parser = IdentificationParser(str(self.data_path))
        return ident_parser.parse()
    
    def load_summary_only(self) -> List[STRRecord]:
        """Load only STR.edf summary data"""
        str_path = self.data_path / "STR.edf"
        if not str_path.exists():
            return []
            
        str_parser = STRParser(str(str_path))
        if str_parser.parse():
            return str_parser.records
        return []
    
    def load_sessions_for_date(self, target_date: date) -> List[SessionData]:
        """Load only sessions for a specific date"""
        datalog_path = self.data_path / "DATALOG"
        if not datalog_path.exists():
            return []
            
        datalog_parser = DatalogParser(str(datalog_path))
        
        # Scan for files on this date
        files_by_date = datalog_parser.scan_files()
        if target_date not in files_by_date:
            return []
            
        # Parse files for this date
        sessions = []
        for filepath in files_by_date[target_date]:
            session = datalog_parser.parse_session_file(filepath)
            if session:
                sessions.append(session)
                
        return sessions
    
    def get_date_range(self) -> Optional[tuple[date, date]]:
        """
        Get date range of available data.
        
        Returns:
            Tuple of (start_date, end_date) or None if no data
        """
        str_path = self.data_path / "STR.edf"
        if not str_path.exists():
            return None
            
        str_parser = STRParser(str(str_path))
        if not str_parser.parse() or not str_parser.records:
            return None
            
        dates = [r.date for r in str_parser.records if r.date]
        if not dates:
            return None
            
        return (min(dates), max(dates))
