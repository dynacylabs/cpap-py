"""
Main API for reading and analyzing CPAP SD card data.
Provides high-level interface for accessing sessions, devices, and therapy data.
"""

import os
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any, Tuple
from collections import defaultdict

from cpap_py.models import Device, Session, SessionSummary, DeviceSettings, ValidationError
from cpap_py.parsers.edf_parser import (
    parse_str_file,
    identify_edf_type,
    parse_eve_file,
)
from cpap_py.parsers.tgt_parser import (
    parse_identification_file,
    parse_tgt_file,
    tgt_to_device_settings,
)
from cpap_py.parsers.crc_parser import CRCValidationMode, validate_directory_crcs


class CPAPReader:
    """
    Main interface for reading CPAP SD card data.
    
    Example usage:
        reader = CPAPReader("/path/to/sdcard")
        devices = reader.get_devices()
        sessions = reader.get_sessions()
        
        for session in sessions:
            print(f"AHI: {session.summary.ahi}")
            pressure_data = session.get_pressure_data()
    """
    
    def __init__(
        self,
        sdcard_path: str,
        crc_validation: CRCValidationMode = CRCValidationMode.PERMISSIVE,
        lazy_load: bool = True
    ):
        """
        Initialize CPAP reader.
        
        Args:
            sdcard_path: Path to SD card root directory
            crc_validation: CRC validation mode (strict, permissive, or disabled)
            lazy_load: If True, only parse files when requested. If False, parse everything immediately.
        """
        self.sdcard_path = Path(sdcard_path)
        self.crc_validation = crc_validation
        self.lazy_load = lazy_load
        
        # Validate path exists
        if not self.sdcard_path.exists():
            raise FileNotFoundError(f"SD card path not found: {sdcard_path}")
        
        # Storage
        self._devices: Optional[List[Device]] = None
        self._sessions: Optional[List[Session]] = None
        self._validation_errors: List[ValidationError] = []
        
        # STR.edf data (session times and summary stats)
        self._str_session_times: List[Tuple[datetime, datetime]] = []
        self._str_summary_stats: Dict[str, Any] = {}
        
        # File structure
        self._datalog_path = self.sdcard_path / "DATALOG"
        self._settings_path = self.sdcard_path / "SETTINGS"
        
        # Run initial scan
        self._scan_structure()
    
    def _scan_structure(self):
        """Scan SD card directory structure."""
        # Validate expected structure
        if not self._datalog_path.exists():
            self._validation_errors.append(ValidationError(
                file_path=str(self.sdcard_path),
                error_type="missing_directory",
                message="DATALOG directory not found",
                severity="error"
            ))
        
        if not self._settings_path.exists():
            self._validation_errors.append(ValidationError(
                file_path=str(self.sdcard_path),
                error_type="missing_directory",
                message="SETTINGS directory not found",
                severity="warning"
            ))
        
        # Optionally validate CRCs
        if self.crc_validation != CRCValidationMode.DISABLED:
            crc_results = validate_directory_crcs(str(self.sdcard_path), self.crc_validation)
            for file_path, result in crc_results.items():
                if not result["valid"]:
                    self._validation_errors.append(ValidationError(
                        file_path=file_path,
                        error_type="crc_mismatch",
                        message=result["error"],
                        severity="warning" if self.crc_validation == CRCValidationMode.PERMISSIVE else "error"
                    ))
    
    def get_devices(self) -> List[Device]:
        """
        Get list of devices found on SD card.
        
        Returns:
            List of Device objects
        """
        if self._devices is not None:
            return self._devices
        
        devices = []
        
        # Try to read Identification.tgt
        id_file = self.sdcard_path / "Identification.tgt"
        if id_file.exists():
            try:
                device_info = parse_identification_file(str(id_file))
                
                # Extract serial number from somewhere (might be in STR.edf or other files)
                # For now, use a placeholder
                serial_number = "UNKNOWN"
                
                # Try to extract from STR.edf header using custom parser
                str_file = self.sdcard_path / "STR.edf"
                if str_file.exists():
                    try:
                        from cpap_py.parsers.str_parser import parse_resmed_str_file
                        session_times, summary_stats = parse_resmed_str_file(str(str_file))
                        # Serial number is in recording_id
                        recording_id = summary_stats.get("recording_id", "")
                        if "SRN=" in recording_id:
                            parts = recording_id.split()
                            for part in parts:
                                if "SRN=" in part:
                                    serial_number = part.split("=")[1]
                                    break
                    except Exception:
                        # STR.edf parsing failed, use placeholder
                        pass
                
                device = Device(
                    serial_number=serial_number,
                    model_name="AirSense 10",  # Could parse from version info
                    firmware_version=str(device_info.get("software_version")) if device_info.get("software_version") else None,
                    last_updated=datetime.now()
                )
                devices.append(device)
                
            except Exception as e:
                self._validation_errors.append(ValidationError(
                    file_path=str(id_file),
                    error_type="parse_warning",
                    message=f"Could not fully parse identification file: {e}",
                    severity="warning"
                ))
        
        # If no identification file, create a generic device entry
        if not devices:
            devices.append(Device(
                serial_number="UNKNOWN",
                model_name="ResMed AirSense",
                last_updated=datetime.now()
            ))
        
        self._devices = devices
        return devices
    
    def get_sessions(
        self,
        device_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        min_duration_hours: float = 0.0
    ) -> List[Session]:
        """
        Get therapy sessions, optionally filtered.
        
        Args:
            device_id: Filter by device serial number
            start_date: Filter sessions on or after this date
            end_date: Filter sessions on or before this date
            min_duration_hours: Minimum session duration in hours
        
        Returns:
            List of Session objects
        """
        if self._sessions is None:
            self._load_sessions()
        
        sessions = self._sessions or []
        
        # Apply filters
        if device_id:
            sessions = [s for s in sessions if s.device_serial == device_id]
        
        if start_date:
            sessions = [s for s in sessions if s.date >= start_date]
        
        if end_date:
            sessions = [s for s in sessions if s.date <= end_date]
        
        if min_duration_hours > 0:
            sessions = [s for s in sessions if s.summary.duration_hours >= min_duration_hours]
        
        return sessions
    
    def _load_sessions(self):
        """Load all sessions from SD card."""
        sessions = []
        
        # Get device info
        devices = self.get_devices()
        device_serial = devices[0].serial_number if devices else "UNKNOWN"
        
        # Parse STR.edf for session times and summary stats
        str_file = self.sdcard_path / "STR.edf"
        
        if str_file.exists():
            try:
                self._str_session_times, self._str_summary_stats = parse_str_file(str(str_file))
            except Exception as e:
                # STR.edf may have non-standard format, this is not critical
                # We can still find sessions from DATALOG files
                self._validation_errors.append(ValidationError(
                    file_path=str(str_file),
                    error_type="parse_warning",
                    message=f"Could not parse STR.edf (non-critical): {e}",
                    severity="info"
                ))
        
        # Scan DATALOG directories for session files
        if self._datalog_path.exists():
            date_dirs = sorted([d for d in self._datalog_path.iterdir() if d.is_dir()])
            
            for date_dir in date_dirs:
                date_str = date_dir.name
                try:
                    session_date = datetime.strptime(date_str, "%Y%m%d").date()
                except ValueError:
                    continue
                
                # Group files by timestamp
                session_files = defaultdict(dict)
                
                for file_path in date_dir.glob("*.edf"):
                    # Parse filename: YYYYMMDD_HHMMSS_TYPE.edf
                    filename = file_path.stem
                    parts = filename.split("_")
                    
                    if len(parts) >= 3:
                        timestamp = f"{parts[0]}_{parts[1]}"
                        file_type = parts[2]
                        
                        session_files[timestamp][file_type] = file_path
                
                # Create session objects
                for timestamp, files in session_files.items():
                    # Parse timestamp
                    try:
                        start_time = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                    except ValueError:
                        continue
                    
                    # Create session with STR data for matching
                    session = self._create_session(
                        device_serial,
                        session_date,
                        start_time,
                        files,
                        str_session_times=self._str_session_times,
                        str_summary_stats=self._str_summary_stats
                    )
                    
                    if session:
                        sessions.append(session)
        
        self._sessions = sessions
    
    def _create_session(
        self,
        device_serial: str,
        session_date: date,
        start_time: datetime,
        files: Dict[str, Path],
        str_session_times: Optional[List[Tuple[datetime, datetime]]] = None,
        str_summary_stats: Optional[Dict[str, Any]] = None
    ) -> Optional[Session]:
        """Create a Session object from file paths and STR data."""
        
        # Determine which files are available
        has_brp = "BRP" in files
        has_pld = "PLD" in files
        has_sad = "SAD" in files or "SA2" in files
        has_eve = "EVE" in files
        has_csl = "CSL" in files
        
        # Try to match this DATALOG session to a STR session by time
        matched_str_session = self._match_str_session(start_time, str_session_times)
        
        # Extract summary statistics from STR data if available
        summary = self._create_session_summary(
            start_time,
            matched_str_session,
            str_summary_stats
        )
        
        # Load settings (try to find appropriate settings file)
        settings = DeviceSettings()
        if self._settings_path.exists():
            # Find a settings file - this is simplified
            tgt_files = list(self._settings_path.glob("*.tgt"))
            if tgt_files:
                try:
                    tgt_data = parse_tgt_file(str(tgt_files[0]))
                    settings = tgt_to_device_settings(tgt_data)
                except Exception:
                    pass
        
        session_id = f"{device_serial}_{start_time.strftime('%Y%m%d_%H%M%S')}"
        
        session = Session(
            session_id=session_id,
            device_serial=device_serial,
            date=session_date,
            start_time=start_time,
            summary=summary,
            settings=settings,
            has_pressure_data=has_brp or has_pld,
            has_flow_data=has_brp,
            has_spo2_data=has_sad,
            has_events=has_eve,
            _brp_file=str(files.get("BRP")) if "BRP" in files else None,
            _pld_file=str(files.get("PLD")) if "PLD" in files else None,
            _sad_file=str(files.get("SAD") or files.get("SA2")) if has_sad else None,
            _eve_file=str(files.get("EVE")) if "EVE" in files else None,
            _csl_file=str(files.get("CSL")) if "CSL" in files else None,
        )
        
        return session
    
    def _match_str_session(
        self,
        datalog_time: datetime,
        str_session_times: Optional[List[Tuple[datetime, datetime]]]
    ) -> Optional[Tuple[datetime, datetime]]:
        """Match a DATALOG session time to the closest STR session.
        
        Args:
            datalog_time: Start time from DATALOG filename
            str_session_times: List of (mask_on, mask_off) tuples from STR.edf
        
        Returns:
            Matched (mask_on, mask_off) tuple or None
        """
        if not str_session_times:
            return None
        
        # Find the STR session that best matches this DATALOG time
        # Look for STR session where DATALOG time falls within or is close to the session
        best_match = None
        min_distance = timedelta(hours=2)  # Max 2 hour tolerance
        
        for mask_on, mask_off in str_session_times:
            # Check if DATALOG time falls within STR session
            if mask_on <= datalog_time <= mask_off:
                return (mask_on, mask_off)
            
            # Otherwise check distance to session start
            distance = abs(datalog_time - mask_on)
            if distance < min_distance:
                min_distance = distance
                best_match = (mask_on, mask_off)
        
        return best_match
    
    def _find_str_session_index(
        self,
        matched_session: Tuple[datetime, datetime],
        all_str_sessions: List[Tuple[datetime, datetime]]
    ) -> int:
        """Find the index of a matched STR session in the full list.
        
        This is used to extract the correct session's data from STR signal arrays.
        
        Args:
            matched_session: The matched (mask_on, mask_off) tuple
            all_str_sessions: All STR sessions from STR.edf
        
        Returns:
            Index of the session (0-based)
        """
        try:
            return all_str_sessions.index(matched_session)
        except (ValueError, AttributeError):
            # If not found, default to first session
            return 0
    
    def _create_session_summary(
        self,
        start_time: datetime,
        matched_str_session: Optional[Tuple[datetime, datetime]],
        str_summary_stats: Optional[Dict[str, Any]]
    ) -> SessionSummary:
        """Create SessionSummary with data from STR.edf if available.
        
        Args:
            start_time: Session start time from DATALOG
            matched_str_session: Matched (mask_on, mask_off) from STR
            str_summary_stats: Summary statistics from STR.edf
        
        Returns:
            SessionSummary object with populated data
        """
        # Extract session-specific summary from STR data
        from cpap_py.parsers.str_parser import extract_session_summary_from_str
        
        # Default values
        duration_seconds = 0
        mask_on_time = start_time
        mask_off_time = None
        str_data = {}
        
        # Use matched STR session if available
        if matched_str_session:
            mask_on_time = matched_str_session[0]
            mask_off_time = matched_str_session[1]
            duration_seconds = (mask_off_time - mask_on_time).total_seconds()
            
            # Try to find which session index this corresponds to in STR data
            if str_summary_stats and 'signals' in str_summary_stats:
                # Find the session index by matching the mask_on time
                session_idx = self._find_str_session_index(
                    matched_str_session,
                    self._str_session_times
                )
                
                str_data = extract_session_summary_from_str(
                    str_summary_stats['signals'],
                    session_idx=session_idx
                )
        
        # Create summary with STR data or defaults
        summary = SessionSummary(
            duration_seconds=duration_seconds,
            duration_hours=duration_seconds / 3600.0,
            mask_on_time=mask_on_time,
            mask_off_time=mask_off_time,
            # Populate from STR data if available
            ahi=str_data.get('ahi'),
            ai=str_data.get('ai'),
            hi=str_data.get('hi'),
            pressure_median=str_data.get('pressure_median'),
            pressure_95th=str_data.get('pressure_95th'),
            leak_median=str_data.get('leak_median'),
            leak_95th=str_data.get('leak_95th'),
            leak_max=str_data.get('leak_max'),
            spo2_median=str_data.get('spo2_median'),
            tidal_volume_median=str_data.get('tidal_volume_median'),
            minute_ventilation_median=str_data.get('minute_ventilation_median'),
            respiratory_rate_median=str_data.get('respiratory_rate_median'),
        )
        
        return summary
    
    def get_validation_errors(self) -> List[ValidationError]:
        """Get list of validation errors encountered during parsing."""
        return self._validation_errors
    
    def get_summary_statistics(
        self,
        device_id: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get aggregate statistics across multiple sessions.
        
        Args:
            device_id: Filter by device
            days: Number of recent days to include
        
        Returns:
            Dictionary of aggregate statistics
        """
        from datetime import timedelta
        
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        sessions = self.get_sessions(
            device_id=device_id,
            start_date=start_date,
            end_date=end_date
        )
        
        if not sessions:
            return {}
        
        # Calculate aggregates
        total_sessions = len(sessions)
        total_hours = sum(s.summary.duration_hours for s in sessions)
        avg_hours = total_hours / total_sessions if total_sessions > 0 else 0
        
        # AHI statistics
        ahis = [s.summary.ahi for s in sessions if s.summary.ahi is not None]
        avg_ahi = sum(ahis) / len(ahis) if ahis else None
        
        # Leak statistics
        leak_95ths = [s.summary.leak_95th for s in sessions if s.summary.leak_95th is not None]
        avg_leak_95th = sum(leak_95ths) / len(leak_95ths) if leak_95ths else None
        
        return {
            "period_days": days,
            "total_sessions": total_sessions,
            "total_hours": total_hours,
            "average_hours_per_session": avg_hours,
            "average_ahi": avg_ahi,
            "average_leak_95th": avg_leak_95th,
            "sessions": [s.to_dict() for s in sessions],
        }
    
    def export_to_dict(self) -> Dict[str, Any]:
        """
        Export all data to a JSON-serializable dictionary.
        Useful for MCP responses.
        
        Returns:
            Complete data export as dictionary
        """
        return {
            "devices": [d.model_dump() for d in self.get_devices()],
            "sessions": [s.to_dict() for s in self.get_sessions()],
            "validation_errors": [e.model_dump() for e in self._validation_errors],
        }
