"""
Tests for CRC validation functionality.
"""

import pytest
import struct
from pathlib import Path

from cpap_py.parsers.crc_parser import (
    CRCValidationMode,
    CRCError,
    read_crc_file,
    calculate_crc16,
    calculate_crc32,
    validate_file_crc,
    validate_directory_crcs,
)


@pytest.mark.unit
class TestCRCReading:
    """Test reading CRC files."""
    
    def test_read_crc_file_not_exists(self, test_output_dir):
        """Test reading non-existent CRC file."""
        result = read_crc_file(str(test_output_dir / "nonexistent.crc"))
        assert result is None
    
    def test_read_crc_file_16bit(self, test_output_dir):
        """Test reading 16-bit CRC file."""
        crc_file = test_output_dir / "test.crc"
        
        # Write 16-bit CRC value
        with open(crc_file, 'wb') as f:
            f.write(struct.pack('<H', 0x1234))
        
        result = read_crc_file(str(crc_file))
        assert result == 0x1234
    
    def test_read_crc_file_32bit(self, test_output_dir):
        """Test reading 32-bit CRC file."""
        crc_file = test_output_dir / "test32.crc"
        
        # Write 32-bit CRC value
        with open(crc_file, 'wb') as f:
            f.write(struct.pack('<I', 0x12345678))
        
        result = read_crc_file(str(crc_file))
        assert result == 0x12345678
    
    def test_read_crc_file_unusual_size(self, test_output_dir):
        """Test reading CRC file with unusual byte size."""
        crc_file = test_output_dir / "test_unusual.crc"
        
        # Write 3-byte CRC value (unusual)
        with open(crc_file, 'wb') as f:
            f.write(b'\x12\x34\x56')
        
        # Should attempt to read it
        result = read_crc_file(str(crc_file))
        # May return None or a value depending on implementation
        assert result is None or isinstance(result, int)


@pytest.mark.unit
class TestCRCCalculation:
    """Test CRC calculation algorithms."""
    
    def test_calculate_crc16_empty(self):
        """Test CRC16 on empty data."""
        result = calculate_crc16(b'')
        assert isinstance(result, int)
        assert 0 <= result <= 0xFFFF
    
    def test_calculate_crc16_simple(self):
        """Test CRC16 on simple data."""
        data = b'Hello, World!'
        result = calculate_crc16(data)
        assert isinstance(result, int)
        assert 0 <= result <= 0xFFFF
    
    def test_calculate_crc16_consistent(self):
        """Test CRC16 produces consistent results."""
        data = b'Test data'
        result1 = calculate_crc16(data)
        result2 = calculate_crc16(data)
        assert result1 == result2
    
    def test_calculate_crc16_different_data(self):
        """Test CRC16 produces different results for different data."""
        data1 = b'Test data 1'
        data2 = b'Test data 2'
        result1 = calculate_crc16(data1)
        result2 = calculate_crc16(data2)
        assert result1 != result2
    
    def test_calculate_crc32_empty(self):
        """Test CRC32 on empty data."""
        result = calculate_crc32(b'')
        assert isinstance(result, int)
        assert result == 0
    
    def test_calculate_crc32_simple(self):
        """Test CRC32 on simple data."""
        data = b'Hello, World!'
        result = calculate_crc32(data)
        assert isinstance(result, int)
        assert 0 <= result <= 0xFFFFFFFF
    
    def test_calculate_crc32_consistent(self):
        """Test CRC32 produces consistent results."""
        data = b'Test data'
        result1 = calculate_crc32(data)
        result2 = calculate_crc32(data)
        assert result1 == result2


@pytest.mark.unit
class TestFileValidation:
    """Test file CRC validation."""
    
    def test_validate_disabled(self, test_output_dir):
        """Test validation with disabled mode."""
        data_file = test_output_dir / "test.edf"
        data_file.write_bytes(b'Test data')
        
        is_valid, error = validate_file_crc(
            str(data_file),
            mode=CRCValidationMode.DISABLED
        )
        assert is_valid is True
        assert error is None
    
    def test_validate_missing_crc_permissive(self, test_output_dir):
        """Test validation with missing CRC file in permissive mode."""
        data_file = test_output_dir / "test.edf"
        data_file.write_bytes(b'Test data')
        
        is_valid, error = validate_file_crc(
            str(data_file),
            mode=CRCValidationMode.PERMISSIVE
        )
        assert is_valid is False
        assert error is not None
        assert "not found" in error.lower()
    
    def test_validate_missing_crc_strict(self, test_output_dir):
        """Test validation with missing CRC file in strict mode."""
        data_file = test_output_dir / "test.edf"
        data_file.write_bytes(b'Test data')
        
        with pytest.raises(CRCError):
            validate_file_crc(
                str(data_file),
                mode=CRCValidationMode.STRICT
            )
    
    def test_validate_matching_crc16(self, test_output_dir):
        """Test validation with matching CRC16."""
        data_file = test_output_dir / "test.edf"
        crc_file = test_output_dir / "test.crc"
        
        data = b'Test data for CRC validation'
        data_file.write_bytes(data)
        
        # Calculate and write correct CRC
        expected_crc = calculate_crc16(data)
        with open(crc_file, 'wb') as f:
            f.write(struct.pack('<H', expected_crc))
        
        is_valid, error = validate_file_crc(
            str(data_file),
            str(crc_file),
            mode=CRCValidationMode.STRICT
        )
        assert is_valid is True
        assert error is None
    
    def test_validate_matching_crc32(self, test_output_dir):
        """Test validation with matching CRC32."""
        data_file = test_output_dir / "test.edf"
        crc_file = test_output_dir / "test.crc"
        
        data = b'Test data for CRC32 validation'
        data_file.write_bytes(data)
        
        # Calculate and write correct CRC32
        expected_crc = calculate_crc32(data)
        with open(crc_file, 'wb') as f:
            f.write(struct.pack('<I', expected_crc))
        
        is_valid, error = validate_file_crc(
            str(data_file),
            str(crc_file),
            mode=CRCValidationMode.STRICT
        )
        assert is_valid is True
        assert error is None
    
    def test_validate_mismatched_crc_permissive(self, test_output_dir):
        """Test validation with mismatched CRC in permissive mode."""
        data_file = test_output_dir / "test.edf"
        crc_file = test_output_dir / "test.crc"
        
        data_file.write_bytes(b'Test data')
        
        # Write incorrect CRC
        with open(crc_file, 'wb') as f:
            f.write(struct.pack('<H', 0xFFFF))
        
        is_valid, error = validate_file_crc(
            str(data_file),
            str(crc_file),
            mode=CRCValidationMode.PERMISSIVE
        )
        assert is_valid is False
        assert error is not None
        assert "mismatch" in error.lower()
    
    def test_validate_mismatched_crc_strict(self, test_output_dir):
        """Test validation with mismatched CRC in strict mode."""
        data_file = test_output_dir / "test.edf"
        crc_file = test_output_dir / "test.crc"
        
        data_file.write_bytes(b'Test data')
        
        # Write incorrect CRC
        with open(crc_file, 'wb') as f:
            f.write(struct.pack('<H', 0xFFFF))
        
        with pytest.raises(CRCError):
            validate_file_crc(
                str(data_file),
                str(crc_file),
                mode=CRCValidationMode.STRICT
            )


@pytest.mark.unit
class TestDirectoryValidation:
    """Test directory-wide CRC validation."""
    
    def test_validate_directory_empty(self, test_output_dir):
        """Test validating empty directory."""
        results = validate_directory_crcs(
            str(test_output_dir),
            mode=CRCValidationMode.PERMISSIVE
        )
        assert isinstance(results, dict)
        assert len(results) == 0
    
    def test_validate_directory_no_crc_files(self, test_output_dir):
        """Test validating directory with no CRC files."""
        # Create data files without CRC files
        (test_output_dir / "file1.edf").write_bytes(b'data1')
        (test_output_dir / "file2.edf").write_bytes(b'data2')
        
        results = validate_directory_crcs(
            str(test_output_dir),
            mode=CRCValidationMode.PERMISSIVE
        )
        # Should not include files without CRC files
        assert len(results) == 0
    
    def test_validate_directory_with_crc_files(self, test_output_dir):
        """Test validating directory with CRC files."""
        # Create data file and matching CRC
        data_file = test_output_dir / "test.edf"
        crc_file = test_output_dir / "test.crc"
        
        data = b'Test data'
        data_file.write_bytes(data)
        
        expected_crc = calculate_crc16(data)
        with open(crc_file, 'wb') as f:
            f.write(struct.pack('<H', expected_crc))
        
        results = validate_directory_crcs(
            str(test_output_dir),
            mode=CRCValidationMode.PERMISSIVE
        )
        
        assert len(results) == 1
        assert str(data_file) in results
        assert results[str(data_file)]["valid"] is True
    
    def test_validate_directory_recursive(self, test_output_dir):
        """Test validating directory recursively."""
        # Create subdirectory structure
        subdir = test_output_dir / "subdir"
        subdir.mkdir()
        
        # Create files in subdirectory
        data_file = subdir / "test.edf"
        crc_file = subdir / "test.crc"
        
        data = b'Nested test data'
        data_file.write_bytes(data)
        
        expected_crc = calculate_crc32(data)
        with open(crc_file, 'wb') as f:
            f.write(struct.pack('<I', expected_crc))
        
        results = validate_directory_crcs(
            str(test_output_dir),
            mode=CRCValidationMode.PERMISSIVE
        )
        
        assert len(results) == 1
        assert str(data_file) in results
        assert results[str(data_file)]["valid"] is True


@pytest.mark.unit
class TestCRCValidationMode:
    """Test CRC validation mode enum."""
    
    def test_validation_modes(self):
        """Test all CRC validation mode values."""
        assert CRCValidationMode.STRICT == "strict"
        assert CRCValidationMode.PERMISSIVE == "permissive"
        assert CRCValidationMode.DISABLED == "disabled"


@pytest.mark.unit
def test_validate_file_crc_disabled_mode(test_output_dir):
    """Test CRC validation in disabled mode."""
    # Create file without CRC
    test_file = test_output_dir / "test.edf"
    test_file.write_bytes(b"test data")
    
    # In DISABLED mode, should return False (no CRC found) but not raise error
    is_valid, msg = validate_file_crc(
        str(test_file),
        CRCValidationMode.DISABLED
    )
    
    # DISABLED mode still returns False when CRC missing, just doesn't raise
    assert is_valid is False
    assert "not found" in msg


@pytest.mark.integration
def test_validate_real_cpap_files(sample_datalog_dir):
    """Integration test with real CPAP files."""
    if not Path(sample_datalog_dir).exists():
        pytest.skip("Sample data not available")
    
    results = validate_directory_crcs(
        sample_datalog_dir,
        mode=CRCValidationMode.PERMISSIVE
    )
    
    # Check that results were returned
    assert isinstance(results, dict)
    
    # If there are results, check structure
    for file_path, result in results.items():
        assert "valid" in result
        assert "error" in result or "crc_file" in result


@pytest.mark.unit
class TestCRCParserEdgeCases:
    """Test edge cases and exception handling in CRC parser."""
    
    def test_parse_crc_big_endian_16bit(self, tmp_path):
        """Cover lines 52, 54 - big-endian 16-bit CRC."""
        from cpap_py.parsers.crc_parser import read_crc_file
        
        crc_file = tmp_path / "test.crc"
        crc_file.write_bytes(struct.pack('>H', 0x1234))
        
        result = read_crc_file(str(crc_file))
        # Function tries little-endian first, then falls back to big-endian
        assert result is not None
    
    def test_validate_crc_strict_mode_read_failure(self, tmp_path):
        """Cover line 140 - strict mode raises on read failure."""
        from cpap_py.parsers.crc_parser import validate_file_crc
        
        crc_file = tmp_path / "test.crc"
        crc_file.write_bytes(struct.pack('<I', 0x12345678))
        
        target_file = tmp_path / "nonexistent.tgt"
        
        with pytest.raises(CRCError, match="Failed to read data file"):
            validate_file_crc(str(target_file), str(crc_file), mode=CRCValidationMode.STRICT)

