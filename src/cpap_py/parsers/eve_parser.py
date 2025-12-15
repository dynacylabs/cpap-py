"""
Custom parser for ResMed EVE.edf files.
Handles discontinuous EDF+ files that pyedflib can't read.
"""

import struct
from datetime import datetime, timedelta
from typing import List, Tuple
from pathlib import Path


def parse_resmed_eve_file(file_path: str) -> List[Tuple[float, float, str]]:
    """
    Parse ResMed EVE.edf file manually to extract event annotations.
    
    ResMed EVE files are EDF+ format with annotations that pyedflib
    often can't read due to discontinuities.
    
    Args:
        file_path: Path to EVE.edf file
    
    Returns:
        List of (onset_seconds, duration_seconds, annotation_text) tuples
    """
    annotations = []
    
    with open(file_path, 'rb') as f:
        # Read main header (256 bytes)
        header = f.read(256)
        
        # Parse header fields
        version = header[0:8].decode('ascii', errors='ignore').strip()
        patient_id = header[8:88].decode('ascii', errors='ignore').strip()
        recording_id = header[88:168].decode('ascii', errors='ignore').strip()
        startdate_str = header[168:176].decode('ascii', errors='ignore').strip()
        starttime_str = header[176:184].decode('ascii', errors='ignore').strip()
        header_bytes = int(header[184:192].decode('ascii', errors='ignore').strip())
        reserved = header[192:236].decode('ascii', errors='ignore').strip()
        num_data_records = int(header[236:244].decode('ascii', errors='ignore').strip() or '0')
        duration_data_record = float(header[244:252].decode('ascii', errors='ignore').strip() or '0')
        num_signals = int(header[252:256].decode('ascii', errors='ignore').strip() or '0')
        
        if num_signals == 0:
            # No signals, check if this is EDF+ with annotations
            # EDF+ files have "EDF+C" or "EDF+D" in reserved field
            if 'EDF+' in reserved:
                # This is an annotation-only file
                # Read signal headers to find annotation signal
                pass
        
        # Read signal headers
        signal_header_size = header_bytes - 256
        signal_headers = f.read(signal_header_size)
        
        # Parse signal information
        def parse_signal_field(data, offset, field_size, num_signals):
            return [data[offset + i*field_size:offset + (i+1)*field_size]
                   .decode('ascii', errors='ignore').strip()
                   for i in range(num_signals)]
        
        offset = 0
        labels = parse_signal_field(signal_headers, offset, 16, num_signals)
        offset += num_signals * 16
        
        transducer_types = parse_signal_field(signal_headers, offset, 80, num_signals)
        offset += num_signals * 80
        
        physical_dims = parse_signal_field(signal_headers, offset, 8, num_signals)
        offset += num_signals * 8
        
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
        
        # Find EDF Annotations signal (EDF+ standard)
        annotation_idx = None
        for idx, label in enumerate(labels):
            if 'EDF Annotations' in label or 'EDF+' in label:
                annotation_idx = idx
                break
        
        if annotation_idx is None:
            # No annotation signal found
            return annotations
        
        # Read data records and extract annotations
        for record_idx in range(num_data_records):
            for sig_idx in range(num_signals):
                num_samples = samples_per_record[sig_idx]
                bytes_to_read = num_samples * 2  # 16-bit integers
                
                if sig_idx == annotation_idx:
                    # Read annotation data as bytes first
                    annotation_bytes = f.read(bytes_to_read)
                    annotation_data = annotation_bytes.decode('ascii', errors='ignore')
                    
                    # Parse EDF+ annotation format used by ResMed
                    # Each record contains:
                    # 1. TAL header: "+0\x14\x14\x00" (timestamp for this data record)
                    # 2. Events: "+onset\x15duration\x14annotation_text\x14"
                    
                    # Find all patterns that look like events
                    i = 0
                    while i < len(annotation_data):
                        # Look for start of annotation (+ or - followed by digit)
                        if (annotation_data[i] in ['+', '-'] and 
                            i + 1 < len(annotation_data) and 
                            annotation_data[i + 1].isdigit()):
                            
                            # Extract onset number
                            onset_start = i
                            i += 1
                            while i < len(annotation_data) and (annotation_data[i].isdigit() or annotation_data[i] == '.'):
                                i += 1
                            
                            onset_str = annotation_data[onset_start:i]
                            
                            # Check what comes next
                            if i < len(annotation_data):
                                sep = annotation_data[i]
                                
                                if sep == '\x15':  # Duration follows
                                    i += 1
                                    duration_start = i
                                    while i < len(annotation_data) and (annotation_data[i].isdigit() or annotation_data[i] == '.'):
                                        i += 1
                                    duration_str = annotation_data[duration_start:i]
                                    
                                    # Now should have \x14 separator before text
                                    if i < len(annotation_data) and annotation_data[i] == '\x14':
                                        i += 1
                                        # Read text until next \x14 or \x00
                                        text_start = i
                                        while i < len(annotation_data) and annotation_data[i] not in ['\x14', '\x00']:
                                            i += 1
                                        text = annotation_data[text_start:i].strip()
                                        
                                        # Parse and store
                                        try:
                                            onset = float(onset_str)
                                            duration = float(duration_str) if duration_str else 0.0
                                            if text:
                                                annotations.append((onset, duration, text))
                                        except ValueError:
                                            pass
                                else:
                                    # No duration, skip this (it's just a time marker)
                                    pass
                        else:
                            i += 1
                else:
                    # Skip other signals
                    f.read(bytes_to_read)
    
    return annotations


if __name__ == "__main__":
    # Test the parser
    import sys
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = "/workspaces/cpap-py/data/DATALOG/20241126/20241127_004009_EVE.edf"
    
    print(f"Parsing: {file_path}")
    annotations = parse_resmed_eve_file(file_path)
    print(f"Found {len(annotations)} annotations:")
    for onset, duration, text in annotations[:20]:
        print(f"  {onset:8.2f}s | {duration:6.2f}s | '{text}'")
