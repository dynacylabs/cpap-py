"""
Tests for identification.py module
"""

import pytest
import json
from pathlib import Path
from cpap_py.identification import IdentificationParser, MachineInfo


class TestMachineInfo:
    """Tests for MachineInfo dataclass"""
    
    def test_machine_info_defaults(self):
        """Test MachineInfo default values"""
        info = MachineInfo()
        assert info.serial == ""
        assert info.model == ""
        assert info.model_number == ""
        assert info.series == ""
        assert info.loader_name == "ResMed"
        assert info.properties == {}
    
    def test_machine_info_initialization(self):
        """Test MachineInfo with custom values"""
        info = MachineInfo(
            serial="12345678",
            model="AirSense 10",
            model_number="37207",
            series="AirSense 10",
            properties={"test": "value"}
        )
        assert info.serial == "12345678"
        assert info.model == "AirSense 10"
        assert info.model_number == "37207"
        assert info.series == "AirSense 10"
        assert info.properties["test"] == "value"


class TestIdentificationParser:
    """Tests for IdentificationParser"""
    
    def test_parser_initialization(self, temp_dir):
        """Test parser initialization"""
        parser = IdentificationParser(str(temp_dir))
        assert parser.base_path == temp_dir
    
    def test_parse_tgt_file(self, sample_tgt_identification, temp_dir):
        """Test parsing .tgt identification file"""
        parser = IdentificationParser(str(temp_dir))
        info = parser.parse()
        
        assert info is not None
        assert info.serial == "12345678"
        assert info.model == "AirSense 10 AutoSet"
        assert info.model_number == "37207"
        assert info.series == "AirSense 10"
        assert info.properties["SRN"] == "12345678"
        assert info.properties["PNA"] == "AirSense 10 AutoSet"
        assert info.properties["MID"] == "AS10-AUTOSET"
    
    def test_parse_json_file(self, sample_json_identification, temp_dir):
        """Test parsing .json identification file"""
        parser = IdentificationParser(str(temp_dir))
        info = parser.parse()
        
        assert info is not None
        assert info.serial == "87654321"
        assert info.model == "AirSense 11 AutoSet"
        assert info.model_number == "38000"
        assert info.series == "AirSense 11"
        assert info.properties["SerialNumber"] == "87654321"
        assert info.properties["ProductName"] == "AirSense 11 AutoSet"
    
    def test_json_priority_over_tgt(self, temp_dir):
        """Test that JSON file is parsed before TGT if both exist"""
        # Create both files
        json_data = {
            "FlowGenerator": {
                "IdentificationProfiles": {
                    "Product": {
                        "SerialNumber": "JSON_SERIAL",
                        "ProductCode": "38000",
                        "ProductName": "AirSense 11"
                    }
                }
            }
        }
        json_path = temp_dir / "Identification.json"
        json_path.write_text(json.dumps(json_data))
        
        tgt_path = temp_dir / "Identification.tgt"
        tgt_path.write_text("#SRN TGT_SERIAL\n#PNA AirSense 10\n")
        
        parser = IdentificationParser(str(temp_dir))
        info = parser.parse()
        
        # Should parse JSON file, not TGT
        assert info.serial == "JSON_SERIAL"
        assert "AirSense 11" in info.model
    
    def test_no_identification_file(self, temp_dir):
        """Test when no identification file exists"""
        parser = IdentificationParser(str(temp_dir))
        info = parser.parse()
        assert info is None
    
    def test_parse_tgt_empty_lines(self, temp_dir):
        """Test parsing TGT with empty lines and comments"""
        content = """
#SRN 12345678

#PNA AirSense 10

#PCD 37207
"""
        filepath = temp_dir / "Identification.tgt"
        filepath.write_text(content)
        
        parser = IdentificationParser(str(temp_dir))
        info = parser.parse()
        
        assert info is not None
        assert info.serial == "12345678"
        assert info.model == "AirSense 10"
    
    def test_parse_tgt_malformed_lines(self, temp_dir):
        """Test parsing TGT with malformed lines"""
        content = """#SRN 12345678
#INVALIDLINE
#PNA AirSense 10
#NOVALUE
"""
        filepath = temp_dir / "Identification.tgt"
        filepath.write_text(content)
        
        parser = IdentificationParser(str(temp_dir))
        info = parser.parse()
        
        assert info is not None
        assert info.serial == "12345678"
        assert info.model == "AirSense 10"
        # Malformed lines should be ignored
        assert "INVALIDLINE" not in info.properties
    
    def test_parse_tgt_s9_series(self, temp_dir):
        """Test detection of S9 series from model name"""
        content = "#SRN 12345678\n#PNA S9 Elite\n"
        filepath = temp_dir / "Identification.tgt"
        filepath.write_text(content)
        
        parser = IdentificationParser(str(temp_dir))
        info = parser.parse()
        
        assert info.series == "S9"
    
    def test_parse_tgt_aircurve(self, temp_dir):
        """Test detection of AirCurve 10 series"""
        content = "#SRN 12345678\n#PNA AirCurve 10 VAuto\n"
        filepath = temp_dir / "Identification.tgt"
        filepath.write_text(content)
        
        parser = IdentificationParser(str(temp_dir))
        info = parser.parse()
        
        assert info.series == "AirSense 10"
        assert "AirCurve" in info.model
    
    def test_parse_json_missing_fields(self, temp_dir):
        """Test parsing JSON with missing fields"""
        json_data = {
            "FlowGenerator": {
                "IdentificationProfiles": {
                    "Product": {
                        "SerialNumber": "12345678"
                        # Missing ProductCode and ProductName
                    }
                }
            }
        }
        filepath = temp_dir / "Identification.json"
        filepath.write_text(json.dumps(json_data))
        
        parser = IdentificationParser(str(temp_dir))
        info = parser.parse()
        
        assert info is not None
        assert info.serial == "12345678"
        assert info.model == ""
        assert info.model_number == ""
    
    def test_parse_json_invalid_structure(self, temp_dir):
        """Test parsing JSON with invalid structure"""
        json_data = {"invalid": "structure"}
        filepath = temp_dir / "Identification.json"
        filepath.write_text(json.dumps(json_data))
        
        parser = IdentificationParser(str(temp_dir))
        info = parser.parse()
        
        # Should return None when serial is empty
        assert info is None
    
    def test_parse_json_malformed(self, temp_dir):
        """Test parsing malformed JSON file"""
        filepath = temp_dir / "Identification.json"
        filepath.write_text("{invalid json content")
        
        parser = IdentificationParser(str(temp_dir))
        info = parser.parse()
        
        assert info is None
    
    def test_parse_tgt_io_error(self, temp_dir):
        """Test handling of I/O errors"""
        filepath = temp_dir / "Identification.tgt"
        filepath.write_text("#SRN 12345678\n")
        filepath.chmod(0o000)  # Remove all permissions
        
        try:
            parser = IdentificationParser(str(temp_dir))
            info = parser.parse()
            # Should handle error gracefully
            assert info is not None  # Returns empty MachineInfo
        finally:
            filepath.chmod(0o644)  # Restore permissions
    
    def test_parse_tgt_all_fields(self, temp_dir):
        """Test parsing TGT with all supported fields"""
        content = """#SRN 12345678
#PNA AirSense 10 AutoSet
#PCD 37207
#MID AS10-AUTOSET
#CID 12345
#SID V10.3.0
"""
        filepath = temp_dir / "Identification.tgt"
        filepath.write_text(content)
        
        parser = IdentificationParser(str(temp_dir))
        info = parser.parse()
        
        assert info.serial == "12345678"
        assert info.model == "AirSense 10 AutoSet"
        assert info.model_number == "37207"
        assert info.properties["ModelID"] == "AS10-AUTOSET"
        assert info.properties["ConfigID"] == "12345"
        assert info.properties["SoftwareID"] == "V10.3.0"
    
    def test_parse_json_airsense_10(self, temp_dir):
        """Test parsing JSON for AirSense 10"""
        json_data = {
            "FlowGenerator": {
                "IdentificationProfiles": {
                    "Product": {
                        "SerialNumber": "12345678",
                        "ProductCode": "37207",
                        "ProductName": "AirSense 10 AutoSet"
                    }
                }
            }
        }
        filepath = temp_dir / "Identification.json"
        filepath.write_text(json.dumps(json_data))
        
        parser = IdentificationParser(str(temp_dir))
        info = parser.parse()
        
        assert info.series == "AirSense 10"
    
    def test_parse_json_no_series_in_name(self, temp_dir):
        """Test parsing JSON when product name doesn't contain series number"""
        json_data = {
            "FlowGenerator": {
                "IdentificationProfiles": {
                    "Product": {
                        "SerialNumber": "12345678",
                        "ProductCode": "12345",
                        "ProductName": "Unknown Device"
                    }
                }
            }
        }
        filepath = temp_dir / "Identification.json"
        filepath.write_text(json.dumps(json_data))
        
        parser = IdentificationParser(str(temp_dir))
        info = parser.parse()
        
        assert info.series == ""
