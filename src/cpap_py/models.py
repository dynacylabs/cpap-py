"""
Data models for CPAP data representation using Pydantic for validation and serialization.
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from enum import Enum

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field, ConfigDict


class EventType(str, Enum):
    """Types of respiratory events recorded by CPAP machines."""
    
    OBSTRUCTIVE_APNEA = "OA"
    CENTRAL_APNEA = "CA"
    HYPOPNEA = "H"
    APNEA = "A"  # Unclassified
    FLOW_LIMITATION = "FL"
    RERA = "RE"  # Respiratory Effort Related Arousal
    VIBRATORY_SNORE = "VS"
    PERIODIC_BREATHING = "PB"
    CHEYNE_STOKES = "CSR"  # Cheyne-Stokes Respiration
    CLEAR_AIRWAY = "CA"
    LARGE_LEAK = "LL"
    MASK_ON = "mask_on"
    MASK_OFF = "mask_off"


class CPAPMode(str, Enum):
    """CPAP therapy modes."""
    
    CPAP = "CPAP"
    APAP = "APAP"
    BILEVEL_T = "BiLevel-T"
    BILEVEL_S = "BiLevel-S"
    BILEVEL_ST = "BiLevel-S/T"
    BILEVEL_AUTO = "BiLevel-Auto"
    ASV = "ASV"
    ASV_AUTO = "ASVAuto"
    IVAPS = "iVAPS"
    AUTO_FOR_HER = "Auto for Her"


class MaskType(str, Enum):
    """Types of CPAP masks."""
    
    NASAL = "Nasal"
    PILLOWS = "Pillows"
    FULL_FACE = "Full Face"
    UNKNOWN = "Unknown"


class Device(BaseModel):
    """Represents a CPAP device."""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    serial_number: str
    model_name: str = "AirSense 10"
    model_id: Optional[int] = None
    firmware_version: Optional[str] = None
    last_updated: Optional[datetime] = None
    
    def model_dump_json(self, **kwargs) -> str:
        """Override to handle datetime serialization."""
        return super().model_dump_json(exclude_none=True, **kwargs)


class Event(BaseModel):
    """Represents a respiratory or device event."""
    
    type: EventType
    timestamp: datetime
    duration: Optional[float] = Field(None, description="Duration in seconds")
    data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional event data")


class WaveformData(BaseModel):
    """Container for time-series waveform data."""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    channel_name: str
    unit: str
    sample_rate: float = Field(description="Samples per second")
    start_time: datetime
    values: np.ndarray = Field(description="Time series values")
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert to pandas DataFrame with datetime index."""
        timestamps = pd.date_range(
            start=self.start_time,
            periods=len(self.values),
            freq=pd.Timedelta(seconds=1/self.sample_rate)
        )
        return pd.DataFrame({
            self.channel_name: self.values
        }, index=timestamps)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return {
            "channel_name": self.channel_name,
            "unit": self.unit,
            "sample_rate": self.sample_rate,
            "start_time": self.start_time.isoformat(),
            "values": self.values.tolist(),
            "length": len(self.values),
        }


class SessionSummary(BaseModel):
    """Summary statistics for a therapy session."""
    
    # Duration metrics
    duration_seconds: float
    duration_hours: float
    
    # Mask metrics
    mask_on_time: Optional[datetime] = None
    mask_off_time: Optional[datetime] = None
    
    # Therapy effectiveness
    ahi: Optional[float] = Field(None, description="Apnea-Hypopnea Index (events/hour)")
    ai: Optional[float] = Field(None, description="Apnea Index")
    hi: Optional[float] = Field(None, description="Hypopnea Index")
    
    # Event counts
    obstructive_apneas: Optional[int] = 0
    central_apneas: Optional[int] = 0
    hypopneas: Optional[int] = 0
    flow_limitations: Optional[int] = 0
    reras: Optional[int] = 0
    
    # Pressure statistics (cmH2O)
    pressure_min: Optional[float] = None
    pressure_max: Optional[float] = None
    pressure_median: Optional[float] = None
    pressure_95th: Optional[float] = None
    
    # Leak statistics (L/min)
    leak_median: Optional[float] = None
    leak_95th: Optional[float] = None
    leak_max: Optional[float] = None
    leak_total: Optional[float] = None
    
    # Flow statistics
    tidal_volume_median: Optional[float] = Field(None, description="Median tidal volume (L)")
    minute_ventilation_median: Optional[float] = Field(None, description="Median minute vent (L/min)")
    respiratory_rate_median: Optional[float] = Field(None, description="Median breaths/min")
    
    # SpO2 statistics (percentage)
    spo2_median: Optional[float] = None
    spo2_min: Optional[float] = None
    spo2_below_88_percent: Optional[float] = Field(None, description="% time SpO2 < 88%")
    
    # Additional metrics
    csr_time: Optional[float] = Field(None, description="Cheyne-Stokes respiration time")
    periodic_breathing_percent: Optional[float] = None


class DeviceSettings(BaseModel):
    """Device configuration settings."""
    
    # Core therapy settings
    mode: Optional[CPAPMode] = None
    pressure: Optional[float] = Field(None, description="Fixed pressure (CPAP mode)")
    pressure_min: Optional[float] = Field(None, description="Min pressure (APAP mode)")
    pressure_max: Optional[float] = Field(None, description="Max pressure (APAP mode)")
    
    # EPR (Expiratory Pressure Relief)
    epr_enabled: Optional[bool] = None
    epr_level: Optional[int] = Field(None, ge=0, le=3, description="EPR level 0-3")
    epr_type: Optional[str] = Field(None, description="Full-time or Ramp-only")
    
    # BiLevel settings
    ipap: Optional[float] = Field(None, description="Inspiratory pressure")
    epap: Optional[float] = Field(None, description="Expiratory pressure")
    
    # Ramp settings
    ramp_enabled: Optional[bool] = None
    ramp_time: Optional[int] = Field(None, description="Ramp time in minutes")
    ramp_start_pressure: Optional[float] = None
    
    # Comfort features
    smart_start: Optional[bool] = None
    auto_stop: Optional[bool] = None
    mask_type: Optional[MaskType] = None
    tube_type: Optional[str] = None
    
    # Humidifier
    humidifier_enabled: Optional[bool] = None
    humidifier_level: Optional[int] = Field(None, ge=0, le=8)
    climate_control: Optional[str] = None
    temperature_enabled: Optional[bool] = None
    temperature: Optional[float] = None
    
    # Response settings
    response: Optional[str] = Field(None, description="AutoSet response (Standard/Soft/For Her)")
    
    # Access and filters
    patient_access_enabled: Optional[bool] = None
    antibacterial_filter: Optional[bool] = None


class Session(BaseModel):
    """Represents a complete therapy session."""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    session_id: str
    device_serial: str
    date: date
    start_time: datetime
    end_time: Optional[datetime] = None
    
    summary: SessionSummary
    settings: DeviceSettings
    
    # Data availability flags
    has_pressure_data: bool = False
    has_flow_data: bool = False
    has_spo2_data: bool = False
    has_events: bool = False
    
    # File references (for lazy loading)
    _brp_file: Optional[str] = None
    _pld_file: Optional[str] = None
    _sad_file: Optional[str] = None
    _eve_file: Optional[str] = None
    _csl_file: Optional[str] = None
    
    # Cached data (populated on demand)
    _events: Optional[List[Event]] = None
    _waveforms: Optional[Dict[str, WaveformData]] = None
    
    def get_events(self, event_type: Optional[EventType] = None) -> List[Event]:
        """Get events for this session, optionally filtered by type."""
        if self._events is None:
            # Lazy load events from EVE file
            from cpap_py.parsers.edf_parser import parse_eve_file
            if self._eve_file:
                self._events = parse_eve_file(self._eve_file, self.start_time)
            else:
                self._events = []
        
        if event_type:
            return [e for e in self._events if e.type == event_type]
        return self._events
    
    def get_pressure_data(self) -> Optional[pd.DataFrame]:
        """Get pressure waveform data as DataFrame."""
        if not self.has_pressure_data:
            return None
        
        from cpap_py.parsers.edf_parser import parse_pressure_file
        if self._brp_file:
            waveforms = parse_pressure_file(self._brp_file)
            # Combine multiple pressure channels into single DataFrame
            dfs = [w.to_dataframe() for w in waveforms if 'pressure' in w.channel_name.lower()]
            if dfs:
                return pd.concat(dfs, axis=1)
        return None
    
    def get_flow_data(self) -> Optional[pd.DataFrame]:
        """Get flow waveform data as DataFrame."""
        if not self.has_flow_data:
            return None
        
        from cpap_py.parsers.edf_parser import parse_pressure_file
        if self._brp_file:
            waveforms = parse_pressure_file(self._brp_file)
            dfs = [w.to_dataframe() for w in waveforms if 'flow' in w.channel_name.lower()]
            if dfs:
                return pd.concat(dfs, axis=1)
        return None
    
    def get_spo2_data(self) -> Optional[pd.DataFrame]:
        """Get SpO2 waveform data as DataFrame."""
        if not self.has_spo2_data:
            return None
        
        from cpap_py.parsers.edf_parser import parse_spo2_file
        if self._sad_file:
            waveforms = parse_spo2_file(self._sad_file)
            if waveforms:
                return pd.concat([w.to_dataframe() for w in waveforms], axis=1)
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return {
            "session_id": self.session_id,
            "device_serial": self.device_serial,
            "date": self.date.isoformat(),
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "summary": self.summary.model_dump(),
            "settings": self.settings.model_dump(),
            "has_pressure_data": self.has_pressure_data,
            "has_flow_data": self.has_flow_data,
            "has_spo2_data": self.has_spo2_data,
            "has_events": self.has_events,
        }


class ValidationError(BaseModel):
    """Represents a data validation error."""
    
    file_path: str
    error_type: str
    message: str
    severity: str = "warning"  # warning, error, critical
    timestamp: datetime = Field(default_factory=datetime.now)
