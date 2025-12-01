"""
Test the main package initialization and exports.
"""

import pytest


@pytest.mark.unit
def test_package_import():
    """Test that the package can be imported."""
    import cpap_py
    assert cpap_py is not None


@pytest.mark.unit
def test_version_exists():
    """Test that version is defined."""
    from cpap_py import __version__
    assert __version__ is not None
    assert isinstance(__version__, str)


@pytest.mark.unit
def test_main_exports():
    """Test that main classes are exported."""
    from cpap_py import (
        CPAPReader,
        Device,
        Session,
        SessionSummary,
        Event,
        WaveformData,
        DeviceSettings,
        SettingsProposal,
    )
    
    # Check that classes exist
    assert CPAPReader is not None
    assert Device is not None
    assert Session is not None
    assert SessionSummary is not None
    assert Event is not None
    assert WaveformData is not None
    assert DeviceSettings is not None
    assert SettingsProposal is not None


@pytest.mark.unit
def test_all_attribute():
    """Test that __all__ is defined and contains expected exports."""
    import cpap_py
    
    assert hasattr(cpap_py, '__all__')
    assert isinstance(cpap_py.__all__, list)
    
    expected_exports = [
        'CPAPReader',
        'Device',
        'Session',
        'SessionSummary',
        'Event',
        'WaveformData',
        'DeviceSettings',
        'SettingsProposal',
    ]
    
    for export in expected_exports:
        assert export in cpap_py.__all__, f"{export} not in __all__"
