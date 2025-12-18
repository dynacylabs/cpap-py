"""
Tests for __init__.py module exports
"""

import pytest


class TestPackageImports:
    """Test that package exports are correct"""
    
    def test_version_exists(self):
        """Test that __version__ is defined"""
        from cpap_py import __version__
        assert __version__ is not None
        assert isinstance(__version__, str)
        assert len(__version__) > 0
    
    def test_all_exports(self):
        """Test that __all__ contains expected exports"""
        from cpap_py import __all__
        
        expected = [
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
        
        for item in expected:
            assert item in __all__
    
    def test_import_identification(self):
        """Test importing identification classes"""
        from cpap_py import IdentificationParser, MachineInfo
        assert IdentificationParser is not None
        assert MachineInfo is not None
    
    def test_import_edf_parser(self):
        """Test importing EDF parser classes"""
        from cpap_py import EDFParser, EDFSignal, EDFHeader
        assert EDFParser is not None
        assert EDFSignal is not None
        assert EDFHeader is not None
    
    def test_import_str_parser(self):
        """Test importing STR parser classes"""
        from cpap_py import STRParser, STRRecord
        assert STRParser is not None
        assert STRRecord is not None
    
    def test_import_datalog_parser(self):
        """Test importing datalog parser classes"""
        from cpap_py import DatalogParser, SessionData, SessionEvent
        assert DatalogParser is not None
        assert SessionData is not None
        assert SessionEvent is not None
    
    def test_import_settings_parser(self):
        """Test importing settings parser classes"""
        from cpap_py import SettingsParser, SettingChange
        assert SettingsParser is not None
        assert SettingChange is not None
    
    def test_import_loader(self):
        """Test importing loader classes"""
        from cpap_py import CPAPLoader, CPAPData
        assert CPAPLoader is not None
        assert CPAPData is not None
    
    def test_direct_import(self):
        """Test direct import of main package"""
        import cpap_py
        assert hasattr(cpap_py, 'IdentificationParser')
        assert hasattr(cpap_py, 'EDFParser')
        assert hasattr(cpap_py, 'STRParser')
        assert hasattr(cpap_py, 'DatalogParser')
        assert hasattr(cpap_py, 'SettingsParser')
        assert hasattr(cpap_py, 'CPAPLoader')
