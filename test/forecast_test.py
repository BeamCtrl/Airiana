import os.path

import MockRequest
import sys

sys.path.append("..")
sys.path.append(".")
import airiana_core


def test_forcast():
    req = MockRequest.MockRequest()
    req.write_register(500, 4)
    dev = airiana_core.Systemair(req)
    assert dev.system_name == "VTC300"
    dev.get_forecast()
    dev.get_local()
    assert os.path.isfile("RAM/forecast.json")
    assert dev.forecast[0] != -1
    assert dev.forecast[1] != -1
    assert dev.forecast[2] != -1
    print(f"Forecast is {dev.forecast}")
    assert dev.integral_forcast != 0
    assert dev.airdata_inst.press != 1013.25
    assert dev.tomorrows_low != 8.00
