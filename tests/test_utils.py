"""
Tests for utils.py module
"""

import pytest
from datetime import datetime, date, timedelta
from cpap_py.utils import (
    split_sessions_by_noon,
    minutes_since_noon,
    format_duration,
    calculate_ahi
)


class TestSplitSessionsByNoon:
    """Tests for split_sessions_by_noon function"""
    
    def test_empty_list(self):
        """Test with empty timestamp list"""
        result = split_sessions_by_noon([])
        assert result == []
    
    def test_single_timestamp_morning(self):
        """Test with single timestamp before noon"""
        # 10 AM on Dec 15, 2024
        dt = datetime(2024, 12, 15, 10, 0, 0)
        ts = int(dt.timestamp())
        
        result = split_sessions_by_noon([ts])
        assert len(result) == 1
        # Before noon belongs to previous day
        assert result[0][0] == date(2024, 12, 14)
        assert result[0][1] == [ts]
    
    def test_single_timestamp_afternoon(self):
        """Test with single timestamp after noon"""
        # 2 PM on Dec 15, 2024
        dt = datetime(2024, 12, 15, 14, 0, 0)
        ts = int(dt.timestamp())
        
        result = split_sessions_by_noon([ts])
        assert len(result) == 1
        # After noon belongs to current day
        assert result[0][0] == date(2024, 12, 15)
        assert result[0][1] == [ts]
    
    def test_multiple_timestamps_same_session(self):
        """Test multiple timestamps in same session"""
        # All after noon on same day
        dt1 = datetime(2024, 12, 15, 13, 0, 0)
        dt2 = datetime(2024, 12, 15, 14, 0, 0)
        dt3 = datetime(2024, 12, 15, 15, 0, 0)
        timestamps = [int(dt.timestamp()) for dt in [dt1, dt2, dt3]]
        
        result = split_sessions_by_noon(timestamps)
        assert len(result) == 1
        assert result[0][0] == date(2024, 12, 15)
        assert len(result[0][1]) == 3
    
    def test_timestamps_spanning_midnight(self):
        """Test timestamps spanning midnight but same session"""
        # From 11 PM to 2 AM next day (all one session)
        dt1 = datetime(2024, 12, 15, 23, 0, 0)
        dt2 = datetime(2024, 12, 16, 1, 0, 0)
        dt3 = datetime(2024, 12, 16, 2, 0, 0)
        timestamps = [int(dt.timestamp()) for dt in [dt1, dt2, dt3]]
        
        result = split_sessions_by_noon(timestamps)
        # dt1 belongs to Dec 15 session
        # dt2 and dt3 belong to Dec 15 session (before noon on Dec 16)
        assert len(result) == 1
        assert result[0][0] == date(2024, 12, 15)
    
    def test_timestamps_multiple_sessions(self):
        """Test timestamps across multiple sessions"""
        # Session 1: Dec 15 afternoon
        dt1 = datetime(2024, 12, 15, 14, 0, 0)
        # Session 2: Dec 16 afternoon
        dt2 = datetime(2024, 12, 16, 14, 0, 0)
        # Session 3: Dec 17 afternoon
        dt3 = datetime(2024, 12, 17, 14, 0, 0)
        timestamps = [int(dt.timestamp()) for dt in [dt1, dt2, dt3]]
        
        result = split_sessions_by_noon(timestamps)
        assert len(result) == 3
        assert result[0][0] == date(2024, 12, 15)
        assert result[1][0] == date(2024, 12, 16)
        assert result[2][0] == date(2024, 12, 17)
    
    def test_zero_timestamps_ignored(self):
        """Test that zero timestamps are ignored"""
        dt = datetime(2024, 12, 15, 14, 0, 0)
        ts = int(dt.timestamp())
        timestamps = [0, ts, 0]
        
        result = split_sessions_by_noon(timestamps)
        assert len(result) == 1
        assert result[0][1] == [ts]
    
    def test_unsorted_timestamps(self):
        """Test that timestamps are sorted automatically"""
        dt1 = datetime(2024, 12, 15, 15, 0, 0)
        dt2 = datetime(2024, 12, 15, 13, 0, 0)
        dt3 = datetime(2024, 12, 15, 14, 0, 0)
        timestamps = [int(dt.timestamp()) for dt in [dt1, dt2, dt3]]
        
        result = split_sessions_by_noon(timestamps)
        assert len(result) == 1
        # Should be sorted
        assert result[0][1] == sorted(timestamps)


class TestMinutesSinceNoon:
    """Tests for minutes_since_noon function"""
    
    def test_exactly_noon(self):
        """Test exactly at noon"""
        dt = datetime(2024, 12, 15, 12, 0, 0)
        assert minutes_since_noon(dt) == 0
    
    def test_after_noon(self):
        """Test time after noon"""
        dt = datetime(2024, 12, 15, 13, 30, 0)  # 1:30 PM
        assert minutes_since_noon(dt) == 90
    
    def test_before_noon(self):
        """Test time before noon"""
        dt = datetime(2024, 12, 15, 11, 30, 0)  # 11:30 AM
        assert minutes_since_noon(dt) == -30
    
    def test_midnight(self):
        """Test at midnight"""
        dt = datetime(2024, 12, 15, 0, 0, 0)
        assert minutes_since_noon(dt) == -720  # -12 hours
    
    def test_one_day_after_noon(self):
        """Test 24 hours after noon"""
        dt = datetime(2024, 12, 16, 12, 0, 0)
        # This is noon on next day, so 24 hours from previous day's noon
        assert minutes_since_noon(dt) == 0


class TestFormatDuration:
    """Tests for format_duration function"""
    
    def test_zero_seconds(self):
        """Test zero duration"""
        assert format_duration(0) == "00:00:00"
    
    def test_one_minute(self):
        """Test one minute"""
        assert format_duration(60) == "00:01:00"
    
    def test_one_hour(self):
        """Test one hour"""
        assert format_duration(3600) == "01:00:00"
    
    def test_full_time(self):
        """Test hours, minutes, and seconds"""
        # 2 hours, 30 minutes, 45 seconds
        assert format_duration(9045) == "02:30:45"
    
    def test_large_duration(self):
        """Test large duration"""
        # 25 hours, 15 minutes, 30 seconds
        assert format_duration(90930) == "25:15:30"
    
    def test_fractional_seconds(self):
        """Test fractional seconds (should truncate)"""
        # 1 hour, 30 minutes, 45.7 seconds
        assert format_duration(5445.7) == "01:30:45"


class TestCalculateAHI:
    """Tests for calculate_ahi function"""
    
    def test_zero_events(self):
        """Test with no events"""
        assert calculate_ahi(0, 0, 1.0) == 0.0
    
    def test_one_hour(self):
        """Test calculation for one hour"""
        # 5 apneas, 3 hypopneas in 1 hour
        ahi = calculate_ahi(5, 3, 1.0)
        assert ahi == 8.0
    
    def test_multiple_hours(self):
        """Test calculation for multiple hours"""
        # 10 apneas, 6 hypopneas in 2 hours
        # AHI = (10 + 6) / 2 = 8.0
        ahi = calculate_ahi(10, 6, 2.0)
        assert ahi == 8.0
    
    def test_fractional_hours(self):
        """Test with fractional hours"""
        # 15 events in 1.5 hours
        ahi = calculate_ahi(9, 6, 1.5)
        assert ahi == 10.0
    
    def test_zero_hours(self):
        """Test with zero hours (should return 0)"""
        ahi = calculate_ahi(5, 3, 0.0)
        assert ahi == 0.0


class TestAdditionalUtilityFunctions:
    """Tests for additional utility functions"""
    
    def test_therapy_mode_name(self):
        """Test therapy mode name function"""
        from cpap_py.utils import therapy_mode_name
        from cpap_py.str_parser import STRParser
        
        assert therapy_mode_name(STRParser.MODE_CPAP) == "CPAP"
        assert therapy_mode_name(STRParser.MODE_APAP) == "APAP"
        assert therapy_mode_name(STRParser.MODE_UNKNOWN) == "Unknown"
    
    def test_downsample_signal_factor_one(self):
        """Test downsampling with factor 1 (no change)"""
        from cpap_py.utils import downsample_signal
        
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = downsample_signal(data, 1)
        assert result == data
    
    def test_downsample_signal_factor_two(self):
        """Test downsampling with factor 2"""
        from cpap_py.utils import downsample_signal
        
        data = [1.0, 3.0, 5.0, 7.0]
        result = downsample_signal(data, 2)
        assert result == [2.0, 6.0]  # Averages: (1+3)/2, (5+7)/2
    
    def test_downsample_signal_uneven(self):
        """Test downsampling with uneven data length"""
        from cpap_py.utils import downsample_signal
        
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = downsample_signal(data, 2)
        assert result == [1.5, 3.5, 5.0]  # Averages: (1+2)/2, (3+4)/2, 5/1
    
    def test_calculate_percentile_50(self):
        """Test calculating 50th percentile (median)"""
        from cpap_py.utils import calculate_percentile
        
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = calculate_percentile(data, 50)
        assert result == 3.0
    
    def test_calculate_percentile_empty(self):
        """Test percentile of empty list"""
        from cpap_py.utils import calculate_percentile
        
        result = calculate_percentile([], 50)
        assert result == 0.0
    
    def test_calculate_percentile_95(self):
        """Test calculating 95th percentile"""
        from cpap_py.utils import calculate_percentile
        
        data = list(range(1, 101))  # 1 to 100
        result = calculate_percentile(data, 95)
        assert 94.0 <= result <= 96.0  # Should be around 95
