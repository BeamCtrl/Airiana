import MockRequest
import sys
import os
sys.path.append("..")
sys.path.append(".")
import airiana_core
os.dup2(sys.stdout.fileno(), airiana_core.ferr)  # Redirect log to screen


def print_locals(dev):
    print("\nprev static:", dev.prev_static_temp)
    print("kinetic compensation:", dev.kinetic_compensation)
    print("inlet_ave:", dev.inlet_ave)
    print("extract_ave:", dev.extract_ave)
    print("humidity :", dev.humidity)
    print("local humidity:", dev.local_humidity)
    print("humidity diff (Pa):", dev.humidity_diff)


def test_target_set():
    req = MockRequest.MockRequest()
    dev = airiana_core.Systemair(req)
    dev.extract_ave = 23
    dev.humidity = 35
    dev.inlet_ave = 10
    dev.get_local()
    print_locals(dev)
    assert dev.prev_static_temp != 8  # Check for non init value
    dev.inlet_ave = -1
    dev.get_local()
    assert dev.prev_static_temp <= -1

