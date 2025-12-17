"""
DATALOG parser for ResMed CPAP session data.

Parses EDF files in DATALOG directory containing detailed waveform data
and events for individual CPAP sessions.
"""

from pathlib import Path
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from .edf_parser import EDFParser, EDFSignal


@dataclass
class SessionEvent:
    """Event recorded during CPAP session"""
    timestamp: float  # Seconds since session start
    event_type: str
    duration: float = 0.0
    data: Dict[str, float] = field(default_factory=dict)


@dataclass
class SessionData:
    """CPAP session data from DATALOG files"""
    date: Optional[date] = None
    start_time: Optional[datetime] = None
    duration: float = 0.0
    
    # Waveform data (signals)
    flow_rate: List[float] = field(default_factory=list)  # L/min
    pressure: List[float] = field(default_factory=list)  # cmH2O
    mask_pressure: List[float] = field(default_factory=list)  # cmH2O
    leak: List[float] = field(default_factory=list)  # L/min
    tidal_volume: List[float] = field(default_factory=list)  # mL
    minute_vent: List[float] = field(default_factory=list)  # L/min
    resp_rate: List[float] = field(default_factory=list)  # breaths/min
    target_ipap: List[float] = field(default_factory=list)  # cmH2O
    target_epap: List[float] = field(default_factory=list)  # cmH2O
    spo2: List[float] = field(default_factory=list)  # %
    pulse: List[float] = field(default_factory=list)  # bpm
    
    # Events
    events: List[SessionEvent] = field(default_factory=list)
    
    # Sample rate (Hz)
    sample_rate: float = 0.0
    
    # File information
    filepath: str = ""
    file_type: str = ""  # BRP, PLD, SAD, EVE, CSL, AEV


class DatalogParser:
    """Parser for DATALOG EDF files"""
    
    # Signal name aliases for different device generations
    SIGNAL_ALIASES = {
        "Flow": ["Flow", "FlowRate", "Flow Rate"],
        "Pressure": ["Pressure", "MaskPressure", "Mask Pressure"],
        "Leak": ["Leak", "TotalLeak", "Total Leak"],
        "TidalVolume": ["Tidal Volume", "TidalVolume", "TV"],
        "MinuteVent": ["Minute Vent", "MinuteVent", "MV", "MinuteVentilation"],
        "RespRate": ["Resp. Rate", "RespRate", "Respiratory Rate", "RR"],
        "TargetIPAP": ["Target IPAP", "TargetIPAP", "IPAP Target", "Tgt IPAP"],
        "TargetEPAP": ["Target EPAP", "TargetEPAP", "EPAP Target", "Tgt EPAP"],
        "SpO2": ["SpO2", "SpO₂", "Oxygen Saturation"],
        "Pulse": ["Pulse", "Pulse Rate", "HeartRate", "Heart Rate"],
    }
    
    # File types
    FILE_TYPES = {
        "BRP": "Breathing Data",
        "PLD": "Pressure/Leak Data",
        "SAD": "Summary/Advanced Data",
        "EVE": "Events",
        "CSL": "Clinical Settings Log",
        "AEV": "Advanced Events",
    }
    
    def __init__(self, datalog_path: str):
        """
        Initialize DATALOG parser.
        
        Args:
            datalog_path: Path to DATALOG directory
        """
        self.datalog_path = Path(datalog_path)
        self.sessions: List[SessionData] = []
        
    def scan_files(self) -> Dict[date, List[Path]]:
        """
        Scan DATALOG directory for session files organized by date.
        
        Returns:
            Dictionary mapping dates to lists of file paths
        """
        files_by_date: Dict[date, List[Path]] = {}
        
        # DATALOG directory contains subdirectories named YYYYMMDD
        for day_dir in sorted(self.datalog_path.iterdir()):
            if not day_dir.is_dir():
                continue
                
            # Parse date from directory name
            try:
                dir_name = day_dir.name
                if len(dir_name) != 8 or not dir_name.isdigit():
                    continue
                    
                year = int(dir_name[0:4])
                month = int(dir_name[4:6])
                day = int(dir_name[6:8])
                session_date = date(year, month, day)
                
                # Find all .edf files in this directory
                edf_files = list(day_dir.glob("*.edf")) + list(day_dir.glob("*.edf.gz"))
                if edf_files:
                    files_by_date[session_date] = sorted(edf_files)
                    
            except (ValueError, OSError):
                continue
                
        return files_by_date
    
    def parse_session_file(self, filepath: Path) -> Optional[SessionData]:
        """
        Parse a single DATALOG session file.
        
        Args:
            filepath: Path to session EDF file
            
        Returns:
            SessionData if successful, None otherwise
        """
        edf = EDFParser(str(filepath))
        if not edf.parse():
            return None
            
        session = SessionData()
        session.filepath = str(filepath)
        session.start_time = edf.header.start_date
        session.duration = edf.header.num_data_records * edf.header.duration_seconds
        
        if session.start_time:
            session.date = session.start_time.date()
            
        # Determine file type from filename
        filename = filepath.stem.split('.')[0]  # Remove .edf or .edf.gz
        for ftype in self.FILE_TYPES:
            if ftype in filename.upper():
                session.file_type = ftype
                break
                
        # Parse signals
        self._parse_signals(edf, session)
        
        # Parse events if present
        self._parse_events(edf, session)
        
        return session
    
    def _parse_signals(self, edf: EDFParser, session: SessionData):
        """Parse waveform signals from EDF"""
        
        # Flow rate
        sig = self._find_signal(edf, "Flow")
        if sig:
            session.flow_rate = self._get_physical_values(sig)
            session.sample_rate = sig.sample_count / edf.header.duration_seconds
            
        # Pressure
        sig = self._find_signal(edf, "Pressure")
        if sig:
            session.pressure = self._get_physical_values(sig)
            
        # Leak
        sig = self._find_signal(edf, "Leak")
        if sig:
            session.leak = self._get_physical_values(sig)
            
        # Tidal volume
        sig = self._find_signal(edf, "TidalVolume")
        if sig:
            session.tidal_volume = self._get_physical_values(sig)
            
        # Minute ventilation
        sig = self._find_signal(edf, "MinuteVent")
        if sig:
            session.minute_vent = self._get_physical_values(sig)
            
        # Respiratory rate
        sig = self._find_signal(edf, "RespRate")
        if sig:
            session.resp_rate = self._get_physical_values(sig)
            
        # Target IPAP
        sig = self._find_signal(edf, "TargetIPAP")
        if sig:
            session.target_ipap = self._get_physical_values(sig)
            
        # Target EPAP
        sig = self._find_signal(edf, "TargetEPAP")
        if sig:
            session.target_epap = self._get_physical_values(sig)
            
        # SpO2
        sig = self._find_signal(edf, "SpO2")
        if sig:
            session.spo2 = self._get_physical_values(sig)
            
        # Pulse
        sig = self._find_signal(edf, "Pulse")
        if sig:
            session.pulse = self._get_physical_values(sig)
    
    def _parse_events(self, edf: EDFParser, session: SessionData):
        """Parse event signals from EDF"""
        
        # Look for event signals - these typically have labels like:
        # "Obstructive Apnea", "Central Apnea", "Hypopnea", "Flow Limitation", etc.
        
        event_types = [
            "Obstructive Apnea", "OA", "ObstructiveApnea",
            "Central Apnea", "CA", "CentralApnea",
            "Hypopnea", "H",
            "Flow Limitation", "FL", "FlowLimitation",
            "RERA", "Arousal",
            "Large Leak", "LL", "LargeLeak",
            "Clear Airway", "CSR",
        ]
        
        for sig in edf.signals:
            # Check if this is an event signal
            event_type = None
            for et in event_types:
                if et.lower() in sig.label.lower():
                    event_type = sig.label
                    break
                    
            if not event_type:
                continue
                
            # Parse event timestamps from signal data
            # Events are typically encoded as non-zero values at specific times
            time_per_sample = edf.header.duration_seconds / edf.header.num_data_records
            
            i = 0
            event_start = None
            for rec in range(edf.header.num_data_records):
                for s in range(sig.sample_count):
                    timestamp = rec * edf.header.duration_seconds + \
                               (s / sig.sample_count) * edf.header.duration_seconds
                    
                    value = sig.data[i]
                    i += 1
                    
                    if value != 0 and event_start is None:
                        # Event started
                        event_start = timestamp
                    elif value == 0 and event_start is not None:
                        # Event ended
                        event = SessionEvent(
                            timestamp=event_start,
                            event_type=event_type,
                            duration=timestamp - event_start
                        )
                        session.events.append(event)
                        event_start = None
                        
            # Handle event that extends to end of recording
            if event_start is not None:
                event = SessionEvent(
                    timestamp=event_start,
                    event_type=event_type,
                    duration=session.duration - event_start
                )
                session.events.append(event)
    
    def _find_signal(self, edf: EDFParser, signal_name: str) -> Optional[EDFSignal]:
        """Find signal by name using aliases"""
        if signal_name not in self.SIGNAL_ALIASES:
            return edf.get_signal(signal_name)
            
        # Try each alias
        for alias in self.SIGNAL_ALIASES[signal_name]:
            sig = edf.get_signal(alias)
            if sig:
                return sig
                
        return None
    
    def _get_physical_values(self, sig: EDFSignal) -> List[float]:
        """Convert digital values to physical values"""
        return [val * sig.gain + sig.offset for val in sig.data]
    
    def parse_all_sessions(self) -> List[SessionData]:
        """
        Parse all session files in DATALOG directory.
        
        Returns:
            List of SessionData objects
        """
        files_by_date = self.scan_files()
        
        for session_date, file_paths in files_by_date.items():
            for filepath in file_paths:
                session = self.parse_session_file(filepath)
                if session:
                    self.sessions.append(session)
                    
        return self.sessions
    
    def get_sessions_by_date(self, target_date: date) -> List[SessionData]:
        """Get all sessions for a specific date"""
        return [s for s in self.sessions if s.date == target_date]
    
    def get_sessions_by_date_range(self, start: date, end: date) -> List[SessionData]:
        """Get sessions within a date range"""
        return [s for s in self.sessions if s.date and start <= s.date <= end]
