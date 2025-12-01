"""
cpap-py: A comprehensive Python library for parsing and analyzing ResMed CPAP machine data.
"""

__version__ = "0.1.0"

from cpap_py.reader import CPAPReader
from cpap_py.models import (
    Device,
    Session,
    SessionSummary,
    Event,
    WaveformData,
    DeviceSettings,
)
from cpap_py.settings import SettingsProposal

__all__ = [
    "CPAPReader",
    "Device",
    "Session",
    "SessionSummary",
    "Event",
    "WaveformData",
    "DeviceSettings",
    "SettingsProposal",
]
