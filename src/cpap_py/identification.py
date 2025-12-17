"""
Identification file parser for ResMed CPAP devices.

Parses both .tgt (text-based) and .json format identification files
to extract device information including serial number, model, and settings.
"""

import json
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass, field


@dataclass
class MachineInfo:
    """Machine identification information"""
    serial: str = ""
    model: str = ""
    model_number: str = ""
    series: str = ""
    loader_name: str = "ResMed"
    properties: Dict[str, str] = field(default_factory=dict)


class IdentificationParser:
    """Parser for Identification files (.tgt and .json formats)"""
    
    def __init__(self, base_path: str):
        """
        Initialize parser with base path to CPAP data.
        
        Args:
            base_path: Path to directory containing Identification files
        """
        self.base_path = Path(base_path)
        
    def parse(self) -> Optional[MachineInfo]:
        """
        Parse identification file and return machine information.
        
        Returns:
            MachineInfo object if file found and parsed successfully, None otherwise
        """
        # Try JSON format first (AirSense 11)
        json_path = self.base_path / "Identification.json"
        if json_path.exists():
            return self._parse_json(json_path)
            
        # Fall back to TGT format (older devices)
        tgt_path = self.base_path / "Identification.tgt"
        if tgt_path.exists():
            return self._parse_tgt(tgt_path)
            
        return None
    
    def _parse_json(self, path: Path) -> Optional[MachineInfo]:
        """Parse JSON format identification file"""
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            
            info = MachineInfo()
            
            # Navigate JSON structure
            if "FlowGenerator" in data and isinstance(data["FlowGenerator"], dict):
                flow = data["FlowGenerator"]
                if "IdentificationProfiles" in flow and isinstance(flow["IdentificationProfiles"], dict):
                    profiles = flow["IdentificationProfiles"]
                    if "Product" in profiles and isinstance(profiles["Product"], dict):
                        product = profiles["Product"]
                        
                        if "SerialNumber" in product:
                            info.serial = product["SerialNumber"]
                            info.properties["SerialNumber"] = product["SerialNumber"]
                            
                        if "ProductCode" in product:
                            info.model_number = product["ProductCode"]
                            info.properties["ProductCode"] = product["ProductCode"]
                            
                        if "ProductName" in product:
                            info.model = product["ProductName"]
                            info.properties["ProductName"] = product["ProductName"]
                            # Extract series from model name (e.g., "AirSense 11")
                            if "11" in info.model:
                                idx = info.model.index("11")
                                info.series = info.model[:idx+2]
                            elif "10" in info.model:
                                idx = info.model.index("10")
                                info.series = info.model[:idx+2]
            
            return info if info.serial else None
            
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error parsing JSON identification file: {e}")
            return None
    
    def _parse_tgt(self, path: Path) -> MachineInfo:
        """Parse TGT format identification file"""
        info = MachineInfo()
        
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if not line or not line.startswith('#'):
                        continue
                    
                    # Parse line format: #KEY value
                    parts = line[1:].split(maxsplit=1)
                    if len(parts) != 2:
                        continue
                        
                    key, value = parts
                    info.properties[key] = value
                    
                    # Extract key fields
                    if key == "SRN":  # Serial Number
                        info.serial = value
                    elif key == "PNA":  # Product Name
                        info.model = value
                    elif key == "PCD":  # Product Code
                        info.model_number = value
                    elif key == "MID":  # Model ID
                        info.properties["ModelID"] = value
                    elif key == "CID":  # Configuration ID
                        info.properties["ConfigID"] = value
                    elif key == "SID":  # Software ID
                        info.properties["SoftwareID"] = value
                        
        except IOError as e:
            print(f"Error reading TGT file: {e}")
            
        # Try to determine series from model
        if info.model:
            if "AirSense" in info.model or "AirCurve" in info.model:
                if "11" in info.model:
                    info.series = "AirSense 11"
                elif "10" in info.model:
                    info.series = "AirSense 10"
            elif "S9" in info.model:
                info.series = "S9"
                
        return info
