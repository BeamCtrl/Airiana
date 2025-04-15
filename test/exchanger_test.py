#
# pytest -s --mode HIL --tty /dev/serial0
# pytest -s
# pytest
#
import sys, os

sys.path.append("..")
sys.path.append(".")

import airiana_core
from request import Request
import time
from pytest import fixture
from MockRequest import MockRequest


@fixture(scope="session")
def mode(pytestconfig):
    return pytestconfig.getoption("--mode")


@fixture(scope="session")
def tty(pytestconfig):
    return pytestconfig.getoption("--tty")


if not os.path.isdir("RAM/"):
    os.system("mkdir -p RAM/")


def test_exchanger(mode, tty):
    """Test the exchanger logic standalone with mocked comms"""
    HIL_is_savecair = False
    if mode != "HIL":
        req = MockRequest()
    else:
        req = Request()
        req.setup(str(tty), "RTU")
        req.modbusregister(12543, 0)
        if req.response != "no data":
            HIL_is_savecair = True
    dev = airiana_core.Systemair(req)
    # Test that dev init is correct
    assert dev.inlet_ave == 0
    assert dev.exhaust_ave == 0
    assert dev.supply_ave == 0
    assert dev.extract_ave == 0

    # Test non-savecair unit logic
    if (mode == "HIL" and not HIL_is_savecair) or not mode:
        dev.savecair = False
        print("Is savecair:", dev.savecair)
        # Set exchanger off
        dev.cycle_exchanger(0)
        assert req.response == 0
        assert dev.exchanger_mode == 0
        # Set exchanger on
        dev.cycle_exchanger(5)
        assert req.response == 5
        assert dev.exchanger_mode == 5

    if (mode == "HIL" and HIL_is_savecair) or not mode:
        # Test savecair logic
        dev.savecair = True
        print("Is savecair:", dev.savecair)
        # Set exchanger off
        dev.cycle_exchanger(0)
        print(time.ctime(dev.inhibit))
        assert dev.exchanger_mode == 0
        assert req.response == 120
        # Set exchanger on
        dev.cycle_exchanger(5)
        assert dev.exchanger_mode == 5
        assert req.response == 220

        # Test cool_mode recycling
        dev.cool_mode = True
        dev.cycle_exchanger(5)
        assert dev.exchanger_mode == 5
        assert req.response == 300
