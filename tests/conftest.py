"""
Test configuration and fixtures for cpap-py.
"""

import os
import pytest
from pathlib import Path
from typing import Dict, Any

# Test data directory
TEST_DATA_DIR = Path(__file__).parent.parent / "data"


@pytest.fixture
def sample_data_dir():
    """Path to sample CPAP data directory."""
    return str(TEST_DATA_DIR)


@pytest.fixture
def sample_identification_tgt():
    """Path to sample Identification.tgt file."""
    return str(TEST_DATA_DIR / "Identification.tgt")


@pytest.fixture
def sample_str_edf():
    """Path to sample STR.edf file."""
    return str(TEST_DATA_DIR / "STR.edf")


@pytest.fixture
def sample_datalog_dir():
    """Path to sample DATALOG directory."""
    return str(TEST_DATA_DIR / "DATALOG" / "20241126")


@pytest.fixture
def sample_settings_dir():
    """Path to sample SETTINGS directory."""
    return str(TEST_DATA_DIR / "SETTINGS")


@pytest.fixture
def sample_brp_file():
    """Path to sample BRP file."""
    files = list((TEST_DATA_DIR / "DATALOG" / "20241126").glob("*_BRP.edf"))
    if files:
        return str(files[0])
    return None


@pytest.fixture
def sample_pld_file():
    """Path to sample PLD file."""
    files = list((TEST_DATA_DIR / "DATALOG" / "20241126").glob("*_PLD.edf"))
    if files:
        return str(files[0])
    return None


@pytest.fixture
def sample_sad_file():
    """Path to sample SAD file."""
    files = list((TEST_DATA_DIR / "DATALOG" / "20241126").glob("*_SAD.edf"))
    if files:
        return str(files[0])
    return None


@pytest.fixture
def sample_eve_file():
    """Path to sample EVE file."""
    files = list((TEST_DATA_DIR / "DATALOG" / "20241126").glob("*_EVE.edf"))
    if files:
        return str(files[0])
    return None


@pytest.fixture
def sample_csl_file():
    """Path to sample CSL file."""
    files = list((TEST_DATA_DIR / "DATALOG" / "20241126").glob("*_CSL.edf"))
    if files:
        return str(files[0])
    return None


@pytest.fixture
def test_output_dir(tmp_path):
    """Temporary directory for test output."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def mock_device_settings() -> Dict[str, Any]:
    """Mock device settings for testing."""
    return {
        "serial_number": "TEST123456",
        "model": "AirSense 10 AutoSet",
        "mode": "APAP",  # Valid CPAPMode enum value
        "min_pressure": 6.0,
        "max_pressure": 20.0,
        "epr": 3,
        "epr_type": "FullTime",
        "ramp_time": 20,
        "ramp_start_pressure": 4.0,
        "ramp_enabled": True,
        "epr_level": 3,
    }


@pytest.fixture
def mock_waveform_data():
    """Mock waveform data for testing."""
    import numpy as np
    return np.array([10.0, 10.5, 11.0, 10.8, 10.2, 10.6, 11.2])


@pytest.fixture
def mock_events():
    """Mock events for testing."""
    from datetime import datetime
    from cpap_py.models import Event, EventType
    
    return [
        Event(
            type=EventType.OBSTRUCTIVE_APNEA,
            timestamp=datetime(2024, 11, 27, 1, 30, 0),
            duration=12.5
        ),
        Event(
            type=EventType.HYPOPNEA,
            timestamp=datetime(2024, 11, 27, 2, 15, 0),
            duration=15.0
        ),
        Event(
            type=EventType.CENTRAL_APNEA,
            timestamp=datetime(2024, 11, 27, 3, 45, 0),
            duration=10.0
        ),
    ]


@pytest.fixture
def mock_session_summary() -> Dict[str, Any]:
    """Mock session summary for testing."""
    return {
        "duration_seconds": 27000,
        "duration_hours": 7.5,
        "ahi": 5.2,
        "ai": 2.1,
        "hi": 3.1,
        "obstructive_apneas": 15,
        "central_apneas": 1,
        "hypopneas": 23,
        "pressure_median": 12.5,
        "pressure_95th": 14.8,
        "leak_median": 3.2,
        "leak_95th": 18.5,
        "spo2_median": 95.0,
        "spo2_min": 89.0,
    }
