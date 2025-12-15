"""
Parser for TGT (Target/Settings) files.
These are plain text files containing device settings in key-value format.
"""

from typing import Dict, Any, Optional
from pathlib import Path

from cpap_py.models import DeviceSettings, CPAPMode, MaskType
from cpap_py.utils.constants import (
    SETTINGS_KEYS,
    MODE_VALUES,
    MASK_VALUES,
    EPR_TYPE_VALUES,
    CLIMATE_CONTROL_VALUES,
)


def parse_tgt_file(file_path: str) -> Dict[str, Any]:
    """
    Parse a TGT settings file.
    
    TGT files contain settings in the format:
    #KEY VALUE
    or
    KEY VALUE
    
    Args:
        file_path: Path to TGT file
    
    Returns:
        Dictionary of parsed settings with normalized keys
    """
    settings = {}
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Parse key-value pairs
            parts = line.split(maxsplit=1)
            if len(parts) == 2:
                key, value = parts
                
                # Map to standard key name
                standard_key = SETTINGS_KEYS.get(key, key)
                
                # Try to parse value as number (handle hex)
                try:
                    # Check if it's a hex value (most ResMed values are hex without 0x prefix)
                    # Values like "0C8", "190", "320", "96" are hex
                    if value.isalnum() and not value.isdigit():
                        # Likely hex
                        value = int(value, 16)
                    elif value.startswith(('0x', '0X')):
                        value = int(value, 16)
                    elif '.' in value:
                        value = float(value)
                    else:
                        # Try as decimal first, then hex if that fails
                        try:
                            value = int(value)
                        except ValueError:
                            value = int(value, 16)
                except ValueError:
                    # Keep as string
                    pass
                
                settings[standard_key] = value
    
    return settings


def tgt_to_device_settings(tgt_data: Dict[str, Any]) -> DeviceSettings:
    """
    Convert raw TGT data to DeviceSettings model.
    
    Args:
        tgt_data: Raw parsed TGT data
    
    Returns:
        DeviceSettings object
    """
    settings = DeviceSettings()
    
    # Mode
    if "mode" in tgt_data:
        mode_val = tgt_data["mode"]
        if isinstance(mode_val, int):
            mode_str = MODE_VALUES.get(mode_val, "Unknown")
            try:
                settings.mode = CPAPMode(mode_str)
            except ValueError:
                pass
    
    # Pressure settings
    # Old format: values in 0.01 cmH2O units (divide by 100)
    # ResMed hex: values in 0.1 cmH2O units (divide by 10)
    if "pressure" in tgt_data:
        settings.pressure = float(tgt_data["pressure"]) / 100.0
    
    if "pressure_min" in tgt_data:
        settings.pressure_min = float(tgt_data["pressure_min"]) / 100.0
    
    if "pressure_min_raw" in tgt_data:
        # ResMed hex values are in 0.1 cmH2O units
        settings.pressure_min = float(tgt_data["pressure_min_raw"]) / 10.0
    
    if "pressure_max" in tgt_data:
        settings.pressure_max = float(tgt_data["pressure_max"]) / 100.0
    
    if "pressure_max_raw" in tgt_data:
        # ResMed hex values are in 0.1 cmH2O units
        settings.pressure_max = float(tgt_data["pressure_max_raw"]) / 10.0
    
    if "start_pressure" in tgt_data:
        settings.ramp_start_pressure = float(tgt_data["start_pressure"]) / 100.0
    
    if "ramp_start_pressure" in tgt_data:
        settings.ramp_start_pressure = float(tgt_data["ramp_start_pressure"]) / 100.0
    
    if "ramp_start_pressure_raw" in tgt_data:
        # ResMed hex values are in 0.1 cmH2O units
        settings.ramp_start_pressure = float(tgt_data["ramp_start_pressure_raw"]) / 10.0
    
    # EPR settings
    if "epr_enable" in tgt_data:
        settings.epr_enabled = bool(tgt_data["epr_enable"])
    
    if "epr_level" in tgt_data:
        settings.epr_level = int(tgt_data["epr_level"])
    
    if "epr_level_raw" in tgt_data:
        # Decode EPR level from hex value
        # The raw value encodes EPR level in lower bits
        raw_val = int(tgt_data["epr_level_raw"])
        # EPR level is typically in bits 0-1 (values 0-3)
        settings.epr_level = raw_val & 0x03
    
    if "epr_type" in tgt_data:
        epr_type_val = tgt_data["epr_type"]
        if isinstance(epr_type_val, int):
            settings.epr_type = EPR_TYPE_VALUES.get(epr_type_val, "Unknown")
    
    if "epr_type_raw" in tgt_data:
        # 1 = ramp only, 2 = full time
        type_val = int(tgt_data["epr_type_raw"])
        if type_val == 1:
            settings.epr_type = "Ramp Only"
        elif type_val == 2:
            settings.epr_type = "Full Time"
    
    # Ramp settings
    if "ramp_enable" in tgt_data:
        settings.ramp_enabled = bool(tgt_data["ramp_enable"])
    
    if "ramp_time" in tgt_data:
        settings.ramp_time = int(tgt_data["ramp_time"])
        # If we have a ramp time, ramp is likely enabled
        if settings.ramp_enabled is None and settings.ramp_time > 0:
            settings.ramp_enabled = True
    
    # Mask and comfort
    if "mask_type" in tgt_data:
        mask_val = tgt_data["mask_type"]
        if isinstance(mask_val, int):
            mask_str = MASK_VALUES.get(mask_val, "Unknown")
            try:
                settings.mask_type = MaskType(mask_str)
            except ValueError:
                pass
    
    if "mask_type_raw" in tgt_data:
        # Decode ResMed mask type: 0=Full Face, 1=Nasal, 2=Pillows
        mask_val = int(tgt_data["mask_type_raw"])
        mask_types = {0: "Full Face", 1: "Nasal", 2: "Pillows"}
        mask_str = mask_types.get(mask_val)
        if mask_str:
            try:
                settings.mask_type = MaskType(mask_str)
            except ValueError:
                pass
    
    if "mode_raw" in tgt_data:
        # Decode mode: 0=CPAP, 1=AutoSet (APAP)
        mode_val = int(tgt_data["mode_raw"])
        mode_str = "APAP" if mode_val == 1 else "CPAP"
        try:
            settings.mode = CPAPMode(mode_str)
        except ValueError:
            pass
    
    if "response_raw" in tgt_data:
        # Decode response: 0=Standard, 1=Soft, 2=For Her
        resp_val = int(tgt_data["response_raw"])
        response_types = {0: "Standard", 1: "Soft", 2: "For Her"}
        settings.response = response_types.get(resp_val)
    
    if "smart_start" in tgt_data:
        settings.smart_start = bool(tgt_data["smart_start"])
    
    if "tube_type" in tgt_data:
        settings.tube_type = str(tgt_data["tube_type"])
    
    if "tube_type_raw" in tgt_data:
        # Decode tube type: 0=SlimLine, 1=Standard
        tube_val = int(tgt_data["tube_type_raw"])
        settings.tube_type = "SlimLine" if tube_val == 0 else "Standard"
    
    if "antibacterial_filter" in tgt_data:
        settings.antibacterial_filter = bool(tgt_data["antibacterial_filter"])
    
    # IPAP/EPAP settings (in 0.1 cmH2O units)
    if "ipap_raw" in tgt_data:
        settings.ipap = float(tgt_data["ipap_raw"]) / 10.0
    
    if "epap_min_raw" in tgt_data:
        settings.epap = float(tgt_data["epap_min_raw"]) / 10.0
    
    # Humidifier
    if "humidifier_enable" in tgt_data:
        settings.humidifier_enabled = bool(tgt_data["humidifier_enable"])
    
    if "humidifier_enabled" in tgt_data:
        settings.humidifier_enabled = bool(tgt_data["humidifier_enabled"])
    
    if "humidifier_level" in tgt_data:
        settings.humidifier_level = int(tgt_data["humidifier_level"])
        # If we have a non-zero level, humidifier must be enabled
        # (Override any explicit enable=false since having a level implies it's on)
        if settings.humidifier_level > 0:
            settings.humidifier_enabled = True
    
    if "temperature_enable" in tgt_data:
        settings.temperature_enabled = bool(tgt_data["temperature_enable"])
    
    if "temperature_enabled" in tgt_data:
        settings.temperature_enabled = bool(tgt_data["temperature_enabled"])
    
    if "temperature" in tgt_data:
        settings.temperature = float(tgt_data["temperature"])
    
    if "temperature_raw" in tgt_data:
        # Temperature in tenths (860 = 86.0 degrees F)
        settings.temperature = int(tgt_data["temperature_raw"]) / 10.0
        # If we have a temp, temp control is likely enabled
        if settings.temperature_enabled is None:
            settings.temperature_enabled = True
    
    if "climate_control" in tgt_data:
        cc_val = tgt_data["climate_control"]
        if isinstance(cc_val, int):
            settings.climate_control = CLIMATE_CONTROL_VALUES.get(cc_val, "Unknown")
        elif isinstance(cc_val, bool):
            # Bool value - interpret as enabled/disabled
            settings.climate_control = "Manual" if cc_val else "Off"
    
    # Access
    if "patient_access" in tgt_data:
        settings.patient_access_enabled = bool(tgt_data["patient_access"])
    
    if "patient_access_raw" in tgt_data:
        settings.patient_access_enabled = bool(tgt_data["patient_access_raw"])
    
    # AutoSet response
    if "autoset_response" in tgt_data:
        settings.response = str(tgt_data["autoset_response"])
    
    return settings


def parse_identification_file(file_path: str) -> Dict[str, Any]:
    """
    Parse Identification.tgt file which contains device information.
    
    Args:
        file_path: Path to Identification.tgt
    
    Returns:
        Dictionary with device identification data
    """
    data = parse_tgt_file(file_path)
    
    # Extract device info
    device_info = {
        "software_version": data.get("software_version"),
        "internal_version": data.get("internal_version"),
        "release_version": data.get("release_version"),
        "platform_version": data.get("platform_version"),
        "platform_variant": data.get("platform_variant"),
    }
    
    return device_info


def find_settings_for_date(settings_dir: str, date_str: str) -> Optional[DeviceSettings]:
    """
    Find and parse the settings file for a specific date.
    
    Settings files in SETTINGS/ directory are named with letter codes (AGL, BGL, etc.)
    Need to determine which one applies to a given date.
    
    Args:
        settings_dir: Path to SETTINGS directory
        date_str: Date string (YYYYMMDD format)
    
    Returns:
        DeviceSettings object or None if not found
    """
    settings_path = Path(settings_dir)
    
    if not settings_path.exists():
        return None
    
    # TODO: Implement logic to map dates to settings files
    # For now, try common patterns
    tgt_files = list(settings_path.glob("*.tgt"))
    
    if tgt_files:
        # Use the most recent or first available for now
        # Better logic would check timestamps or file metadata
        tgt_data = parse_tgt_file(str(tgt_files[0]))
        return tgt_to_device_settings(tgt_data)
    
    return None
