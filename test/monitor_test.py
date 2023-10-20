import MockRequest
import sys
import os
sys.path.append("..")
sys.path.append(".")
import airiana_core
os.dup2(sys.stdout.fileno(), airiana_core.ferr)  # Redirect log to screen

def test_target_set():
    req = MockRequest.MockRequest()
    dev = airiana_core.Systemair(req)
    dev.savecair = False
    monitoring = True

    # If inlet average is below 13, target temp should increase
    dev.inlet_ave = 20
    dev.target_temperature()
    prev = dev.target
    dev.inlet_ave = 12
    dev.target_temperature()
    assert dev.target > prev

    # turn on cooling and retest for lower target
    dev.cool_mode = True
    prev = dev.target
    dev.target_temperature()
    assert dev.target < prev


def test_exchanger():
    req = MockRequest.MockRequest()
    dev = airiana_core.Systemair(req)
    dev.savecair = True
    monitoring = True
    # Test for exchanger change to 0 when inlet is above 10C
    # and the extraction temp is higher than target.
    dev.cool_mode = False
    dev.shower = False
    dev.modetoken = 0
    print("Turn on exchanger")
    dev.cycle_exchanger(5)  # Turn on exchanger
    assert dev.exchanger_mode == 5
    dev.inlet_ave = 10.1
    dev.extract_ave = dev.target + 0.1
    print("Auto exchanger turn off", dev.extract_ave)
    dev.exchanger_control()
    assert dev.exchanger_mode == 0

    # Test exchanger set to 0 when supply temperature is above target
    dev.cycle_exchanger(5)
    dev.modetoken = 0
    assert dev.exchanger_mode == 5
    dev.supply_ave = dev.target + 0.1
    dev.exchanger_control()
    assert dev.exchanger_mode == 0

    dev.extract_ave = dev.target - 1.1
    dev.modetoken = 0
    dev.exchanger_control()
    assert dev.exchanger_mode == 5

    dev.supply_ave = 10 - 1
    dev.extract_ave = dev.target - 1
    dev.cycle_exchanger(0)
    dev.modetoken = 0
    dev.exchanger_control()
    assert dev.exchanger_mode == 5

    dev.cycle_exchanger(0)
    dev.inlet_ave = 10 - 1
    dev.set_fanspeed(1)
    dev.forecast = [10, 0, 100]
    dev.modetoken = 0
    dev.exchanger_control()
    assert dev.exchanger_mode == 5
def test_cooling():
    req = MockRequest.MockRequest()
    dev = airiana_core.Systemair(req)
    dev.savecair = True
    monitoring = True
    dev.cycle_exchanger(5)
    dev.extract_ave = 25
    dev.inlet_ave = 20
    dev.supply_ave = 22
    dev.shower = False
    dev.ac_active = False
    dev.inhibit = 0
    dev.cool_mode = False
    dev.integral_forcast = 0 + 1
    dev.forecast = [dev.cooling_limit + 1, 0, 0]
    dev.tomorrows_low[0] = dev.house_heat_limit + 1
    dev.set_fanspeed(1)

    # Start cooling
    dev.inhibit = 0  # Wait ten minutes
    dev.check_cooling()
    assert dev.exchanger_mode == 0
    assert dev.cool_mode
    assert dev.sf == dev.ef
    assert dev.fanspeed == 3

    # Cooling completed
    dev.extract_ave = 20  # Cooling completed
    dev.inhibit = 0  # Wait ten minutes
    dev.check_cooling()
    assert dev.cool_mode
    assert dev.fanspeed == 1

    # Cooling Returns
    dev.extract_ave = 21 + 0.1
    dev.inhibit = 0  # Wait ten minutes
    dev.check_cooling()
    assert dev.fanspeed == 3

    # Cooling Reduced
    dev.inhibit = 0  # Wait ten minutes
    dev.supply_ave = 12 - 0.1
    dev.extract_ave = 22 - 0.1
    dev.check_cooling()
    assert dev.fanspeed == 2

    # Cooling no longer Reduced
    dev.inhibit = 0  # Wait ten minutes
    dev.supply_ave = 13 + 0.1
    dev.check_cooling()
    assert dev.fanspeed == 3

    # Inlet temperature is too high
    dev.inhibit = 0  # Wait ten minutes
    dev.inlet_ave = dev.extract_ave + 1
    dev.check_cooling()
    assert dev.fanspeed == 1

def test_fan_control():
    req = MockRequest.MockRequest()
    dev = airiana_core.Systemair(req)
    dev.savecair = False
    monitoring = True
    # Dynamic fanspeed control
    dev.dynamic_fan_control()


def test_fan_control():
    req = MockRequest.MockRequest()
    dev = airiana_core.Systemair(req)
    dev.savecair = False
    monitoring = True

    # Dynamic pressure control
    dev.dynamic_pressure_control()