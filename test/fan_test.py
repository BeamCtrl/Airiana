import MockRequest
import sys
sys.path.append("..")
sys.path.append(".")
import airiana_core
def test_fanspeed_sets():
    """Set fanspeed to 0, 1, 2, 3 valid sets, invalid 4<  or <0"""
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
        dev.savecair = True # do another run with savecair set