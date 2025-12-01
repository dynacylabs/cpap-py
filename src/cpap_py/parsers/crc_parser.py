"""
CRC (Cyclic Redundancy Check) parser and validator.
Handles verification of data integrity for CPAP files.
"""

import struct
from pathlib import Path
from typing import Optional, Tuple
from enum import Enum


class CRCValidationMode(str, Enum):
    """CRC validation modes."""
    STRICT = "strict"  # Raise exception on mismatch
    PERMISSIVE = "permissive"  # Log warning but continue
    DISABLED = "disabled"  # Skip validation


class CRCError(Exception):
    """Raised when CRC validation fails in strict mode."""
    pass


def read_crc_file(crc_file_path: str) -> Optional[int]:
    """
    Read CRC checksum from .crc file.
    
    CRC files are typically 2-4 bytes containing the checksum value.
    
    Args:
        crc_file_path: Path to .crc file
    
    Returns:
        CRC value as integer, or None if file doesn't exist
    """
    crc_path = Path(crc_file_path)
    
    if not crc_path.exists():
        return None
    
    with open(crc_file_path, 'rb') as f:
        crc_bytes = f.read()
    
    # Try to parse as different integer sizes
    if len(crc_bytes) == 2:
        return struct.unpack('<H', crc_bytes)[0]  # 16-bit little-endian
    elif len(crc_bytes) == 4:
        return struct.unpack('<I', crc_bytes)[0]  # 32-bit little-endian
    else:
        # Unknown format, try to read as big-endian too
        if len(crc_bytes) == 2:
            return struct.unpack('>H', crc_bytes)[0]
        elif len(crc_bytes) == 4:
            return struct.unpack('>I', crc_bytes)[0]
    
    return None


def calculate_crc16(data: bytes) -> int:
    """
    Calculate CRC-16 checksum (CCITT variant commonly used in medical devices).
    
    Args:
        data: Bytes to calculate CRC for
    
    Returns:
        16-bit CRC value
    """
    crc = 0xFFFF  # Initial value
    polynomial = 0x1021  # CRC-16-CCITT polynomial
    
    for byte in data:
        crc ^= (byte << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ polynomial) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    
    return crc


def calculate_crc32(data: bytes) -> int:
    """
    Calculate CRC-32 checksum (IEEE 802.3 variant).
    
    Args:
        data: Bytes to calculate CRC for
    
    Returns:
        32-bit CRC value
    """
    import zlib
    return zlib.crc32(data) & 0xFFFFFFFF


def validate_file_crc(
    data_file_path: str,
    crc_file_path: Optional[str] = None,
    mode: CRCValidationMode = CRCValidationMode.PERMISSIVE
) -> Tuple[bool, Optional[str]]:
    """
    Validate a data file against its CRC checksum.
    
    Args:
        data_file_path: Path to data file (e.g., .edf file)
        crc_file_path: Path to CRC file. If None, assumes same name with .crc extension
        mode: Validation mode (strict, permissive, or disabled)
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if mode == CRCValidationMode.DISABLED:
        return True, None
    
    # Determine CRC file path
    if crc_file_path is None:
        data_path = Path(data_file_path)
        # Remove .gz if present, then replace extension
        name = data_path.name.replace('.gz', '')
        name = name.rsplit('.', 1)[0] + '.crc'
        crc_file_path = str(data_path.parent / name)
    
    # Read expected CRC
    expected_crc = read_crc_file(crc_file_path)
    
    if expected_crc is None:
        error_msg = f"CRC file not found: {crc_file_path}"
        if mode == CRCValidationMode.STRICT:
            raise CRCError(error_msg)
        return False, error_msg
    
    # Read data file
    try:
        with open(data_file_path, 'rb') as f:
            data = f.read()
    except Exception as e:
        error_msg = f"Failed to read data file: {e}"
        if mode == CRCValidationMode.STRICT:
            raise CRCError(error_msg)
        return False, error_msg
    
    # Calculate CRC - try both 16-bit and 32-bit
    calculated_crc16 = calculate_crc16(data)
    calculated_crc32 = calculate_crc32(data)
    
    # Check if either matches
    is_valid = (expected_crc == calculated_crc16) or (expected_crc == calculated_crc32)
    
    if not is_valid:
        error_msg = (
            f"CRC mismatch for {data_file_path}: "
            f"expected {expected_crc:04X}, "
            f"calculated CRC16={calculated_crc16:04X}, CRC32={calculated_crc32:08X}"
        )
        if mode == CRCValidationMode.STRICT:
            raise CRCError(error_msg)
        return False, error_msg
    
    return True, None


def validate_directory_crcs(
    directory: str,
    mode: CRCValidationMode = CRCValidationMode.PERMISSIVE
) -> dict:
    """
    Validate all files in a directory against their CRC files.
    
    Args:
        directory: Directory containing data and CRC files
        mode: Validation mode
    
    Returns:
        Dictionary mapping file paths to validation results
    """
    results = {}
    dir_path = Path(directory)
    
    # Find all data files (excluding .crc files)
    data_files = [
        f for f in dir_path.rglob('*')
        if f.is_file() and not f.name.endswith('.crc')
    ]
    
    for data_file in data_files:
        # Check if corresponding .crc file exists
        crc_file = data_file.parent / (data_file.stem + '.crc')
        
        if crc_file.exists():
            is_valid, error_msg = validate_file_crc(
                str(data_file),
                str(crc_file),
                mode
            )
            results[str(data_file)] = {
                "valid": is_valid,
                "error": error_msg,
                "crc_file": str(crc_file)
            }
    
    return results
