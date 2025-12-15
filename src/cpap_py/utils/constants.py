"""
Constants for CPAP data parsing including channel IDs, event types, and settings codes.
Based on ResMed AirSense 10/11 specifications and OSCAR project research.
"""

from typing import Dict

# EDF File Type Identifiers
EDF_TYPES = {
    "BRP": "Breathing/Respiratory/Pressure",
    "PLD": "Detailed Pressure",
    "SAD": "SpO2/Oximetry Data",
    "SA2": "SpO2/Oximetry Data (alternate)",
    "EVE": "Events",
    "CSL": "Clinical Summary",
    "STR": "Summary Statistics",
}

# ResMed Channel Codes (from OSCAR source and C# SignalNames.cs)
# Maps ResMed-specific signal names to standardized names
CHANNEL_CODES = {
    # Pressure channels - High Resolution (40ms sampling)
    "Press.40ms": "Mask Pressure",
    "Press": "Mask Pressure",
    
    # Pressure channels - Low Resolution (2s sampling)
    "MaskPress.2s": "Mask Pressure (Low)",
    "MaskPress": "Mask Pressure (Low)",
    "Press.2s": "Pressure",
    
    # EPAP/EPR Pressure
    "EprPress.2s": "EPAP",
    "EPRPress.2s": "EPAP",
    "EprPress": "EPAP",
    "EPAP": "EPAP",
    "S.BL.EPAP": "EPAP",
    
    # Generic pressure mappings
    "MaskPressure": "Mask Pressure",
    "IPAP": "Inspiratory PAP",
    "Pressure": "Pressure",
    
    # Flow channels - High Resolution (40ms sampling)
    "Flow.40ms": "Flow Rate",
    "Flow": "Flow Rate",
    
    # Flow channels - Low Resolution (2s sampling)  
    "Flow.2s": "Flow Rate",
    
    # Respiratory metrics
    "TidVol.2s": "Tidal Volume",
    "TidVol": "Tidal Volume",
    "Tidal Volume": "Tidal Volume",
    
    "MinVent.2s": "Minute Ventilation",
    "MinVent": "Minute Ventilation",
    
    "RespRate.2s": "Respiratory Rate",
    "RespRate": "Respiratory Rate",
    "RespEvent": "Respiratory Event",
    
    "TgMV": "Target Ventilation",
    "TgtVent.2s": "Target Ventilation",
    
    # Flow Limitation (CRITICAL - Missing from extraction)
    "FlowLim.2s": "Flow Limitation",
    "FlowLim": "Flow Limitation",
    
    # Snore Detection
    "Snore.2s": "Snore",
    "Snore": "Snore",
    
    # Respiratory Timing
    "InspTime": "Inspiration Time",
    "ExpTime": "Expiration Time",
    "IERatio": "I:E Ratio",
    
    # Leak channels
    "Leak.2s": "Leak Rate",
    "Leak": "Leak Rate",
    "LeakRate": "Leak Rate",
    "TotalLeak": "Total Leak",
    
    # Flow/Mask
    "MaskFlow": "Mask Flow",
    
    # SpO2 channels - High Resolution (1s sampling)
    "SpO2.1s": "Oxygen Saturation",
    "SpO2": "Oxygen Saturation",
    
    "Pulse.1s": "Pulse Rate",
    "Pulse": "Pulse Rate",
    
    # Device status
    "Device": "Device Status",
    
    # Events/Annotations
    "Annotations": "Event Annotations",
    
    # STR.edf file signal names
    "AHI": "AHI",
    "AI": "Apnea Index",
    "CAI": "Central Apnea Index",
    "HI": "Hypopnea Index",
    "OAI": "Obstructive Apnea Index",
    "UAI": "Unclassified Apnea Index",
    "RIN": "RIN",
    "CSR": "Cheyne-Stokes Respiration",
}

# Event type mappings (from EDF annotations)
EVENT_TYPE_MAP = {
    "Obstructive Apnea": "OA",
    "Obstructive": "OA",
    "OA": "OA",
    "Central Apnea": "CA",
    "Central": "CA",
    "CA": "CA",
    "Hypopnea": "H",
    "H": "H",
    "Apnea": "A",
    "RERA": "RE",
    "Flow Limitation": "FL",
    "FL": "FL",
    "Vibratory Snore": "VS",
    "VS": "VS",
    "Periodic Breathing": "PB",
    "PB": "PB",
    "Cheyne-Stokes": "CSR",
    "CSR": "CSR",
    "Clear Airway": "CA",
    "Large Leak": "LL",
    "LL": "LL",
}

# Settings file (TGT) key mappings
SETTINGS_KEYS = {
    # Device identification  
    "#IMF": "software_version",
    "#VIR": "internal_version",
    "#RIR": "release_version",
    "#PVR": "platform_version",
    "#PVD": "platform_variant",
    "#STP": "ramp_start_pressure",  # Start pressure - in 0.1 cmH2O (200 = 20.0)
    "#SRN": "serial_number_tgt",  # Serial from TGT (not used - comes from STR.edf)
    "#IPC": "product_name",  # Product name (confirmed from data)
    "#PNA": "epr_extended",  # EPR extended (alternate key)
    
    # Therapy mode
    "Mode": "mode",
    "S.Mode": "mode",
    
    # Pressure settings (ResMed hex codes - values in 0.1 cmH2O)
    "#MPA": "pressure_max_raw",  # Max pressure (in 0.1 cmH2O units - needs /10)
    "#MPI": "pressure_min_raw",  # Min pressure (in 0.1 cmH2O units - needs /10)
    "#STP": "ramp_start_pressure_raw",  # Start pressure (in 0.1 cmH2O units - needs /10)
    "Press": "pressure",
    "S.C.Press": "pressure",
    "S.C.StartPress": "start_pressure",
    "S.AS.MaxPress": "pressure_max",
    "S.AS.MinPress": "pressure_min",
    "MaxPress": "pressure_max",
    "MinPress": "pressure_min",
    
    # EPR settings (ResMed hex codes)
    "#EPR": "epr_level_raw",  # Raw EPR value (needs decoding)
    "#EPA": "epr_enable",  # EPR enable
    "#EPT": "epr_type_raw",  # EPR type (1=ramp only, etc)
    "#EPX": "epr_extended",  # Extended EPR
    "S.EPR.ClinEnable": "epr_clinical_enable",
    "S.EPR.EPREnable": "epr_enable",
    "S.EPR.Level": "epr_level",
    "S.EPR.EPRType": "epr_type",
    
    # Ramp settings (ResMed hex codes)
    "#RMT": "ramp_time",  # Ramp time in minutes
    "S.RampEnable": "ramp_enable",
    "S.RampTime": "ramp_time",
    "RampTime": "ramp_time",
    
    # Mask and comfort (ResMed hex codes)
    "#MSK": "mask_type_raw",  # Mask type (0=Full Face, 1=Nasal, 2=Pillows)
    "#TBT": "tube_type_raw",  # Tube type (0=SlimLine, 1=Standard)
    "#ABF": "antibacterial_filter",  # Antibacterial filter
    "#SST": "smart_start",  # Smart Start enable
    "#MOP": "mode_raw",  # Mode (0=CPAP, 1=AutoSet)
    "#RSC": "response_raw",  # Response mode (0=Standard, 1=Soft, 2=For Her)
    "#AXS": "patient_access_raw",  # Patient access enable
    "S.Mask": "mask_type",
    "Mask": "mask_type",
    "S.SmartStart": "smart_start",
    "SmartStart": "smart_start",
    "S.Tube": "tube_type",
    "TubeType": "tube_type",
    "S.ABFilter": "antibacterial_filter",
    
    # Humidifier (ResMed hex codes)
    "#HME": "humidifier_enabled",  # Humidifier enable
    "#HMS": "humidifier_level",  # Humidifier level (1-8)
    "#CCO": "climate_control",  # Climate control enable
    "#TMU": "temperature_enabled",  # Temperature enable
    "#HTF": "temperature_raw",  # Temperature (in tenths)
    "S.HumEnable": "humidifier_enable",
    "S.HumLevel": "humidifier_level",
    "HumLevel": "humidifier_level",
    "S.TempEnable": "temperature_enable",
    "S.Temp": "temperature",
    "S.ClimateControl": "climate_control",
    "ClimateControl": "climate_control",
    
    # IPAP/EPAP (for BiPAP modes - in 0.1 cmH2O units)
    "#IPP": "ipap_raw",  # IPAP pressure
    "#EPI": "epap_min_raw",  # EPAP min pressure
    "#EPP": "epap_max_raw",  # EPAP max pressure
    
    # Access
    "S.PtAccess": "patient_access",
    "PtAccess": "patient_access",
    
    # AutoSet settings
    "S.AS.Comfort": "autoset_comfort",
    "Response": "autoset_response",
}

# Mode value mappings (numeric to string)
MODE_VALUES = {
    0: "CPAP",
    1: "APAP",
    2: "BiLevel-T",
    3: "BiLevel-S",
    4: "BiLevel-S/T",
    5: "BiLevel-T",
    6: "VPAPauto",
    7: "ASV",
    8: "ASVAuto",
    9: "iVAPS",
    10: "PAC",
    11: "Auto for Her",
    16: "Unknown",
}

# Mask type mappings
MASK_VALUES = {
    0: "Nasal",
    1: "Pillows",
    2: "Full Face",
    3: "Unknown",
}

# EPR type mappings
EPR_TYPE_VALUES = {
    0: "Off",
    1: "Ramp Only",
    2: "Full Time",
}

# Climate control mappings
CLIMATE_CONTROL_VALUES = {
    0: "Off",
    1: "Manual",
    2: "Auto",
}

# Unit mappings for channels
CHANNEL_UNITS = {
    # Pressure
    "Pressure": "cmH2O",
    "Mask Pressure": "cmH2O",
    "Mask Pressure (Low)": "cmH2O",
    "IPAP": "cmH2O",
    "Inspiratory PAP": "cmH2O",
    "EPAP": "cmH2O",
    "Expiratory PAP": "cmH2O",
    
    # Flow
    "Flow Rate": "L/s",
    "Flow": "L/s",
    "Mask Flow": "L/min",
    
    # Leak
    "Leak": "L/s",
    "Leak Rate": "L/min",
    "Total Leak": "L/min",
    
    # Respiratory Metrics
    "Tidal Volume": "L",
    "Minute Ventilation": "L/min",
    "Target Ventilation": "L/min",
    "Respiratory Rate": "bpm",
    
    # Respiratory Timing
    "Inspiration Time": "seconds",
    "Expiration Time": "seconds",
    "I:E Ratio": "ratio",
    
    # Flow Limitation & Snore (dimensionless 0-1 scale)
    "Flow Limitation": "index",
    "Snore": "index",
    
    # SpO2/Pulse
    "Oxygen Saturation": "%",
    "SpO2": "%",
    "Pulse Rate": "bpm",
    "Pulse": "bpm",
    
    # Indices
    "AHI": "events/hour",
    "Apnea Index": "events/hour",
    "Central Apnea Index": "events/hour",
    "Hypopnea Index": "events/hour",
    "Obstructive Apnea Index": "events/hour",
    "Unclassified Apnea Index": "events/hour",
}

# Clinical thresholds and limits
CLINICAL_LIMITS = {
    "pressure_min": 4.0,  # cmH2O
    "pressure_max": 20.0,  # cmH2O
    "epr_level_max": 3,
    "ramp_time_max": 45,  # minutes
    "humidifier_level_max": 8,
    "temperature_min": 60,  # Fahrenheit
    "temperature_max": 86,  # Fahrenheit
}

# AHI severity classifications
AHI_SEVERITY = {
    "normal": (0, 5),
    "mild": (5, 15),
    "moderate": (15, 30),
    "severe": (30, float('inf')),
}

def get_ahi_severity(ahi: float) -> str:
    """Classify AHI severity."""
    for severity, (low, high) in AHI_SEVERITY.items():
        if low <= ahi < high:
            return severity
    return "unknown"
