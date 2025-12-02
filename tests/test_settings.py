"""
Tests for settings proposals and validation.
"""

import pytest
from datetime import datetime

from cpap_py.settings import (
    SettingsProposal,
    SettingChange,
    ChangeReason,
    ChangeSeverity,
    create_pressure_adjustment_proposal,
    create_comfort_improvement_proposal,
)
from cpap_py.models import DeviceSettings, CPAPMode


@pytest.mark.unit
class TestSettingChange:
    """Test SettingChange model."""
    
    def test_setting_change_creation(self):
        """Test creating a setting change."""
        change = SettingChange(
            setting_name="pressure",
            current_value=10.0,
            proposed_value=12.0,
            reason=ChangeReason.REDUCE_AHI,
            rationale="Increase pressure to reduce AHI from 8.5 to target <5"
        )
        assert change.setting_name == "pressure"
        assert change.current_value == 10.0
        assert change.proposed_value == 12.0
        assert change.is_safe is True
    
    def test_setting_change_with_supporting_data(self):
        """Test change with supporting data."""
        change = SettingChange(
            setting_name="pressure_max",
            current_value=15.0,
            proposed_value=18.0,
            reason=ChangeReason.OPTIMIZE_THERAPY,
            rationale="Increase max pressure based on 95th percentile data",
            supporting_data={
                "current_95th_percentile": 14.8,
                "ahi": 12.5,
                "leak_rate": 3.2
            }
        )
        assert "current_95th_percentile" in change.supporting_data
        assert change.supporting_data["ahi"] == 12.5
    
    def test_setting_change_severity_levels(self):
        """Test different severity levels."""
        for severity in [ChangeSeverity.MINOR, ChangeSeverity.MODERATE, 
                        ChangeSeverity.MAJOR, ChangeSeverity.CRITICAL]:
            change = SettingChange(
                setting_name="epr_level",
                current_value=1,
                proposed_value=2,
                reason=ChangeReason.IMPROVE_COMFORT,
                rationale="Test",
                severity=severity
            )
            assert change.severity == severity


@pytest.mark.unit
class TestSettingChangeValidation:
    """Test safety validation of setting changes."""
    
    def test_validate_safe_pressure_change(self):
        """Test validation of safe pressure change."""
        change = SettingChange(
            setting_name="pressure",
            current_value=10.0,
            proposed_value=12.0,
            reason=ChangeReason.REDUCE_AHI,
            rationale="Increase pressure"
        )
        is_safe = change.validate_safety()
        assert is_safe is True
        assert len(change.safety_warnings) == 0
    
    def test_validate_pressure_too_low(self):
        """Test validation catches pressure below minimum."""
        change = SettingChange(
            setting_name="pressure",
            current_value=6.0,
            proposed_value=3.0,
            reason=ChangeReason.IMPROVE_COMFORT,
            rationale="Lower pressure"
        )
        is_safe = change.validate_safety()
        assert is_safe is False
        assert len(change.safety_warnings) > 0
        assert "below minimum" in change.safety_warnings[0]
    
    def test_validate_pressure_too_high(self):
        """Test validation catches pressure above maximum."""
        change = SettingChange(
            setting_name="pressure_max",
            current_value=18.0,
            proposed_value=25.0,
            reason=ChangeReason.REDUCE_AHI,
            rationale="Increase max pressure"
        )
        is_safe = change.validate_safety()
        assert is_safe is False
        assert len(change.safety_warnings) > 0
        assert "exceeds maximum" in change.safety_warnings[0]
    
    def test_validate_epr_level_too_high(self):
        """Test validation catches EPR level above maximum."""
        change = SettingChange(
            setting_name="epr_level",
            current_value=2,
            proposed_value=5,
            reason=ChangeReason.IMPROVE_COMFORT,
            rationale="Increase EPR"
        )
        is_safe = change.validate_safety()
        assert is_safe is False
        assert len(change.safety_warnings) > 0
    
    def test_validate_ramp_time_too_long(self):
        """Test validation catches excessive ramp time."""
        change = SettingChange(
            setting_name="ramp_time",
            current_value=20,
            proposed_value=60,
            reason=ChangeReason.IMPROVE_COMFORT,
            rationale="Longer ramp"
        )
        is_safe = change.validate_safety()
        assert is_safe is False
        assert len(change.safety_warnings) > 0
    
    def test_validate_major_change_requires_approval(self):
        """Test that major changes require clinical approval."""
        change = SettingChange(
            setting_name="pressure",
            current_value=10.0,
            proposed_value=15.0,
            reason=ChangeReason.REDUCE_AHI,
            rationale="Significant pressure increase",
            severity=ChangeSeverity.MAJOR
        )
        change.validate_safety()
        assert change.requires_clinical_approval is True


@pytest.mark.unit
class TestSettingsProposal:
    """Test SettingsProposal model."""
    
    def test_proposal_creation(self, mock_device_settings):
        """Test creating a settings proposal."""
        current_settings = DeviceSettings(**mock_device_settings)
        
        change = SettingChange(
            setting_name="pressure_max",
            current_value=20.0,
            proposed_value=18.0,
            reason=ChangeReason.REDUCE_LEAKS,
            rationale="Reduce max pressure to minimize leaks"
        )
        
        proposal = SettingsProposal(
            device_serial="TEST123456",
            current_settings=current_settings,
            proposed_changes=[change],
            overall_rationale="Patient experiencing large leaks at high pressures",
            expected_outcomes=["Reduced leak rate", "Improved comfort"]
        )
        
        assert proposal.device_serial == "TEST123456"
        assert len(proposal.proposed_changes) == 1
        assert len(proposal.expected_outcomes) == 2
    
    def test_proposal_validation(self, mock_device_settings):
        """Test proposal validation."""
        current_settings = DeviceSettings(**mock_device_settings)
        
        # Create a safe change
        change1 = SettingChange(
            setting_name="epr_level",
            current_value=2,
            proposed_value=3,
            reason=ChangeReason.IMPROVE_COMFORT,
            rationale="Increase EPR for comfort"
        )
        
        # Create an unsafe change
        change2 = SettingChange(
            setting_name="pressure",
            current_value=10.0,
            proposed_value=25.0,
            reason=ChangeReason.REDUCE_AHI,
            rationale="Excessive pressure increase"
        )
        
        proposal = SettingsProposal(
            device_serial="TEST123",
            current_settings=current_settings,
            proposed_changes=[change1, change2],
            overall_rationale="Test proposal"
        )
        
        is_safe = proposal.validate_all_changes()
        assert is_safe is False
        assert proposal.all_changes_safe is False
    
    def test_proposal_apply_to_settings(self, mock_device_settings):
        """Test applying proposal to create new settings."""
        current_settings = DeviceSettings(**mock_device_settings)
        
        change = SettingChange(
            setting_name="epr_level",
            current_value=3,
            proposed_value=2,
            reason=ChangeReason.IMPROVE_COMFORT,
            rationale="Reduce EPR"
        )
        
        proposal = SettingsProposal(
            device_serial="TEST123",
            current_settings=current_settings,
            proposed_changes=[change],
            overall_rationale="Test"
        )
        
        new_settings = proposal.apply_to_settings(current_settings)
        assert new_settings.epr_level == 2
        # Original should be unchanged
        assert current_settings.epr_level == 3
    
    def test_proposal_to_dict(self, mock_device_settings):
        """Test converting proposal to dictionary."""
        current_settings = DeviceSettings(**mock_device_settings)
        
        change = SettingChange(
            setting_name="pressure_max",
            current_value=20.0,
            proposed_value=18.0,
            reason=ChangeReason.REDUCE_LEAKS,
            rationale="Reduce leaks"
        )
        
        proposal = SettingsProposal(
            device_serial="TEST123",
            current_settings=current_settings,
            proposed_changes=[change],
            overall_rationale="Test proposal",
            expected_outcomes=["Better therapy"]
        )
        
        data = proposal.to_dict()
        assert isinstance(data, dict)
        assert "proposal_id" in data
        assert "device_serial" in data
        assert "proposed_changes" in data
        assert len(data["proposed_changes"]) == 1
    
    def test_proposal_to_summary(self, mock_device_settings):
        """Test generating human-readable summary."""
        current_settings = DeviceSettings(**mock_device_settings)
        
        change = SettingChange(
            setting_name="epr_level",
            current_value=2,
            proposed_value=3,
            reason=ChangeReason.IMPROVE_COMFORT,
            rationale="Increase EPR for better comfort"
        )
        
        proposal = SettingsProposal(
            device_serial="TEST123",
            current_settings=current_settings,
            proposed_changes=[change],
            overall_rationale="Improve patient comfort",
            expected_outcomes=["Better sleep", "Higher compliance"]
        )
        
        summary = proposal.to_summary()
        assert isinstance(summary, str)
        assert "TEST123" in summary
        assert "epr_level" in summary
        assert "2 → 3" in summary
    
    def test_proposal_with_clinical_context(self, mock_device_settings):
        """Test proposal with clinical context fields."""
        current_settings = DeviceSettings(**mock_device_settings)
        
        change = SettingChange(
            setting_name="pressure_max",
            current_value=15.0,
            proposed_value=18.0,
            reason=ChangeReason.REDUCE_AHI,
            rationale="Increase pressure to control AHI"
        )
        
        proposal = SettingsProposal(
            device_serial="TEST123",
            current_settings=current_settings,
            proposed_changes=[change],
            overall_rationale="High AHI needs addressing",
            patient_ahi=12.5,
            recent_leak_issues=False,
            comfort_complaints=False
        )
        
        assert proposal.patient_ahi == 12.5
        assert proposal.recent_leak_issues is False
        assert proposal.comfort_complaints is False


@pytest.mark.unit
class TestProposalHelpers:
    """Test helper functions for creating proposals."""
    
    def test_create_pressure_adjustment_cpap(self):
        """Test creating pressure adjustment for CPAP mode."""
        current_settings = DeviceSettings(
            mode=CPAPMode.CPAP,
            pressure=10.0
        )
        
        proposal = create_pressure_adjustment_proposal(
            device_serial="TEST123",
            current_settings=current_settings,
            target_pressure=12.0,
            reason="AHI is 8.5, target <5",
            ahi=8.5
        )
        
        assert len(proposal.proposed_changes) == 1
        assert proposal.proposed_changes[0].setting_name == "pressure"
        assert proposal.proposed_changes[0].proposed_value == 12.0
        assert proposal.patient_ahi == 8.5
    
    def test_create_pressure_adjustment_apap(self):
        """Test creating pressure adjustment for APAP mode."""
        current_settings = DeviceSettings(
            mode=CPAPMode.APAP,
            pressure_min=6.0,
            pressure_max=15.0
        )
        
        proposal = create_pressure_adjustment_proposal(
            device_serial="TEST123",
            current_settings=current_settings,
            target_pressure=18.0,
            reason="95th percentile at max, AHI elevated"
        )
        
        assert len(proposal.proposed_changes) == 1
        assert proposal.proposed_changes[0].setting_name == "pressure_max"
        assert proposal.proposed_changes[0].proposed_value == 18.0
    
    def test_create_comfort_improvement(self):
        """Test creating comfort improvement proposal."""
        current_settings = DeviceSettings(
            epr_enabled=False,
            epr_level=0,
            ramp_enabled=False
        )
        
        proposal = create_comfort_improvement_proposal(
            device_serial="TEST123",
            current_settings=current_settings,
            enable_epr=True,
            epr_level=2,
            enable_ramp=True,
            ramp_time=20
        )
        
        # Should have 4 changes: epr_enabled, epr_level, ramp_enabled, ramp_time
        assert len(proposal.proposed_changes) == 4
        assert proposal.comfort_complaints is True
    
    def test_create_comfort_improvement_partial(self):
        """Test comfort improvement when EPR already enabled."""
        current_settings = DeviceSettings(
            epr_enabled=True,
            epr_level=2,
            ramp_enabled=False
        )
        
        proposal = create_comfort_improvement_proposal(
            device_serial="TEST123",
            current_settings=current_settings,
            enable_epr=True,
            epr_level=2,
            enable_ramp=True,
            ramp_time=15
        )
        
        # Should only have ramp changes since EPR already at target
        ramp_changes = [c for c in proposal.proposed_changes 
                       if "ramp" in c.setting_name.lower()]
        assert len(ramp_changes) == 2


@pytest.mark.unit
class TestChangeReasons:
    """Test change reason enum."""
    
    def test_all_change_reasons(self):
        """Test all change reason values."""
        reasons = [
            ChangeReason.REDUCE_AHI,
            ChangeReason.REDUCE_LEAKS,
            ChangeReason.IMPROVE_COMFORT,
            ChangeReason.INCREASE_COMPLIANCE,
            ChangeReason.ADJUST_PRESSURE,
            ChangeReason.OPTIMIZE_THERAPY,
            ChangeReason.CLINICAL_GUIDELINE,
            ChangeReason.PATIENT_REQUEST,
            ChangeReason.OTHER,
        ]
        for reason in reasons:
            assert isinstance(reason.value, str)


@pytest.mark.unit
class TestChangeSeverity:
    """Test change severity enum."""
    
    def test_all_severity_levels(self):
        """Test all severity level values."""
        severities = [
            ChangeSeverity.MINOR,
            ChangeSeverity.MODERATE,
            ChangeSeverity.MAJOR,
            ChangeSeverity.CRITICAL,
        ]
        for severity in severities:
            assert isinstance(severity.value, str)


@pytest.mark.unit
def test_setting_change_str_representation():
    """Test SettingChange string representation."""
    # Use a valid ChangeReason with required fields
    change = SettingChange(
        setting_name="pressure",
        current_value=10.0,
        proposed_value=12.0,
        reason=ChangeReason.REDUCE_AHI,
        rationale="Increase pressure to reduce residual AHI",
        severity=ChangeSeverity.MODERATE
    )
    
    # Should have string representation
    str_repr = str(change)
    assert "pressure" in str_repr or "SettingChange" in str_repr


@pytest.mark.unit  
def test_settings_proposal_empty_changes():
    """Test creating a proposal with no changes."""
    current = DeviceSettings(mode=CPAPMode.CPAP)
    
    proposal = SettingsProposal(
        device_serial="TEST123",
        current_settings=current,
        proposed_changes=[],  # Empty list of changes
        overall_rationale="No changes needed - settings are optimal"
    )
    
    assert len(proposal.proposed_changes) == 0


@pytest.mark.unit
class TestSettingsValidationEdgeCases:
    """Test edge cases in settings validation and formatting."""
    
    def test_validate_safety_requires_clinical_approval(self):
        """Cover line 154 - requires_clinical_approval flag."""
        from cpap_py.settings import ChangeReason
        change = SettingChange(
            setting_name="pressure_min",
            current_value=4.0,
            proposed_value=8.0,
            reason=ChangeReason.REDUCE_AHI,
            rationale="Increase minimum pressure"
        )
        change.requires_clinical_approval = True
        
        proposal = SettingsProposal(
            device_serial="TEST123",
            current_settings=DeviceSettings(),
            proposed_changes=[change],
            overall_rationale="Test",
            expected_outcomes=["Better therapy"]
        )
        
        result = proposal.validate_all_changes()
        assert proposal.requires_clinical_review is True
    
    def test_format_proposal_with_warnings(self):
        """Cover line 229 - safety warnings in formatted proposal."""
        from cpap_py.settings import ChangeReason
        change = SettingChange(
            setting_name="pressure_max",
            current_value=10.0,
            proposed_value=20.0,
            reason=ChangeReason.REDUCE_AHI,
            rationale="Increase max pressure"
        )
        change.safety_warnings = ["High pressure warning"]
        
        proposal = SettingsProposal(
            device_serial="TEST123",
            current_settings=DeviceSettings(),
            proposed_changes=[change],
            overall_rationale="Test",
            expected_outcomes=["Better AHI"]
        )
        
        formatted = proposal.to_summary()
        assert "⚠️  Warnings:" in formatted
    
    def test_format_proposal_requires_clinical_review(self):
        """Cover line 243 - clinical review warning."""
        from cpap_py.settings import ChangeReason
        change = SettingChange(
            setting_name="pressure_min",
            current_value=4.0,
            proposed_value=12.0,
            reason=ChangeReason.REDUCE_AHI,
            rationale="Significant increase"
        )
        
        proposal = SettingsProposal(
            device_serial="TEST123",
            current_settings=DeviceSettings(),
            proposed_changes=[change],
            overall_rationale="Major adjustment",
            expected_outcomes=["Improved therapy"],
            requires_clinical_review=True
        )
        
        formatted = proposal.to_summary()
        assert "⚠️  This proposal requires clinical review" in formatted

