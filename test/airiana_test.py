import sys, os
sys.path.append("..")
sys.path.append(".")
#from airiana_core import Systemair
import airiana_core
from request import Request
import time

os.system("mkdiir -p RAM/")

class MockRequest():
    def __init__(self):
        self.response = ""
        self.data = {}

    def write_register(self, address, value):
        print("Writing to", address, "the value", value)
        self.data[address] = value
        self.response = value
        return True

    def modbusregister(self, address, decimals):
        self.response =  1 * (decimals+1)
        try:
            self.response = self.data[address]
            print("Reading the address", address, "which has", self.response, "and decimals at", decimals)
            return self.data[address]
        except:
            print("No data found using:", self.response)
            return self.response

    def modbusregisters(self, start_address, count, signed):
        return True

    def setup(self, device, mode):
        pass


def test_exchanger():
    """Test the exchanger logic standalone with mocked comms"""
    req = MockRequest()
    dev = airiana_core.Systemair(req)
    dev.savecair = False
    print("Is dev.savecair:", dev.savecair)
    ferr = os.open("RAM/test_log",os.O_CREAT)
    # Test that dev init is correct
    assert dev.inlet_ave == 0
    assert dev.exhaust_ave == 0
    assert dev.supply_ave == 0
    assert dev.extract_ave == 0

    # Test non-savecair unit logic
    dev.savecair = False
    print("Is dev.savecair:", dev.savecair)
    # Set exchanger off
    dev.cycle_exchanger(0)
    assert req.response == 0
    assert dev.exchanger_mode == 0
    # Set exchanger on
    dev.cycle_exchanger(5)
    assert req.response == 5
    assert dev.exchanger_mode == 5

    # Test savecair logic
    dev.savecair = True
    print("Is dev.savecair:", dev.savecair)
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


