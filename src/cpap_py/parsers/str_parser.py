"""
Custom parser for ResMed STR.edf files which may not be fully EDF+ compliant.
Handles missing physical dimensions and other ResMed-specific quirks.
"""

import struct
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path


def parse_resmed_str_file(file_path: str) -> Tuple[List[Tuple[datetime, datetime]], Dict[str, Any]]:
    """
    Parse ResMed STR.edf file with custom handling for non-compliant format.
    
    ResMed STR files may have:
    - Empty physical dimension fields
    - Non-standard reserved field content
    - Custom signal encoding
    
    Args:
        file_path: Path to STR.edf file
    
    Returns:
        Tuple of (session_times, summary_stats)
        - session_times: List of (mask_on, mask_off) datetime tuples
        - summary_stats: Dictionary of summary data
    """
    with open(file_path, 'rb') as f:
        # Read main header (256 bytes)
        header = f.read(256)
        
        # Parse fixed header fields
        version = header[0:8].decode('ascii', errors='ignore').strip()
        patient_id = header[8:88].decode('ascii', errors='ignore').strip()
        recording_id = header[88:168].decode('ascii', errors='ignore').strip()
        startdate_str = header[168:176].decode('ascii', errors='ignore').strip()
        starttime_str = header[176:184].decode('ascii', errors='ignore').strip()
        header_bytes = int(header[184:192].decode('ascii', errors='ignore').strip())
        reserved = header[192:236].decode('ascii', errors='ignore').strip()
        num_data_records = int(header[236:244].decode('ascii', errors='ignore').strip())
        duration_data_record = float(header[244:252].decode('ascii', errors='ignore').strip())
        num_signals = int(header[252:256].decode('ascii', errors='ignore').strip())
        
        # Parse start date/time
        # Format: dd.mm.yy and hh.mm.ss
        try:
            day, month, year = startdate_str.split('.')
            hour, minute, second = starttime_str.split('.')
            year = int(year)
            if year < 85:
                year += 2000
            else:
                year += 1900
            start_datetime = datetime(year, int(month), int(day), 
                                    int(hour), int(minute), int(second))
        except:
            start_datetime = datetime.now()
        
        # Read signal headers
        signal_header_size = header_bytes - 256
        signal_headers = f.read(signal_header_size)
        
        # Parse signal information (each field is ns * field_size bytes)
        def parse_signal_field(data, offset, field_size, num_signals):
            return [data[offset + i*field_size:offset + (i+1)*field_size]
                   .decode('ascii', errors='ignore').strip()
                   for i in range(num_signals)]
        
        offset = 0
        labels = parse_signal_field(signal_headers, offset, 16, num_signals)
        offset += num_signals * 16
        
        transducer_types = parse_signal_field(signal_headers, offset, 80, num_signals)
        offset += num_signals * 80
        
        # Physical dimensions - these may be empty!
        physical_dims = parse_signal_field(signal_headers, offset, 8, num_signals)
        offset += num_signals * 8
        
        # Replace empty dimensions with a default
        physical_dims = [dim if dim else '' for dim in physical_dims]
        
        physical_mins = parse_signal_field(signal_headers, offset, 8, num_signals)
        offset += num_signals * 8
        
        physical_maxs = parse_signal_field(signal_headers, offset, 8, num_signals)
        offset += num_signals * 8
        
        digital_mins = parse_signal_field(signal_headers, offset, 8, num_signals)
        offset += num_signals * 8
        
        digital_maxs = parse_signal_field(signal_headers, offset, 8, num_signals)
        offset += num_signals * 8
        
        prefiltering = parse_signal_field(signal_headers, offset, 80, num_signals)
        offset += num_signals * 80
        
        samples_per_record = [int(s) if s else 0 
                             for s in parse_signal_field(signal_headers, offset, 8, num_signals)]
        offset += num_signals * 8
        
        reserved_signal = parse_signal_field(signal_headers, offset, 32, num_signals)
        
        # Read data records
        signal_data = {label: [] for label in labels}
        
        for record_idx in range(num_data_records):
            for sig_idx in range(num_signals):
                num_samples = samples_per_record[sig_idx]
                if num_samples == 0:
                    continue
                
                # Read samples as 16-bit integers
                samples = []
                for _ in range(num_samples):
                    sample_bytes = f.read(2)
                    if len(sample_bytes) == 2:
                        sample = struct.unpack('<h', sample_bytes)[0]
                        samples.append(sample)
                
                # Convert digital to physical values
                if samples:
                    try:
                        dig_min = float(digital_mins[sig_idx])
                        dig_max = float(digital_maxs[sig_idx])
                        phys_min = float(physical_mins[sig_idx])
                        phys_max = float(physical_maxs[sig_idx])
                        
                        # Scale from digital to physical
                        scale = (phys_max - phys_min) / (dig_max - dig_min)
                        offset_val = phys_min - scale * dig_min
                        
                        physical_samples = [s * scale + offset_val for s in samples]
                        signal_data[labels[sig_idx]].extend(physical_samples)
                    except:
                        # If conversion fails, keep digital values
                        signal_data[labels[sig_idx]].extend(samples)
        
        # Extract mask on/off times
        session_times = []
        mask_on_data = signal_data.get('MaskOn', [])
        mask_off_data = signal_data.get('MaskOff', [])
        
        # MaskOn/MaskOff may be in minutes since midnight or epoch time
        # We'll try to match them with the start date
        for on_val, off_val in zip(mask_on_data, mask_off_data):
            # Skip invalid values
            if on_val in [-32768, 0, 32767, 65534, 65535] or off_val in [-32768, 0, 32767, 65534, 65535]:
                continue
                
            try:
                # If values are small, they're likely minutes since midnight
                if on_val < 1440 and off_val < 1440:  # 1440 = minutes in a day
                    # Add minutes to start_datetime
                    mask_on = start_datetime + timedelta(minutes=on_val)
                    mask_off = start_datetime + timedelta(minutes=off_val)
                else:
                    # Otherwise treat as epoch timestamp
                    mask_on = datetime.fromtimestamp(on_val)
                    mask_off = datetime.fromtimestamp(off_val)
                
                if mask_on != mask_off and mask_off > mask_on:
                    session_times.append((mask_on, mask_off))
            except (ValueError, OSError):
                # Skip invalid dates
                continue
        
        # Build summary statistics
        summary_stats = {
            'start_time': start_datetime,
            'duration': num_data_records * duration_data_record,
            'patient_id': patient_id,
            'recording_id': recording_id,
            'num_signals': num_signals,
            'signals': {}
        }
        
        # Store signal data
        for label, data in signal_data.items():
            if data and label not in ['MaskOn', 'MaskOff']:
                sig_idx = labels.index(label)
                summary_stats['signals'][label] = {
                    'data': data,
                    'unit': physical_dims[sig_idx],
                    'samples': len(data)
                }
        
        return session_times, summary_stats


def extract_session_summary_from_str(
    signal_data: Dict[str, List[float]],
    session_idx: int = 0
) -> Dict[str, Any]:
    """
    Extract session summary statistics from STR signal data.
    
    Args:
        signal_data: Dictionary of signal name to data values
        session_idx: Index of session in the data (for multi-session days)
    
    Returns:
        Dictionary of summary statistics
    """
    summary = {}
    
    # Map STR signal names to summary fields
    mappings = {
        'AHI': 'ahi',
        'AI': 'ai',
        'HI': 'hi',
        'OAI': 'obstructive_ai',
        'CAI': 'central_ai',
        'MaskPress.50': 'pressure_median',
        'MaskPress.95': 'pressure_95th',
        'Leak.50': 'leak_median',
        'Leak.95': 'leak_95th',
        'Leak.Max': 'leak_max',
        'SpO2.50': 'spo2_median',
        'SpO2.95': 'spo2_95th',
        'SpO2.Max': 'spo2_max',
        'Duration': 'duration_minutes',
        'OnDuration': 'on_duration_minutes',
        'TidVol.50': 'tidal_volume_median',
        'MinVent.50': 'minute_ventilation_median',
        'RespRate.50': 'respiratory_rate_median',
    }
    
    for str_name, summary_field in mappings.items():
        if str_name in signal_data:
            data = signal_data[str_name]['data']
            if data and len(data) > session_idx:
                value = data[session_idx]
                # Filter out invalid values (common in ResMed files)
                if value not in [-32768, 32767, 65534, 65535]:
                    summary[summary_field] = value
    
    return summary
