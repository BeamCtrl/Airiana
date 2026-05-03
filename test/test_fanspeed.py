import pytest
import sys
import os
import time
import math
from unittest.mock import Mock, MagicMock, patch

sys.path.append("..")
sys.path.append(".")

# Patch global ferr and os.write before importing airiana_core
with patch("builtins.open", create=True):
    with patch("os.open", return_value=999):
        with patch("os.write"):
            import airiana_core


class TestSetFanspeed:
    """Tests for set_fanspeed() method - validates state changes and boundaries."""

    @pytest.fixture
    def mock_device(self):
        """Create a mock Systemair device for testing."""
        device = Mock(spec=airiana_core.Systemair)
        device.savecair = False
        device.fanspeed = 1
        device.status_field = [0, 0, 0, 0]
        device.inhibit = 0
        device.coef_inhibit = 0
        device.req = Mock()
        device.req.write_register = Mock()
        device.update_airflow = Mock()
        
        # Bind real method
        device.set_fanspeed = airiana_core.Systemair.set_fanspeed.__get__(device, airiana_core.Systemair)
        device.get_fanspeed = airiana_core.Systemair.get_fanspeed.__get__(device, airiana_core.Systemair)
        
        return device

    def test_set_fanspeed_valid_speed_0(self, mock_device):
        """Test setting fanspeed to 0 (off)."""
        with patch.object(mock_device, "get_fanspeed", return_value=0):
            with patch.object(mock_device, "update_airflow"):
                with patch("os.write"):
                    mock_device.set_fanspeed(0)

        mock_device.req.write_register.assert_called()
        assert mock_device.fanspeed == 0

    def test_set_fanspeed_valid_speed_1(self, mock_device):
        """Test setting fanspeed to 1."""
        with patch.object(mock_device, "get_fanspeed", return_value=1):
            with patch.object(mock_device, "update_airflow"):
                with patch("os.write"):
                    mock_device.set_fanspeed(1)

        assert mock_device.fanspeed == 1
        mock_device.req.write_register.assert_called()

    def test_set_fanspeed_clamps_high_value(self, mock_device):
        """Test that fanspeed >= 4 clamps to 0."""
        with patch.object(mock_device, "get_fanspeed", return_value=0):
            with patch.object(mock_device, "update_airflow"):
                with patch("os.write"):
                    mock_device.set_fanspeed(4)

        assert mock_device.fanspeed == 0

    def test_set_fanspeed_clamps_negative_value(self, mock_device):
        """Test that negative fanspeed clamps to 0."""
        with patch.object(mock_device, "get_fanspeed", return_value=0):
            with patch.object(mock_device, "update_airflow"):
                with patch("os.write"):
                    mock_device.set_fanspeed(-1)

        assert mock_device.fanspeed == 0

    def test_set_fanspeed_increments_status_on_change(self, mock_device):
        """Test that status_field[0] increments when speed changes."""
        mock_device.fanspeed = 1
        initial_status = mock_device.status_field[0]

        with patch.object(mock_device, "get_fanspeed", return_value=2):
            with patch.object(mock_device, "update_airflow"):
                with patch("os.write"):
                    mock_device.set_fanspeed(2)

        assert mock_device.status_field[0] == initial_status + 1

    def test_set_fanspeed_no_status_increment_when_same(self, mock_device):
        """Test that status_field[0] does NOT increment if speed unchanged."""
        mock_device.fanspeed = 1
        initial_status = mock_device.status_field[0]

        with patch.object(mock_device, "get_fanspeed", return_value=1):
            with patch.object(mock_device, "update_airflow"):
                with patch("os.write"):
                    mock_device.set_fanspeed(1)

        assert mock_device.status_field[0] == initial_status

    def test_set_fanspeed_calls_update_airflow(self, mock_device):
        """Test that set_fanspeed calls update_airflow at end."""
        with patch.object(mock_device, "get_fanspeed", return_value=2):
            with patch.object(mock_device, "update_airflow") as mock_airflow:
                with patch("os.write"):
                    mock_device.set_fanspeed(2)

        mock_airflow.assert_called_once()

    def test_set_fanspeed_sets_inhibit_timer(self, mock_device):
        """Test that set_fanspeed sets inhibit and coef_inhibit timers."""
        before = time.time()

        with patch.object(mock_device, "get_fanspeed", return_value=2):
            with patch.object(mock_device, "update_airflow"):
                with patch("os.write"):
                    mock_device.set_fanspeed(2)

        after = time.time()

        assert before <= mock_device.inhibit <= after
        assert before <= mock_device.coef_inhibit <= after

    def test_set_fanspeed_savecair_false_uses_register_100(self, mock_device):
        """Test that savecair=False writes to register 100."""
        mock_device.savecair = False

        with patch.object(mock_device, "get_fanspeed", return_value=2):
            with patch.object(mock_device, "update_airflow"):
                with patch("os.write"):
                    mock_device.set_fanspeed(2)

        calls = mock_device.req.write_register.call_args_list
        assert len(calls) > 0
        assert calls[0][0][0] == 100

    def test_set_fanspeed_savecair_true_uses_register_1130(self, mock_device):
        """Test that savecair=True writes to register 1130 with offset."""
        mock_device.savecair = True

        with patch.object(mock_device, "get_fanspeed", return_value=2):
            with patch.object(mock_device, "update_airflow"):
                with patch("os.write"):
                    mock_device.set_fanspeed(2)

        calls = mock_device.req.write_register.call_args_list
        assert len(calls) > 0
        assert calls[0][0][0] == 1130
        assert calls[0][0][1] == 3

    def test_set_fanspeed_savecair_true_speed_0_no_offset(self, mock_device):
        """Test that savecair=True at speed 0 does NOT add offset."""
        mock_device.savecair = True

        with patch.object(mock_device, "get_fanspeed", return_value=0):
            with patch.object(mock_device, "update_airflow"):
                with patch("os.write"):
                    mock_device.set_fanspeed(0)

        calls = mock_device.req.write_register.call_args_list
        assert len(calls) > 0
        assert calls[0][0][1] == 0


class TestGetFanspeed:
    """Tests for get_fanspeed() method - validates reading and caching."""

    @pytest.fixture
    def mock_device(self):
        """Create a mock Systemair device for testing."""
        device = Mock(spec=airiana_core.Systemair)
        device.savecair = False
        device.fanspeed = 1
        device.req = Mock()
        device.req.modbusregister = Mock()
        device.req.response = 2
        
        # Bind real method
        device.get_fanspeed = airiana_core.Systemair.get_fanspeed.__get__(device, airiana_core.Systemair)
        
        return device

    def test_get_fanspeed_returns_integer(self, mock_device):
        """Test that get_fanspeed returns an integer."""
        with patch("airiana_core.check_req"):
            result = mock_device.get_fanspeed()

        assert isinstance(result, int)

    def test_get_fanspeed_updates_attribute(self, mock_device):
        """Test that get_fanspeed updates self.fanspeed attribute."""
        mock_device.req.response = 3
        with patch("airiana_core.check_req"):
            mock_device.get_fanspeed()

        assert mock_device.fanspeed == 3

    def test_get_fanspeed_savecair_false_reads_register_100(self, mock_device):
        """Test that savecair=False reads from register 100."""
        mock_device.savecair = False
        mock_device.req.response = 1

        with patch("airiana_core.check_req"):
            mock_device.get_fanspeed()

        mock_device.req.modbusregister.assert_called_with(100, 0)

    def test_get_fanspeed_savecair_true_reads_register_1130(self, mock_device):
        """Test that savecair=True reads from register 1130."""
        mock_device.savecair = True
        mock_device.req.response = 2

        with patch("airiana_core.check_req"):
            mock_device.get_fanspeed()

        calls = mock_device.req.modbusregister.call_args_list
        assert any(call[0][0] == 1130 for call in calls)

    def test_get_fanspeed_returns_value(self, mock_device):
        """Test that get_fanspeed returns self.fanspeed."""
        mock_device.req.response = 2
        with patch("airiana_core.check_req"):
            result = mock_device.get_fanspeed()

        assert result == mock_device.fanspeed


class TestUpdateFanRpm:
    """Tests for update_fan_rpm() method - validates RPM reading and power calculation."""

    @pytest.fixture
    def mock_device(self):
        """Create a mock Systemair device for testing."""
        device = Mock(spec=airiana_core.Systemair)
        device.savecair = False
        device.req = Mock()
        device.req.modbusregisters = Mock()
        device.req.modbusregister = Mock()
        device.req.response = [2000, 2500]
        device.system_name = "VR400"
        device.rotor_active = "No"
        device.electric_power = 0
        device.electric_power_sum = 0
        device.elec_now = time.time()
        device.sf_rpm = 0
        device.ef_rpm = 0
        
        # Bind real method
        device.update_fan_rpm = airiana_core.Systemair.update_fan_rpm.__get__(device, airiana_core.Systemair)
        
        return device

    def test_update_fan_rpm_savecair_false_reads_registers(self, mock_device):
        """Test that savecair=False reads from registers 110-111."""
        mock_device.savecair = False
        mock_device.req.response = [2000, 2500]

        mock_device.update_fan_rpm()

        mock_device.req.modbusregisters.assert_called_with(110, 2)

    def test_update_fan_rpm_updates_rpm_attributes(self, mock_device):
        """Test that sf_rpm and ef_rpm are updated from response."""
        mock_device.savecair = False
        mock_device.req.response = [2000, 2500]

        mock_device.update_fan_rpm()

        assert mock_device.sf_rpm == 2000
        assert mock_device.ef_rpm == 2500

    def test_update_fan_rpm_calculates_vr400_power(self, mock_device):
        """Test VR400 power calculation."""
        mock_device.savecair = False
        mock_device.system_name = "VR400"
        mock_device.rotor_active = "No"
        mock_device.req.response = [1381, 1381]

        mock_device.update_fan_rpm()

        assert mock_device.electric_power > 0
        assert mock_device.electric_power >= 5

    def test_update_fan_rpm_adds_rotor_power_if_active(self, mock_device):
        """Test that 10W is added to power when rotor is active."""
        mock_device.savecair = False
        mock_device.rotor_active = "Yes"
        mock_device.req.response = [1000, 1000]

        mock_device.update_fan_rpm()

        assert mock_device.electric_power >= 15

    def test_update_fan_rpm_adds_controller_power(self, mock_device):
        """Test that controller power (5W) is always added."""
        mock_device.savecair = False
        mock_device.rotor_active = "No"
        mock_device.req.response = [1000, 1000]

        mock_device.electric_power = 0

        mock_device.update_fan_rpm()

        assert mock_device.electric_power >= 5

    def test_update_fan_rpm_integrates_power_over_time(self, mock_device):
        """Test that power consumption is integrated over time."""
        mock_device.savecair = False
        mock_device.req.response = [2000, 2000]
        mock_device.elec_now = time.time() - 1
        mock_device.electric_power = 10
        mock_device.electric_power_sum = 0

        mock_device.update_fan_rpm()

        assert mock_device.electric_power_sum > 0

    def test_update_fan_rpm_handles_zero_division_error(self, mock_device):
        """Test that zero division in power calculation is handled gracefully."""
        mock_device.savecair = False
        mock_device.req.response = [0, 0]

        try:
            mock_device.update_fan_rpm()
            power_set = True
        except ZeroDivisionError:
            power_set = False

        assert power_set
        assert mock_device.electric_power >= 5

    def test_update_fan_rpm_savecair_true_reads_separate_registers(self, mock_device):
        """Test that savecair=True reads SF and EF RPM from separate registers."""
        mock_device.savecair = True
        mock_device.req.response = 2000

        mock_device.update_fan_rpm()

        calls = mock_device.req.modbusregister.call_args_list
        registers = [call[0][0] for call in calls]
        assert 12400 in registers
        assert 12401 in registers


class TestUpdateFanspeed:
    """Tests for update_fanspeed() method - validates simple getter."""

    @pytest.fixture
    def mock_device(self):
        """Create a mock Systemair device for testing."""
        device = Mock(spec=airiana_core.Systemair)
        device.fanspeed = 1
        
        # Bind real method
        device.update_fanspeed = airiana_core.Systemair.update_fanspeed.__get__(device, airiana_core.Systemair)
        
        return device

    def test_update_fanspeed_calls_get_fanspeed(self, mock_device):
        """Test that update_fanspeed calls get_fanspeed()."""
        with patch.object(mock_device, "get_fanspeed", return_value=2) as mock_get:
            mock_device.update_fanspeed()

        mock_get.assert_called_once()

    def test_update_fanspeed_updates_attribute(self, mock_device):
        """Test that update_fanspeed updates self.fanspeed attribute."""
        with patch.object(mock_device, "get_fanspeed", return_value=3):
            mock_device.update_fanspeed()

        assert mock_device.fanspeed == 3

    def test_update_fanspeed_handles_different_speeds(self, mock_device):
        """Test update_fanspeed with different speed values."""
        for speed in [0, 1, 2, 3]:
            with patch.object(mock_device, "get_fanspeed", return_value=speed):
                mock_device.update_fanspeed()
                assert mock_device.fanspeed == speed
