"""
Tests for utility functions and constants.
"""

import pytest

from cpap_py.utils.constants import (
    CHANNEL_CODES,
    CHANNEL_UNITS,
    EVENT_TYPE_MAP,
    SETTINGS_KEYS,
    MODE_VALUES,
    MASK_VALUES,
    EPR_TYPE_VALUES,
    CLIMATE_CONTROL_VALUES,
    CLINICAL_LIMITS,
    AHI_SEVERITY,
    get_ahi_severity,
)


@pytest.mark.unit
class TestChannelCodes:
    """Test channel code mappings."""
    
    def test_channel_codes_exist(self):
        """Test that channel codes dictionary exists and has entries."""
        assert isinstance(CHANNEL_CODES, dict)
        assert len(CHANNEL_CODES) > 0
    
    def test_pressure_channel_mappings(self):
        """Test pressure channel mappings."""
        assert CHANNEL_CODES["Press.40ms"] == "Mask Pressure"
        assert CHANNEL_CODES["Press"] == "Mask Pressure"
        assert CHANNEL_CODES["MaskPress.2s"] == "Mask Pressure (Low)"
    
    def test_flow_channel_mappings(self):
        """Test flow channel mappings."""
        assert CHANNEL_CODES["Flow.40ms"] == "Flow Rate"
        assert CHANNEL_CODES["Flow"] == "Flow Rate"
    
    def test_leak_channel_mappings(self):
        """Test leak channel mappings."""
        assert CHANNEL_CODES["Leak.2s"] == "Leak Rate"
        assert CHANNEL_CODES["Leak"] == "Leak Rate"
    
    def test_spo2_channel_mappings(self):
        """Test SpO2 channel mappings."""
        assert CHANNEL_CODES["SpO2.1s"] == "Oxygen Saturation"
        assert CHANNEL_CODES["Pulse.1s"] == "Pulse Rate"
    
    def test_respiratory_channel_mappings(self):
        """Test respiratory metric mappings."""
        assert CHANNEL_CODES["TidVol.2s"] == "Tidal Volume"
        assert CHANNEL_CODES["MinVent.2s"] == "Minute Ventilation"
        assert CHANNEL_CODES["RespRate.2s"] == "Respiratory Rate"


@pytest.mark.unit
class TestChannelUnits:
    """Test channel unit mappings."""
    
    def test_channel_units_exist(self):
        """Test that channel units dictionary exists."""
        assert isinstance(CHANNEL_UNITS, dict)
        assert len(CHANNEL_UNITS) > 0
    
    def test_pressure_units(self):
        """Test pressure channel units."""
        assert CHANNEL_UNITS["Pressure"] == "cmH2O"
        assert CHANNEL_UNITS["Mask Pressure"] == "cmH2O"
        assert CHANNEL_UNITS["IPAP"] == "cmH2O"
        assert CHANNEL_UNITS["EPAP"] == "cmH2O"
    
    def test_flow_units(self):
        """Test flow channel units."""
        assert CHANNEL_UNITS["Flow Rate"] == "L/s"
        assert CHANNEL_UNITS["Leak Rate"] == "L/min"
    
    def test_volume_units(self):
        """Test volume channel units."""
        assert CHANNEL_UNITS["Tidal Volume"] == "L"
        assert CHANNEL_UNITS["Minute Ventilation"] == "L/min"
    
    def test_spo2_units(self):
        """Test SpO2 channel units."""
        assert CHANNEL_UNITS["Oxygen Saturation"] == "%"
        assert CHANNEL_UNITS["SpO2"] == "%"
        assert CHANNEL_UNITS["Pulse Rate"] == "bpm"
    
    def test_index_units(self):
        """Test index channel units."""
        assert CHANNEL_UNITS["AHI"] == "events/hour"
        assert CHANNEL_UNITS["Apnea Index"] == "events/hour"


@pytest.mark.unit
class TestEventTypeMappings:
    """Test event type mappings."""
    
    def test_event_type_map_exists(self):
        """Test that event type map exists."""
        assert isinstance(EVENT_TYPE_MAP, dict)
        assert len(EVENT_TYPE_MAP) > 0
    
    def test_apnea_mappings(self):
        """Test apnea event mappings."""
        assert EVENT_TYPE_MAP["Obstructive Apnea"] == "OA"
        assert EVENT_TYPE_MAP["Central Apnea"] == "CA"
        assert EVENT_TYPE_MAP["Apnea"] == "A"
    
    def test_hypopnea_mapping(self):
        """Test hypopnea mapping."""
        assert EVENT_TYPE_MAP["Hypopnea"] == "H"
    
    def test_flow_limitation_mapping(self):
        """Test flow limitation mapping."""
        assert EVENT_TYPE_MAP["Flow Limitation"] == "FL"
    
    def test_leak_mapping(self):
        """Test large leak mapping."""
        assert EVENT_TYPE_MAP["Large Leak"] == "LL"


@pytest.mark.unit
class TestSettingsKeyMappings:
    """Test settings key mappings."""
    
    def test_settings_keys_exist(self):
        """Test that settings keys dictionary exists."""
        assert isinstance(SETTINGS_KEYS, dict)
        assert len(SETTINGS_KEYS) > 0
    
    def test_version_key_mappings(self):
        """Test version key mappings."""
        assert SETTINGS_KEYS["#IMF"] == "software_version"
        assert SETTINGS_KEYS["#VIR"] == "internal_version"
        assert SETTINGS_KEYS["#RIR"] == "release_version"
    
    def test_mode_key_mappings(self):
        """Test mode key mappings."""
        assert SETTINGS_KEYS["Mode"] == "mode"
        assert SETTINGS_KEYS["S.Mode"] == "mode"
    
    def test_pressure_key_mappings(self):
        """Test pressure key mappings."""
        assert SETTINGS_KEYS["Press"] == "pressure"
        assert SETTINGS_KEYS["MaxPress"] == "pressure_max"
        assert SETTINGS_KEYS["MinPress"] == "pressure_min"
    
    def test_epr_key_mappings(self):
        """Test EPR key mappings."""
        assert SETTINGS_KEYS["S.EPR.EPREnable"] == "epr_enable"
        assert SETTINGS_KEYS["S.EPR.Level"] == "epr_level"
        assert SETTINGS_KEYS["S.EPR.EPRType"] == "epr_type"


@pytest.mark.unit
class TestModeValues:
    """Test mode value mappings."""
    
    def test_mode_values_exist(self):
        """Test that mode values dictionary exists."""
        assert isinstance(MODE_VALUES, dict)
        assert len(MODE_VALUES) > 0
    
    def test_basic_modes(self):
        """Test basic mode mappings."""
        assert MODE_VALUES[0] == "CPAP"
        assert MODE_VALUES[1] == "APAP"
    
    def test_bilevel_modes(self):
        """Test BiLevel mode mappings."""
        assert MODE_VALUES[2] == "BiLevel-T"
        assert MODE_VALUES[3] == "BiLevel-S"
        assert MODE_VALUES[4] == "BiLevel-S/T"
    
    def test_advanced_modes(self):
        """Test advanced mode mappings."""
        assert MODE_VALUES[7] == "ASV"
        assert MODE_VALUES[8] == "ASVAuto"


@pytest.mark.unit
class TestMaskValues:
    """Test mask type value mappings."""
    
    def test_mask_values_exist(self):
        """Test that mask values dictionary exists."""
        assert isinstance(MASK_VALUES, dict)
        assert len(MASK_VALUES) > 0
    
    def test_mask_types(self):
        """Test mask type mappings."""
        assert MASK_VALUES[0] == "Nasal"
        assert MASK_VALUES[1] == "Pillows"
        assert MASK_VALUES[2] == "Full Face"
        assert MASK_VALUES[3] == "Unknown"


@pytest.mark.unit
class TestEPRTypeValues:
    """Test EPR type value mappings."""
    
    def test_epr_type_values_exist(self):
        """Test that EPR type values dictionary exists."""
        assert isinstance(EPR_TYPE_VALUES, dict)
    
    def test_epr_types(self):
        """Test EPR type mappings."""
        assert EPR_TYPE_VALUES[0] == "Off"
        assert EPR_TYPE_VALUES[1] == "Ramp Only"
        assert EPR_TYPE_VALUES[2] == "Full Time"


@pytest.mark.unit
class TestClimateControlValues:
    """Test climate control value mappings."""
    
    def test_climate_control_values_exist(self):
        """Test that climate control values dictionary exists."""
        assert isinstance(CLIMATE_CONTROL_VALUES, dict)
    
    def test_climate_control_types(self):
        """Test climate control mappings."""
        assert CLIMATE_CONTROL_VALUES[0] == "Off"
        assert CLIMATE_CONTROL_VALUES[1] == "Manual"
        assert CLIMATE_CONTROL_VALUES[2] == "Auto"


@pytest.mark.unit
class TestClinicalLimits:
    """Test clinical limit constants."""
    
    def test_clinical_limits_exist(self):
        """Test that clinical limits dictionary exists."""
        assert isinstance(CLINICAL_LIMITS, dict)
        assert len(CLINICAL_LIMITS) > 0
    
    def test_pressure_limits(self):
        """Test pressure limit values."""
        assert CLINICAL_LIMITS["pressure_min"] == 4.0
        assert CLINICAL_LIMITS["pressure_max"] == 20.0
        assert CLINICAL_LIMITS["pressure_min"] < CLINICAL_LIMITS["pressure_max"]
    
    def test_epr_limits(self):
        """Test EPR limit values."""
        assert CLINICAL_LIMITS["epr_level_max"] == 3
        assert CLINICAL_LIMITS["epr_level_max"] >= 0
    
    def test_ramp_limits(self):
        """Test ramp time limit values."""
        assert CLINICAL_LIMITS["ramp_time_max"] == 45
        assert CLINICAL_LIMITS["ramp_time_max"] > 0
    
    def test_humidifier_limits(self):
        """Test humidifier limit values."""
        assert CLINICAL_LIMITS["humidifier_level_max"] == 8
        assert CLINICAL_LIMITS["humidifier_level_max"] > 0
    
    def test_temperature_limits(self):
        """Test temperature limit values."""
        assert CLINICAL_LIMITS["temperature_min"] == 60
        assert CLINICAL_LIMITS["temperature_max"] == 86
        assert CLINICAL_LIMITS["temperature_min"] < CLINICAL_LIMITS["temperature_max"]


@pytest.mark.unit
class TestAHISeverity:
    """Test AHI severity classification."""
    
    def test_ahi_severity_exists(self):
        """Test that AHI severity dictionary exists."""
        assert isinstance(AHI_SEVERITY, dict)
        assert len(AHI_SEVERITY) > 0
    
    def test_ahi_severity_ranges(self):
        """Test AHI severity range definitions."""
        assert AHI_SEVERITY["normal"] == (0, 5)
        assert AHI_SEVERITY["mild"] == (5, 15)
        assert AHI_SEVERITY["moderate"] == (15, 30)
        assert AHI_SEVERITY["severe"][0] == 30
    
    def test_get_ahi_severity_normal(self):
        """Test classifying normal AHI."""
        assert get_ahi_severity(0.0) == "normal"
        assert get_ahi_severity(2.5) == "normal"
        assert get_ahi_severity(4.9) == "normal"
    
    def test_get_ahi_severity_mild(self):
        """Test classifying mild AHI."""
        assert get_ahi_severity(5.0) == "mild"
        assert get_ahi_severity(10.0) == "mild"
        assert get_ahi_severity(14.9) == "mild"
    
    def test_get_ahi_severity_moderate(self):
        """Test classifying moderate AHI."""
        assert get_ahi_severity(15.0) == "moderate"
        assert get_ahi_severity(20.0) == "moderate"
        assert get_ahi_severity(29.9) == "moderate"
    
    def test_get_ahi_severity_severe(self):
        """Test classifying severe AHI."""
        assert get_ahi_severity(30.0) == "severe"
        assert get_ahi_severity(50.0) == "severe"
        assert get_ahi_severity(100.0) == "severe"
    
    def test_get_ahi_severity_edge_cases(self):
        """Test AHI classification edge cases."""
        # Boundary values
        assert get_ahi_severity(5.0) == "mild"
        assert get_ahi_severity(15.0) == "moderate"
        assert get_ahi_severity(30.0) == "severe"
    
    def test_get_ahi_severity_out_of_range(self):
        """Test AHI classification with out of range values."""
        # Negative values should return unknown
        assert get_ahi_severity(-1.0) == "unknown"
        # Very high values fall into severe range (30 to inf)
        assert get_ahi_severity(999.0) == "severe"  # Still in severe range
    
    def test_get_ahi_severity_very_high(self):
        """Test AHI classification for extreme values."""
        # Very high AHI should be classified as severe (30 to infinity)
        assert get_ahi_severity(150.0) == "severe"


@pytest.mark.unit
class TestConstantConsistency:
    """Test consistency across constant dictionaries."""
    
    def test_channel_codes_have_units(self):
        """Test that major channels in CHANNEL_CODES have unit definitions."""
        important_channels = [
            "Mask Pressure",
            "Flow Rate",
            "Leak Rate",
            "Oxygen Saturation",
            "Tidal Volume",
        ]
        
        for channel in important_channels:
            assert channel in CHANNEL_UNITS, f"{channel} missing from CHANNEL_UNITS"
    
    def test_all_modes_have_values(self):
        """Test that all documented modes have value mappings."""
        # Verify we have common modes
        assert any("CPAP" in v for v in MODE_VALUES.values())
        assert any("APAP" in v for v in MODE_VALUES.values())
        assert any("BiLevel" in v for v in MODE_VALUES.values())
    
    def test_clinical_limits_reasonable(self):
        """Test that clinical limits are reasonable values."""
        # Pressure range check
        assert 3 <= CLINICAL_LIMITS["pressure_min"] <= 6
        assert 18 <= CLINICAL_LIMITS["pressure_max"] <= 25
        
        # EPR check
        assert 2 <= CLINICAL_LIMITS["epr_level_max"] <= 5
        
        # Ramp time check
        assert 30 <= CLINICAL_LIMITS["ramp_time_max"] <= 60
