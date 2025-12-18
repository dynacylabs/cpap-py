"""
CPAP Data Parser Library

A Python library for parsing ResMed CPAP data files including:
- Identification files (.tgt, .json)
- STR.edf files (summary data)
- DATALOG EDF files (BRP, PLD, SAD, EVE, CSL, AEV)
- Settings files

Based on the OSCAR CPAP analysis software.
"""

from .identification import IdentificationParser, MachineInfo
from .edf_parser import EDFParser, EDFSignal, EDFHeader
from .str_parser import STRParser, STRRecord
from .datalog_parser import DatalogParser, SessionData, SessionEvent
from .settings_parser import SettingsParser, SettingChange
from .loader import CPAPLoader, CPAPData

try:
    from ._version import version as __version__
except ImportError:
    __version__ = "unknown"
__all__ = [
    "IdentificationParser",
    "MachineInfo", 
    "EDFParser",
    "EDFSignal",
    "EDFHeader",
    "STRParser",
    "STRRecord",
    "DatalogParser",
    "SessionData",
    "SessionEvent",
    "SettingsParser",
    "SettingChange",
    "CPAPLoader",
    "CPAPData",
]
