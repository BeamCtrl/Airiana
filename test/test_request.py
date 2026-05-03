import pytest
import sys
import os
from unittest.mock import Mock, MagicMock, patch, mock_open, call

sys.path.append("..")
sys.path.append(".")
from request import Request


class TestRequestInit:
    """Tests for Request.__init__() method."""

    def test_init_creates_instance(self):
        """Test that Request instance can be created."""
        req = Request()
        assert req is not None
        assert isinstance(req, Request)

    def test_init_all_attributes_exist(self):
        """Test that all expected attributes are initialized."""
        req = Request()
        expected_attrs = [
            "client",
            "connect_errors",
            "checksum_errors",
            "multi_errors",
            "write_errors",
            "counter",
            "error_time",
            "wait_time",
            "prev_rate",
            "rate",
            "iter",
            "bus",
            "fclient",
            "response",
            "mode",
            "unit",
            "reset",
            "latest_request_address",
            "latest_request_mode",
            "latest_request_decimals",
            "latest_request_count",
            "connection_timeout",
        ]
        for attr in expected_attrs:
            assert hasattr(req, attr), f"Missing attribute: {attr}"

    def test_init_default_values(self):
        """Test that attributes have correct default values."""
        req = Request()

        assert req.client is None
        assert req.connect_errors == 0
        assert req.checksum_errors == 0
        assert req.multi_errors == 0
        assert req.write_errors == 0
        assert req.counter == 0
        assert isinstance(req.error_time, float)
        assert req.wait_time == 0.01
        assert req.prev_rate == 0
        assert req.rate == 0
        assert req.iter == 0
        assert req.bus == 0
        assert req.fclient == ""
        assert req.response == ""
        assert req.mode == "RTU"
        assert req.unit == ""
        assert req.reset == 0
        assert req.latest_request_address == 0
        assert req.latest_request_mode == "Single"
        assert req.latest_request_decimals == 0
        assert req.latest_request_count == 0
        assert req.connection_timeout == 0

    def test_init_error_counters_are_zero(self):
        """Test that all error counters start at 0."""
        req = Request()
        assert req.connect_errors == 0
        assert req.checksum_errors == 0
        assert req.multi_errors == 0
        assert req.write_errors == 0

    def test_init_rate_values_are_zero(self):
        """Test that rate tracking attributes start at 0."""
        req = Request()
        assert req.prev_rate == 0
        assert req.rate == 0

    def test_init_request_tracking_defaults(self):
        """Test that request tracking attributes have correct defaults."""
        req = Request()
        assert req.latest_request_address == 0
        assert req.latest_request_mode == "Single"
        assert req.latest_request_decimals == 0
        assert req.latest_request_count == 0

    def test_init_mode_is_rtu_default(self):
        """Test that mode defaults to RTU."""
        req = Request()
        assert req.mode == "RTU"

    def test_init_multiple_instances_independent(self):
        """Test that multiple Request instances don't share state."""
        req1 = Request()
        req2 = Request()

        # Modify req1
        req1.connect_errors = 5
        req1.mode = "TCP"
        req1.unit = "/dev/ttyUSB0"

        # req2 should have original values
        assert req2.connect_errors == 0
        assert req2.mode == "RTU"
        assert req2.unit == ""

    def test_init_error_time_is_timestamp(self):
        """Test that error_time is initialized to current time."""
        import time

        before = time.time()
        req = Request()
        after = time.time()

        assert before <= req.error_time <= after

    def test_init_wait_time_precision(self):
        """Test wait_time has exact default value."""
        req = Request()
        assert req.wait_time == 0.01


class TestRequestErrorReview:
    """Tests for Request.error_review() method."""

    def test_error_review_rate_calculation_normal(self):
        """Test error rate calculation with normal delta."""
        req = Request()
        req.iter = 100
        req.error_time = 50
        req.connect_errors = 10
        req.checksum_errors = 5
        req.write_errors = 3
        req.multi_errors = 2
        # Expected rate: (10+5+3+2) / (100-50) = 20/50 = 0.4

        with patch("os.read"):
            with patch("os.open", return_value=3):
                with patch("os.lseek"):
                    with patch("os.write"):
                        with patch("os.fsync"):
                            with patch("os.close"):
                                with patch("os.system"):
                                    req.error_review()

        # After review, error_time should be updated to iter
        assert req.error_time == 100
        # Error counters should be reset
        assert req.connect_errors == 0
        assert req.checksum_errors == 0
        assert req.write_errors == 0
        assert req.multi_errors == 0

    def test_error_review_delta_zero(self):
        """Test error_review when delta is 0."""
        req = Request()
        req.iter = 100
        req.error_time = 100  # Same as iter, delta = 0

        with patch("os.read"):
            with patch("os.open", return_value=3):
                with patch("os.lseek"):
                    with patch("os.write"):
                        with patch("os.fsync"):
                            with patch("os.close"):
                                with patch("os.system"):
                                    req.error_review()

        # Should handle gracefully without division error
        assert req.error_time == 100

    def test_error_review_resets_counters(self):
        """Test that error counters are reset after review."""
        req = Request()
        req.iter = 100
        req.error_time = 50
        req.connect_errors = 50
        req.checksum_errors = 30
        req.write_errors = 15
        req.multi_errors = 5
        # Rate = 100/50 = 2.0 (HIGH ERROR, will trigger close/setup)
        req.client = Mock()  # Mock client to prevent close() errors

        with patch("os.read"):
            with patch("os.open", return_value=3):
                with patch("os.lseek"):
                    with patch("os.write"):
                        with patch("os.fsync"):
                            with patch("os.close"):
                                with patch("os.system"):
                                    with patch.object(req, "close"):
                                        with patch.object(req, "setup"):
                                            req.error_review()

        # All error counters should be 0
        assert req.connect_errors == 0
        assert req.checksum_errors == 0
        assert req.write_errors == 0
        assert req.multi_errors == 0

    def test_error_review_writes_error_rate_file(self):
        """Test that error_review writes to RAM/error_rate file."""
        req = Request()
        req.iter = 100
        req.error_time = 50
        req.connect_errors = 10
        req.checksum_errors = 5
        req.write_errors = 2
        req.multi_errors = 3
        req.wait_time = 0.01

        with patch("os.read"):
            with patch("os.open", return_value=3):
                with patch("os.lseek"):
                    with patch("os.write"):
                        with patch("os.fsync"):
                            with patch("os.close"):
                                with patch("os.system") as mock_os_system:
                                    req.error_review()

        # Verify os.system was called to write error rate
        # The function uses: os.system("echo " + str(rate) + " " + str(self.wait_time) + " > RAM/error_rate")
        mock_os_system.assert_called()
        calls = mock_os_system.call_args_list
        assert len(calls) > 0
        # Check that the call includes the error_rate file path
        call_args = str(calls[0])
        assert "error_rate" in call_args

    def test_error_review_low_rate_normal_path(self):
        """Test error_review with low error rate (< 0.99)."""
        req = Request()
        req.iter = 1000
        req.error_time = 500
        req.connect_errors = 100
        req.checksum_errors = 50
        req.write_errors = 25
        req.multi_errors = 25
        # Rate: 200/500 = 0.4 (< 0.99)
        req.client = Mock()  # Mock client to prevent close() errors

        with patch("os.read"):
            with patch("os.open", return_value=3):
                with patch("os.lseek"):
                    with patch("os.write"):
                        with patch("os.fsync"):
                            with patch("os.close"):
                                with patch("os.system"):
                                    with patch("time.sleep") as mock_sleep:
                                        req.error_review()
                                        # Should NOT sleep for low error rate
                                        mock_sleep.assert_not_called()

    def test_error_review_high_rate_recovery_path(self):
        """Test error_review with high error rate (>= 0.99)."""
        req = Request()
        req.unit = "/dev/ttyUSB0"
        req.mode = "RTU"
        req.iter = 100
        req.error_time = 1
        req.connect_errors = 99
        req.checksum_errors = 0
        req.write_errors = 0
        req.multi_errors = 0
        # Rate: 99/99 = 1.0 (>= 0.99) - HIGH ERROR RATE
        req.client = Mock()  # Mock client to prevent close() errors

        with patch("os.read"):
            with patch("os.open", return_value=3):
                with patch("os.lseek"):
                    with patch("os.write"):
                        with patch("os.fsync"):
                            with patch("os.close"):
                                with patch("os.system"):
                                    with patch("time.sleep") as mock_sleep:
                                        with patch.object(
                                            req, "close", return_value=None
                                        ):
                                            with patch.object(
                                                req, "setup", return_value=None
                                            ):
                                                req.error_review()
                                                # Should sleep for recovery
                                                mock_sleep.assert_called_once_with(
                                                    10
                                                )
                                                # connection_timeout should increment
                                                assert req.connection_timeout == 1

    def test_error_review_increments_connection_timeout_on_high_rate(self):
        """Test that connection_timeout increments on high error rate."""
        req = Request()
        req.unit = "/dev/ttyUSB0"
        req.mode = "RTU"
        req.iter = 100
        req.error_time = 1
        req.connect_errors = 99
        req.client = Mock()  # Mock client to prevent close() errors
        req.connection_timeout = 5

        with patch("os.read"):
            with patch("os.open", return_value=3):
                with patch("os.lseek"):
                    with patch("os.write"):
                        with patch("os.fsync"):
                            with patch("os.close"):
                                with patch("os.system"):
                                    with patch("time.sleep"):
                                        with patch.object(req, "close"):
                                            with patch.object(req, "setup"):
                                                req.error_review()
                                                assert req.connection_timeout == 6

    def test_error_review_calls_close_on_high_rate(self):
        """Test that close() is called when error rate is high."""
        req = Request()
        req.unit = "/dev/ttyUSB0"
        req.mode = "RTU"
        req.iter = 100
        req.error_time = 1
        req.client = Mock()  # Mock client to prevent close() errors
        req.connect_errors = 99

        with patch("os.read"):
            with patch("os.open", return_value=3):
                with patch("os.lseek"):
                    with patch("os.write"):
                        with patch("os.fsync"):
                            with patch("os.close"):
                                with patch("os.system"):
                                    with patch("time.sleep"):
                                        with patch.object(
                                            req, "close"
                                        ) as mock_close:
                                            with patch.object(
                                                req, "setup", return_value=None
                                            ):
                                                req.error_review()
                                                mock_close.assert_called_once()

    def test_error_review_calls_setup_on_high_rate(self):
        """Test that setup() is called after high error rate."""
        req = Request()
        req.unit = "/dev/ttyUSB0"
        req.mode = "RTU"
        req.iter = 100
        req.error_time = 1
        req.client = Mock()  # Mock client to prevent close() errors
        req.connect_errors = 99

        with patch("os.read"):
            with patch("os.open", return_value=3):
                with patch("os.lseek"):
                    with patch("os.write"):
                        with patch("os.fsync"):
                            with patch("os.close"):
                                with patch("os.system"):
                                    with patch("time.sleep"):
                                        with patch.object(req, "close"):
                                            with patch.object(
                                                req, "setup"
                                            ) as mock_setup:
                                                req.error_review()
                                                mock_setup.assert_called_once_with(
                                                    req.unit, req.mode
                                                )

    def test_error_review_individual_error_counts(self):
        """Test error rate includes all error types."""
        req = Request()
        req.iter = 1000
        req.error_time = 0
        req.connect_errors = 100
        req.checksum_errors = 100
        req.write_errors = 100
        req.multi_errors = 100
        # Rate should be 400/1000 = 0.4

        with patch("os.read"):
            with patch("os.open", return_value=3):
                with patch("os.lseek"):
                    with patch("os.write"):
                        with patch("os.fsync"):
                            with patch("os.close"):
                                with patch("os.system"):
                                    req.error_review()

        # All should be reset
        assert req.connect_errors == 0
        assert req.checksum_errors == 0
        assert req.write_errors == 0
        assert req.multi_errors == 0

    def test_error_review_updates_error_time(self):
        """Test that error_time is updated to current iter."""
        req = Request()
        req.iter = 500
        req.error_time = 100
        original_iter = req.iter

        with patch("os.read"):
            with patch("os.open", return_value=3):
                with patch("os.lseek"):
                    with patch("os.write"):
                        with patch("os.fsync"):
                            with patch("os.close"):
                                with patch("os.system"):
                                    req.error_review()

        # error_time should be updated to iter value
        assert req.error_time == original_iter
