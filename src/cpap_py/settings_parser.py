"""
Settings parser for ResMed CPAP configuration files.

Parses .tgt files in SETTINGS directory containing device configuration
changes and clinical settings.
"""

from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
import json


@dataclass
class SettingChange:
    """A single setting change record"""
    timestamp: Optional[datetime] = None
    setting_name: str = ""
    old_value: Any = None
    new_value: Any = None
    category: str = ""  # e.g., "PressureSettings", "ComfortSettings"
    properties: Dict[str, Any] = field(default_factory=dict)


class SettingsParser:
    """Parser for settings .tgt files"""
    
    # Known settings file prefixes
    SETTINGS_PREFIXES = [
        "AGL",  # ?
        "BGL",  # ?
        "CGL",  # Clinical Settings
        "DGL",  # ?
        "EGL",  # ?
        "IGL",  # ?
        "MGL",  # ?
        "NGL",  # ?
        "PGL",  # ?
        "QXH",  # ?
        "QXJ",  # ?
        "RGL",  # ?
        "SGL",  # ?
        "UGL",  # User Settings
        "VGL",  # ?
        "XGL",  # ?
    ]
    
    def __init__(self, settings_path: str):
        """
        Initialize settings parser.
        
        Args:
            settings_path: Path to SETTINGS directory
        """
        self.settings_path = Path(settings_path)
        self.changes: List[SettingChange] = []
        
    def parse_all(self) -> List[SettingChange]:
        """
        Parse all settings files in SETTINGS directory.
        
        Returns:
            List of SettingChange objects
        """
        # Find all .tgt files in SETTINGS directory
        tgt_files = list(self.settings_path.glob("*.tgt"))
        
        for filepath in sorted(tgt_files):
            changes = self.parse_file(filepath)
            self.changes.extend(changes)
            
        # Sort by timestamp
        self.changes.sort(key=lambda c: c.timestamp if c.timestamp else datetime.min)
        
        return self.changes
    
    def parse_file(self, filepath: Path) -> List[SettingChange]:
        """
        Parse a single settings .tgt file.
        
        Args:
            filepath: Path to .tgt file
            
        Returns:
            List of SettingChange objects from this file
        """
        changes = []
        
        try:
            # Try parsing as JSON first (newer format)
            with open(filepath, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    changes = self._parse_json_settings(data, filepath.stem)
                    return changes
                except json.JSONDecodeError:
                    # Not JSON, try text format
                    pass
            
            # Fall back to text-based parsing
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                current_change = None
                
                for line in f:
                    line = line.strip()
                    
                    # Skip empty lines
                    if not line:
                        if current_change and current_change.setting_name:
                            changes.append(current_change)
                            current_change = None
                        continue
                        
                    # Lines starting with # are key-value pairs
                    if line.startswith('#'):
                        if current_change is None:
                            current_change = SettingChange()
                            
                        # Parse key-value
                        parts = line[1:].split(maxsplit=1)
                        if len(parts) == 2:
                            key, value = parts
                            current_change.properties[key] = value
                            
                            # Extract key fields
                            if key == "TIM":  # Timestamp
                                current_change.timestamp = self._parse_timestamp(value)
                            elif key == "SET":  # Setting name
                                current_change.setting_name = value
                            elif key == "OLD":  # Old value
                                current_change.old_value = value
                            elif key == "NEW":  # New value
                                current_change.new_value = value
                                
                # Don't forget last change
                if current_change and current_change.setting_name:
                    changes.append(current_change)
                    
        except IOError as e:
            print(f"Error reading settings file {filepath}: {e}")
            
        return changes
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """
        Parse timestamp from settings file.
        
        Format appears to be YYYYMMDDHHmmss or similar
        """
        try:
            # Try standard format: YYYYMMDDHHmmss
            if len(timestamp_str) == 14 and timestamp_str.isdigit():
                year = int(timestamp_str[0:4])
                month = int(timestamp_str[4:6])
                day = int(timestamp_str[6:8])
                hour = int(timestamp_str[8:10])
                minute = int(timestamp_str[10:12])
                second = int(timestamp_str[12:14])
                return datetime(year, month, day, hour, minute, second)
                
            # Try with separators
            for fmt in [
                "%Y-%m-%d %H:%M:%S",
                "%Y/%m/%d %H:%M:%S",
                "%d.%m.%Y %H:%M:%S",
            ]:
                try:
                    return datetime.strptime(timestamp_str, fmt)
                except ValueError:
                    continue
                    
        except ValueError:
            pass
            
        return None
    
    def _parse_json_settings(self, data: Dict[str, Any], file_prefix: str) -> List[SettingChange]:
        """
        Parse JSON format settings file and extract pressure/therapy settings.
        
        Args:
            data: Parsed JSON data
            file_prefix: File prefix (e.g., "UGL", "CGL")
            
        Returns:
            List of SettingChange objects
        """
        changes = []
        
        # Extract timestamp if available
        timestamp = None
        if "Timestamp" in data:
            timestamp_str = data["Timestamp"]
            timestamp = self._parse_timestamp(str(timestamp_str))
        
        # Navigate JSON structure to find FlowGenerator settings
        if "FlowGenerator" in data and isinstance(data["FlowGenerator"], dict):
            flow = data["FlowGenerator"]
            
            # Look for TherapyProfiles which contain pressure settings
            if "TherapyProfiles" in flow and isinstance(flow["TherapyProfiles"], dict):
                therapy = flow["TherapyProfiles"]
                
                # Pressure Settings
                if "PressureSettings" in therapy and isinstance(therapy["PressureSettings"], dict):
                    pressure = therapy["PressureSettings"]
                    
                    for key, value in pressure.items():
                        change = SettingChange(
                            timestamp=timestamp,
                            setting_name=key,
                            new_value=value,
                            category="PressureSettings",
                            properties={"file": file_prefix}
                        )
                        changes.append(change)
                
                # Comfort Settings
                if "ComfortSettings" in therapy and isinstance(therapy["ComfortSettings"], dict):
                    comfort = therapy["ComfortSettings"]
                    
                    for key, value in comfort.items():
                        change = SettingChange(
                            timestamp=timestamp,
                            setting_name=key,
                            new_value=value,
                            category="ComfortSettings",
                            properties={"file": file_prefix}
                        )
                        changes.append(change)
                
                # Humidification Settings
                if "HumidificationSettings" in therapy and isinstance(therapy["HumidificationSettings"], dict):
                    humid = therapy["HumidificationSettings"]
                    
                    for key, value in humid.items():
                        change = SettingChange(
                            timestamp=timestamp,
                            setting_name=key,
                            new_value=value,
                            category="HumidificationSettings",
                            properties={"file": file_prefix}
                        )
                        changes.append(change)
                
                # Mode Settings
                if "ModeSettings" in therapy and isinstance(therapy["ModeSettings"], dict):
                    mode = therapy["ModeSettings"]
                    
                    for key, value in mode.items():
                        change = SettingChange(
                            timestamp=timestamp,
                            setting_name=key,
                            new_value=value,
                            category="ModeSettings",
                            properties={"file": file_prefix}
                        )
                        changes.append(change)
        
        return changes
    
    def get_changes_by_setting(self, setting_name: str) -> List[SettingChange]:
        """Get all changes for a specific setting"""
        return [c for c in self.changes if c.setting_name == setting_name]
    
    def get_changes_by_date_range(self, start: datetime, end: datetime) -> List[SettingChange]:
        """Get changes within a date range"""
        return [c for c in self.changes 
                if c.timestamp and start <= c.timestamp <= end]
