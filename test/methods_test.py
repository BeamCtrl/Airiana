import MockRequest
import sys
sys.path.append("..")
sys.path.append(".")
import airiana_core


def test_methods():
    req = MockRequest.MockRequest()
    dev = airiana_core.Systemair(req)
    dev.savecair = False
    monitoring = True
    for i in range(2):
        dev.get_password()
        dev.system_name = "TestSystem"
        dev.system_setup()
        dev.get_heater()
        dev.set_heater(True)
        dev.set_system_name()
        dev.get_coef_mode()
        dev.coef_debug()
        dev.get_RH()
        dev.get_filter_status()
        dev.get_temp_status()
        dev.get_fanspeed()
        dev.update_temps()
        dev.get_tcomp(23, 10)
        dev.set_fanspeed(1)
        dev.update_fan_rpm()
        dev.update_fanspeed()
        dev.update_airflow()
        dev.update_airdata_instance()
        dev.update_xchanger()
        dev.check_ac_mode()
        dev.calc_exhaust()
        dev.get_rotor_state()
        dev.moisture_calcs()
        dev.derivatives()
        dev.shower_detect()
        sys.argv = ["debug", "humidity", "keep-log", "temperatur.nu", "home-Ass"]
        dev.print_xchanger()
        dev.cycle_exchanger(1)
        dev.check_flags()
        dev.monitor()
        dev.get_forecast()
        dev.set_differential(10)
        dev.check_flow_offset()
        dev.get_local()
        dev.print_json()
        dev.check_coef()
        dev.reset_fanspeed(3)
        dev.savecair = True