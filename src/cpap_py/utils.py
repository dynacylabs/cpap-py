"""
Utility functions for CPAP data parsing.
"""

from datetime import datetime, date, timedelta
from typing import List, Tuple


def split_sessions_by_noon(timestamps: List[int]) -> List[Tuple[date, List[int]]]:
    """
    Split timestamps into sessions by noon boundary.
    
    ResMed devices split days at noon (12:00) rather than midnight.
    
    Args:
        timestamps: List of Unix timestamps
        
    Returns:
        List of (date, timestamps) tuples for each session day
    """
    if not timestamps:
        return []
        
    sessions = []
    current_day = None
    current_stamps = []
    
    for ts in sorted(timestamps):
        if ts == 0:
            continue
            
        dt = datetime.fromtimestamp(ts)
        
        # Determine which session day this belongs to
        if dt.hour < 12:
            # Before noon - belongs to previous day's session
            session_date = dt.date() - timedelta(days=1)
        else:
            # After noon - belongs to current day's session
            session_date = dt.date()
            
        if current_day is None:
            current_day = session_date
            
        if session_date != current_day:
            # Save current session and start new one
            if current_stamps:
                sessions.append((current_day, current_stamps))
            current_day = session_date
            current_stamps = [ts]
        else:
            current_stamps.append(ts)
            
    # Don't forget last session
    if current_stamps:
        sessions.append((current_day, current_stamps))
        
    return sessions


def minutes_since_noon(dt: datetime) -> int:
    """
    Calculate minutes since noon for a datetime.
    
    Used for mask on/off time encoding in STR.edf files.
    
    Args:
        dt: Datetime to convert
        
    Returns:
        Minutes since noon (can be negative for times before noon)
    """
    noon = datetime.combine(dt.date(), datetime.min.time().replace(hour=12))
    delta = dt - noon
    return int(delta.total_seconds() / 60)


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds as HH:MM:SS string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def calculate_ahi(apneas: int, hypopneas: int, hours: float) -> float:
    """
    Calculate Apnea-Hypopnea Index.
    
    Args:
        apneas: Number of apnea events
        hypopneas: Number of hypopnea events
        hours: Duration in hours
        
    Returns:
        AHI value (events per hour)
    """
    if hours <= 0:
        return 0.0
    return (apneas + hypopneas) / hours


def therapy_mode_name(mode: int) -> str:
    """
    Get human-readable name for therapy mode.
    
    Args:
        mode: Mode constant from STRParser
        
    Returns:
        Mode name string
    """
    from .str_parser import STRParser
    
    mode_names = {
        STRParser.MODE_UNKNOWN: "Unknown",
        STRParser.MODE_CPAP: "CPAP",
        STRParser.MODE_APAP: "APAP",
        STRParser.MODE_BILEVEL_FIXED: "BiLevel Fixed",
        STRParser.MODE_BILEVEL_AUTO_FIXED_PS: "BiLevel Auto (Fixed PS)",
        STRParser.MODE_BILEVEL_AUTO_VARIABLE_PS: "BiLevel Auto (Variable PS)",
        STRParser.MODE_ASV: "ASV",
        STRParser.MODE_ASV_VARIABLE_EPAP: "ASV (Variable EPAP)",
        STRParser.MODE_AVAPS: "AVAPS",
        STRParser.MODE_TRILEVEL_AUTO_VARIABLE_PDIFF: "TriLevel Auto",
    }
    
    return mode_names.get(mode, "Unknown")


def downsample_signal(data: List[float], factor: int) -> List[float]:
    """
    Downsample signal by averaging consecutive samples.
    
    Args:
        data: Original signal data
        factor: Downsampling factor
        
    Returns:
        Downsampled signal
    """
    if factor <= 1:
        return data
        
    result = []
    for i in range(0, len(data), factor):
        chunk = data[i:i+factor]
        if chunk:
            result.append(sum(chunk) / len(chunk))
            
    return result


def calculate_percentile(data: List[float], percentile: float) -> float:
    """
    Calculate percentile of data.
    
    Args:
        data: List of values
        percentile: Percentile to calculate (0-100)
        
    Returns:
        Percentile value
    """
    if not data:
        return 0.0
        
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * (percentile / 100.0)
    f = int(k)
    c = f + 1
    
    if c >= len(sorted_data):
        return sorted_data[-1]
        
    d0 = sorted_data[f] * (c - k)
    d1 = sorted_data[c] * (k - f)
    
    return d0 + d1
