"""
EDF (European Data Format) file parser for ResMed CPAP data files.
Handles BRP, PLD, SAD, EVE, and CSL file types.
"""

import os
import gzip
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Dict, Any
from pathlib import Path

import numpy as np
import pyedflib

from cpap_py.models import WaveformData, Event, EventType, SessionSummary
from cpap_py.utils.constants import CHANNEL_CODES, CHANNEL_UNITS, EVENT_TYPE_MAP


class EDFParser:
    """Base parser for EDF files."""
    
    def __init__(self, file_path: str, validate_crc: bool = True):
        """
        Initialize EDF parser.
        
        Args:
            file_path: Path to EDF file (can be .edf or .edf.gz)
            validate_crc: Whether to validate CRC checksums
        """
        self.file_path = file_path
        self.validate_crc = validate_crc
        self._is_compressed = file_path.endswith('.gz')
    
    def _open_file(self) -> pyedflib.EdfReader:
        """Open EDF file, handling compression if needed."""
        if self._is_compressed:
            # pyedflib doesn't support compressed files directly
            # We'd need to decompress to temp file or memory
            raise NotImplementedError("Compressed EDF files not yet supported")
        
        return pyedflib.EdfReader(self.file_path)
    
    def get_header_info(self) -> Dict[str, Any]:
        """Extract header information from EDF file."""
        with self._open_file() as edf:
            return {
                "patient_id": edf.getPatientCode(),
                "recording_id": edf.getAdmincode(),
                "start_time": edf.getStartdatetime(),
                "duration_seconds": edf.getFileDuration(),
                "num_signals": edf.signals_in_file,
                "signal_labels": edf.getSignalLabels(),
            }
    
    def get_signal_info(self, signal_index: int) -> Dict[str, Any]:
        """Get detailed information about a specific signal."""
        with self._open_file() as edf:
            if signal_index >= edf.signals_in_file:
                raise ValueError(f"Signal index {signal_index} out of range")
            
            return {
                "label": edf.getLabel(signal_index),
                "sample_frequency": edf.getSampleFrequency(signal_index),
                "physical_dimension": edf.getPhysicalDimension(signal_index),
                "physical_min": edf.getPhysicalMinimum(signal_index),
                "physical_max": edf.getPhysicalMaximum(signal_index),
                "digital_min": edf.getDigitalMinimum(signal_index),
                "digital_max": edf.getDigitalMaximum(signal_index),
                "prefilter": edf.getPrefilter(signal_index),
                "transducer": edf.getTransducer(signal_index),
            }
    
    def read_signal(self, signal_index: int) -> np.ndarray:
        """Read signal data from EDF file."""
        with self._open_file() as edf:
            return edf.readSignal(signal_index)
    
    def read_all_signals(self) -> List[Tuple[str, np.ndarray, Dict[str, Any]]]:
        """Read all signals from file."""
        signals = []
        with self._open_file() as edf:
            for i in range(edf.signals_in_file):
                label = edf.getLabel(i)
                data = edf.readSignal(i)
                
                # Get signal info directly without reopening file
                info = {
                    "label": edf.getLabel(i),
                    "sample_frequency": edf.getSampleFrequency(i),
                    "physical_dimension": edf.getPhysicalDimension(i),
                    "physical_min": edf.getPhysicalMinimum(i),
                    "physical_max": edf.getPhysicalMaximum(i),
                    "digital_min": edf.getDigitalMinimum(i),
                    "digital_max": edf.getDigitalMaximum(i),
                    "prefilter": edf.getPrefilter(i),
                    "transducer": edf.getTransducer(i),
                }
                
                signals.append((label, data, info))
        return signals
    
    def read_annotations(self) -> List[Tuple[float, Optional[float], str]]:
        """
        Read EDF+ annotations.
        
        Returns:
            List of (onset_time, duration, annotation_text) tuples
        """
        try:
            with self._open_file() as edf:
                annotations = edf.readAnnotations()
                return annotations
        except Exception:
            return []


def parse_pressure_file(file_path: str, start_time: Optional[datetime] = None) -> List[WaveformData]:
    """
    Parse BRP (Breathing/Respiratory/Pressure) EDF file.
    
    Contains high-resolution waveform data for:
    - Mask pressure (high-res @ 25Hz from Press.40ms)
    - Flow rate (high-res @ 25Hz from Flow.40ms)
    - Tidal volume
    - Respiratory rate
    - Leak rate
    - Flow Limitation (IMPORTANT clinical signal)
    - Snore detection
    - EPAP (for BiLevel/EPR machines)
    - Target Ventilation (for adaptive modes)
    
    Args:
        file_path: Path to BRP EDF file
        start_time: Session start time (from STR file), uses EDF header if None
    
    Returns:
        List of WaveformData objects, one per channel
        Note: Prioritizes high-resolution signals over low-resolution
    """
    parser = EDFParser(file_path)
    header = parser.get_header_info()
    
    if start_time is None:
        start_time = header["start_time"]
    
    waveforms = []
    signals = parser.read_all_signals()
    
    # Track which standard names we've seen to prioritize high-res signals
    seen_signals = {}
    
    for label, data, info in signals:
        # Skip annotation channels and CRC channels
        if "Annotation" in label or label.strip() == "" or "crc" in label.lower():
            continue
        
        # Map label to standard name using comprehensive mapping
        raw_label = label.strip()
        channel_name = CHANNEL_CODES.get(raw_label, raw_label)
        
        # Prioritize high-resolution signals over low-resolution
        # If we've seen this channel before, check if new one is higher res
        if channel_name in seen_signals:
            existing_freq = seen_signals[channel_name]["frequency"]
            new_freq = info["sample_frequency"]
            
            # Keep the higher frequency signal
            if new_freq <= existing_freq:
                continue  # Skip lower resolution version
            else:
                # Remove lower resolution version, will add higher res
                waveforms = [w for w in waveforms if w.channel_name != channel_name]
        
        # Get unit from signal or our mapping
        unit = info["physical_dimension"].strip() if info["physical_dimension"] else ""
        if not unit:
            unit = CHANNEL_UNITS.get(channel_name, "")
        
        # Convert L/s to L/min for leak and flow rate to match C# implementation
        if channel_name in ["Flow Rate", "Leak Rate"]:
            if unit == "L/s":
                data = data * 60.0  # Convert L/s to L/min
                unit = "L/min"
        
        waveform = WaveformData(
            channel_name=channel_name,
            unit=unit,
            sample_rate=info["sample_frequency"],
            start_time=start_time,
            values=data,
        )
        waveforms.append(waveform)
        
        # Track this signal
        seen_signals[channel_name] = {
            "frequency": info["sample_frequency"],
            "label": raw_label
        }
    
    return waveforms


def parse_detailed_pressure_file(file_path: str, start_time: Optional[datetime] = None) -> List[WaveformData]:
    """
    Parse PLD (Detailed Pressure) EDF file.
    
    Contains higher resolution pressure data, typically at 25 Hz or higher.
    
    Args:
        file_path: Path to PLD EDF file
        start_time: Session start time
    
    Returns:
        List of WaveformData objects
    """
    # PLD files have similar structure to BRP but higher sampling rate
    return parse_pressure_file(file_path, start_time)


def parse_spo2_file(file_path: str, start_time: Optional[datetime] = None) -> List[WaveformData]:
    """
    Parse SAD (SpO2/Oximetry) EDF file.
    
    Contains:
    - SpO2 (oxygen saturation) percentage
    - Pulse rate (heart rate)
    
    Args:
        file_path: Path to SAD EDF file
        start_time: Session start time
    
    Returns:
        List of WaveformData objects for SpO2 and pulse
    """
    parser = EDFParser(file_path)
    header = parser.get_header_info()
    
    if start_time is None:
        start_time = header["start_time"]
    
    waveforms = []
    signals = parser.read_all_signals()
    
    for label, data, info in signals:
        if "Annotation" in label or label.strip() == "":
            continue
        
        # Clean up label
        channel_name = label.strip()
        if "SpO2" in label or "Pulse" in label:
            channel_name = CHANNEL_CODES.get(label, channel_name)
        
        unit = info["physical_dimension"] or CHANNEL_UNITS.get(channel_name, "")
        
        waveform = WaveformData(
            channel_name=channel_name,
            unit=unit,
            sample_rate=info["sample_frequency"],
            start_time=start_time,
            values=data,
        )
        waveforms.append(waveform)
    
    return waveforms


def parse_eve_file(file_path: str, start_time: datetime) -> List[Event]:
    """
    Parse EVE (Events) EDF file.
    
    Contains annotations for respiratory events:
    - Obstructive apneas
    - Central apneas
    - Hypopneas
    - Flow limitations
    - RERAs
    - Large leaks
    
    Args:
        file_path: Path to EVE EDF file
        start_time: Session start time (for absolute timestamps)
    
    Returns:
        List of Event objects
    """
    annotations = []
    
    # Try standard parser first
    try:
        parser = EDFParser(file_path)
        annotations = parser.read_annotations()
    except (OSError, Exception) as e:
        # If pyedflib fails (discontinuous file), annotations will be empty
        pass
    
    # If no annotations found, try custom parser (handles discontinuous files)
    if not annotations:
        from cpap_py.parsers.eve_parser import parse_resmed_eve_file
        annotations = parse_resmed_eve_file(file_path)
    
    events = []
    for onset, duration, text in annotations:
        # Parse event type from annotation text
        event_type_str = EVENT_TYPE_MAP.get(text.strip(), None)
        
        if event_type_str is None:
            # Try partial matching
            for key, value in EVENT_TYPE_MAP.items():
                if key.lower() in text.lower():
                    event_type_str = value
                    break
        
        if event_type_str:
            try:
                event_type = EventType(event_type_str)
            except ValueError:
                # Unknown event type, skip
                continue
            
            event_time = start_time + timedelta(seconds=onset)
            
            event = Event(
                type=event_type,
                timestamp=event_time,
                duration=duration,
                data={"annotation": text}
            )
            events.append(event)
    
    return events


def parse_csl_file(file_path: str, start_time: datetime) -> Tuple[List[Event], Dict[str, Any]]:
    """
    Parse CSL (Clinical Summary / Cheyne-Stokes) EDF file.
    
    Contains:
    - Cheyne-Stokes Respiration (CSR) events with timing
    - Session-level clinical summary annotations
    - Additional respiratory pattern data
    
    Args:
        file_path: Path to CSL EDF file
        start_time: Session start time for event timestamps
    
    Returns:
        Tuple of (events_list, summary_data)
        - events_list: CSR events with start/end times
        - summary_data: Dictionary of summary statistics
    """
    parser = EDFParser(file_path)
    
    # CSL files contain both annotations and potentially signal data
    annotations = parser.read_annotations()
    
    events = []
    summary_data = {}
    csr_start_time = None
    
    for onset, duration, text in annotations:
        # Skip timekeeping annotations
        if not text or text.startswith("+") or text.startswith("Recording"):
            continue
        
        # Check for Cheyne-Stokes events
        text_lower = text.lower()
        
        if "csr" in text_lower or "cheyne" in text_lower:
            if "start" in text_lower or "begin" in text_lower:
                csr_start_time = onset
            elif "end" in text_lower and csr_start_time is not None:
                # Create CSR event with duration
                event_time = start_time + timedelta(seconds=csr_start_time)
                event_duration = onset - csr_start_time
                
                event = Event(
                    type=EventType.CHEYNE_STOKES,
                    timestamp=event_time,
                    duration=event_duration,
                    data={"annotation": "Cheyne-Stokes Respiration"}
                )
                events.append(event)
                csr_start_time = None
        
        # Parse key-value summary data
        if ":" in text or "=" in text:
            parts = text.replace("=", ":").split(":", 1)
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip()
                summary_data[key] = value
    
    return events, summary_data


def parse_str_file(file_path: str) -> Tuple[List[Tuple[datetime, datetime]], Dict[str, Any]]:
    """
    Parse STR.edf (Summary Statistics) file.
    
    This is the master summary file containing:
    - Mask on/off times for all sessions
    - Daily summary statistics
    - Device settings for each day
    
    Args:
        file_path: Path to STR.edf file
    
    Returns:
        Tuple of (session_times, summary_stats)
        - session_times: List of (mask_on, mask_off) datetime tuples
        - summary_stats: Dictionary of summary data by date
    """
    # Use custom parser for ResMed's non-compliant STR files
    from cpap_py.parsers.str_parser import parse_resmed_str_file
    
    try:
        return parse_resmed_str_file(file_path)
    except Exception as e:
        # Fallback to empty results if parsing fails
        import logging
        logging.warning(f"Failed to parse STR file {file_path}: {e}")
        return ([], {})


def identify_edf_type(file_path: str) -> str:
    """
    Identify the type of EDF file based on filename.
    
    Args:
        file_path: Path to EDF file
    
    Returns:
        File type identifier (BRP, PLD, SAD, EVE, CSL, STR, or UNKNOWN)
    """
    filename = Path(file_path).name.upper()
    
    if "STR" in filename:
        return "STR"
    
    # Extract the type code from filename (usually last part before extension)
    # Format: YYYYMMDD_HHMMSS_TYPE.edf
    parts = filename.replace(".EDF", "").replace(".GZ", "").split("_")
    if len(parts) >= 3:
        type_code = parts[-1]
        if type_code in ["BRP", "PLD", "SAD", "SA2", "EVE", "CSL", "AEV"]:
            return type_code
    
    return "UNKNOWN"
