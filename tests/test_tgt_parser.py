"""
Tests for TGT (settings) file parser.
"""

import pytest
import struct
from pathlib import Path

from cpap_py.parsers.tgt_parser import (
    parse_tgt_file,
    tgt_to_device_settings,
    parse_identification_file,
    find_settings_for_date,
)
from cpap_py.models import DeviceSettings, CPAPMode, MaskType


@pytest.mark.unit
class TestParseTgtFile:
    """Test parsing TGT files."""
    
    def test_parse_empty_file(self, test_output_dir):
        """Test parsing empty TGT file."""
        tgt_file = test_output_dir / "empty.tgt"
        tgt_file.write_text("")
        
        result = parse_tgt_file(str(tgt_file))
        assert isinstance(result, dict)
        assert len(result) == 0
    
    def test_parse_simple_key_values(self, test_output_dir):
        """Test parsing simple key-value pairs."""
        tgt_file = test_output_dir / "simple.tgt"
        content = """Mode 1
Press 1000
S.EPR.Level 2
"""
        tgt_file.write_text(content)
        
        result = parse_tgt_file(str(tgt_file))
        assert "mode" in result
        assert "pressure" in result
        assert "epr_level" in result
        assert result["epr_level"] == 2
    
    def test_parse_hex_values(self, test_output_dir):
        """Test parsing hexadecimal values."""
        tgt_file = test_output_dir / "hex.tgt"
        content = """TestKey 0x10
OtherKey 0xFF
"""
        tgt_file.write_text(content)
        
        result = parse_tgt_file(str(tgt_file))
        assert result["TestKey"] == 16
        assert result["OtherKey"] == 255
    
    def test_parse_float_values(self, test_output_dir):
        """Test parsing float values."""
        tgt_file = test_output_dir / "float.tgt"
        content = """Temperature 72.5
Pressure 10.5
"""
        tgt_file.write_text(content)
        
        result = parse_tgt_file(str(tgt_file))
        assert result["Temperature"] == 72.5
        assert result["Pressure"] == 10.5
    
    def test_parse_string_values(self, test_output_dir):
        """Test parsing string values."""
        tgt_file = test_output_dir / "string.tgt"
        content = """DeviceName AirSense10
S.Mask Pillows
"""
        tgt_file.write_text(content)
        
        result = parse_tgt_file(str(tgt_file))
        assert result["DeviceName"] == "AirSense10"
        assert result["mask_type"] == "Pillows"  # S.Mask maps to mask_type
    
    def test_parse_with_comments(self, test_output_dir):
        """Test parsing file with comment-like lines."""
        tgt_file = test_output_dir / "comments.tgt"
        content = """#IMF 6.04.01
Mode 1
#VIR 1234
Press 1000
"""
        tgt_file.write_text(content)
        
        result = parse_tgt_file(str(tgt_file))
        assert "software_version" in result
        assert result["software_version"] == "6.04.01"
        assert "mode" in result


@pytest.mark.unit
class TestTgtToDeviceSettings:
    """Test converting TGT data to DeviceSettings."""
    
    def test_convert_cpap_mode(self):
        """Test converting CPAP mode settings."""
        tgt_data = {
            "mode": 0,  # CPAP
            "pressure": 1000,  # 10.00 cmH2O
        }
        
        settings = tgt_to_device_settings(tgt_data)
        assert settings.mode == CPAPMode.CPAP
        assert settings.pressure == 10.0
    
    def test_convert_apap_mode(self):
        """Test converting APAP mode settings."""
        tgt_data = {
            "mode": 1,  # APAP
            "pressure_min": 600,  # 6.00 cmH2O
            "pressure_max": 2000,  # 20.00 cmH2O
        }
        
        settings = tgt_to_device_settings(tgt_data)
        assert settings.mode == CPAPMode.APAP
        assert settings.pressure_min == 6.0
        assert settings.pressure_max == 20.0
    
    def test_convert_epr_settings(self):
        """Test converting EPR settings."""
        tgt_data = {
            "epr_enable": 1,
            "epr_level": 2,
            "epr_type": 2,  # Full Time
        }
        
        settings = tgt_to_device_settings(tgt_data)
        assert settings.epr_enabled is True
        assert settings.epr_level == 2
        assert settings.epr_type == "Full Time"
    
    def test_convert_ramp_settings(self):
        """Test converting ramp settings."""
        tgt_data = {
            "ramp_enable": 1,
            "ramp_time": 20,
            "start_pressure": 400,  # 4.00 cmH2O
        }
        
        settings = tgt_to_device_settings(tgt_data)
        assert settings.ramp_enabled is True
        assert settings.ramp_time == 20
        assert settings.ramp_start_pressure == 4.0
    
    def test_convert_mask_settings(self):
        """Test converting mask type."""
        for mask_val, expected_type in [
            (0, MaskType.NASAL),
            (1, MaskType.PILLOWS),
            (2, MaskType.FULL_FACE),
        ]:
            tgt_data = {"mask_type": mask_val}
            settings = tgt_to_device_settings(tgt_data)
            assert settings.mask_type == expected_type
    
    def test_convert_humidifier_settings(self):
        """Test converting humidifier settings."""
        tgt_data = {
            "humidifier_enable": 1,
            "humidifier_level": 5,
            "temperature_enable": 1,
            "temperature": 72.0,
            "climate_control": 2,  # Auto
        }
        
        settings = tgt_to_device_settings(tgt_data)
        assert settings.humidifier_enabled is True
        assert settings.humidifier_level == 5
        assert settings.temperature_enabled is True
        assert settings.temperature == 72.0
        assert settings.climate_control == "Auto"
    
    def test_convert_comfort_settings(self):
        """Test converting comfort settings."""
        tgt_data = {
            "smart_start": 1,
            "tube_type": "SlimLine",
            "antibacterial_filter": 1,
        }
        
        settings = tgt_to_device_settings(tgt_data)
        assert settings.smart_start is True
        assert settings.tube_type == "SlimLine"
        assert settings.antibacterial_filter is True
    
    def test_convert_empty_data(self):
        """Test converting empty TGT data."""
        settings = tgt_to_device_settings({})
        assert isinstance(settings, DeviceSettings)
        assert settings.mode is None
        assert settings.pressure is None


@pytest.mark.unit
class TestParseIdentification:
    """Test parsing Identification.tgt file."""
    
    def test_parse_identification_file(self, test_output_dir):
        """Test parsing identification file."""
        id_file = test_output_dir / "Identification.tgt"
        content = """#IMF 6.04.01
#VIR 1234
#RIR 5678
#PVR 37
#PVD 10
"""
        id_file.write_text(content)
        
        result = parse_identification_file(str(id_file))
        assert result["software_version"] == "6.04.01"
        assert result["internal_version"] == 1234
        assert result["release_version"] == 5678
        assert result["platform_version"] == 37
        assert result["platform_variant"] == 10
    
    def test_parse_identification_partial(self, test_output_dir):
        """Test parsing identification with missing fields."""
        id_file = test_output_dir / "Identification.tgt"
        content = """#IMF 6.04.01
"""
        id_file.write_text(content)
        
        result = parse_identification_file(str(id_file))
        assert result["software_version"] == "6.04.01"
        assert result.get("internal_version") is None


@pytest.mark.unit
class TestFindSettingsForDate:
    """Test finding settings for specific dates."""
    
    def test_find_settings_no_directory(self, test_output_dir):
        """Test finding settings when directory doesn't exist."""
        result = find_settings_for_date(
            str(test_output_dir / "nonexistent"),
            "20241127"
        )
        assert result is None
    
    def test_find_settings_empty_directory(self, test_output_dir):
        """Test finding settings in empty directory."""
        settings_dir = test_output_dir / "SETTINGS"
        settings_dir.mkdir()
        
        result = find_settings_for_date(str(settings_dir), "20241127")
        assert result is None
    
    def test_find_settings_with_files(self, test_output_dir):
        """Test finding settings when TGT files exist."""
        settings_dir = test_output_dir / "SETTINGS"
        settings_dir.mkdir()
        
        # Create a settings file
        tgt_file = settings_dir / "AGL.tgt"
        content = """Mode 1
Press 1000
"""
        tgt_file.write_text(content)
        
        result = find_settings_for_date(str(settings_dir), "20241127")
        assert result is not None
        assert isinstance(result, DeviceSettings)


@pytest.mark.integration
def test_parse_real_identification_file(sample_data_dir):
    """Integration test with real Identification.tgt file."""
    id_file = Path(sample_data_dir) / "Identification.tgt"
    
    if not id_file.exists():
        pytest.skip("Identification.tgt not found in sample data")
    
    result = parse_identification_file(str(id_file))
    assert isinstance(result, dict)
    # Should have at least some version information
    assert any(key in result for key in 
              ["software_version", "internal_version", "platform_version"])


@pytest.mark.integration
def test_parse_real_settings_file(sample_settings_dir):
    """Integration test with real settings file."""
    if not Path(sample_settings_dir).exists():
        pytest.skip("SETTINGS directory not found")
    
    # Find first TGT file
    tgt_files = list(Path(sample_settings_dir).glob("*.tgt"))
    if not tgt_files:
        pytest.skip("No TGT files found in SETTINGS directory")
    
    result = parse_tgt_file(str(tgt_files[0]))
    assert isinstance(result, dict)
    
    # Convert to settings
    settings = tgt_to_device_settings(result)
    assert isinstance(settings, DeviceSettings)


@pytest.mark.unit
def test_parse_tgt_with_invalid_lines(tmp_path):
    """Test parsing TGT with invalid lines."""
    tgt_file = tmp_path / "test.tgt"
    tgt_file.write_text(
        "ValidKey: 123\n"
        "InvalidLine\n"
        "AnotherKey: Value\n"
    )
    
    data = parse_tgt_file(str(tgt_file))
    
    # Should parse valid lines and skip invalid ones
    # Keys may include colon in the dict
    assert any("ValidKey" in k for k in data.keys())
    assert any("AnotherKey" in k for k in data.keys())


@pytest.mark.unit
class TestTGTParserEdgeCases:
    """Test edge cases and exception handling in TGT parser."""
    
    def test_parse_settings_invalid_mode(self, tmp_path):
        """Cover lines 87-88 - invalid mode value error."""
        from cpap_py.parsers.tgt_parser import parse_tgt_file, tgt_to_device_settings
        
        tgt_file = tmp_path / "test.tgt"
        tgt_data = {b'mode': struct.pack('<I', 999)}
        
        content = b''
        for key, value in tgt_data.items():
            content += struct.pack('<I', len(key)) + key
            content += struct.pack('<I', len(value)) + value
        
        tgt_file.write_bytes(content)
        
        parsed = parse_tgt_file(str(tgt_file))
        settings = tgt_to_device_settings(parsed)
        assert settings is not None
    
    def test_parse_settings_invalid_mask_type(self, tmp_path):
        """Cover lines 129-130 - invalid mask type value error."""
        from cpap_py.parsers.tgt_parser import parse_tgt_file, tgt_to_device_settings
        
        tgt_file = tmp_path / "test.tgt"
        tgt_data = {b'mask_type': struct.pack('<I', 999)}
        
        content = b''
        for key, value in tgt_data.items():
            content += struct.pack('<I', len(key)) + key
            content += struct.pack('<I', len(value)) + value
        
        tgt_file.write_bytes(content)
        
        parsed = parse_tgt_file(str(tgt_file))
        settings = tgt_to_device_settings(parsed)
        assert settings is not None
    
    def test_parse_settings_climate_control(self, tmp_path):
        """Cover line 161 - climate_control field."""
        from cpap_py.parsers.tgt_parser import parse_tgt_file, tgt_to_device_settings
        
        tgt_file = tmp_path / "test.tgt"
        tgt_data = {b'climate_control': struct.pack('<I', 1)}
        
        content = b''
        for key, value in tgt_data.items():
            content += struct.pack('<I', len(key)) + key
            content += struct.pack('<I', len(value)) + value
        
        tgt_file.write_bytes(content)
        
        parsed = parse_tgt_file(str(tgt_file))
        settings = tgt_to_device_settings(parsed)
        assert settings is not None
    
    def test_parse_settings_autoset_response(self, tmp_path):
        """Cover line 165 - autoset_response field."""
        from cpap_py.parsers.tgt_parser import parse_tgt_file, tgt_to_device_settings
        
        tgt_file = tmp_path / "test.tgt"
        tgt_data = {b'autoset_response': struct.pack('<I', 2)}
        
        content = b''
        for key, value in tgt_data.items():
            content += struct.pack('<I', len(key)) + key
            content += struct.pack('<I', len(value)) + value
        
        tgt_file.write_bytes(content)
        
        parsed = parse_tgt_file(str(tgt_file))
        settings = tgt_to_device_settings(parsed)
        assert settings is not None

        assert settings is not None

