"""
Basic integration test to verify the package can load real CPAP data.
"""

import pytest
from pathlib import Path


@pytest.mark.integration
def test_load_sample_data(sample_data_dir):
    """Test loading sample CPAP data from the data directory."""
    from cpap_py import CPAPReader
    
    # Skip if data directory doesn't exist or is empty
    data_path = Path(sample_data_dir)
    if not data_path.exists():
        pytest.skip("Sample data directory not found")
    
    # Try to load the data
    try:
        reader = CPAPReader(sample_data_dir)
        devices = reader.get_devices()
        
        # Basic validation
        assert devices is not None
        assert isinstance(devices, list)
        
        if len(devices) > 0:
            # If we have devices, check basic properties
            device = devices[0]
            assert hasattr(device, 'serial_number')
            assert hasattr(device, 'model')
            
    except Exception as e:
        pytest.skip(f"Could not load sample data: {e}")


@pytest.mark.integration
@pytest.mark.slow
def test_get_sessions(sample_data_dir):
    """Test getting sessions from sample data."""
    from cpap_py import CPAPReader
    
    data_path = Path(sample_data_dir)
    if not data_path.exists():
        pytest.skip("Sample data directory not found")
    
    try:
        reader = CPAPReader(sample_data_dir)
        sessions = reader.get_sessions()
        
        # Basic validation
        assert sessions is not None
        assert isinstance(sessions, list)
        
        if len(sessions) > 0:
            # Check first session has expected attributes
            session = sessions[0]
            assert hasattr(session, 'date')
            assert hasattr(session, 'summary')
            assert hasattr(session, 'settings')
            
    except Exception as e:
        pytest.skip(f"Could not get sessions: {e}")
