"""
Settings models and proposal system for CPAP configuration changes.
Allows AI/users to propose settings changes without directly writing files.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator

from cpap_py.models import DeviceSettings, CPAPMode
from cpap_py.utils.constants import CLINICAL_LIMITS


class ChangeReason(str, Enum):
    """Reasons for proposing a settings change."""
    
    REDUCE_AHI = "reduce_ahi"
    REDUCE_LEAKS = "reduce_leaks"
    IMPROVE_COMFORT = "improve_comfort"
    INCREASE_COMPLIANCE = "increase_compliance"
    ADJUST_PRESSURE = "adjust_pressure"
    OPTIMIZE_THERAPY = "optimize_therapy"
    CLINICAL_GUIDELINE = "clinical_guideline"
    PATIENT_REQUEST = "patient_request"
    OTHER = "other"


class ChangeSeverity(str, Enum):
    """Severity/priority of proposed change."""
    
    MINOR = "minor"  # Small comfort adjustment
    MODERATE = "moderate"  # Potentially meaningful therapy change
    MAJOR = "major"  # Significant therapy modification
    CRITICAL = "critical"  # Urgent change needed


class SettingChange(BaseModel):
    """Represents a single proposed change to a device setting."""
    
    setting_name: str
    current_value: Any
    proposed_value: Any
    reason: ChangeReason
    rationale: str = Field(description="Detailed explanation for the change")
    severity: ChangeSeverity = ChangeSeverity.MODERATE
    
    # Supporting data
    supporting_data: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Metrics or data supporting this change"
    )
    
    # Safety checks
    is_safe: bool = True
    safety_warnings: List[str] = Field(default_factory=list)
    requires_clinical_approval: bool = False
    
    def validate_safety(self, clinical_limits: Dict[str, Any] = CLINICAL_LIMITS) -> bool:
        """
        Validate that the proposed change is within safe clinical limits.
        
        Args:
            clinical_limits: Dictionary of clinical safety limits
        
        Returns:
            True if safe, False otherwise
        """
        warnings = []
        
        # Check pressure limits
        if "pressure" in self.setting_name.lower():
            if isinstance(self.proposed_value, (int, float)):
                if self.proposed_value < clinical_limits["pressure_min"]:
                    warnings.append(
                        f"Proposed pressure {self.proposed_value} cmH2O is below minimum "
                        f"{clinical_limits['pressure_min']} cmH2O"
                    )
                elif self.proposed_value > clinical_limits["pressure_max"]:
                    warnings.append(
                        f"Proposed pressure {self.proposed_value} cmH2O exceeds maximum "
                        f"{clinical_limits['pressure_max']} cmH2O"
                    )
        
        # Check EPR level
        if "epr_level" in self.setting_name.lower():
            if isinstance(self.proposed_value, int):
                if self.proposed_value > clinical_limits["epr_level_max"]:
                    warnings.append(
                        f"Proposed EPR level {self.proposed_value} exceeds maximum "
                        f"{clinical_limits['epr_level_max']}"
                    )
        
        # Check ramp time
        if "ramp_time" in self.setting_name.lower():
            if isinstance(self.proposed_value, int):
                if self.proposed_value > clinical_limits["ramp_time_max"]:
                    warnings.append(
                        f"Proposed ramp time {self.proposed_value} min exceeds maximum "
                        f"{clinical_limits['ramp_time_max']} min"
                    )
        
        self.safety_warnings = warnings
        self.is_safe = len(warnings) == 0
        
        # Major changes should require approval
        if self.severity in [ChangeSeverity.MAJOR, ChangeSeverity.CRITICAL]:
            self.requires_clinical_approval = True
        
        return self.is_safe


class SettingsProposal(BaseModel):
    """
    A complete proposal for device settings changes.
    This is what the AI generates when recommending configuration changes.
    """
    
    proposal_id: str = Field(default_factory=lambda: f"proposal_{datetime.now().timestamp()}")
    created_at: datetime = Field(default_factory=datetime.now)
    
    device_serial: str
    current_settings: DeviceSettings
    proposed_changes: List[SettingChange]
    
    # Overall assessment
    overall_rationale: str = Field(
        description="High-level explanation of why these changes are proposed"
    )
    expected_outcomes: List[str] = Field(
        default_factory=list,
        description="Expected improvements from these changes"
    )
    
    # Clinical context
    patient_ahi: Optional[float] = None
    recent_leak_issues: bool = False
    comfort_complaints: bool = False
    
    # Validation
    all_changes_safe: bool = True
    requires_clinical_review: bool = False
    
    def validate_all_changes(self) -> bool:
        """Validate safety of all proposed changes."""
        all_safe = True
        requires_review = False
        
        for change in self.proposed_changes:
            if not change.validate_safety():
                all_safe = False
            if change.requires_clinical_approval:
                requires_review = True
        
        self.all_changes_safe = all_safe
        self.requires_clinical_review = requires_review
        
        return all_safe
    
    def apply_to_settings(self, settings: DeviceSettings) -> DeviceSettings:
        """
        Apply proposed changes to create new settings object.
        Does NOT write to files - returns a new settings object.
        
        Args:
            settings: Base settings to modify
        
        Returns:
            New DeviceSettings object with changes applied
        """
        # Create a copy
        new_settings = settings.model_copy(deep=True)
        
        # Apply each change
        for change in self.proposed_changes:
            # Map setting name to attribute
            attr_name = change.setting_name
            
            # Handle nested attributes or special cases
            if hasattr(new_settings, attr_name):
                setattr(new_settings, attr_name, change.proposed_value)
        
        return new_settings
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary for MCP."""
        return {
            "proposal_id": self.proposal_id,
            "created_at": self.created_at.isoformat(),
            "device_serial": self.device_serial,
            "current_settings": self.current_settings.model_dump(),
            "proposed_changes": [
                {
                    "setting": change.setting_name,
                    "current": change.current_value,
                    "proposed": change.proposed_value,
                    "reason": change.reason,
                    "rationale": change.rationale,
                    "severity": change.severity,
                    "is_safe": change.is_safe,
                    "warnings": change.safety_warnings,
                }
                for change in self.proposed_changes
            ],
            "overall_rationale": self.overall_rationale,
            "expected_outcomes": self.expected_outcomes,
            "all_changes_safe": self.all_changes_safe,
            "requires_clinical_review": self.requires_clinical_review,
        }
    
    def to_summary(self) -> str:
        """Generate human-readable summary of proposal."""
        lines = [
            f"Settings Proposal {self.proposal_id}",
            f"Created: {self.created_at.strftime('%Y-%m-%d %H:%M')}",
            f"Device: {self.device_serial}",
            "",
            "Proposed Changes:",
        ]
        
        for i, change in enumerate(self.proposed_changes, 1):
            lines.append(
                f"{i}. {change.setting_name}: "
                f"{change.current_value} → {change.proposed_value}"
            )
            lines.append(f"   Reason: {change.rationale}")
            if change.safety_warnings:
                lines.append(f"   ⚠️  Warnings: {', '.join(change.safety_warnings)}")
        
        lines.extend([
            "",
            "Overall Rationale:",
            self.overall_rationale,
            "",
            "Expected Outcomes:",
        ])
        
        for outcome in self.expected_outcomes:
            lines.append(f"• {outcome}")
        
        if self.requires_clinical_review:
            lines.append("\n⚠️  This proposal requires clinical review before implementation.")
        
        return "\n".join(lines)


def create_pressure_adjustment_proposal(
    device_serial: str,
    current_settings: DeviceSettings,
    target_pressure: float,
    reason: str,
    ahi: Optional[float] = None
) -> SettingsProposal:
    """
    Helper function to create a pressure adjustment proposal.
    
    Args:
        device_serial: Device serial number
        current_settings: Current device settings
        target_pressure: Desired pressure or max pressure
        reason: Reason for adjustment
        ahi: Current AHI if available
    
    Returns:
        SettingsProposal object
    """
    changes = []
    
    # Determine what to adjust based on mode
    if current_settings.mode == CPAPMode.CPAP:
        # Adjust fixed pressure
        changes.append(SettingChange(
            setting_name="pressure",
            current_value=current_settings.pressure,
            proposed_value=target_pressure,
            reason=ChangeReason.ADJUST_PRESSURE,
            rationale=f"Adjust fixed CPAP pressure to {target_pressure} cmH2O. {reason}",
            severity=ChangeSeverity.MODERATE
        ))
    elif current_settings.mode == CPAPMode.APAP:
        # Adjust max pressure
        changes.append(SettingChange(
            setting_name="pressure_max",
            current_value=current_settings.pressure_max,
            proposed_value=target_pressure,
            reason=ChangeReason.ADJUST_PRESSURE,
            rationale=f"Adjust maximum APAP pressure to {target_pressure} cmH2O. {reason}",
            severity=ChangeSeverity.MODERATE
        ))
    
    proposal = SettingsProposal(
        device_serial=device_serial,
        current_settings=current_settings,
        proposed_changes=changes,
        overall_rationale=reason,
        expected_outcomes=[
            "Improved therapy effectiveness",
            "Better AHI control" if ahi and ahi > 5 else "Maintained therapy quality",
        ],
        patient_ahi=ahi,
    )
    
    proposal.validate_all_changes()
    return proposal


def create_comfort_improvement_proposal(
    device_serial: str,
    current_settings: DeviceSettings,
    enable_epr: bool = True,
    epr_level: int = 2,
    enable_ramp: bool = True,
    ramp_time: int = 20
) -> SettingsProposal:
    """
    Helper function to create a comfort improvement proposal.
    
    Args:
        device_serial: Device serial number
        current_settings: Current device settings
        enable_epr: Whether to enable EPR
        epr_level: EPR level (0-3)
        enable_ramp: Whether to enable ramp
        ramp_time: Ramp time in minutes
    
    Returns:
        SettingsProposal object
    """
    changes = []
    
    if enable_epr and (not current_settings.epr_enabled or current_settings.epr_level != epr_level):
        changes.append(SettingChange(
            setting_name="epr_enabled",
            current_value=current_settings.epr_enabled,
            proposed_value=True,
            reason=ChangeReason.IMPROVE_COMFORT,
            rationale="Enable EPR to reduce pressure during exhalation, improving comfort",
            severity=ChangeSeverity.MINOR
        ))
        
        changes.append(SettingChange(
            setting_name="epr_level",
            current_value=current_settings.epr_level,
            proposed_value=epr_level,
            reason=ChangeReason.IMPROVE_COMFORT,
            rationale=f"Set EPR level to {epr_level} for optimal comfort vs therapy balance",
            severity=ChangeSeverity.MINOR
        ))
    
    if enable_ramp and not current_settings.ramp_enabled:
        changes.append(SettingChange(
            setting_name="ramp_enabled",
            current_value=current_settings.ramp_enabled,
            proposed_value=True,
            reason=ChangeReason.IMPROVE_COMFORT,
            rationale="Enable pressure ramp for easier sleep onset",
            severity=ChangeSeverity.MINOR
        ))
        
        changes.append(SettingChange(
            setting_name="ramp_time",
            current_value=current_settings.ramp_time,
            proposed_value=ramp_time,
            reason=ChangeReason.IMPROVE_COMFORT,
            rationale=f"Set ramp time to {ramp_time} minutes for gradual pressure increase",
            severity=ChangeSeverity.MINOR
        ))
    
    proposal = SettingsProposal(
        device_serial=device_serial,
        current_settings=current_settings,
        proposed_changes=changes,
        overall_rationale="Improve patient comfort to enhance therapy compliance",
        expected_outcomes=[
            "Easier sleep onset",
            "Reduced pressure sensation during exhalation",
            "Improved therapy adherence",
        ],
        comfort_complaints=True,
    )
    
    proposal.validate_all_changes()
    return proposal
