"""
STR.edf parser for ResMed CPAP summary data.

The STR.edf file contains daily summary statistics and settings
for each day of CPAP usage.
"""

from datetime import datetime, date, time, timedelta
from pathlib import Path
from typing import List, Optional, Dict
from dataclasses import dataclass, field
from .edf_parser import EDFParser, EDFSignal


@dataclass
class STRRecord:
    """Daily summary record from STR.edf"""
    date: Optional[date] = None
    
    # Mask on/off times (timestamps in seconds since epoch)
    mask_on: List[int] = field(default_factory=list)
    mask_off: List[int] = field(default_factory=list)
    mask_events: int = 0
    mask_duration: float = 0.0
    
    # Therapy mode
    mode: int = 0  # CPAP mode
    rms9_mode: int = 0  # ResMed-specific mode code
    
    # Pressure settings
    min_pressure: float = 0.0
    max_pressure: float = 0.0
    set_pressure: float = 0.0
    ramp_pressure: float = 0.0
    
    # BiLevel settings
    ipap: float = 0.0
    epap: float = 0.0
    min_ipap: float = 0.0
    max_ipap: float = 0.0
    min_epap: float = 0.0
    max_epap: float = 0.0
    ps: float = 0.0
    min_ps: float = 0.0
    max_ps: float = 0.0
    epap_auto: int = 0
    
    # EPR (Expiratory Pressure Relief)
    epr: int = -1
    epr_level: int = -1
    
    # Statistics (leak)
    leak_50: float = 0.0  # Median leak
    leak_95: float = 0.0  # 95th percentile leak
    leak_max: float = 0.0  # Maximum leak
    
    # Statistics (respiratory rate)
    rr_50: float = 0.0  # Median respiratory rate
    rr_95: float = 0.0
    rr_max: float = 0.0
    
    # Statistics (minute ventilation)
    mv_50: float = 0.0
    mv_95: float = 0.0
    mv_max: float = 0.0
    
    # Statistics (tidal volume)
    tv_50: float = 0.0
    tv_95: float = 0.0
    tv_max: float = 0.0
    
    # Statistics (mask pressure)
    mp_50: float = 0.0
    mp_95: float = 0.0
    mp_max: float = 0.0
    
    # Statistics (target EPAP/IPAP)
    tgt_epap_50: float = 0.0
    tgt_epap_95: float = 0.0
    tgt_epap_max: float = 0.0
    tgt_ipap_50: float = 0.0
    tgt_ipap_95: float = 0.0
    tgt_ipap_max: float = 0.0
    
    # Statistics (I:E ratio)
    ie_50: float = 0.0
    ie_95: float = 0.0
    ie_max: float = 0.0
    
    # Event indices
    ahi: float = 0.0  # Apnea-Hypopnea Index
    ai: float = 0.0   # Apnea Index
    hi: float = 0.0   # Hypopnea Index
    uai: float = 0.0  # Unobstructed Apnea Index
    cai: float = 0.0  # Central Apnea Index
    oai: float = 0.0  # Obstructive Apnea Index
    csr: float = 0.0  # Cheyne-Stokes Respiration
    
    # Settings
    s_ramp_time: float = -1
    s_ramp_enable: int = -1
    s_epr_enable: int = -1
    s_epr_clin_enable: int = -1
    s_comfort: int = -1
    s_ab_filter: int = -1
    s_climate_control: int = -1
    s_mask: int = -1
    s_pt_access: int = -1
    s_pt_view: int = -1
    s_smart_start: int = -1
    s_smart_stop: int = -1
    s_hum_enable: int = -1
    s_hum_level: int = -1
    s_temp_enable: int = -1
    s_temp: float = -1
    s_tube: int = -1
    s_easy_breathe: int = -1
    s_rise_enable: int = -1
    s_rise_time: float = -1
    s_cycle: int = -1
    s_trigger: int = -1
    s_ti_max: float = -1
    s_ti_min: float = -1


class STRParser:
    """Parser for STR.edf summary files"""
    
    # CPAP Mode constants
    MODE_UNKNOWN = 0
    MODE_CPAP = 1
    MODE_APAP = 2
    MODE_BILEVEL_FIXED = 3
    MODE_BILEVEL_AUTO_FIXED_PS = 4
    MODE_BILEVEL_AUTO_VARIABLE_PS = 5
    MODE_ASV = 6
    MODE_ASV_VARIABLE_EPAP = 7
    MODE_AVAPS = 8
    MODE_TRILEVEL_AUTO_VARIABLE_PDIFF = 9
    
    def __init__(self, filepath: str, serial_number: Optional[str] = None):
        """
        Initialize STR parser.
        
        Args:
            filepath: Path to STR.edf file
            serial_number: Expected serial number (for verification)
        """
        self.filepath = Path(filepath)
        self.serial_number = serial_number
        self.edf = EDFParser(str(filepath))
        self.records: List[STRRecord] = []
        
    def parse(self) -> bool:
        """
        Parse STR.edf file.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.edf.parse():
            return False
            
        # Extract records
        num_records = self.edf.header.num_data_records
        start_date = self.edf.header.start_date
        
        if not start_date:
            print("Error: No start date in STR.edf header")
            return False
            
        # Get key signals
        mask_on = self.edf.get_signal("Mask On") or self.edf.get_signal("MaskOn")
        mask_off = self.edf.get_signal("Mask Off") or self.edf.get_signal("MaskOff")
        mask_events = self.edf.get_signal("Mask Events") or self.edf.get_signal("MaskEvents")
        
        if not mask_on or not mask_off or not mask_events:
            print("Error: Missing required signals in STR.edf")
            return False
            
        # Parse each day's record
        for rec_idx in range(num_records):
            record_date = start_date.date() + timedelta(days=rec_idx)
            record = self._parse_record(rec_idx, record_date, mask_on, mask_off, mask_events)
            if record:
                self.records.append(record)
                
        return True
    
    def _parse_record(self, rec_idx: int, record_date: date, 
                     mask_on: EDFSignal, mask_off: EDFSignal, 
                     mask_events: EDFSignal) -> Optional[STRRecord]:
        """Parse a single daily record"""
        
        record = STRRecord()
        record.date = record_date
        
        # Calculate noon timestamp for this date
        noon_dt = datetime.combine(record_date, time(12, 0, 0))
        noon_stamp = int(noon_dt.timestamp())
        
        # Parse mask on/off times
        rec_start = rec_idx * mask_on.sample_count
        record.mask_on = []
        record.mask_off = []
        
        valid_day = False
        for i in range(mask_on.sample_count):
            on_val = mask_on.data[rec_start + i]
            off_val = mask_off.data[rec_start + i]
            
            # Values are minutes since noon
            if on_val > 0:
                record.mask_on.append(noon_stamp + (on_val * 60))
            else:
                record.mask_on.append(0)
                
            if off_val > 0:
                record.mask_off.append(noon_stamp + (off_val * 60))
                valid_day = True
            else:
                record.mask_off.append(0)
                
        if not valid_day:
            return None  # Skip days with no mask events
            
        # Handle session spanning noon
        if record.mask_on[0] == 0 and record.mask_off[0] > 0:
            record.mask_on[0] = noon_stamp
            
        record.mask_events = mask_events.data[rec_idx]
        
        # Parse other statistics and settings
        self._parse_statistics(rec_idx, record)
        self._parse_settings(rec_idx, record)
        
        return record
    
    def _parse_statistics(self, rec_idx: int, record: STRRecord):
        """Parse statistics for a record"""
        
        # Mask duration
        sig = self.edf.get_signal("Mask Dur") or self.edf.get_signal("Duration")
        if sig:
            record.mask_duration = sig.data[rec_idx] * sig.gain + sig.offset
            
        # Leak statistics
        sig = self.edf.get_signal("Leak Med") or self.edf.get_signal("Leak.50")
        if sig:
            record.leak_50 = sig.data[rec_idx] * sig.gain * 60.0
            
        sig = self.edf.get_signal("Leak Max") or self.edf.get_signal("Leak.Max")
        if sig:
            record.leak_max = sig.data[rec_idx] * sig.gain * 60.0
            
        sig = self.edf.get_signal("Leak 95") or self.edf.get_signal("Leak.95")
        if sig:
            record.leak_95 = sig.data[rec_idx] * sig.gain * 60.0
            
        # Respiratory rate
        sig = self.edf.get_signal("RespRate.50") or self.edf.get_signal("RR Med")
        if sig:
            record.rr_50 = sig.data[rec_idx] * sig.gain + sig.offset
            
        sig = self.edf.get_signal("RespRate.Max") or self.edf.get_signal("RR Max")
        if sig:
            record.rr_max = sig.data[rec_idx] * sig.gain + sig.offset
            
        sig = self.edf.get_signal("RespRate.95") or self.edf.get_signal("RR 95")
        if sig:
            record.rr_95 = sig.data[rec_idx] * sig.gain + sig.offset
            
        # Mask pressure statistics (actual delivered pressure)
        sig = self.edf.get_signal("Press.50") or self.edf.get_signal("MaskPres.50")
        if sig:
            record.mp_50 = sig.data[rec_idx] * sig.gain + sig.offset
            
        sig = self.edf.get_signal("Press.95") or self.edf.get_signal("MaskPres.95")
        if sig:
            record.mp_95 = sig.data[rec_idx] * sig.gain + sig.offset
            
        sig = self.edf.get_signal("Press.Max") or self.edf.get_signal("MaskPres.Max")
        if sig:
            record.mp_max = sig.data[rec_idx] * sig.gain + sig.offset
            
        # Minute ventilation
        sig = self.edf.get_signal("MV.50") or self.edf.get_signal("MinuteVent.50")
        if sig:
            record.mv_50 = sig.data[rec_idx] * sig.gain + sig.offset
            
        sig = self.edf.get_signal("MV.95") or self.edf.get_signal("MinuteVent.95")
        if sig:
            record.mv_95 = sig.data[rec_idx] * sig.gain + sig.offset
            
        sig = self.edf.get_signal("MV.Max") or self.edf.get_signal("MinuteVent.Max")
        if sig:
            record.mv_max = sig.data[rec_idx] * sig.gain + sig.offset
            
        # Tidal volume
        sig = self.edf.get_signal("TV.50") or self.edf.get_signal("TidalVol.50")
        if sig:
            record.tv_50 = sig.data[rec_idx] * sig.gain + sig.offset
            
        sig = self.edf.get_signal("TV.95") or self.edf.get_signal("TidalVol.95")
        if sig:
            record.tv_95 = sig.data[rec_idx] * sig.gain + sig.offset
            
        sig = self.edf.get_signal("TV.Max") or self.edf.get_signal("TidalVol.Max")
        if sig:
            record.tv_max = sig.data[rec_idx] * sig.gain + sig.offset
            
        # Event indices
        sig = self.edf.get_signal("AHI")
        if sig:
            record.ahi = sig.data[rec_idx] * sig.gain + sig.offset
            
        sig = self.edf.get_signal("AI")
        if sig:
            record.ai = sig.data[rec_idx] * sig.gain + sig.offset
            
        sig = self.edf.get_signal("HI")
        if sig:
            record.hi = sig.data[rec_idx] * sig.gain + sig.offset
            
        sig = self.edf.get_signal("CAI")
        if sig:
            record.cai = sig.data[rec_idx] * sig.gain + sig.offset
            
        sig = self.edf.get_signal("OAI")
        if sig:
            record.oai = sig.data[rec_idx] * sig.gain + sig.offset
            
        sig = self.edf.get_signal("UAI")
        if sig:
            record.uai = sig.data[rec_idx] * sig.gain + sig.offset
            
        sig = self.edf.get_signal("CSR")
        if sig:
            record.csr = sig.data[rec_idx] * sig.gain + sig.offset
            
    def _parse_settings(self, rec_idx: int, record: STRRecord):
        """Parse settings for a record"""
        
        # CPAP mode
        sig = self.edf.get_signal("Mode")
        if sig:
            mode_val = int(sig.data[rec_idx] * sig.gain + sig.offset)
            record.rms9_mode = mode_val
            record.mode = self._map_mode(mode_val)
            
        # Pressure settings (configured limits)
        sig = self.edf.get_signal("Pressure") or self.edf.get_signal("SetPres")
        if sig:
            val = sig.data[rec_idx] * sig.gain + sig.offset
            if val >= 0:
                record.set_pressure = val
            
        sig = self.edf.get_signal("Max Pres") or self.edf.get_signal("MaxPres") or self.edf.get_signal("MaxPress")
        if sig:
            val = sig.data[rec_idx] * sig.gain + sig.offset
            if val >= 0:
                record.max_pressure = val
            
        sig = self.edf.get_signal("Min Pres") or self.edf.get_signal("MinPres") or self.edf.get_signal("MinPress")
        if sig:
            val = sig.data[rec_idx] * sig.gain + sig.offset
            if val >= 0:
                record.min_pressure = val
                
        sig = self.edf.get_signal("Ramp Pres") or self.edf.get_signal("RampPres")
        if sig:
            val = sig.data[rec_idx] * sig.gain + sig.offset
            if val >= 0:
                record.ramp_pressure = val
                
        # BiLevel pressure settings
        sig = self.edf.get_signal("IPAP") or self.edf.get_signal("IPAPHi")
        if sig:
            val = sig.data[rec_idx] * sig.gain + sig.offset
            if val >= 0:
                record.ipap = val
                
        sig = self.edf.get_signal("EPAP") or self.edf.get_signal("EPAPLo")
        if sig:
            val = sig.data[rec_idx] * sig.gain + sig.offset
            if val >= 0:
                record.epap = val
                
        sig = self.edf.get_signal("PS") or self.edf.get_signal("PressureSupport")
        if sig:
            val = sig.data[rec_idx] * sig.gain + sig.offset
            if val >= 0:
                record.ps = val
            
        # EPR
        sig = self.edf.get_signal("EPR")
        if sig:
            record.epr = int(sig.data[rec_idx] * sig.gain + sig.offset)
            
        sig = self.edf.get_signal("EPR Level")
        if sig:
            record.epr_level = int(sig.data[rec_idx] * sig.gain + sig.offset)
            
        # Device settings
        sig = self.edf.get_signal("S.RampTime")
        if sig:
            record.s_ramp_time = sig.data[rec_idx] * sig.gain + sig.offset
            
        sig = self.edf.get_signal("S.RampEnable")
        if sig:
            record.s_ramp_enable = int(sig.data[rec_idx] * sig.gain + sig.offset)
            
        sig = self.edf.get_signal("S.EPR.ClinEnable")
        if sig:
            record.s_epr_clin_enable = int(sig.data[rec_idx] * sig.gain + sig.offset)
            
        sig = self.edf.get_signal("S.EPR.EPREnable")
        if sig:
            record.s_epr_enable = int(sig.data[rec_idx] * sig.gain + sig.offset)
            
        sig = self.edf.get_signal("S.ABFilter")
        if sig:
            record.s_ab_filter = int(sig.data[rec_idx] * sig.gain + sig.offset)
            
        sig = self.edf.get_signal("S.ClimateControl")
        if sig:
            record.s_climate_control = int(sig.data[rec_idx] * sig.gain + sig.offset)
            
        sig = self.edf.get_signal("S.Mask")
        if sig:
            record.s_mask = int(sig.data[rec_idx] * sig.gain + sig.offset)
            
        sig = self.edf.get_signal("S.PtAccess")
        if sig:
            record.s_pt_access = int(sig.data[rec_idx] * sig.gain + sig.offset)
            
        sig = self.edf.get_signal("S.SmartStart")
        if sig:
            record.s_smart_start = int(sig.data[rec_idx] * sig.gain + sig.offset)
            
        sig = self.edf.get_signal("S.SmartStop")
        if sig:
            record.s_smart_stop = int(sig.data[rec_idx] * sig.gain + sig.offset)
            
        sig = self.edf.get_signal("S.HumEnable")
        if sig:
            record.s_hum_enable = int(sig.data[rec_idx] * sig.gain + sig.offset)
            
        sig = self.edf.get_signal("S.HumLevel")
        if sig:
            record.s_hum_level = int(sig.data[rec_idx] * sig.gain + sig.offset)
            
        sig = self.edf.get_signal("S.TempEnable")
        if sig:
            record.s_temp_enable = int(sig.data[rec_idx] * sig.gain + sig.offset)
            
        sig = self.edf.get_signal("S.Temp")
        if sig:
            record.s_temp = sig.data[rec_idx] * sig.gain + sig.offset
            
        sig = self.edf.get_signal("S.Tube")
        if sig:
            record.s_tube = int(sig.data[rec_idx] * sig.gain + sig.offset)
            
        # BiLevel settings (modes 2-5)
        if record.rms9_mode >= 2 and record.rms9_mode <= 5:
            sig = self.edf.get_signal("S.EasyBreathe") or self.edf.get_signal("S.S.EasyBreathe")
            if sig and record.rms9_mode == 3:  # S mode only
                record.s_easy_breathe = int(sig.data[rec_idx] * sig.gain + sig.offset)
                
            sig = self.edf.get_signal("S.RiseEnable") or self.edf.get_signal("S.S.RiseEnable")
            if sig:
                record.s_rise_enable = int(sig.data[rec_idx] * sig.gain + sig.offset)
                
            sig = self.edf.get_signal("S.RiseTime") or self.edf.get_signal("S.S.RiseTime")
            if sig:
                record.s_rise_time = sig.data[rec_idx] * sig.gain + sig.offset
                
            if record.rms9_mode == 3 or record.rms9_mode == 4:  # S or ST mode
                sig = self.edf.get_signal("S.Cycle") or self.edf.get_signal("S.S.Cycle")
                if sig:
                    record.s_cycle = int(sig.data[rec_idx] * sig.gain + sig.offset)
                    
                sig = self.edf.get_signal("S.Trigger") or self.edf.get_signal("S.S.Trigger")
                if sig:
                    record.s_trigger = int(sig.data[rec_idx] * sig.gain + sig.offset)
                    
            if record.rms9_mode == 4 or record.rms9_mode == 5:  # ST or T mode
                sig = self.edf.get_signal("S.TiMax") or self.edf.get_signal("S.S.TiMax")
                if sig:
                    record.s_ti_max = sig.data[rec_idx] * sig.gain + sig.offset
                    
                sig = self.edf.get_signal("S.TiMin") or self.edf.get_signal("S.S.TiMin")
                if sig:
                    record.s_ti_min = sig.data[rec_idx] * sig.gain + sig.offset
            
    def _map_mode(self, rms9_mode: int) -> int:
        """Map ResMed mode code to standard CPAP mode"""
        mode_map = {
            0: self.MODE_CPAP,
            1: self.MODE_APAP,
            2: self.MODE_BILEVEL_FIXED,
            3: self.MODE_BILEVEL_FIXED,
            4: self.MODE_BILEVEL_FIXED,
            5: self.MODE_BILEVEL_FIXED,
            6: self.MODE_BILEVEL_AUTO_FIXED_PS,
            7: self.MODE_ASV,
            8: self.MODE_ASV_VARIABLE_EPAP,
            9: self.MODE_AVAPS,
            10: self.MODE_UNKNOWN,
            11: self.MODE_APAP,  # APAP for Her
        }
        return mode_map.get(rms9_mode, self.MODE_UNKNOWN)
    
    def get_records_by_date_range(self, start: date, end: date) -> List[STRRecord]:
        """Get records within a date range"""
        return [r for r in self.records if r.date and start <= r.date <= end]
