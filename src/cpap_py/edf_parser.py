"""
EDF (European Data Format) Parser for CPAP data files.

Parses EDF and EDF+ files containing waveform data and annotations
from ResMed CPAP devices.
"""

import struct
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple
from dataclasses import dataclass, field
import gzip


@dataclass
class EDFHeader:
    """EDF file header information"""
    version: int = 0
    patient_ident: str = ""
    recording_ident: str = ""
    start_date: Optional[datetime] = None
    num_header_bytes: int = 0
    reserved: str = ""
    num_data_records: int = 0
    duration_seconds: float = 0.0
    num_signals: int = 0


@dataclass
class EDFSignal:
    """EDF signal descriptor"""
    label: str = ""
    transducer_type: str = ""
    physical_dimension: str = ""
    physical_minimum: float = 0.0
    physical_maximum: float = 0.0
    digital_minimum: int = 0
    digital_maximum: int = 0
    gain: float = 1.0
    offset: float = 0.0
    prefiltering: str = ""
    sample_count: int = 0
    reserved: str = ""
    data: List[int] = field(default_factory=list)
    
    def __post_init__(self):
        """Calculate gain and offset after initialization"""
        if self.digital_maximum != self.digital_minimum:
            self.gain = (self.physical_maximum - self.physical_minimum) / \
                       (self.digital_maximum - self.digital_minimum)
            self.offset = self.physical_maximum - self.gain * self.digital_maximum


@dataclass
class Annotation:
    """EDF+ annotation"""
    offset: float = 0.0
    duration: float = -1.0
    text: str = ""


class EDFParser:
    """Parser for EDF and EDF+ files"""
    
    ANNO_SEP = b'\x14'  # ASCII 20
    ANNO_DUR_MARK = b'\x15'  # ASCII 21
    ANNO_END = b'\x00'  # ASCII 0
    
    def __init__(self, filepath: str):
        """
        Initialize EDF parser.
        
        Args:
            filepath: Path to EDF file (can be .edf or .edf.gz)
        """
        self.filepath = Path(filepath)
        self.header = EDFHeader()
        self.signals: List[EDFSignal] = []
        self.annotations: List[List[Annotation]] = []
        self._data: Optional[bytes] = None
        
    def open(self) -> bool:
        """
        Open and read EDF file into memory.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.filepath.suffix == '.gz':
                with gzip.open(self.filepath, 'rb') as f:
                    self._data = f.read()
            else:
                with open(self.filepath, 'rb') as f:
                    self._data = f.read()
                    
            if len(self._data) < 256:  # Minimum header size
                print(f"File too short: {self.filepath}")
                return False
                
            return True
            
        except IOError as e:
            print(f"Error opening file: {e}")
            return False
    
    def parse_header(self) -> bool:
        """
        Parse EDF header from loaded data.
        
        Returns:
            True if successful, False otherwise
        """
        if not self._data:
            return False
            
        try:
            # Parse fixed header (256 bytes)
            self.header.version = int(self._data[0:8].decode('latin-1').strip())
            self.header.patient_ident = self._data[8:88].decode('latin-1').strip()
            self.header.recording_ident = self._data[88:168].decode('latin-1').strip()
            
            # Parse date and time
            date_str = self._data[168:184].decode('latin-1').strip()
            try:
                self.header.start_date = self._parse_date(date_str)
            except ValueError as e:
                print(f"Warning: Could not parse date: {e}")
                
            self.header.num_header_bytes = int(self._data[184:192].decode('latin-1').strip())
            self.header.reserved = self._data[192:236].decode('latin-1').strip()
            self.header.num_data_records = int(self._data[236:244].decode('latin-1').strip())
            self.header.duration_seconds = float(self._data[244:252].decode('latin-1').strip())
            self.header.num_signals = int(self._data[252:256].decode('latin-1').strip())
            
            return True
            
        except (ValueError, UnicodeDecodeError) as e:
            print(f"Error parsing header: {e}")
            return False
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse EDF date/time string (dd.MM.yyHH.mm.ss)"""
        day = int(date_str[0:2])
        month = int(date_str[3:5])
        year = int(date_str[6:8])
        hour = int(date_str[8:10])
        minute = int(date_str[11:13])
        second = int(date_str[14:16])
        
        # Handle 2-digit year (assumes 1985-2084)
        if year < 85:
            year += 2000
        else:
            year += 1900
            
        return datetime(year, month, day, hour, minute, second)
    
    def parse_signal_headers(self) -> bool:
        """
        Parse signal headers from EDF file.
        
        Returns:
            True if successful, False otherwise
        """
        if not self._data or self.header.num_signals == 0:
            return False
            
        try:
            ns = self.header.num_signals
            offset = 256
            
            self.signals = [EDFSignal() for _ in range(ns)]
            
            # Read signal headers (each field is ns * field_size bytes)
            # Labels (16 bytes each)
            for i in range(ns):
                self.signals[i].label = self._data[offset:offset+16].decode('latin-1').strip()
                offset += 16
                
            # Transducer types (80 bytes each)
            for i in range(ns):
                self.signals[i].transducer_type = self._data[offset:offset+80].decode('latin-1').strip()
                offset += 80
                
            # Physical dimensions (8 bytes each)
            for i in range(ns):
                self.signals[i].physical_dimension = self._data[offset:offset+8].decode('latin-1').strip()
                offset += 8
                
            # Physical minimums (8 bytes each)
            for i in range(ns):
                self.signals[i].physical_minimum = float(self._data[offset:offset+8].decode('latin-1').strip())
                offset += 8
                
            # Physical maximums (8 bytes each)
            for i in range(ns):
                self.signals[i].physical_maximum = float(self._data[offset:offset+8].decode('latin-1').strip())
                offset += 8
                
            # Digital minimums (8 bytes each)
            for i in range(ns):
                self.signals[i].digital_minimum = int(self._data[offset:offset+8].decode('latin-1').strip())
                offset += 8
                
            # Digital maximums (8 bytes each)
            for i in range(ns):
                self.signals[i].digital_maximum = int(self._data[offset:offset+8].decode('latin-1').strip())
                offset += 8
                
            # Prefiltering (80 bytes each)
            for i in range(ns):
                self.signals[i].prefiltering = self._data[offset:offset+80].decode('latin-1').strip()
                offset += 80
                
            # Number of samples per data record (8 bytes each)
            for i in range(ns):
                self.signals[i].sample_count = int(self._data[offset:offset+8].decode('latin-1').strip())
                offset += 8
                
            # Reserved (32 bytes each)
            for i in range(ns):
                self.signals[i].reserved = self._data[offset:offset+32].decode('latin-1').strip()
                offset += 32
                
            # Calculate gain and offset for each signal
            for signal in self.signals:
                if signal.digital_maximum != signal.digital_minimum:
                    signal.gain = (signal.physical_maximum - signal.physical_minimum) / \
                                 (signal.digital_maximum - signal.digital_minimum)
                    signal.offset = signal.physical_maximum - signal.gain * signal.digital_maximum
                    
            return True
            
        except (ValueError, UnicodeDecodeError, IndexError) as e:
            print(f"Error parsing signal headers: {e}")
            return False
    
    def parse_data(self) -> bool:
        """
        Parse signal data from EDF file.
        
        Returns:
            True if successful, False otherwise
        """
        if not self._data or not self.signals:
            return False
            
        try:
            offset = self.header.num_header_bytes
            
            # Initialize data arrays
            for signal in self.signals:
                total_samples = signal.sample_count * self.header.num_data_records
                signal.data = []
                
            # Read data records
            for rec in range(self.header.num_data_records):
                for signal in self.signals:
                    # Read samples as 16-bit signed integers (little-endian)
                    for _ in range(signal.sample_count):
                        if offset + 2 > len(self._data):
                            return False
                        value = struct.unpack('<h', self._data[offset:offset+2])[0]
                        signal.data.append(value)
                        offset += 2
                        
            return True
            
        except (struct.error, IndexError) as e:
            print(f"Error parsing data: {e}")
            return False
    
    def parse(self) -> bool:
        """
        Parse entire EDF file (header, signal headers, and data).
        
        Returns:
            True if successful, False otherwise
        """
        if not self.open():
            return False
        if not self.parse_header():
            return False
        if not self.parse_signal_headers():
            return False
        if not self.parse_data():
            return False
        return True
    
    def get_signal(self, label: str, index: int = 0) -> Optional[EDFSignal]:
        """
        Get signal by label.
        
        Args:
            label: Signal label to search for
            index: Index if multiple signals have same label (default: 0)
            
        Returns:
            EDFSignal if found, None otherwise
        """
        matches = [s for s in self.signals if s.label == label]
        if index < len(matches):
            return matches[index]
        return None
    
    def get_physical_values(self, signal: EDFSignal) -> List[float]:
        """
        Convert digital values to physical values using gain and offset.
        
        Args:
            signal: EDFSignal to convert
            
        Returns:
            List of physical (scaled) values
        """
        return [val * signal.gain + signal.offset for val in signal.data]
