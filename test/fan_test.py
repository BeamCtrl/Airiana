import threading
import time

import MockRequest
import sys

sys.path.append("..")
sys.path.append(".")
import airiana_core


def test_fanspeed_sets():
    """Set fanspeed to 0, 1, 2, 3 valid sets, invalid 4<  or <0
    Do this for both sets as savecair and not savecair"""
    req = MockRequest.MockRequest()
    dev = airiana_core.Systemair(req)
    dev.savecair = False
    for i in range(2):
        dev.set_fanspeed(1)
        assert dev.get_fanspeed() == 1

        dev.set_fanspeed(2)
        assert dev.get_fanspeed() == 2

        dev.set_fanspeed(3)
        assert dev.get_fanspeed() == 3

        dev.set_fanspeed(4)
        assert dev.get_fanspeed() == 0

        dev.set_fanspeed(0)
        assert dev.get_fanspeed() == 0

        dev.set_fanspeed(-1)
        assert dev.get_fanspeed() == 0

        dev.set_fanspeed(5)
        assert dev.get_fanspeed() == 0
        dev.savecair = True  # do another run with savecair set


def test_forced_fans():
    """Test the forced ventilation 2hrs timer"""
    req = MockRequest.MockRequest()
    dev = airiana_core.Systemair(req)

    assert dev.monitoring is True
    airiana_core.forced_ventilation(dev)
    time.sleep(1)
    assert dev.timer < time.time() + 1
    assert dev.monitoring is False

    ok = False
    for thread in threading.enumerate():
        if thread.name == "Timer":
            ok = True
    assert ok is True

    ok = False
    for thread in threading.enumerate():
        if thread.name == "MonitorTimer":
            ok = True
    assert ok is True

    airiana_core.forced_ventilation(dev)
    time.sleep(0.5)
    assert dev.monitoring is True
    for thread in threading.enumerate():
        if (
            thread.name == "Timer" or thread.name == "MonitorTimer"
        ) and thread.is_alive():
            ok = False
            print(
                "Found a thread that should not be alive.",
                thread,
                threading.enumerate(),
            )
    assert ok is True


def test_fireplace_mode():
    """Test the forced ventilation 2hrs timer"""
    req = MockRequest.MockRequest()
    dev = airiana_core.Systemair(req)
    dev.inlet_ave = 20.0
    dev.indoor_dewpoint = 5.0
    dev.extract_ave = 21.0
    dev.set_fanspeed(1)
    assert dev.fanspeed == 1
    airiana_core.fireplace_mode(dev)
    time.sleep(1)
    assert dev.inhibit != 0
    assert dev.pressure_diff == -10
    ok = False
    for thread in threading.enumerate():
        if thread.name == "fire":
            ok = True
    assert ok is True
    assert dev.fanspeed == 3

    airiana_core.fireplace_mode(dev)
    dev.inhibit = 0
    dev.forecast = [1, 2, 3]
    dev.dynamic_fan_control()
    dev.inhibit = 0
    dev.dynamic_pressure_control()
    time.sleep(1.5)
    assert dev.pressure_diff >= 0
    ok = True
    for thread in threading.enumerate():
        if thread.name == "fire" and thread.is_alive():
            ok = False
    assert ok is True
    assert dev.fanspeed != 3
