#!/usr/bin/env python3
"""
Example: Extract CPAP data for AI analysis

This script demonstrates how to extract comprehensive CPAP data from SD card files
and format it for consumption by AI systems (LLMs, analysis tools, etc.)

USAGE:
    python extract_for_ai.py

OUTPUT FILES:
    - cpap_data_for_ai.json: Complete structured data in JSON format

WHAT THIS EXTRACTS:
    1. Device Information:
       - Serial number, model, firmware version
    
    2. Session Data (per therapy session):
       - Date, start/end times
       - Duration
       - AHI (Apnea-Hypopnea Index)
       - Pressure statistics (median, 95th percentile)
       - Leak rates
       - Respiratory metrics (rate, tidal volume, minute ventilation)
       - SpO2 (blood oxygen saturation)
       - Device settings used
    
    3. Events:
       - Apneas (obstructive, central)
       - Hypopneas
       - Flow limitations
       - Snoring
       - Mask on/off times
    
    4. Waveform Data (time-series):
       - Pressure readings
       - Flow measurements
       - SpO2 values
       - Note: Can be very large; example shows both full data and summary stats

CUSTOMIZATION:
    - Change sdcard_path in main() to point to your SD card location
    - Comment out full waveform extraction if data is too large (line ~110-115)
    - Adjust which summary fields to include based on your needs
"""

from cpap_py import CPAPReader
import json
from datetime import datetime
from pathlib import Path


def extract_cpap_data_for_ai(sdcard_path: str) -> dict:
    """
    Extract all relevant CPAP data and return as a structured dictionary
    suitable for AI consumption.
    
    Args:
        sdcard_path: Path to SD card root directory
        
    Returns:
        Dictionary containing all device info, sessions, and waveform data
    """
    reader = CPAPReader(sdcard_path)
    
    # Main data structure
    cpap_data = {
        "extraction_date": datetime.now().isoformat(),
        "devices": [],
        "sessions": []
    }
    
    # Extract device information
    devices = reader.get_devices()
    for device in devices:
        device_info = {
            "serial_number": device.serial_number,
            "model_name": device.model_name,
            "model_id": device.model_id,
            "firmware_version": device.firmware_version,
            "settings": {}
        }
        
        # Note: Settings are per-session, not per-device
        # We'll extract settings from sessions instead
        
        cpap_data["devices"].append(device_info)
    
    # Extract session data
    sessions = reader.get_sessions()
    for session in sessions:
        session_data = {
            "date": session.date.isoformat(),
            "start_time": session.start_time.isoformat() if session.start_time else None,
            "end_time": session.end_time.isoformat() if session.end_time else None,
            "device_serial": session.device_serial,
            
            # Summary statistics
            "summary": {
                "duration_hours": session.summary.duration_hours,
                "ahi": session.summary.ahi,
                "ai": session.summary.ai,
                "hi": session.summary.hi,
                "central_apneas": session.summary.central_apneas,
                "obstructive_apneas": session.summary.obstructive_apneas,
                "hypopneas": session.summary.hypopneas,
                "pressure_median": session.summary.pressure_median,
                "pressure_95th": session.summary.pressure_95th,
                "leak_median": session.summary.leak_median,
                "leak_95th": session.summary.leak_95th,
                "respiratory_rate_median": session.summary.respiratory_rate_median,
                "tidal_volume_median": session.summary.tidal_volume_median,
                "minute_ventilation_median": session.summary.minute_ventilation_median,
                "spo2_median": session.summary.spo2_median,
            },
            
            # Device settings for this session
            "settings": {
                "mode": str(session.settings.mode) if session.settings.mode else None,
                "pressure": session.settings.pressure,
                "pressure_min": session.settings.pressure_min,
                "pressure_max": session.settings.pressure_max,
                "ipap": session.settings.ipap,
                "epap": session.settings.epap,
                "epr_enabled": session.settings.epr_enabled,
                "epr_level": session.settings.epr_level,
                "epr_type": session.settings.epr_type,
                "ramp_enabled": session.settings.ramp_enabled,
                "ramp_time": session.settings.ramp_time,
                "ramp_start_pressure": session.settings.ramp_start_pressure,
                "smart_start": session.settings.smart_start,
                "auto_stop": session.settings.auto_stop,
                "mask_type": str(session.settings.mask_type) if session.settings.mask_type else None,
                "tube_type": session.settings.tube_type,
                "humidifier_enabled": session.settings.humidifier_enabled,
                "humidifier_level": session.settings.humidifier_level,
                "climate_control": session.settings.climate_control,
                "temperature_enabled": session.settings.temperature_enabled,
                "temperature": session.settings.temperature,
                "response": session.settings.response,
                "patient_access_enabled": session.settings.patient_access_enabled,
                "antibacterial_filter": session.settings.antibacterial_filter,
            },
            
            # Waveform data availability
            "available_data": {
                "pressure": session.has_pressure_data,
                "flow": session.has_flow_data,
                "spo2": session.has_spo2_data,
                "events": True,  # Always available
            },
            
            # Events summary
            "events": [],
            
            # Waveform data (sample or full)
            "waveforms": {}
        }
        
        # Extract events
        events = session.get_events()
        for event in events:
            event_data = {
                "type": str(event.type),
                "timestamp": event.timestamp.isoformat() if event.timestamp else None,
                "duration_seconds": event.duration,
            }
            # Add any additional event data
            if event.data:
                event_data["data"] = event.data
            session_data["events"].append(event_data)
        
        # Extract waveform data
        # Note: For AI, you might want to sample or summarize waveforms
        # Full waveforms can be very large
        
        if session.has_pressure_data:
            pressure_df = session.get_pressure_data()
            if pressure_df is not None and not pressure_df.empty:
                # Get the first column (pressure values)
                pressure_col = pressure_df.columns[0]
                
                # Only send summary statistics (full waveform is too large for AI)
                session_data["waveforms"]["pressure_stats"] = {
                    "count": len(pressure_df),
                    "mean": float(pressure_df[pressure_col].mean()),
                    "std": float(pressure_df[pressure_col].std()),
                    "min": float(pressure_df[pressure_col].min()),
                    "max": float(pressure_df[pressure_col].max()),
                    "median": float(pressure_df[pressure_col].median()),
                }
        
        if session.has_flow_data:
            flow_df = session.get_flow_data()
            if flow_df is not None and not flow_df.empty:
                flow_col = flow_df.columns[0]
                session_data["waveforms"]["flow_stats"] = {
                    "count": len(flow_df),
                    "mean": float(flow_df[flow_col].mean()),
                    "std": float(flow_df[flow_col].std()),
                    "min": float(flow_df[flow_col].min()),
                    "max": float(flow_df[flow_col].max()),
                }
        
        if session.has_spo2_data:
            spo2_df = session.get_spo2_data()
            if spo2_df is not None and not spo2_df.empty:
                spo2_col = spo2_df.columns[0]
                session_data["waveforms"]["spo2_stats"] = {
                    "count": len(spo2_df),
                    "mean": float(spo2_df[spo2_col].mean()),
                    "std": float(spo2_df[spo2_col].std()),
                    "min": float(spo2_df[spo2_col].min()),
                    "max": float(spo2_df[spo2_col].max()),
                }
        
        cpap_data["sessions"].append(session_data)
    
    return cpap_data


def create_ai_prompt(cpap_data: dict) -> str:
    """
    Create a human-readable prompt for AI analysis.
    
    Args:
        cpap_data: Structured CPAP data dictionary
        
    Returns:
        Formatted text prompt suitable for AI consumption
    """
    lines = ["CPAP Therapy Data Analysis\n" + "="*50 + "\n"]
    
    # Device information
    lines.append("DEVICES:")
    for device in cpap_data["devices"]:
        lines.append(f"  - Serial: {device['serial_number']}")
        lines.append(f"    Model: {device['model_name']}")
        if device.get('firmware_version'):
            lines.append(f"    Firmware: {device['firmware_version']}")
        lines.append("")
    
    # Session summaries
    lines.append(f"\nSESSIONS ({len(cpap_data['sessions'])} total):")
    for session in cpap_data["sessions"]:
        lines.append(f"\n  Session Date: {session['date']}")
        
        summary = session['summary']
        lines.append(f"  Duration: {summary['duration_hours']:.2f} hours")
        
        if summary['ahi'] is not None:
            lines.append(f"  AHI: {summary['ahi']:.1f} events/hour")
        
        if summary['pressure_median'] is not None and summary['pressure_95th'] is not None:
            lines.append(f"  Pressure (median/95th): {summary['pressure_median']:.1f} / {summary['pressure_95th']:.1f} cmH2O")
        
        if summary['leak_median'] is not None and summary['leak_95th'] is not None:
            lines.append(f"  Leak (median/95th): {summary['leak_median']:.1f} / {summary['leak_95th']:.1f} L/min")
        
        if summary['respiratory_rate_median']:
            lines.append(f"  Respiratory Rate: {summary['respiratory_rate_median']:.1f} bpm")
        if summary['minute_ventilation_median']:
            lines.append(f"  Minute Ventilation: {summary['minute_ventilation_median']:.1f} L/min")
        if summary['spo2_median']:
            lines.append(f"  SpO2 (median): {summary['spo2_median']:.1f}%")
        
        # Event counts
        event_types = {}
        for event in session['events']:
            event_type = event['type']
            event_types[event_type] = event_types.get(event_type, 0) + 1
        
        if event_types:
            lines.append("  Events:")
            for event_type, count in sorted(event_types.items()):
                lines.append(f"    - {event_type}: {count}")
            
            # Show total event count
            total_events = sum(event_types.values())
            lines.append(f"  Total Events: {total_events}")
            
            # Show sample events (first 3)
            if len(session['events']) > 0:
                lines.append("  Sample Events:")
                for i, event in enumerate(session['events'][:3], 1):
                    duration = event.get('duration_seconds')
                    duration_str = f" ({duration:.1f}s)" if duration else ""
                    lines.append(f"    {i}. {event['type']} at {event['timestamp']}{duration_str}")
    
    return "\n".join(lines)


def main():
    """Main example execution"""
    # Path to your CPAP SD card data
    sdcard_path = "/workspaces/cpap-py/data"
    
    print("Extracting CPAP data...")
    cpap_data = extract_cpap_data_for_ai(sdcard_path)
    
    # Save as JSON for programmatic AI consumption
    output_json = "cpap_data_for_ai.json"
    with open(output_json, 'w') as f:
        json.dump(cpap_data, f, indent=2, default=str)
    print(f"\n✓ Saved structured data to: {output_json}")
    
    # Display summary
    print(f"\nExtracted data summary:")
    print(f"  - Devices: {len(cpap_data['devices'])}")
    print(f"  - Sessions: {len(cpap_data['sessions'])}")


if __name__ == "__main__":
    main()
