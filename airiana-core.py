#!/usr/bin/env python3
# -*- coding: utf-8 -*-
############################
vers = "13.03"
import airdata  # noqa
import numpy  # noqa
import select  # noqa
import threading  # noqa
import os  # noqa
import traceback  # noqa
import time  # noqa
import sys  # noqa
import signal  # noqa
import math  # noqa
import pathlib  # noqa
import pickle  # noqa
import pprint  # noqa
import socket  # noqa
import syslog  # noqa
import yaml  # noqa
from pprint import pprint  # noqa
from request import Request  # noqa

numpy.seterr("ignore")
numpy.set_printoptions(legacy="1.25")
#############################

Running = True
savecair = False
mode = "RTU"
holdoff_t = time.time() - 3000  # now - 50 minutes
config_file = "public/config.yaml"
config = ""
if "TCP" in sys.argv:
    mode = "TCP"


class ControlledExit(Exception):
    """
    Exit exception
    """

    pass


def write_log(message):
    os.write(
        ferr,
        bytes(
            message + "\t" + str(time.ctime()) + "\n",
            encoding="utf8",
        ),
    )


# Register cleanup
def exit_callback(self, return_code):
    global Running
    Running = False
    print("Graceful shutdown\nexiting on signal", self, return_code)
    sys.stdout.flush()
    now = device.iter
    shutdown = time.time()
    os.system("cp ./RAM/data.log ./data.save")
    if threading.enumerate()[-1].name == "Timer":
        threading.enumerate()[
            -1
        ].cancel()  # noqa this is a threading.Timer, is has cancel()
    cmd_socket.close()
    os.write(
        ferr,
        bytes("Exiting in a safe way\t" + str(time.ctime()) + "\n", encoding="utf8"),
    )
    # Sleep until one iteration has passed, or we've been in shutdown for 3 sec.
    while time.time() < shutdown + 3:
        if device.iter > now:  # if main loop completes an iteration, exit.
            break
        time.sleep(0.5)
    syslog.syslog("Controlled shutdown of airiana-core")
    raise ControlledExit


signal.signal(signal.SIGTERM, exit_callback)  # noqa ignore arg type check
signal.signal(signal.SIGINT, exit_callback)  # noqa ignore arg type check
path = ""
try:
    path = os.path.abspath(__file__).replace(__file__.split("/")[-1], "")
    syslog.syslog("file is " + __file__.split("/")[-1])
    syslog.syslog("changing to " + path)
    os.chdir(path)
except FileNotFoundError:
    syslog.syslog("unable to chdir to:" + path)
    exit(22)

# exec util fnctns
os.chdir(path + "/public")
os.system("./ip-replace.sh")  # reset ip-addresses on buttons.html
os.chdir(path)
os.system("./http &> /dev/null")  # Start web service
listme = []
#  cpy saved data to RAM ##
if not os.path.lexists("./data.save"):
    os.system("touch data.save")
else:
    os.system("cp data.save ./RAM/data.log")
#################################
if not os.path.lexists("./RAM/forecast.txt"):
    os.system("touch ./RAM/forecast.txt")
#################################
if "debug" in sys.argv and not os.path.lexists("./sensors"):
    os.system("touch sensors")
#################################
starttime = time.time()
# Setup daemon env
if not os.path.isdir("./RAM"):
    os.system("mkdir ./RAM")
ferr = os.open("./RAM/err", os.O_WRONLY | os.O_CREAT)
air_out = os.open("./RAM/air.out", os.O_WRONLY | os.O_CREAT)
if "daemon" in sys.argv:
    fout = os.open("./RAM/out", os.O_WRONLY | os.O_CREAT)
    os.dup2(fout, sys.stdout.fileno())
    print("Output redirected to file;")
    os.dup2(ferr, sys.stderr.fileno())
    os.lseek(ferr, 0, os.SEEK_END)
    stats = os.stat("RAM/err")
    size_t = stats.st_size
    if size_t > 1024 * 1024 and "keep-log" not in sys.argv:
        print("Clearing logfile...;")
        os.lseek(ferr, 0, os.SEEK_SET)
        os.ftruncate(ferr, 0)
        os.fsync(ferr)


# Setup serial, RS 485 to machine
if os.path.lexists("/dev/ttyUSB0"):
    print("Communication started on device ttyUSB0;")
    unit = "/dev/ttyUSB0"
    write_log("\n\nUsing /dev/ttyUSB0")

elif os.path.lexists("/dev/serial0"):
    print("Communication started on device Serial0;")
    unit = "/dev/serial0"
    write_log("\n\nUsing /dev/Serial0")
else:
    print("Communication started on device ttyAMA0;")
    unit = "/dev/ttyAMA0"
    write_log("\n\nUsing /dev/ttyAMA0")

# Command socket setup
hostname = os.popen("hostname").read()[:-1]
print("Trying to Run on host:", hostname, ", for 60sec;")
cmd_socket = None
while True:
    try:
        cmd_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        cmd_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        cmd_socket.bind(("0.0.0.0", 9876))
        break
    except socket.SO_ERROR:
        traceback.print_exc(ferr)
        os.system("sleep 1")
        print("sleeping;")
        if time.time() - starttime > 60:
            break
#  Utility functions, clear screen, count_down etc.
sensor_dict = {}


def count_down(inhibit, target_time):
    inhibit = int(target_time - (time.time() - inhibit))
    if inhibit > 3600:
        hrs = math.floor(inhibit / 3600)
        inhibit = int(inhibit - (hrs * 3600))
        return (
            str(hrs)
            + "h "
            + str(math.floor(inhibit / 60))
            + "min "
            + str(inhibit % 60).zfill(2)
            + "s"
        )
    if inhibit % 60 == 0:
        return str(math.floor(inhibit / 60)) + "min"
    if inhibit > 60:
        return str(math.floor(inhibit / 60)) + "min " + str(inhibit % 60).zfill(2) + "s"
    if inhibit < 60:
        return str(inhibit).zfill(2) + "s"


# SEND PING TO EPIC HEADMASTER
def report_alive():
    global holdoff_t
    message = ""
    hw_addr = ""
    fd = 0
    try:
        msg = os.popen("/sbin/ifconfig wlan0").readlines()
        for each in msg:
            if each.find("HWaddr") != -1 or each.find("ether") != -1:
                message = each
                message += os.popen("hostname -I").read()
                hw_addr = str(each.split(" ")[9]).replace(":", "_")
                try:
                    message += "\n###status:" + str(device.status_field) + "\n###<br>"
                except ValueError:
                    message += "\nstatus: initialization " + str(vers) + "\n\n<br>"
                try:
                    fd = os.open("RAM/err", os.O_RDONLY)
                    stats = os.stat("RAM/err")
                    size_t = stats.st_size
                    if size_t > 1024 * 5:
                        size_t = 1024 * 5
                    os.lseek(fd, -size_t, os.SEEK_END)
                    temp = os.read(fd, size_t)
                    os.close(fd)
                    if size_t == 5 * 1024 and "keep-log" not in sys.argv:
                        os.lseek(ferr, 0, os.SEEK_SET)
                        os.ftruncate(ferr, 0)
                        os.fsync(ferr)
                        os.write(ferr, temp)
                        os.fsync(ferr)
                    try:
                        if os.path.lexists("update.log"):
                            log_file = os.open("update.log", os.O_RDONLY)
                            log_data = os.read(log_file, 5000)
                            temp += bytes("\n\n", "utf-8")
                            temp += log_data
                            os.close(log_file)
                        if os.path.lexists("./RAM/request.log"):
                            with open("./RAM/request.log") as reqlog:
                                temp += bytes("\n\n", "utf-8")
                                temp += bytes(reqlog.read(), "utf-8")
                    except KeyboardInterrupt:
                        pass
                    temp = temp.replace(b"\n", b"<br>")
                    temp = temp.replace(b"\t", b"&emsp;")
                    message += temp.decode("utf-8") + "<br>"
                    message += os.popen("df |grep RAM").read() + "<br>"
                    message += os.popen("df |grep var").read() + "<br>"
                    message += (
                        "Source:('"
                        + os.popen("./geoloc.py printIp 2>/dev/null").read()
                        + "')<br>"
                    )
                    if os.path.lexists("RAM/error_rate"):
                        message += os.popen("cat RAM/error_rate").read() + "<br>"
                except:  # noqa do not care if this is failing
                    os.write(
                        ferr,
                        bytes(
                            "Ping error " + str(traceback.print_exc()) + "\n",
                            encoding="utf8",
                        ),
                    )
                    try:
                        os.close(fd)
                    except FileError:
                        os.write(
                            ferr,
                            bytes(
                                "File Error: " + str(traceback.print_exc()) + "\n",
                                encoding="utf8",
                            ),
                        )

        html = """ <html>[DA]</html>"""
        if holdoff_t < (time.time() - 3600):  # wait for one hour
            stat = open("RAM/" + hw_addr, "w")
            stat.write(html.replace("[DA]", message))
            os.system(
                'curl -s -X DELETE "https://filebin.net/5zzbcj2n0y5f2jfw/'
                + hw_addr
                + '.html"'
            )
            tmp = (
                '-s -X POST "https://filebin.net/5zzbcj2n0y5f2jfw/' + hw_addr + '.html"'
            )
            tmp += " -d @RAM/" + hw_addr
            stat.close()
            res = os.popen("curl " + tmp).read()
            if res.find("Insufficient storage") != -1:
                write_log("Holdoff time in effect, will re-ping in one hour.\n")
            holdoff_t = time.time()

        # sock =  socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        # sock.sendto(message, (socket.gethostbyname("lappy.asuscomm.com"), 59999))
        # #sock.close()
    except NameError:
        write_log("unable to ping, network error")
        traceback.print_exc(ferr)


# READ AVAIL SENSOR DATA
def update_sensors():
    try:
        with open("sensors", "r") as fd:
            for each in fd.readlines():
                sensor_unit = each.split(":")
                sensor_id = sensor_unit[0]
                sensor_unit.pop(0)
                tmp = {}
                for sensor in sensor_unit:
                    dat = sensor.split(";")
                    tmp[dat[0]] = dat[1]
                sensor_dict[sensor_id] = tmp
            try:
                device.sensor_temp = float(sensor_dict["91"]["temperature"])
                device.sensor_humid = int(sensor_dict["91"]["humidity"])
                device.airdata_inst.humid = float(device.sensor_humid) / 100
            except KeyError:
                pass
            try:
                device.inside = float(sensor_dict["92"]["temperature"])
                device.inside_humid = int(sensor_dict["92"]["humidity"])
            # device.inside_humid += 5 +(75-device.inside_humid)/10 use if sensor has incorrect tuning
            except KeyError:
                pass  # device.msg +="\nerror on sensor 92"
            try:
                device.sensor_exhaust = float(sensor_dict["94"]["temperature"])
            except KeyError:
                pass  # device.msg +="\nerror on sensor 94"

    except IndexError:
        device.msg += "\nnew sensor data error"
        traceback.print_exc()


# WRITE TO DATA.LOG
def logger():
    try:
        with open("./RAM/data.log", "a+") as fdo:
            # +str(device.extract_humidity*100)\
            cmd = (
                ""
                + str(time.time())
                + ":"
                + str(device.sensor_temp)
                + ":"
                + str(round(device.extract_ave, 2))
                + ":"
                + str(round(device.sensor_humid, 2))
                + ":"
                + str(round(device.humidity, 2))
                + ":"
                + str(round(device.inlet_ave, 2))
                + ":"
                + str(round(device.exhaust_ave, 2))
                + ":"
                + str(round(device.supply_ave, 2))
                + ":"
                + str(round(device.local_humidity, 2))
                + ":"
                + str(device.inside)
                + ":"
                + str(round(numpy.average(device.cond_data), 1))
                + ":"
                + str(device.inside_humid)
                + ":"
                + str(device.moist_in)
                + ":"
                + str(device.moist_out)
                + ":"
                + str(device.humidity_diff)
            )
            fdo.write(cmd + "\n")
    except FileError:
        traceback.print_exc(ferr)
    if "homeAss" in sys.argv:
        os.system(
            "./ha-httpsensor.py -n ftx_Indoor -u °C -d temperature -v "
            + str(round(device.extract_ave, 1))
            + ">/dev/null &"
        )
        os.system(
            "./ha-httpsensor.py -n ftx_Outside -u °C -d temperature -v "
            + str(round(device.inlet_ave, 1))
            + ">/dev/null &"
        )
        try:
            os.system(
                "./ha-httpsensor.py -n ftx_Efficiency -u % -d calculated -v "
                + str(round(numpy.average(device.eff_ave), 2))
                + ">/dev/null &"
            )
        except:  # noqa this section is deprecated
            traceback.print_exc(ferr)

        os.system(
            "./ha-httpsensor.py -n ftx_Humidity -d humidity -u % -v "
            + str(int(device.humidity))
            + ">/dev/null &"
        )
        os.system(
            "./ha-httpsensor.py -n ftx_ExtractFan -d fanspeed -u rpm -v "
            + str(int(device.ef_rpm))
            + ">/dev/null &"
        )


# PRINT COMM SETTING
def display_settings():
    clear_screen()
    print(str(req.client).replace(",", "\n"))


# CLEAR WHATS ON SCREEN AND RETURN TO UPPER LEFT
def clear_screen():
    if "daemon" in sys.argv:
        os.lseek(fout, 0, 0)
        os.ftruncate(fout, 0)
        os.fsync(fout)
    else:
        print(chr(27) + "[2J\x1b[H")


##############################################
class FileError(Exception):
    """Custom file exception"""

    pass


# ####################################################################
start = time.time()  # START TIME
sys.stdout.flush()


# ########### DEVICE CLASS FOR SYSTEMAIR #############################
def check_req(request, test, name):
    if request.response != test:
        if request.latest_request_mode == "Single":
            request.modbusregister(
                request.latest_request_address, request.latest_request_decimals
            )
        if request.response != test:
            os.write(
                ferr,
                bytes(
                    f"Retrieved value for {name}={request.response},"
                    f" but airiana was set to {test}, data updated."
                    f"\t{time.ctime(time.time())}\n",
                    "utf-8",
                ),
            )
            return False  # Return False as second request has been made and test is still false.
        return True  # Return True as response test is valid after re-read.
    return True  # Return True as response test is valid.


class Systemair(object):
    def __init__(self, request_object, config_file):
        self.config = {}
        self.loaded_config_mtime = 0
        self.used_energy = None
        self.use_calc_exhaust = False
        self.eff = None
        self.coef_prev_inlet = None
        self.shower_initial = None
        self.initial_fanspeed = None
        self.req = request_object
        self.savecair = False
        self.elec_now = 0
        self.showerRH = None
        self.initial_temp = None
        self.fanspeed = -1
        self.system_types = {
            0: "VR400",
            1: "VR700",
            2: "VR700DK",
            3: "VR400DE",
            4: "VTC300",
            5: "VTC700",
            12: "VTR150K",
            13: "VTR200B",
            14: "VSR300",
            15: "VSR500",
            16: "VSR150",
            17: "VTR300",
            18: "VTR500",
            19: "VSR300DE",
            20: "VTC200",
            21: "VTC100",
        }
        self.has_RH_sensor = ["VTR300", "VSR300", "savecair"]
        self.rotor_states = {
            0: "Normal",
            1: "Rotor Fault",
            2: "Rotor Fault Detected",
            3: "Summer Mode transitioning",
            4: "Summer Mode",
            5: "Leaving Summer Mode",
            6: "Manual Summer Mode",
            7: "Rotor Cleaning in Summer Mode",
            8: "Rotor cleaning in manual summer mode",
            9: "Fans off",
            10: "Rotor Cleaning during fans off",
            11: "Rotor Fault, but conditions normal",
        }
        self.speeds = {0: "Off", 1: "Low", 2: "Normal", 3: "High", 4: "undefined"}
        self.AC_energy = 0
        self.ac_active = False
        self.avg_frame_time = 1
        self.coef_new = 0
        self.coef_prev_supply = 0
        self.coef_fanspeed = 0
        self.rawdata = []
        self.press_inhibit = 0
        self.local_humidity = 0.0
        self.eff_ave = [90]
        self.diff_ave = [0]
        self.total_energy = 0.0
        self.average_limit = 1800  # min122
        self.sf = 20
        self.ef = 20
        self.sf_base = 20
        self.ef_base = 20
        self.ef_rpm = 1500
        self.sf_rpm = 1500
        self.inlet = []
        self.inlet_ave = 0
        self.supply = []
        self.supply_ave = 0
        self.extract = []
        self.extract_ave = 0.0
        self.electric_power = 1
        self.flowOffset = [0, 0]
        self.filter_raw = 0
        self.humidity_target = 0
        self.exhaust = []
        self.exhaust_ave = 0
        self.supply_power = 0
        self.extract_power = 0
        self.extract_combined = 0
        self.gain = 0
        self.loss = 0
        self.register = {}
        self.kinetic_compensation = 0
        self.starttime = time.time()
        self.timer = 0
        self.defrost = False
        self.current_mode = 0
        self.extract_humidity = 0.40  # relative humidity
        self.extract_humidity_comp = 0.00  # relative humidity re compensated
        self.humidity_diff = 0
        self.condensate_compensation = 0
        self.filter_remaining = 0
        self.cond_eff = 1
        self.dur = 1.0
        self.extract_dt = 0.0
        self.update_airdata_instance()
        self.shower = False
        self.det_limit = 0
        self.dyn_coef = 0
        self.msg = ""
        self.inside = 0
        self.inside_humid = 0
        self.exchanger_mode = -1
        self.reset_fans = False
        self.rotor_state = 0
        self.rotor_active = "Yes"
        self.inhibit = time.time()
        self.integral_forcast = 0
        self.system_name = ""
        self.sensor_temp = 0
        self.sensor_humid = 0
        self.modetoken = 0
        self.cooling = 0
        self.forecast = [-1, -1, -1]
        self.dt_hold = 0
        self.dt_entries = 0
        self.extract_dt_long_time = time.time()
        self.iter = 1
        self.extract_dt_long = 0
        self.cool_mode = False
        self.temps = []
        self.temp_state = 0
        self.condensate = 0
        self.coef = 0.17
        self.coef_prev_temp = 0
        self.new_coef = 0
        self.tcomp = 0
        self.inlet_coef = 0.1
        self.filter = 0
        self.filter_limit = 0
        self.cond_data = []
        self.cond_valid = False
        self.cond_dev = 0
        self.i_diff = []
        self.time = []
        self.extract_dt_list = [0]
        self.humidity_comp = 0
        self.pressure_diff = 0
        self.prev_static_temp = 8
        self.indoor_dewpoint = 0
        self.target = 22
        self.tomorrows_low = [0, 0, 0, 0, 0]
        self.energy_diff = 0
        self.humidity = 40.0
        self.moist_in = 0
        self.moist_out = 0
        self.monitoring = True
        self.set_system_name()
        self.RH_valid = 0
        self.hum_list = []
        self.status_field = [
            -1,
            self.exchanger_mode,
            0,
            self.system_name,
            vers,
            os.popen("git log --pretty=format:'%h' -n 1").read(),
            0,
            self.inlet_ave,
            self.extract_ave,
            self.ef,
            self.humidity,
            0,
            self.cool_mode,
            self.supply_ave,
            self.exhaust_ave,
            self.pressure_diff,
            self.det_limit,
        ]
        self.heater = 0
        self.exchanger_speed = 0
        self.unit_comp = []
        self.coef_dict = {0: {}, 1: {}, 2: {}, 3: {}}
        self.coef_test_bool = False
        self.coef_inhibit = time.time()
        self.sensor_exhaust = -60
        self.admin_password = ""
        self.electric_power_sum = 0.0
        self.config_file = config_file
        self.check_config()
        self.cooling_limit = self.config["systemair"]["control"][
            "forcastIntegralCoolingLimit"
        ]
        self.house_heat_limit = self.config["systemair"]["control"][
            "forcastDailyLowCoolingInhibit"
        ]

    # Check if config has been updated.
    def check_config(self):
        file_path = pathlib.Path(self.config_file)
        if not file_path.exists():
            write_log("Did not find a config file, copying")
            os.system(f"cp ./systemfiles/config.template {self.config_file}")
        if os.path.getmtime(self.config_file) != self.loaded_config_mtime:
            write_log("Config file updated, reloading configuration.")
            self.load_config()
            self.system_setup()

    # Load config from file.
    def load_config(self):
        try:
            self.loaded_config_mtime = os.path.getmtime(self.config_file)
            with open(self.config_file, "r") as file:
                self.config_template = yaml.safe_load(
                    open("public/config.template", "r")
                )
                self.config = yaml.safe_load(file)
                if self.config == None or len(self.config.keys()) == 0:
                    raise TypeError("The configuration file was empty.")
                missing = self.find_missing_keys(
                    self.config_template, self.config, path=""
                )
                print("Missing keys in config: ", missing)
            write_log(
                "Loading config:\n"
                + self.config.__str__()
                + "\n"
                + "Missing keys in config: "
                + str(missing)
                + "\n"
            )
        except IOError as e:
            print(e)
            write_log("Unable to open configurationfile.")
            exit(-11)
        except yaml.YAMLError as e:
            write_log("There is an error in the YAML config file:\n" + e.__str__())
            exit(-12)
        except TypeError as e:
            print(
                "There was an error with the configuration file.",
                self.config,
                e.__str__(),
            )
            os.write(
                ferr,
                bytes(
                    "There was an error in the configuration file. " + e.__str__(),
                    encoding="utf-8",
                ),
            )
            with open("./public/config.template", "r") as template:
                self.config = yaml.safe_load(template)

    def find_missing_keys(self, template, config, path=""):
        missing = []
        for key in template:
            full_path = f"{path}.{key}" if path else key
            if key not in config:
                missing.append(full_path)
            elif isinstance(template[key], dict):
                if not isinstance(config.get(key), dict):
                    missing.append(full_path + " (should be a dict)")
                    config[key] = template[key]
                    print(f"ADDING {template[key]}", key)
                else:
                    # config[key] = template[key]
                    missing += self.find_missing_keys(
                        template[key], config[key], full_path
                    )
        return missing

    def set_monitoring(self, val):
        self.inhibit = 0
        self.press_inhibit = 0
        self.modetoken = 0
        self.monitoring = val

    def reset_fanspeed(self, speed):
        self.reset_fans = speed

    def get_password(self):
        self.req.modbusregister(16000, 0)
        self.admin_password = "{0}{1}{2}{3}".format(
            str(self.req.response & 0b1),
            str(self.req.response & 0b1000 >> 3),
            str(self.req.response & 0b10000000 >> 7),
            str(self.req.response & 0b100000000000 >> 11),
        )

    def system_setup(self):
        try:
            if os.path.isfile("coeficients.dat"):
                self.coef_dict = pickle.load(open("coeficients.dat", "rb"))
            else:
                pickle.dump(self.coef_dict, open("coeficients.dat", "wb"))
        except EOFError:
            traceback.print_exc(ferr)
            pickle.dump(self.coef_dict, open("coeficients.dat", "wb"))

        if self.savecair:
            self.get_password()
            self.req.write_register(
                1400, self.config["systemair"]["savecair"]["efMinFlow"]
            )
            self.req.write_register(
                1401, self.config["systemair"]["savecair"]["sfMinFlow"]
            )
            self.req.write_register(
                1402, self.config["systemair"]["savecair"]["efLowFlow"]
            )
            self.req.write_register(
                1403, self.config["systemair"]["savecair"]["sfLowFlow"]
            )
            self.req.write_register(
                1404, self.config["systemair"]["savecair"]["efNormFlow"]
            )
            self.req.write_register(
                1405, self.config["systemair"]["savecair"]["sfNormFlow"]
            )
            self.req.write_register(
                1406, self.config["systemair"]["savecair"]["efHighFlow"]
            )
            self.req.write_register(
                1407, self.config["systemair"]["savecair"]["sfNormFlow"]
            )
            self.req.write_register(
                1408, self.config["systemair"]["savecair"]["efMaxFlow"]
            )
            self.req.write_register(
                1409, self.config["systemair"]["savecair"]["sfMaxFlow"]
            )

        else:
            if self.system_name not in self.config["systemair"]["legacy"].keys():
                self.system_name = "VR400"
            self.get_heater()
            # make sure the electric heater is oFF
            if self.heater != 0:
                self.set_heater(0)
            # check if there is an RH sensor available even though it's not listed
            self.get_RH()
            if self.RH_valid and self.system_name not in self.has_RH_sensor:
                self.has_RH_sensor.append(self.system_name)

            # setup airflow levels
            self.sf_base = self.config["systemair"]["legacy"][self.system_name][
                "sfBaseFlow"
            ]
            # TODO: make a better comment for what this does.
            self.req.modbusregister(137, 0)
            if int(self.req.response) == 1:
                self.req.write_register(137, 0)
                self.req.modbusregister(107, 0)
            if int(self.req.response) == 1:
                self.req.write_register(107, 0)
            # SET BASE FLOW RATES
            self.req.write_register(
                101, self.config["systemair"]["legacy"][self.system_name]["sfBaseFlow"]
            )
            self.req.write_register(
                102, self.config["systemair"]["legacy"][self.system_name]["efBaseFlow"]
            )
            self.req.write_register(
                103, self.config["systemair"]["legacy"][self.system_name]["sfMedFlow"]
            )
            self.req.write_register(
                104, self.config["systemair"]["legacy"][self.system_name]["efMedFlow"]
            )
            self.req.write_register(
                105, self.config["systemair"]["legacy"][self.system_name]["sfHighFlow"]
            )
            self.req.write_register(
                106, self.config["systemair"]["legacy"][self.system_name]["efHighFlow"]
            )

    # get heater status
    def get_heater(self):
        if not self.savecair:
            self.req.modbusregister(200, 0)
            check_req(self.req, self.heater, "electric_heater")
            self.heater = int(self.req.response)
        else:
            self.heater = 0

    # set heater status
    def set_heater(self, heater):
        if not self.savecair:
            self.req.write_register(200, heater)

    # get and set the Unit System name, from system types dict
    def set_system_name(self):
        if not self.savecair:
            self.req.modbusregister(500, 0)
            self.system_name = self.system_types[self.req.response]

    # get the coef mode, for dict matching
    def get_coef_mode(self):
        operating_mode = 0
        if self.exchanger_mode == 5 and self.exchanger_speed == 100:
            operating_mode += 1
        if self.sf != self.ef:
            operating_mode += 2
        return operating_mode

    # calculate a new coef as fanspeed change renders high dt values  //UNused
    def coef_debug(self):
        if (
            self.fanspeed == 3
            and not self.coef_test_bool
            and self.inhibit
            and not self.shower
        ):
            self.press_inhibit = time.time()
            self.modetoken = time.time() - 3000
            fd = open("coeficients.dat", "rb")
            self.coef_dict = pickle.load(fd)
            fd.close()
            self.coef_test_bool = True
            self.coef_prev_temp = 0
            for each in self.rawdata:
                self.coef_prev_temp += float(each[1]) / 10
            self.coef_prev_temp = self.coef_prev_temp / len(self.rawdata)
            self.coef_prev_inlet = self.inlet_ave
            self.coef_prev_extract = self.extract_ave

        # END the test and save the coef at the current temp delta
        if (self.inhibit == 0 or self.fanspeed == 2) and self.coef_test_bool:
            temp = 0
            for each in self.rawdata:
                temp += float(each[1]) / 10
            temp = temp / len(self.rawdata)
            temp_diff = self.coef_prev_extract - self.coef_prev_inlet
            delta = self.coef_prev_temp - temp
            new_coef = delta / temp_diff
            os.system(
                'echo "newCoef:'
                + str(new_coef)
                + "\nAmbientDiff:"
                + str(temp_diff)
                + '" >> newCoef.txt'
            )
            os.system(
                'echo "delta:'
                + str(delta)
                + " list:"
                + str(self.get_coef_mode())
                + "\ntemp:"
                + str(temp)
                + " prev_tmp:"
                + str(self.coef_prev_temp)
                + '\n" >> newCoef.txt'
            )
            try:
                keys = list(self.coef_dict[self.get_coef_mode()].keys())
            except KeyError:
                keys = []
            if int(temp_diff) not in keys:
                self.coef_dict[self.get_coef_mode()][int(temp_diff)] = new_coef
            else:
                # add 10% of diff from new coef to dict if already tested and rerun
                self.coef_dict[self.get_coef_mode()][int(temp_diff)] += (
                    new_coef - self.coef_dict[self.get_coef_mode()][int(temp_diff)]
                ) * 0.1
            if len(self.coef_dict) != 0:
                pickle.dump(self.coef_dict, open("coeficients.dat", "wb"))
            self.coef_test_bool = False
            self.set_fanspeed(1)

    # Get relative humidity from internal sensor, valid units in self.has_RH_sensor tuple
    def get_RH(self):
        if "noRH" in sys.argv:
            self.RH_valid = 0
            return 0
        if not self.savecair:
            self.req.modbusregister(382, 0)
            self.RH_valid = int(self.req.response)
            if self.RH_valid:
                self.req.modbusregister(380, 0)
                self.humidity = float(self.req.response)
        else:
            self.req.modbusregister(12135, 0)
            if self.req.response != 0:
                self.RH_valid = 1
                self.humidity = float(self.req.response)
        if self.RH_valid:
            self.hum_list.insert(0, self.humidity)
            if len(self.hum_list) > self.average_limit:
                self.hum_list.pop(-1)
            try:
                # if an update of the humidity value on the sensor exceeds 2 points reuse last known value
                if abs(self.humidity - self.hum_list[1]) > 2:
                    self.humidity = self.hum_list[1]
                    self.hum_list[0] = self.humidity
            except IndexError:
                pass

    # get the nr of days  used and alarm lvl for filters
    def get_filter_status(self):
        if not self.savecair:
            self.req.modbusregister(600, 0)
            self.filter_limit = int(self.req.response) * 31
            self.req.modbusregister(601, 0)
            self.filter = self.req.response
            try:
                self.filter_remaining = round(
                    100 * (1 - (float(self.filter) / self.filter_limit)), 1
                )
            except (ValueError, ZeroDivisionError):
                traceback.print_exc(ferr)

            if self.filter_remaining < 0:
                self.filter_remaining = 0
        else:
            self.req.modbusregister(7000, 0)
            self.filter_limit = int(self.req.response) * 30
            self.req.modbusregister(7004, 0)
            lowend = self.req.response
            self.req.modbusregister(7005, 0)
            highend = self.req.response << 16
            self.filter_raw = lowend + highend
            self.filter = self.filter_limit - (lowend + highend) / (3600 * 24)
            try:
                self.filter_remaining = round(
                    100 * (1 - (float(self.filter) / self.filter_limit)), 1
                )
            except ZeroDivisionError:
                traceback.print_exc(ferr)
            if self.filter_remaining < 0:
                self.filter_remaining = 0

    # get status byte for temp probes
    def get_temp_status(self):
        if not self.savecair:
            self.req.modbusregister(218, 0)
            self.temp_state = self.req.response

    def print_attributes(self):
        for each in dir(self):
            obj = None
            exec(str("obj = self." + each))
            if isinstance(obj, (int, float, str, list)) or True:
                exec(str("print (each,  self." + each + ")"))
        if "daemon" not in sys.argv:
            input("press enter to resume")
        else:
            print("break")
            os.system("sleep 2")

    def get_fanspeed(self):
        if not self.savecair:
            self.req.modbusregister(100, 0)
            check_req(self.req, self.fanspeed, "fanspeed")
            self.fanspeed = int(self.req.response)
            return self.fanspeed
        else:
            self.req.modbusregister(1130, 0)
            self.req.response -= 1
            check_req(self.req, self.fanspeed, "fanspeed")
            self.req.modbusregister(1130, 0)
            if self.req.response <= 0:
                self.fanspeed = 0
            else:
                self.fanspeed = self.req.response - 1
            return self.fanspeed

    def update_temps(self):
        if not self.savecair:
            self.req.modbusregisters(213, 5)  # Temp sensors 1 -5
            self.time.insert(0, time.time())
            if len(self.time) > self.average_limit:
                self.time.pop(-1)

            # NEGATIVE VAL sign bit twos complement
            if self.req.response[4] > 6000:
                self.req.response[4] -= 0xFFFF
            if self.req.response[2] > 6000:
                self.req.response[2] -= 0xFFFF

            self.temps = self.req.response[:]
            self.rawdata.insert(0, self.temps)
            if len(self.rawdata) > self.average_limit:
                self.rawdata.pop(-1)

            # self.request.response[1] #EXTRACT
            # self.request.response[2] #EXHAUST
            # self.request.response[0] #Supply pre elec heater
            # self.request.response[3] #Supply post electric heater
            # self.request.response[4] Inlet

            # update [4] with inlet coef
            self.req.response[4] -= (
                self.req.response[1] - self.req.response[4]
            ) * self.inlet_coef  # inlet compensation exchanger OFF/ON
            # update [1] with tcomp, after calc of [4]
            self.tcomp = 10 * self.get_tcomp(
                float(self.req.response[1]) / 10, float(self.req.response[4]) / 10
            )
            self.req.response[1] += self.tcomp

            self.extract.insert(0, float(self.req.response[1]) / 10)
            self.exhaust.insert(0, float(self.req.response[2]) / 10)
            self.supply.insert(0, float(self.req.response[3]) / 10)
            self.inlet.insert(0, float(self.req.response[4]) / 10)

            # limit array size
            for each in [self.inlet, self.supply, self.extract, self.exhaust]:
                if len(each) > self.average_limit:
                    each.pop(-1)
        else:  # self.savecair SECTION
            self.time.insert(0, time.time())

            # EXTRACT
            extract = "no data"
            cnt = 0
            while extract == "no data" and cnt < 10:
                self.req.modbusregister(12543, 1)
                extract = self.req.response
            try:  # replace erroneous data input when temp diff exceeds 1C between samples
                if extract - self.rawdata[0][1] > 50 and (
                    extract != 0.0 or self.rawdata[1][1] != 0.0
                ):
                    os.write(
                        ferr,
                        bytes(
                            "temp read error at: "
                            + str(extract)
                            + "C \t"
                            + str(time.ctime())
                            + "\n",
                            encoding="utf8",
                        ),
                    )
                    extract = self.rawdata[1][1]
            except IndexError:
                pass
            except TypeError:
                os.write(
                    ferr,
                    bytes(
                        "temp read type error at: "
                        + str(extract)
                        + "C \t"
                        + str(time.ctime())
                        + "\n",
                        encoding="utf8",
                    ),
                )
                traceback.print_exc(ferr)
                extract = self.rawdata[1][1]
                pass

            self.req.modbusregister(12102, 1)
            supply = self.req.response
            self.req.modbusregister(12101, 1)
            inlet = self.req.response
            # self.request.response[1] #EXTRACT
            # self.request.response[2] #EXHAUST
            # self.request.response[0] #Supply pre elec heater
            # self.request.response[3] #Supply post electric heater
            # self.request.response[4] Inlet
            self.rawdata.insert(0, (0, extract * 10, 0, supply * 10, inlet * 10))
            if len(self.rawdata) > self.average_limit:
                self.rawdata.pop(-1)
            self.tcomp = self.get_tcomp(extract, inlet)
            self.extract.insert(0, float(extract + self.tcomp))
            # SUPPLY
            self.supply.insert(0, float(supply))
            # INLET
            # if self.rotor_active =="No"  and self.inlet_coef <0.03:self.inlet_coef+= 0.0001 #OFF
            # if self.rotor_active =="Yes" and self.inlet_coef >0.00:self.inlet_coef-= 0.0001 # ON
            tweak = 0
            try:
                inlet_comp = ((float(3200) / self.sf_rpm) - 1) * 0.01
                tweak = (
                    extract - inlet
                ) * inlet_comp  # inlet compensation exchanger OFF/ON
            except ZeroDivisionError:
                pass
            self.inlet.insert(0, float(inlet - tweak))

            if len(self.extract) > self.average_limit:
                self.extract.pop(-1)
            if len(self.exhaust) > self.average_limit:
                self.exhaust.pop(-1)
            if len(self.supply) > self.average_limit:
                self.supply.pop(-1)
            if len(self.inlet) > self.average_limit:
                self.inlet.pop(-1)
            if len(self.time) > self.average_limit:
                self.time.pop(-1)
        try:
            self.eff = (
                (self.supply_ave - self.inlet_ave)
                / (self.extract_ave - self.inlet_ave)
                * 100
            )
        except ZeroDivisionError:
            self.eff = 100
        self.eff_ave.insert(0, self.eff)
        if len(self.eff_ave) > self.average_limit:
            self.eff_ave.pop(-1)

    # Return the Tcomp temperature offset for extraction temps
    def get_tcomp(self, extract, inlet):
        tcomp = 0
        try:
            diff = extract - inlet
            dyn_coef = 0
            try:
                if self.fanspeed and len(self.coef_dict[self.get_coef_mode()]) != 0:
                    dyn_coef = (
                        numpy.median(
                            list(self.coef_dict[self.get_coef_mode()].values())
                        )
                        * float(1)
                        / self.fanspeed
                    )
                    # self.dyn_coef #float(7*34)/self.sf
                    # compensation (heat transfer from duct) + (supply flow component)
                if self.fanspeed == 3:
                    dyn_coef = 0
            except KeyError:
                if len(self.coef_dict):
                    dyn_coef = numpy.average(
                        list(self.coef_dict[self.get_coef_mode()].values())
                    )
                    if numpy.isnan(dyn_coef):
                        dyn_coef = 0
            except ZeroDivisionError:
                traceback.print_exc(ferr)

            if dyn_coef != self.new_coef:
                self.new_coef += 0.0001 * (dyn_coef - self.new_coef)
                if abs(dyn_coef - self.new_coef) < 0.001:
                    self.new_coef = dyn_coef
            tcomp = diff * -self.new_coef
        except ZeroDivisionError:
            pass
        if numpy.isnan(tcomp):
            return 0
        return tcomp

    def set_fanspeed(self, target_fanspeed):
        self.inhibit = time.time()
        self.coef_inhibit = time.time()
        if target_fanspeed != self.fanspeed:  # add one to bucket
            self.status_field[0] += 1
            os.write(
                ferr,
                bytes(
                    "Changing fanspeed to:"
                    + str(target_fanspeed)
                    + " \t\t"
                    + str(time.ctime())
                    + "\n",
                    encoding="utf8",
                ),
            )
        # print actual,"->",target
        if target_fanspeed >= 4:
            target_fanspeed = 0
        if target_fanspeed < 0:
            target_fanspeed = 0

        if not self.savecair:
            self.req.write_register(100, target_fanspeed)
            self.fanspeed = target_fanspeed
        else:
            if target_fanspeed == 0:
                self.req.write_register(1130, target_fanspeed)
                self.fanspeed = target_fanspeed
            else:
                self.req.write_register(1130, target_fanspeed + 1)
                self.fanspeed = target_fanspeed
        if self.get_fanspeed() != target_fanspeed:
            os.write(
                ferr,
                bytes(
                    "Incorrectly set fanspeed "
                    + str(self.get_fanspeed())
                    + " to "
                    + str(target_fanspeed)
                    + " \t"
                    + str(time.ctime())
                    + "\n",
                    encoding="utf8",
                ),
            )
        self.update_airflow()

    def update_fan_rpm(self):
        if not self.savecair:
            self.req.modbusregisters(110, 2)
            self.sf_rpm, self.ef_rpm = self.req.response[0], self.req.response[1]
            try:
                if self.system_name in ("VR400"):
                    self.electric_power = self.ef_rpm / (
                        100 / (float(float(self.ef_rpm) / 1381) ** 1.89)
                    ) + self.sf_rpm / (100 / (float(float(self.sf_rpm) / 1381) ** 1.89))
                if self.system_name in ("VSR300"):
                    self.electric_power = 0.2 * (
                        self.ef_rpm / (100 / (float(float(self.ef_rpm) / 1381) ** 1.89))
                        + self.sf_rpm
                        / (100 / (float(float(self.sf_rpm) / 1381) ** 1.89))
                    )
                if self.system_name in ("VTR300"):
                    self.electric_power = 0.2 * (
                        self.ef_rpm / (100 / (float(float(self.ef_rpm) / 1381) ** 1.89))
                        + self.sf_rpm
                        / (100 / (float(float(self.sf_rpm) / 1381) ** 1.89))
                    )

            except ZeroDivisionError:
                self.electric_power = 0
            if "Yes" in self.rotor_active:
                self.electric_power += 10  # rotor motor 10Watts
            self.electric_power += 5  # controller power

        else:
            self.req.modbusregister(12400, 0)
            self.sf_rpm = self.req.response
            self.req.modbusregister(12401, 0)
            self.ef_rpm = self.req.response
            try:
                self.electric_power = 3.404 * math.exp(
                    0.001 * self.ef_rpm
                ) + 3.404 * math.exp(0.001 * self.sf_rpm)
            except ZeroDivisionError:
                self.electric_power = 0
            if "Yes" in self.rotor_active:
                self.electric_power += 10  # rotor motor 10Watts
            self.electric_power += 5  # controller board power
        if (
            self.elec_now != 0
        ):  # integral of the electric power used by fans and controller
            self.electric_power_sum += (
                self.electric_power * (time.time() - self.elec_now)
            ) / 3600
        self.elec_now = time.time()

    def update_fanspeed(self):
        self.fanspeed = self.get_fanspeed()

    def update_airflow(self):
        if not self.savecair:
            self.req.modbusregisters(101, 6)
            sf = [self.req.response[0], self.req.response[2], self.req.response[4]]
            ef = [self.req.response[1], self.req.response[3], self.req.response[5]]
            tmp = self.fanspeed  # self.get_fanspeed()
            if tmp <= 0:
                tmp = 1
            self.sf = sf[tmp - 1]
            self.ef = ef[tmp - 1]
            if self.fanspeed == 0:
                self.ef = 0
                self.sf = 0
        else:
            self.req.modbusregister(14000, 0)
            self.sf = int(self.req.response)
            self.req.modbusregister(14001, 0)
            self.ef = int(self.req.response)

    def update_airdata_instance(self):
        self.airdata_inst = airdata.Energy()

    def update_xchanger(self):
        if len(self.inlet):
            self.inlet_ave = numpy.average(self.inlet)
            self.supply_ave = numpy.average(self.supply)
            self.extract_ave = numpy.average(self.extract)
            if self.system_name == "VR400" and not self.use_calc_exhaust:
                self.exhaust_ave = numpy.average(self.exhaust)
                if self.exhaust_ave < -40.0:
                    self.use_calc_exhaust = True
        else:
            self.inlet_ave = self.inlet[0]
            self.supply_ave = self.supply[0]
            self.extract_ave = self.extract[0]
            if self.system_name == "VR400":
                self.exhaust_ave = self.exhaust[0]

        if self.fanspeed != 0:
            # self.available_energy =  self.airdata_inst.energy_flow(self.ef, self.extract_ave, self.inlet_ave)
            #                             + self.airdata_inst.condensation_energy(
            #                             (self.airdata_inst.vapor_max(self.exhaust_ave)
            #                             - self.airdata_inst.vapor_max(self.inlet_ave)) * ((self.ef) / 1000))
            self.used_energy = self.airdata_inst.energy_flow(
                self.sf, self.supply_ave, self.inlet_ave
            )
            factor = 1  # casing transfer correction factor
            if self.rotor_active == "Yes":
                if self.fanspeed == 3:
                    factor = 0  # 3.3
                elif self.fanspeed == 1:
                    if self.ef == self.sf:
                        factor = 0  # 3.95
                    else:
                        factor = 0  # 2.9
                elif self.fanspeed == 2:  # corrective factors W/deg
                    factor = 0  # 5.65
            elif self.rotor_active == "No":
                if self.fanspeed == 1:
                    factor = 0  # 3#  - 16 constant# red  from casing heat transfer
                elif self.fanspeed == 2:
                    factor = 0  # 1.9#  - 16 constant# red  from casing heat transfer
                elif self.fanspeed == 3:
                    factor = 0
            else:
                factor = 1
            if self.rotor_active == "Yes":
                self.supply_power = (
                    self.used_energy - 00 - (self.extract_ave - self.inlet_ave) * factor
                )  # constant# red  from casing heat transfer
            else:
                self.supply_power = (
                    self.used_energy - 0 - (self.extract_ave - self.inlet_ave) * factor
                )  # constant# red  from casing heat transfer

            try:
                self.extract_exchanger = self.airdata_inst.energy_flow(
                    self.ef, self.extract_ave, self.exhaust_ave
                )
            except:
                self.extract_exchanger = 0
            self.extract_offset = 0  # float(8)*(self.extract_ave-self.supply_ave)# + 20Watt/degC transfer after exchanger unit
            self.extract_power = self.extract_exchanger + self.extract_offset
            self.extract_combined = self.extract_power + self.condensate_compensation
            self.energy_diff = self.supply_power - self.extract_power
            try:
                self.loss = self.airdata_inst.energy_flow(
                    self.ef, self.exhaust_ave, self.inlet_ave
                ) + self.airdata_inst.energy_flow(
                    self.sf, self.extract_ave, self.supply_ave
                )
            except:
                self.loss = 0
            try:
                self.diff_ave.insert(
                    0,
                    (
                        -1
                        * (self.extract_combined - self.supply_power)
                        / ((self.supply_power + self.extract_combined) / 2)
                    )
                    * 100,
                )
            except ZeroDivisionError:
                pass

            if len(self.diff_ave) > self.average_limit:
                self.diff_ave.pop(-1)
            self.i_diff.append((self.extract_combined - self.supply_power) * -1)
            if len(self.i_diff) > 15:
                self.i_diff.pop(0)
            try:
                self.dur = self.time[0] - self.time[1]
                if self.rotor_active == "Yes":
                    self.total_energy += (self.loss * self.dur) / 3600
                elif (
                    self.exhaust_ave > self.extract_ave
                    and self.exhaust_ave > self.inlet_ave
                    and self.ac_active
                ):
                    self.AC_energy += (
                        self.airdata_inst.energy_flow(
                            self.ef, self.exhaust_ave, self.inlet_ave
                        )
                        * self.dur
                        / 3600
                    )
                elif self.extract_ave > self.supply_ave:
                    self.cooling += (self.loss * self.dur) / 3600
                else:
                    self.gain += (self.loss * self.dur) / 3600
            except IndexError:
                pass
            except:
                traceback.print_exc(ferr)

            self.cond_data.append(self.energy_diff)
            if len(self.cond_data) > self.average_limit + 5000:
                self.cond_data.pop(0)

    # test if exhaust temperatures are indicative of ac hot flow connected to cooker exhaust line
    def check_ac_mode(self):
        # use external exhaust sensor if it measures more 30C, airCond mode.
        if (
            self.sensor_exhaust >= 30
            or (self.exhaust_ave - self.inlet_ave > 5 and self.exhaust_ave > 30)
        ) and not self.ac_active:
            self.ac_active = True
            os.write(
                ferr,
                bytes(
                    "A/C mode engaged. Detected high exhaust temperatures at \t"
                    + time.ctime()
                    + "\n",
                    encoding="utf8",
                ),
            )
            if self.fanspeed != 3:
                self.set_fanspeed(3)
        if self.ac_active and (
            self.sensor_exhaust <= 30
            or (
                self.exhaust_ave - self.extract_ave < 5
                and self.exhaust_ave < 30
                and self.sensor_exhaust <= 30
            )
        ):
            self.ac_active = False
            os.write(
                ferr,
                bytes(
                    "A/C mode disengaged. no AC conditions detected at \t"
                    + time.ctime()
                    + "\n",
                    encoding="utf8",
                ),
            )
        if "sensors" in sys.argv and self.ac_active:
            self.exhaust_ave = self.sensor_exhaust

    # For units without exhaust temp sensor calc expected exhaust temp based on transferred energy in supply
    def calc_exhaust(self):
        if self.supply_power and self.ef and not self.ac_active:
            if self.supply_ave > self.inlet_ave:
                exhaust = self.extract_ave - self.airdata_inst.temp_diff(
                    self.supply_power, self.extract_ave, self.ef
                )
            else:
                exhaust = self.extract_ave + self.airdata_inst.temp_diff(
                    -1 * self.supply_power, self.extract_ave, self.ef
                )
            self.exhaust_ave = exhaust

    # Retrieve the rotor state from the unit
    def get_rotor_state(self):
        if not self.savecair:
            self.req.modbusregister(206, 0)
            check_req(self.req, self.exchanger_mode, "exchanger_mode")
            self.exchanger_mode = self.req.response
            self.req.modbusregister(350, 0)
            check_req(self.req, self.rotor_state, "rotor_state")
            self.rotor_state = self.req.response
            self.req.modbusregister(351, 0)
            check_req(self.req, self.rotor_active == "Yes", "rotor_active")
            if self.req.response:
                self.rotor_active = "Yes"
                self.exchanger_speed = 100
            else:
                self.rotor_active = "No"
        else:
            self.req.modbusregister(2140, 0)
            self.exchanger_speed = self.req.response
            if self.req.response != 0:
                self.req.response = 5
            check_req(self.req, self.exchanger_mode, "exchanger_mode")
            if self.req.response:
                self.rotor_active = "Yes"
                self.exchanger_mode = 5
            else:
                self.exchanger_mode = 0
                self.rotor_active = "No"
            self.rotor_state = 0
        self.status_field[1] = self.exchanger_mode

    # do moisture calculations
    def moisture_calcs(
        self, temperature_reference=None
    ):  # Calculate moisture/humidities
        self.moist_in = 1000 * self.airdata_inst.sat_vapor_press(
            self.airdata_inst.dew_point(self.humidity, self.extract_ave)
        )
        self.moist_out = 1000 * self.airdata_inst.sat_vapor_press(
            self.airdata_inst.dew_point(self.local_humidity, self.extract_ave)
        )
        self.humidity_diff = self.moist_in - self.moist_out
        self.cond_eff = 1.0  # 1 -((self.extract_ave-self.supply_ave)/35)#!abs(self.inlet_ave-self.exhaust_ave)/20
        # Update saturation moisture
        if self.energy_diff > 0 and self.rotor_active == "Yes":
            try:
                d_pw = (
                    self.airdata_inst.energy_to_pwdiff(
                        self.energy_diff, self.extract_ave
                    )
                    / self.cond_eff
                ) / (float(self.ef) / 1000)
            except:
                d_pw = 0
        else:
            d_pw = 0

        max_pw = self.airdata_inst.sat_vapor_press(self.extract_ave) * 1000
        div = self.prev_static_temp - self.kinetic_compensation  # to test new ref
        low_pw = self.airdata_inst.sat_vapor_press(div) * 1000

        # create humidity if no sensor data avail
        if numpy.isnan(self.humidity):  # reset nan error
            self.humidity = 20
        if not self.RH_valid:
            tmp_rh = ((low_pw + d_pw) / max_pw) * 100
            self.humidity += (tmp_rh - self.humidity) * 0.001
            self.hum_list.insert(0, self.humidity)
            if len(self.hum_list) > self.average_limit:
                self.hum_list.pop(-1)

        # query for a ref humidity at temp
        if temperature_reference is not None:
            max_pw = self.airdata_inst.sat_vapor_press(self.extract_ave)
            low_pw = self.airdata_inst.sat_vapor_press(temperature_reference)
        return low_pw / max_pw * 100

    # Calc long and short derivatives
    def derivatives(self):
        # Short
        if len(self.extract) > self.average_limit - 1:
            self.extract_dt = numpy.average(self.extract[0:14]) - numpy.average(
                self.extract[self.average_limit - 15 : self.average_limit - 1]
            )
            self.extract_dt = self.extract_dt / (
                (self.time[0] - self.time[self.average_limit - 1]) / 60
            )
            self.extract_dt_list.append(self.extract_dt)
            if len(self.extract_dt_list) > 500:
                self.extract_dt_list.pop(0)
        # Long
        if self.iter % round(360 / self.avg_frame_time, -2) == 0:
            if self.dt_hold == 0:
                self.dt_hold = self.extract_ave
            self.extract_dt_long = float((self.extract_ave - self.dt_hold)) / (
                (time.time() - self.extract_dt_long_time) / 360
            )
            self.extract_dt_long_time = time.time()
            self.dt_hold = self.extract_ave
            self.avg_frame_time = (time.time() - starttime) / self.iter

    # Detect if shower is on
    def shower_detect(self):
        def turnoff():
            if self.savecair:
                self.req.write_register(1161, 2)
            else:
                self.set_fanspeed(self.initial_fanspeed)

        if "debug" in sys.argv and self.shower and self.RH_valid:
            self.msg = (
                "Shower wait state, "
                + str(round(self.extract_ave, 2))
                + "C "
                + str(round(self.initial_temp + 0.3, 2))
                + "C RH: "
                + str(self.showerRH + 5)
                + "\n"
            )
        if self.RH_valid == 1 and not self.shower:  # Shower humidity sensor control
            try:
                shower_RH_limit = self.config["systemair"]["control"][
                    "showerTriggerLimit"
                ]
                if (
                    self.hum_list[0] - self.hum_list[-1] > shower_RH_limit
                    and numpy.average(self.extract_dt_list) * 60 > 0.0
                ):
                    self.shower = True
                    self.initial_temp = self.extract_ave
                    self.initial_fanspeed = self.fanspeed
                    if self.savecair:
                        self.req.write_register(1103, 45)
                        self.req.write_register(1161, 4)
                    else:
                        self.set_fanspeed(3)
                    if self.RH_valid:
                        self.showerRH = self.hum_list[-1]
                    self.inhibit = time.time()
                    self.coef_inhibit = time.time()
                    self.shower_initial = self.inhibit
                    self.msg = "Shower mode engaged\n"
                    os.write(
                        ferr,
                        bytes(
                            "Engaged Shower mode at\t" + str(time.ctime()) + "\n",
                            encoding="utf8",
                        ),
                    )
                    self.status_field[0] += 1
            except IndexError:
                pass
        elif not self.shower and not self.RH_valid:
            # Shower derivative controller
            lim = 0.07
            if self.ef > 50:
                lim = 0.07
            if (
                len(self.extract_dt_list)
                and self.extract_dt > lim + float(self.det_limit) / 100
                and self.inhibit == 0
                and numpy.average(self.extract_dt_list) * 60 > 1.40
            ):
                self.msg = "Shower mode engaged\n"
                if not self.shower:
                    self.shower = True
                    self.initial_temp = self.extract_ave
                    self.initial_fanspeed = self.fanspeed
                    self.set_fanspeed(3)
                    self.humidity += 30
                    self.inhibit = time.time()
                    self.coef_inhibit = time.time()
                    self.shower_initial = self.inhibit
                    self.status_field[0] += 1
                    os.write(
                        ferr,
                        bytes(
                            "Engaged Shower mode at \t" + str(time.ctime()) + "\n",
                            encoding="utf8",
                        ),
                    )

        if (
            len(self.extract_dt_list) != 0
            and numpy.average(self.extract_dt_list) * 60 < 0.25
            and self.shower
            and self.shower_initial - time.time() < -60
        ):
            state = False
            if not self.RH_valid and self.extract_ave <= (self.initial_temp + 0.3):
                state = True
            if self.RH_valid and self.showerRH + 5 > self.humidity:
                if "debug" in sys.argv:
                    self.msg += "RH after shower now OK\n"
                    os.write(
                        ferr,
                        bytes(
                            "Shower mode off RH is ok \t" + str(time.ctime()) + "\n",
                            encoding="utf8",
                        ),
                    )
                state = True
            if state is True:
                if self.shower_initial - time.time() > -120:
                    self.det_limit += 1
                try:
                    os.write(
                        ferr,
                        bytes(
                            "Leaving Shower mode dT: "
                            + str(numpy.max(self.extract) - numpy.min(self.extract))
                            + " \t"
                            + str(time.ctime())
                            + "\n",
                            encoding="utf8",
                        ),
                    )
                    self.msg = "Shower mode off, returning to " + str(
                        self.speeds[self.initial_fanspeed] + "\n"
                    )
                except IOError:
                    pass
                self.shower = False
                self.shower_initial = 0
                turnoff()
        # Shower mode with timeout
        shower_timeout = self.config["systemair"]["control"]["showerTimeout"]
        if self.shower and self.shower_initial - time.time() < -shower_timeout * 60:
            self.shower = False
            os.write(
                ferr,
                bytes(
                    "Shower mode ended on timeout at:\t" + str(time.ctime()) + "\n",
                    encoding="utf8",
                ),
            )
            turnoff()

    # PRINT OUTPUT
    def print_xchanger(self):
        global vers
        tmp = self.system_name
        if self.savecair:
            tmp = "Airiana Savecair"
        tmp += (
            " "
            + time.ctime()
            + " status: "
            + str(int(time.time() - starttime))
            + "("
            + str(self.iter)
            + ")"
            + str(round((time.time() - starttime) / self.iter, 2))
            + " Vers. "
            + vers
            + " ***\n"
        )
        if "debug" in sys.argv:
            try:
                tmp += (
                    "Errors -- Connect: "
                    + str(self.req.connect_errors)
                    + " Checksum: "
                    + str(self.req.checksum_errors)
                    + " Write: "
                    + str(self.req.write_errors)
                    + " Multi: "
                    + str(self.req.multi_errors)
                    + "\n"
                )
                tmp += (
                    "temp sensor state: "
                    + str(bin(self.temp_state))
                    + " Heater:"
                    + str(self.heater)
                    + "\n"
                )
                if self.savecair:
                    tmp += "Unit admin password: " + self.admin_password + "\n"
                tmp += str(sys.argv) + "\n"
            except:
                pass
        try:
            if len(self.extract_dt_list):
                tmp += (
                    "Inlet: <b>"
                    + str("%.2f" % self.inlet_ave)
                    + "C</b>\t\tSupply: "
                    + str("%.2f" % self.supply_ave)
                    + "C\td_in : "
                    + str(round(self.supply_ave - self.inlet_ave, 2))
                    + "C"
                )
                tmp += (
                    "\nExtract: <b>"
                    + str("%.2f" % self.extract_ave)
                    + "C</b>\tExhaust: "
                    + str("%.2f" % self.exhaust_ave)
                    + "C\td_out: "
                    + str(round(self.extract_ave - self.exhaust_ave, 2))
                    + "C\n"
                )
                tmp += (
                    "Extract dT/dt: "
                    + str(round(self.extract_dt, 3))
                    + "degC/min dT/dt: "
                    + str(round(numpy.average(self.extract_dt_list) * 60, 3))
                    + "degC/hr\n\n"
                )
                if "debug" in sys.argv:
                    tmp += (
                        "Tcomp:"
                        + str(self.tcomp)
                        + " at T1:"
                        + str(self.rawdata[0][1])
                        + " coef:"
                        + str(round(self.coef, 4))
                        + " inlet coef:"
                        + str(self.inlet_coef)
                        + " dyn:"
                        + str(self.new_coef)
                        + "\n"
                    )
                    tmp += (
                        "Extract:"
                        + str(self.rawdata[0][1])
                        + "\tInlet:"
                        + str(self.rawdata[0][4])
                        + "\tExhaust:"
                        + str(self.rawdata[0][2])
                        + "\tSupply,pre:"
                        + str(self.rawdata[0][0])
                        + "\tSupply,post:"
                        + str(self.rawdata[0][3])
                        + "\n"
                    )
        except:
            pass
        # self.request.response[1] #EXTRACT
        # self.request.response[2] #EXHAUST
        # self.request.response[0] #Supply pre elec heater
        # self.request.response[3] #Supply post electric heater
        # self.request.response[4] Inlet
        if not self.savecair:
            tmp += (
                "Exchanger Setting: "
                + str(self.exchanger_mode)
                + " State: "
                + self.rotor_states[self.rotor_state]
                + ", Rotor Active: "
                + self.rotor_active
                + "\n"
            )
        else:
            tmp += (
                "Exchanger Rotor speed: "
                + str(self.exchanger_speed)
                + "% set target:"
                + str(self.target)
                + "C exchanger setting: "
                + str(self.exchanger_mode)
                + "\n"
            )
        if self.rotor_active == "Yes" or "debug" in sys.argv:
            tmp += "HeatExchange supply " + str(round(self.supply_power, 1)) + "W \n"
            tmp += (
                "HeatExchange extract "
                + str(round(self.extract_power + self.condensate_compensation, 1))
                + "W\n"
            )
            if "debug" in sys.argv:
                tmp += (
                    "Diff:"
                    + str(round(numpy.average(self.diff_ave), 2))
                    + "% "
                    + str(round(self.energy_diff, 1))
                    + "W\n"
                )
            if "humidity" in sys.argv and "debug" in sys.argv:
                tmp += (
                    "\nCondensation  efficiency: "
                    + str(round(self.cond_eff, 2) * 100)
                    + "%\n"
                )
        if "humidity" in sys.argv:
            if "debug" in sys.argv:
                tmp += (
                    "Static RH low: "
                    + str(round(self.local_humidity, 2))
                    + "% "
                    + str(round(self.prev_static_temp - self.kinetic_compensation, 2))
                    + "C\n"
                )
                if self.RH_valid:
                    tmp += (
                        "Humidity d/dt:"
                        + str(self.hum_list[0] - self.hum_list[-1])
                        + "%\n"
                    )
            if self.RH_valid:
                tmp += (
                    "Relative humidity: "
                    + str(round(self.humidity, 2))
                    + "% Dewpoint: "
                    + str(
                        round(
                            self.airdata_inst.dew_point(
                                self.humidity, float(self.rawdata[0][1]) / 10
                            ),
                            2,
                        )
                    )
                    + "C\n"
                )
        if "sensors" in sys.argv:
            tmp += (
                "Outdoor Sensor:\t "
                + str(self.sensor_temp)
                + "C "
                + str(self.sensor_humid)
                + "% Dewpoint: "
                + str(
                    round(
                        self.airdata_inst.dew_point(
                            self.sensor_humid, self.sensor_temp
                        ),
                        2,
                    )
                )
                + "C\n"
            )
            tmp += (
                "Indoor Sensor:\t "
                + str(self.inside)
                + "C "
                + str(self.inside_humid)
                + "% Dewpoint: "
                + str(
                    round(
                        self.airdata_inst.dew_point(self.inside_humid, self.inside), 2
                    )
                )
                + "C\n"
            )
            tmp += "Sensor exhaust:\t" + str(self.sensor_exhaust) + "\n"
        if "debug" in sys.argv:
            try:
                tmp += "Fanspeed level: " + str(self.fanspeed) + "\n"
                tmp += "Long dt: " + str(self.extract_dt_long) + "\n"
                if self.coef_test_bool:
                    tmp += "In Test:" + str(time.ctime(self.coef_inhibit + 3600)) + "\n"
            except TypeError:
                pass
            tmp += (
                "diff. humidity partial pressure in-out: "
                + str(int(round(self.humidity_diff, 0)))
                + "Pa\n"
            )

        if "humidity" in sys.argv:
            tmp += "Pressure limit: " + str(round(self.indoor_dewpoint, 2)) + "C\n"

        if self.rotor_active == "Yes":
            tmp += (
                "\nElectric power:"
                + str(round(self.electric_power, 0))
                + "W COP:"
                + str(round(self.supply_power / self.electric_power, 1))
                + "\n"
            )
        else:
            tmp += (
                "\nElectric power:"
                + str(round(self.electric_power, 0))
                + "W COP:"
                + str(round(self.loss / self.electric_power, 1))
                + "\n"
            )
        if self.supply_ave < self.extract_ave:
            tmp += "Energy Loss: " + str(round(self.loss, 1)) + "W\n"
        else:
            tmp += "Energy gain: " + str(round(self.loss, 1)) + "W\n"
        tmp += (
            "Loss total: "
            + str(round(self.total_energy / 1000, 3))
            + "kWh Average:"
            + str(round(self.total_energy / ((time.time() - starttime) / 3600), 1))
            + "W\n"
        )
        tmp += "Cooling total: " + str(round(self.cooling / 1000, 3)) + "kWh\n"
        tmp += "Heat gain total: " + str(round(self.gain / 1000, 3)) + "kWh\n"
        tmp += (
            "Unit electric total: "
            + str(round(self.electric_power_sum / 1000, 3))
            + "kWh\n"
        )
        tmp += (
            "Supply:"
            + str(self.sf)
            + " l/s,"
            + str(self.sf_rpm)
            + "rpm\tExtract:"
            + str(self.ef)
            + " l/s,"
            + str(self.ef_rpm)
            + "rpm\n"
        )
        if self.ac_active:
            tmp += "AirCondition unit detected ON\n"
        if self.AC_energy:
            tmp += "AC-energy: " + str(round(self.AC_energy / 1000, 3)) + "kWh\n"
        if self.rotor_active == "Yes" or "debug" in sys.argv:
            tmp += (
                "Temperature Efficiency: "
                + str(round(numpy.average(self.eff_ave), 2))
                + "%\n"
            )
        tmp += (
            "Filter has been installed for "
            + str(math.ceil(self.filter))
            + " days ,"
            + str(self.filter_remaining)
            + "% remaining. \n\n"
        )
        tmp += "Ambient Pressure:" + str(round(self.airdata_inst.press, 2)) + "hPa\n"
        if self.forecast[1] != -1:
            tmp += (
                "Weather forecast (12:00 tomorrow): "
                + str(self.forecast[0])
                + "C "
                + str(self.forecast[1] / 8 * 100)
                + "% cloud cover RH:"
                + str(self.forecast[2])
                + "%\n\n"
            )
        if "Timer" in threading.enumerate()[-1].name:
            tmp += "Ventilation timer on: " + count_down(self.timer, 120 * 60) + "\n"
        if self.shower:
            tmp += "Shower mode engaged at:" + time.ctime(self.shower_initial) + "\n"
        if self.inhibit > 0:
            tmp += "Status change inhibited (" + count_down(self.inhibit, 600) + ")\n"
        if self.press_inhibit > 0:
            tmp += (
                "Pressure change inhibited ("
                + count_down(self.press_inhibit, 1800)
                + ")\n"
            )
        if self.modetoken >= 1:
            tmp += (
                "Exchanger mode change inhibited ("
                + count_down(self.modetoken, 3600)
                + ")\n"
            )
        if self.cool_mode:
            tmp += "Cooling mode is in effect, target is 20.7C extraction temperature\n"
        if not self.monitoring:
            tmp += "\nSystem Automation off\n"

        self.status_field[2] = round((time.time() - starttime) / self.iter, 2)
        self.status_field[6] = round((time.time() - starttime) / 3600, 1)
        tmp += self.msg + "\n"
        tmp = tmp.replace("\n", ";\n")
        tmp = tmp.replace("\t", "'\t")
        # CLEAR SCREEN AND REPRINT
        clear_screen()
        print(tmp)

    # change exchanger mode target is "to", if to = None, flip 0 or 5
    def cycle_exchanger(self, to=None):
        os.write(
            ferr,
            bytes(
                "cycle exchanger to: "
                + str(to)
                + " from "
                + str(self.exchanger_mode)
                + "\t"
                + str(time.ctime())
                + "\n",
                encoding="utf8",
            ),
        )
        if not self.savecair:

            def set_val(val):
                try:
                    self.req.write_register(206, val)
                    print("Setting exchanger to:", val)
                    os.write(
                        ferr,
                        bytes(
                            "write exchanger to: "
                            + str(val)
                            + "\t"
                            + str(time.ctime())
                            + "\n",
                            encoding="utf8",
                        ),
                    )
                    return 1
                except:
                    return 0

            def get_val():
                try:
                    self.req.modbusregister(206, 0)
                    self.current_mode = self.req.response
                    return self.current_mode
                except:
                    pass  # print "read error"

            # Set functions
            try:
                if to is None:
                    self.msg += "manual state change\n"
                    os.write(ferr, bytes("Exchanger mode toggling\n", encoding="utf-8"))
                    self.current_mode = get_val()
                    if self.current_mode > 0:
                        to = 0
                    else:
                        to = 5
                i = 0
                if to == 0:
                    while not set_val(0):
                        # self.msg += "\n write error"
                        time.sleep(0.2)  # set summer mode
                        i += 1
                        if i > 10:
                            os.write(
                                ferr,
                                bytes("Exchanger write failed\n", encoding="utf-8"),
                            )
                else:
                    while not set_val(5):
                        # self.msg +="\n write error"
                        time.sleep(0.2)  # set winter mode
                        i += 1
                        if i > 10:
                            os.write(
                                ferr,
                                bytes("Exchanger write failed\n", encoding="utf-8"),
                            )
                self.modetoken = time.time()
                self.inhibit = (
                    time.time()
                )  # set inhibit time to prevent derivatives sensing when returning
            except:
                # self.msg +=  "\n exit due to error"
                traceback.print_exc(ferr)
            finally:
                self.exchanger_mode = get_val()
        else:
            if to == 0:
                self.req.write_register(2000, 120)
                self.exchanger_mode = 0
            if to == 5:
                self.exchanger_mode = 5
                if not self.cool_mode:
                    self.req.write_register(2000, self.target * 10)
                else:
                    self.req.write_register(2000, 300)

            if to is None:
                self.req.modbusregister(2000, 0)
                if int(self.req.response) == 120:
                    if not self.cool_mode:
                        self.req.write_register(2000, self.target * 10)
                    else:
                        self.req.write_register(2000, 300)
                    self.exchanger_mode = 5
                else:
                    self.req.write_register(2000, 120)
                    self.exchanger_mode = 0
        self.coef_inhibit = (
            time.time()
        )  # set inhibit time to prevent derivatives sensing when returning

    # clear flags as timeouts occur
    def check_flags(self):
        #  Inhibits and limiters
        now = time.time()
        if self.inhibit < now - (60 * 10):
            self.inhibit = 0
        if self.modetoken < now - (60 * 60):
            self.modetoken = 0
        if self.press_inhibit < now - (60 * 30):
            self.press_inhibit = 0
        if self.coef_inhibit < now - (60 * 60):
            self.coef_inhibit = 0
        if (
            self.flowOffset[1] - time.time() < -3600
            and self.flowOffset[0] > 0
            and self.humidity_diff < 350
        ):
            self.flowOffset[0] -= 1
            self.flowOffset[1] = time.time()  # noqa

    # Monitor Logical criteria for state changes on exchanger, pressure, RPMs, forecast
    def monitor(self):
        # Set inhibit on VR400 systems if sudden drop in rpm,
        # this is caused by increased supply flow not initiated by the unit.
        if "VR400" in self.system_name:
            # FAN RPM VR400 monitoring
            if self.sf_rpm < 1550 and self.fanspeed == 2:
                self.inhibit = time.time()
                self.coef_inhibit = time.time()
            if self.sf_rpm < 1000 and self.fanspeed == 1:
                self.coef_inhibit = time.time()
                self.inhibit = time.time()

        # Set target temperature
        self.target_temperature()
        # Exchanger Control
        self.exchanger_control()
        # Forecast related cooling
        self.check_cooling()
        # Dynamic fanspeed control
        self.dynamic_fan_control()
        # Dynamic pressure control
        self.dynamic_pressure_control()

    def exchanger_control(self):
        if self.modetoken <= 0 and self.cool_mode is False:
            if (
                self.extract_ave > self.target
                and self.exchanger_mode != 0
                and self.shower is False
                and self.inlet_ave > 10
            ):
                self.cycle_exchanger(0)
                self.modetoken = time.time()
                os.write(
                    ferr,
                    bytes(
                        "Exchange set to 0 inlet>10C and extr above target \t"
                        + str(time.ctime())
                        + "\n",
                        encoding="utf8",
                    ),
                )

            if (
                self.supply_ave > self.target
                and self.exchanger_mode != 0
                and self.shower is False
            ):
                self.cycle_exchanger(0)
                self.modetoken = time.time()
                os.write(
                    ferr,
                    bytes(
                        "Exchange set to 0 supply>target \t" + str(time.ctime()) + "\n",
                        encoding="utf8",
                    ),
                )

            if (
                self.extract_ave < self.target - 1
                and self.exchanger_mode != 5
                and not self.cool_mode
            ):
                self.cycle_exchanger(5)
                self.modetoken = time.time()
                os.write(
                    ferr,
                    bytes(
                        "1.Exchange set to 5. extract is less than target-1C \t"
                        + str(time.ctime())
                        + "\n",
                        encoding="utf8",
                    ),
                )

            if (
                self.supply_ave < 10
                and self.extract_ave < self.target
                and self.exchanger_mode != 5
                and not self.cool_mode
            ):
                self.cycle_exchanger(5)
                os.write(
                    ferr,
                    bytes(
                        "2.Exchange set to 5 supply<10C and extract< target \t"
                        + str(time.ctime())
                        + "\n",
                        encoding="utf8",
                    ),
                )
                self.modetoken = time.time()
            if (
                self.exchanger_mode != 5
                and self.inlet_ave < 10
                and self.forecast[0] <= 10
                and self.forecast[1] > -1
                and self.fanspeed == 1
                and not self.cool_mode
                and not self.shower
            ):
                self.modetoken = time.time()
                self.cycle_exchanger(5)
                os.write(
                    ferr,
                    bytes(
                        "3.Exchange set to 5 inlet<10C \t" + str(time.ctime()) + "\n",
                        encoding="utf8",
                    ),
                )

    def target_temperature(self):
        if self.inlet_ave < self.config["systemair"]["control"]["targetWinterLimit"]:
            self.target = self.config["systemair"]["control"]["targetTemperature"] + 1
        else:
            self.target = self.config["systemair"]["control"]["targetTemperature"]
        if self.cool_mode:
            self.target = self.config["systemair"]["control"]["coolModeLowTarget"]

    def dynamic_pressure_control(self):
        if not self.shower:
            if (
                self.humidity > 20.0
            ):  # Low humidity limit, restriction to not set margin lower than 20%RH
                if self.savecair or self.RH_valid:
                    self.indoor_dewpoint = self.airdata_inst.dew_point(
                        self.humidity + 5, self.extract_ave
                    )
                else:
                    self.indoor_dewpoint = self.airdata_inst.dew_point(
                        self.humidity + 10, self.extract_ave
                    )
            else:
                self.indoor_dewpoint = (
                    5.0  # lock indoor dew point at 5C for extra safety margin
                )
            if not self.cool_mode:
                if (
                    self.inlet_ave > self.indoor_dewpoint + 0.2
                    and self.pressure_diff != 0
                    and not self.press_inhibit
                    and not self.forecast[1] == -1
                ):
                    self.set_differential(0)
                    if "debug" in sys.argv:
                        self.msg += "Pressure diff to 0%\n"
                if (
                    self.inlet_ave < self.indoor_dewpoint - 0.1
                    and self.pressure_diff != 10
                    and self.inlet_ave < 15
                    and not self.press_inhibit
                ) or (self.forecast[-1] == -1 and self.sf == self.ef):
                    self.set_differential(10)
                    if "debug" in sys.argv:
                        self.msg += "Pressure diff to +10%\n"

    def dynamic_fan_control(self):
        dP_high = self.config["systemair"]["control"][
            "humidityFlowHighPartialPressureDiff"
        ]
        dP_reduce = self.config["systemair"]["control"][
            "humidityFlowReducePartialPressureDiff"
        ]
        if not self.inhibit and not self.shower and not self.cool_mode:
            # dynamic with RH-sensor
            if self.RH_valid:
                if self.fanspeed == 1 and (
                    (
                        self.extract_ave > self.target + 0.6
                        and self.extract_ave - self.supply_ave > 0.1
                    )
                    or self.humidity_diff > dP_high
                ):
                    self.set_fanspeed(2)
                    self.msg += "Dynamic fanspeed 2\n"
                    if self.humidity_diff > dP_high:
                        self.flowOffset = [self.flowOffset[0] + 5, time.time()]
                        os.write(
                            ferr,
                            bytes(
                                "Dynamic fanspeed 2 with RH \t"
                                + str(time.ctime())
                                + "\n",
                                encoding="utf8",
                            ),
                        )
                    else:
                        os.write(
                            ferr,
                            bytes(
                                "Dynamic fanspeed 2 no RH\t" + str(time.ctime()) + "\n",
                                encoding="utf8",
                            ),
                        )
                if self.fanspeed == 2 and (
                    (
                        self.extract_ave < self.target + 0.5
                        and self.extract_ave - self.supply_ave > 0.1
                        and self.humidity_diff < dP_reduce
                        or (
                            self.humidity_diff < dP_reduce - 50
                            and not self.extract_ave > self.target + 0.5
                        )
                    )
                ):
                    self.set_fanspeed(1)
                    if self.humidity_diff < dP_reduce - 50:
                        self.msg += "Dynamic fanspeed 1, Air quality Good\n"
                        os.write(
                            ferr,
                            bytes(
                                "Dynamic fanspeed 1 with RH\t"
                                + str(time.ctime())
                                + "\n",
                                encoding="utf8",
                            ),
                        )
                    else:
                        self.msg += "Dynamic fanspeed 1\n"
                        os.write(
                            ferr,
                            bytes(
                                "Dynamic fanspeed 1 no RH\t" + str(time.ctime()) + "\n",
                                encoding="utf8",
                            ),
                        )
            # dynamic without Rhsensor
            else:
                if (
                    self.fanspeed == 2
                    and self.extract_ave < self.target + 0.5
                    and self.extract_ave - self.supply_ave > 0.1
                ):
                    self.set_fanspeed(1)
                    self.msg += "Dynamic fanspeed 1\n"
                    os.write(
                        ferr,
                        bytes(
                            "Dynamic fanspeed 1 without RH\t"
                            + str(time.ctime())
                            + "\n",
                            encoding="utf8",
                        ),
                    )

                if self.fanspeed == 1 and (
                    self.extract_ave > self.target + 0.6
                    and self.extract_ave - self.supply_ave > 0.1
                ):
                    self.set_fanspeed(2)
                    self.msg += "Dynamic fanspeed 2\n"
                    os.write(
                        ferr,
                        bytes(
                            "Dynamic fanspeed 2 extr > target +0.5C without RH\t"
                            + str(time.ctime())
                            + "\n",
                            encoding="utf8",
                        ),
                    )
            # dynamic 3 if temp is climbing and exchanger is off, and extract is above target +1.2C
            if (
                self.fanspeed == 2
                and self.extract_ave - 0.1 > self.supply_ave
                and (
                    self.extract_ave >= self.target + 1.2
                    or (self.extract_dt_long >= 0.7 and self.inlet_ave > 5)
                )
                and self.exchanger_mode != 5
                and not self.extract_dt_long < -0.2
            ):
                self.set_fanspeed(3)
                self.msg += "Dynamic fanspeed 3\n"
                os.write(
                    ferr,
                    bytes(
                        "Dynamic fanspeed 3 target+1.2C or dt long > 0.7C/h ("
                        + str(self.extract_dt_long)
                        + ")\t"
                        + str(time.ctime())
                        + "\n",
                        encoding="utf8",
                    ),
                )

            # Recover cold air if outside is hotter
            if (
                self.extract_ave < self.supply_ave
                and self.fanspeed != 1
                and self.cool_mode
            ):
                self.set_fanspeed(1)
                self.msg += "Dynamic fanspeed, recover cool air\n"
                os.write(
                    ferr,
                    bytes(
                        "Dynamic fanspeed 1 recover cool air "
                        + str(time.ctime())
                        + "\n"
                        + str(self.extract_ave)
                        + " "
                        + str(self.supply_ave)
                        + "\n",
                        encoding="utf8",
                    ),
                )

            # Lower to fanspeed 2 if long dt is less than -0.5 and outside is less than 12C
            # also lower from 3 when below target+0.8 and not rising above 0.7C/hr
            if (
                self.fanspeed == 3
                and self.extract_ave < self.target + 0.8
                and not self.extract_dt_long > 0.7
            ) or (self.supply_ave < 12 and self.extract_dt_long < -0.5):
                self.set_fanspeed(2)
                self.msg += "Dynamic fanspeed 2 with long dt\n"
                os.write(
                    ferr,
                    bytes(
                        "Dynamic fanspeed 2 with long dt from 3\t"
                        + str(time.ctime())
                        + "\n",
                        encoding="utf8",
                    ),
                )

    def check_cooling(self):
        try:
            if (
                self.forecast[0] > self.cooling_limit
                and self.tomorrows_low[0] > self.house_heat_limit
                and self.integral_forcast > 0
                and self.cool_mode is False
                and self.extract_ave
                > self.config["systemair"]["control"]["coolModeLowTarget"]
                or self.inlet_ave > self.target + 2
                and not self.cool_mode
            ):
                self.msg += "Cooling engaged\n"
                if self.pressure_diff != 0:
                    self.set_differential(0)
                if self.savecair:
                    self.req.write_register(
                        1407, self.config["systemair"]["savecair"]["sfMaxFlow"]
                    )
                    self.req.write_register(
                        1406, self.config["systemair"]["savecair"]["efMaxFlow"]
                    )

                if self.exchanger_mode != 0:
                    self.cycle_exchanger(0)
                self.set_differential(0)
                self.cool_mode = True
                write_log("Cooling activated.")
                self.set_fanspeed(3)
        except:
            os.write(
                ferr,
                bytes(
                    "Forecast cooling error "
                    + str(self.integral_forcast)
                    + " "
                    + str(time.ctime())
                    + "\n",
                    encoding="utf8",
                ),
            )
        if (
            self.cool_mode
            and not self.inhibit
            and not self.shower
            and not self.ac_active
        ):
            if (
                self.extract_ave
                < self.config["systemair"]["control"]["coolModeLowTarget"]
                and self.fanspeed != 1
            ):
                self.set_fanspeed(1)
                self.msg += "Cooling complete\n"
                write_log("Cooling complete 20.7C reached.")

            if self.fanspeed == 3 and (
                self.supply_ave
                < self.config["systemair"]["control"]["coolModeLowLimit"]
                and self.extract_ave < 22
            ):
                self.set_fanspeed(2)
                self.msg += "Cooling reduced\n"
                os.write(
                    ferr,
                    bytes(
                        "Cooling reduced to medium, supply below 12C \t"
                        + str(time.ctime())
                        + "\n",
                        encoding="utf8",
                    ),
                )

            if (
                self.fanspeed == 2
                and self.supply_ave
                > self.config["systemair"]["control"]["coolModeLowLimit"] + 1
            ):
                self.set_fanspeed(3)
                self.msg += "Cooling returned to High.\n"
                os.write(
                    ferr,
                    bytes(
                        "Cooling returned to high from medium, supply above required level. \t"
                        + str(time.ctime())
                        + "\n",
                        encoding="utf8",
                    ),
                )

            if (
                self.fanspeed == 1
                and self.extract_ave
                > self.config["systemair"]["control"]["coolModeLowTarget"] + 0.2
                and self.extract_ave + 0.1 > self.inlet_ave
            ):
                self.set_fanspeed(3)
                self.msg += "Cooling returned to High, indoor is hotter than outside.\n"
                write_log(
                    f"Cooling returned to high, indoor is hotter than outside. {self.extract_ave}, {self.inlet_ave}, {self.fanspeed}"
                )

            if (
                self.inlet_ave + 0.1 > self.extract_ave
                and self.fanspeed != 1
                and self.extract_ave > 21
            ):
                self.set_fanspeed(1)
                self.msg += "No cooling possible due to temperature conditions\n"
                write_log(
                    "Cooling will wait, will try to recycle cold air by low fanspeed."
                )

            try:
                if (
                    self.integral_forcast < 0
                    and time.localtime().tm_hour > 12
                    and self.inlet_ave
                    < self.config["systemair"]["control"]["targetTemperature"] + 2
                ):
                    self.cool_mode = False
                    write_log("Cooling mode turned off.")
                    if self.savecair and self.ef == 100:
                        self.req.write_register(
                            1407, self.config["systemair"]["savecair"]["sfHighFlow"]
                        )
                        self.req.write_register(
                            1406, self.config["systemair"]["savecair"]["efHighFlow"]
                        )
            except ValueError:
                write_log("Forecast error.")

    # Get the active forecast
    def get_forecast(self):
        # Weather forecast modes
        self.forecast = [-1, -1, -1]
        try:
            forcast = os.popen("./forcast2.0.py tomorrow").readlines()
            # First line
            forcast1 = forcast[0].split(" ")
            forcast2 = forcast[1].split(" ")
            self.forecast[0] = float(forcast1[0])
            self.forecast[1] = float(forcast1[1])
            # Second line
            self.forecast[2] = float(forcast2[0])
            # get tomorrows-low values
            tomorrows_low = (
                os.popen("./forcast2.0.py tomorrows-low").read()[:-1].split(" ")
            )
            for index in range(len(tomorrows_low)):
                self.tomorrows_low[index] = float(tomorrows_low[index])  # noqa
            # print self.tomorrows_low
            # get integral for coming days
            self.integral_forcast = float(
                os.popen("./forcast2.0.py integral " + str(self.cooling_limit)).read()
            )
            # print self.integral_forcast
            if os.stat("./RAM/forecast.json").st_ctime < time.time() - 3600 * 24:
                raise Exception("FileError: file too old")
        except IOError:
            traceback.print_exc(ferr)
            self.msg += "error getting forecast.(io error)\n" + str(self.forecast)
            self.forecast = [-1, -1, -1]
        except IndexError:
            traceback.print_exc(ferr)
            self.msg += "error getting forecast.(index error)\n" + str(self.forecast)
        # self.forecast=[-1,-1]
        except FileError:
            traceback.print_exc(ferr)
            self.msg += "error getting forecast.(file too old)\n" + str(self.forecast)

    # set the fan pressure diff
    def set_differential(self, percent):
        os.write(
            ferr,
            bytes(
                "Pressure difference set to: "
                + str(percent)
                + "%\t"
                + str(time.ctime())
                + "\n",
                encoding="utf8",
            ),
        )
        self.coef_inhibit = time.time()
        if percent > 20:
            percent = 20
        if percent < -20:
            percent = -20
        if not self.savecair and not self.shower:
            if "debug" in sys.argv:
                self.msg += "start pressure change " + str(percent) + "\n"
            self.req.modbusregister(103, 0)  # nominal supply flow
            # print "sf_nom is", self.request.response
            target_flow = int(
                self.req.response + self.req.response * (float(percent) / 100)
            )
            # print "to set ef_no to",target
            self.req.write_register(104, target_flow)  # nominal extract flow
            self.req.modbusregister(104, 0)  # nominal supply flow
            if self.req.response == target_flow:
                self.press_inhibit = time.time()
            if "debug" in sys.argv:
                if self.req.response == target_flow:
                    self.msg += "supply flow change completed \n"
            high_flow = self.config["systemair"]["legacy"][self.system_name][
                "efHighFlow"
            ]
            if percent < 0:
                high_flow += high_flow * float(percent) / 100
            # print "high should be extract:", int(high_flow)
            self.req.write_register(106, int(high_flow))  # reset high extract
            # raw_input(" diff set done")
            if "debug" in sys.argv:
                self.msg += "change completed\n"
            self.press_inhibit = time.time()

        elif self.savecair and not self.shower:
            self.press_inhibit = time.time()

            for each in range(1400, 1408, 2):
                self.req.modbusregister(each, 0)
                # raw_input(str(percent)+"% "+str(each)+"-"+str(int(self.request.response*(1+(float(percent)/100)))))
                self.req.write_register(each + 1, int(self.req.response + percent))
        if not self.savecair and not self.shower and self.system_name == "VTR300":
            if "debug" in sys.argv:
                self.msg += "start pressure change " + str(percent) + "\n"

            self.req.modbusregister(101, 0)  # LOW supply flow
            target_flow = int(
                self.req.response + self.req.response * (float(percent) / 100)
            )
            self.req.write_register(102, target_flow)  # LOW extract flow

            self.req.modbusregister(103, 0)  # nominal supply flow
            target_flow = int(
                self.req.response + self.req.response * (float(percent) / 100)
            )
            self.req.write_register(104, target_flow)  # nominal extract flow

            self.req.modbusregister(106, 0)  # nominal supply flow
            target_flow = int(
                self.req.response - self.req.response * abs(float(percent) / 100)
            )
            self.req.write_register(105, target_flow)  # nominal extract flow

            if self.req.response == target_flow:
                self.press_inhibit = time.time()
            if "debug" in sys.argv:
                self.msg += "change completed\n"
        self.pressure_diff = percent
        self.update_airflow()

    def check_flow_offset(self):
        """Set base flow rate with an offset to regulate humidity in a more clever manner.
        the offset only applies when in low speed pushes the fanspeed slightly higher
        when there are conscutive transitions up due to moisture."""
        if self.flowOffset[0] > 20:  # Maximum offset allowed
            self.flowOffset[0] = 20
        if self.savecair:
            base = (
                self.config["systemair"]["savecair"]["efLowFlow"] + self.pressure_diff
            )
            self.req.modbusregister(1403, 0)
            ef = int(self.req.response)
            if (
                self.fanspeed == 1
                and ef != base + self.flowOffset[0]
                and not self.shower
                and not self.cool_mode
            ):
                self.req.write_register(1403, base + self.flowOffset[0])
                self.req.write_register(
                    1402,
                    self.config["systemair"]["savecair"]["sfLowFlow"]
                    + self.flowOffset[0],
                )
                os.write(
                    ferr,
                    bytes(
                        "Extract flow offset to: "
                        + str(ef)
                        + "/"
                        + str(self.flowOffset[0])
                        + "/"
                        + str(base)
                        + "\t"
                        + str(time.ctime())
                        + "\n",
                        encoding="utf8",
                    ),
                )
                self.ef = base + self.flowOffset[0]
                self.sf = self.sf_base + self.flowOffset[0]
        if self.has_RH_sensor and not self.savecair:
            base = (
                self.config["systemair"]["legacy"][self.system_name]["efBaseFlow"]
                + self.pressure_diff
            )
            if (
                self.fanspeed == 1
                and self.ef != base + self.flowOffset[0]
                and not self.shower
            ):
                self.req.write_register(
                    102, base + self.flowOffset[0]
                )  # Extract flow with offset at low.
                #  No need to set supply flow it's calculated by the unit as the ratio of sf/ef from mid lvl flow.
                os.write(
                    ferr,
                    bytes(
                        "Updated extract flow offset to: "
                        + str(self.flowOffset[0])
                        + "\t"
                        + str(time.ctime())
                        + "\n",
                        "utf8",
                    ),
                )
                self.ef = base + self.flowOffset[0]
                self.sf = self.sf_base + self.flowOffset[0]

    # get and set the local low/static temperature and humidity
    def get_local(self):
        if self.prev_static_temp == 8:  # 8 Is initialization value.
            if os.path.lexists("RAM/latest_static"):
                try:
                    self.prev_static_temp = float(
                        os.popen("cat RAM/latest_static").readline().split("\n")[0]
                    )
                except:
                    self.prev_static_temp = self.inlet_ave
                    os.write(
                        ferr,
                        bytes(
                            "Unable to load latest_static temp\t"
                            + str(time.ctime())
                            + "\n",
                            encoding="utf8",
                        ),
                    )
            else:
                fd = os.open("RAM/latest_static", os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
                os.write(fd, bytes(str(self.prev_static_temp), encoding="utf8"))
                os.close(fd)

        out = os.popen("./humid.py " + str(self.extract_ave)).readline()
        sat_point = out.split(" ")
        wthr = [-1, -1, -1]
        sun = 0
        try:
            saturation_point = float(sat_point[1])
        except TypeError:
            os.write(
                ferr,
                bytes(
                    "Unable to cast 24h low temp "
                    + str(sat_point)
                    + "\t"
                    + str(time.ctime())
                    + "\n",
                    encoding="utf8",
                ),
            )
            os.system(f"echo {self.inlet_ave} > ./RAM/latest_static")
            saturation_point = self.inlet_ave
        except IndexError:
            os.write(
                ferr,
                bytes(
                    "Saturation point was unavailable. "
                    + str(sat_point)
                    + "\t"
                    + str(time.ctime())
                    + "\n",
                    encoding="utf8",
                ),
            )
            saturation_point = self.inlet_ave
        # if no forecast is avail
        if self.forecast[1] != -1:
            try:
                sun = int(os.popen("./forcast2.0.py sun").readlines()[0].split(":")[0])
            except ValueError:
                sun = 7
                os.write(
                    ferr,
                    bytes(
                        "Unable set weather or sunrise "
                        + "\t"
                        + str(time.ctime())
                        + "\n",
                        encoding="utf8",
                    ),
                )
            except IndexError:
                os.write(
                    ferr,
                    bytes(
                        "Forcast does not return proper data."
                        + " "
                        + str(time.ctime())
                        + "\n",
                        encoding="utf8",
                    ),
                )

        else:
            os.write(
                ferr,
                bytes(
                    "forecast unavailible. "
                    + " "
                    + str(self.forecast)
                    + str(time.ctime())
                    + "\n",
                    encoding="utf8",
                ),
            )
            sun = 7

        if self.prev_static_temp >= self.inlet_ave:
            self.local_humidity = self.moisture_calcs(
                self.inlet_ave - self.kinetic_compensation
            )  # if 24hr low is higher than current temp
        else:
            self.local_humidity = self.moisture_calcs(
                self.prev_static_temp - self.kinetic_compensation
            )  # if 24hr low is lower than current temp

        if (
            self.prev_static_temp + self.kinetic_compensation > self.inlet_ave
        ):  # Reduce the effect of kinet_comp when near inlet_ave
            self.prev_static_temp = self.inlet_ave - self.kinetic_compensation
            self.kinetic_compensation = self.kinetic_compensation * 0.98

        if (
            time.localtime().tm_hour == sun
            and time.localtime().tm_min < 5
            or self.prev_static_temp == 8
        ):
            self.kinetic_compensation = 0
            if self.forecast[1] != -1:
                try:
                    weather = os.popen("./forcast2.0.py -f wind/fog ").read().split(" ")
                    fog_cover = float(weather[-1])
                    wind = float(weather[-2])
                    if wind > 2:  # compensate for windy conditions
                        self.kinetic_compensation += wind / 16
                    if fog_cover > 75:  # if fog over 75% compensate at 0
                        self.kinetic_compensation = 0
                except ValueError:
                    os.write(
                        ferr,
                        bytes(
                            "Unable to update morning low with wind/fog compensation"
                            + "\t"
                            + str(time.ctime())
                            + "\n",
                            "utf-8",
                        ),
                    )

            self.prev_static_temp = (
                self.inlet_ave
            )  # Set inlet static low to current inlet ave.
            self.prev_static_temp -= (
                self.kinetic_compensation
            )  # Compensate for low alt. atmospheric mixing.
            fd = os.open("RAM/latest_static", os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
            os.write(
                fd,
                bytes(
                    str(self.prev_static_temp - self.kinetic_compensation),
                    encoding="utf8",
                ),
            )  # Write2file
            os.close(fd)

    # print Json data to air.out for third party processing
    def print_json(self):
        tmp = ""
        try:
            json_vars = {
                "extract": f"{float(self.extract_ave)}",
                "coolingMode": str(self.cool_mode).lower(),
                "supply": f"{float(self.supply_ave)}",
                "sf": self.sf,
                "ef": self.ef,
                "exhaust": f"{float(self.exhaust_ave)}",
                "autoON": str(self.monitoring).lower(),
                "shower": str(self.shower).lower(),
                "rotorSpeed": self.exchanger_speed,
                "sfRPM": self.sf_rpm,
                "energyXfer": f"{float(self.loss)}",
                "efficiency": f"{float(self.eff)}",
                "efRPM": self.ef_rpm,
                "name": self.system_name,
                "filterPercentRemaining": self.filter_remaining,
                "pressure": self.airdata_inst.press,
                "filterInstalledDays": self.filter,
                "rotorActive": str(self.rotor_active).lower(),
                "elecHeater": self.heater,
                "inlet": f"{float(self.inlet_ave)}",
                "electricPower": self.electric_power,
                "electricPowerTotal": round(self.electric_power_sum, 2),
                "referenceHumidity": round(self.local_humidity, 1),
            }
            if len(self.hum_list) and self.RH_valid:
                json_vars.update({"measuredHumidity": round(self.hum_list[0], 1)})
            else:
                json_vars.update({"calculatedHumidity": round(self.hum_list[0], 1)})
            tmp = str(json_vars).replace("'", '"')
        except IndexError:
            os.write(
                ferr,
                bytes(f"json-writer humidity IndexError {self.hum_list}\n", "utf-8"),
            )
        os.ftruncate(air_out, 0)
        os.lseek(air_out, 0, os.SEEK_SET)
        os.write(air_out, bytes(tmp, encoding="utf8"))

    def check_coef(self):
        """CHECK IF COEF IS AVAILABLE AND IF NOT in inhibit and current fans are at 1 ,
        run a set of max speed fans to generate new coef data
        """
        try:
            self.coef_dict[int(self.get_coef_mode())][
                int(self.extract_ave - self.inlet_ave)
            ]
        except KeyError:
            if (
                self.get_fanspeed() == 1
                and not self.inhibit
                and not self.coef_inhibit
                and self.monitor
                and not self.cool_mode
            ):
                os.write(
                    ferr,
                    bytes(
                        "Starting coefAI test @  "
                        + str(int(self.extract_ave - self.inlet_ave))
                        + "C\t"
                        + str(time.ctime())
                        + "\n",
                        "utf-8",
                    ),
                )
                self.set_fanspeed(3)
                self.coef_debug()


def system_start():
    """This is run once at startup before the main iteration loop"""
    global starttime
    clear_screen()
    print("First PASS;")
    print("Updating fan-speeds;")
    device.system_setup()
    device.update_airflow()
    sys.stdout.flush()
    print("Updating fans rpms;")
    device.update_fan_rpm()
    sys.stdout.flush()
    print("Reading Filter Status;")
    device.get_filter_status()
    sys.stdout.flush()
    print("Reading internal heater state;")
    device.get_heater()
    sys.stdout.flush()
    print("Retrieving weather forecast;")
    device.get_forecast()
    sys.stdout.flush()
    print("Generating historical graphs;")
    if "debug" in sys.argv:
        os.system("nice ./grapher.py debug &")
    else:
        os.system("nice ./grapher.py &")
    sys.stdout.flush()
    if "debug" in sys.argv:
        print("Checking for sensor data;")
        update_sensors()
        sys.stdout.flush()
    print("Updating current rotor status;")
    device.get_rotor_state()
    print("Setting up coefficients;")
    sys.stdout.flush()
    if device.rotor_active == "No":
        device.coef = 0.09
        device.inlet_coef = 0.07
    else:
        device.coef = 0.09
        device.inlet_coef = 0.07
    print("Read initial temperatures;")
    device.update_temps()
    device.update_xchanger()
    # Check if the exhaust sensor is working
    if "humidity" in sys.argv:
        device.get_RH()
        # device.humidity = device.moisture_calcs(10.0)
        device.get_local()
    sys.stdout.flush()
    starttime = time.time()
    print("System started:", time.ctime(starttime), ";")


def forced_ventilation(dev):
    thread_counter = 0
    for thread in threading.enumerate():
        if thread.name == "MonitorTimer" and thread.is_alive():
            thread.cancel()  # noqa the class is actually threading.Timer
            thread_counter += 1

        if thread.name == "Timer" and thread.is_alive():
            thread.cancel()  # noqa the class is actually threading.Timer
            dev.msg += "Removed Forced ventilation timer\n"
            os.write(
                ferr,
                bytes(
                    bytes(
                        "Vent Timer canceled at:\t" + str(time.ctime()) + "\n",
                        encoding="utf8",
                    )
                ),
            )
            dev.set_monitoring(True)
            dev.monitor()
            dev.timer = False
            dev.inhibit = 0
            thread_counter += 1
        if thread_counter == 2:
            return

    os.write(
        ferr,
        bytes("Vent timer started at:\t" + str(time.ctime()) + "\n", encoding="utf8"),
    )
    prev = dev.fanspeed
    dev.set_fanspeed(3)
    dev.set_monitoring(False)
    dev.msg += "Forced Ventilation on timer\n"
    tim2 = threading.Timer(60.0 * 120 + 2, dev.set_monitoring, [True])
    tim2.name = "MonitorTimer"
    tim2.start()
    tim = threading.Timer(60.0 * 120, dev.reset_fanspeed, [prev])
    tim.name = "Timer"
    dev.timer = time.time()
    dev.inhibit = 0
    tim.start()


def fireplace_mode(dev):
    try:
        thread_counter = 0
        for thread in threading.enumerate():
            if thread.name == "fire" and thread.is_alive():
                thread.cancel()  # noqa the class is actually threading.Timer.
                dev.msg += "Removed fire starter ventilation timer\n"
                os.write(
                    ferr,
                    bytes(
                        bytes(
                            "Fire timer canceled at:\t" + str(time.ctime()) + "\n",
                            encoding="utf8",
                        )
                    ),
                )
                dev.set_monitoring(True)
                thread_counter += 1
            if thread.name == "fireMonitor" and thread.is_alive():
                thread.cancel()  # noqa the class is actually threading.Timer.
                thread_counter += 1
            if thread_counter == 2:
                return

        os.write(
            ferr, bytes("Fire start at:\t" + str(time.ctime()) + "\n", encoding="utf8")
        )
        dev.set_monitoring(False)
        prev = dev.fanspeed
        dev.set_differential(-10)
        dev.press_inhibit = 0
        dev.set_fanspeed(3)
        dev.msg += "Fire start Ventilation on timer\n"
        tim2 = threading.Timer(60.0 * 10 + 2, dev.set_monitoring, [True])
        tim2.name = "fireMonitor"
        tim2.start()
        tim = threading.Timer(60.0 * 10, dev.reset_fanspeed, [prev])
        tim.name = "fire"
        tim.start()
    except IndexError:
        traceback.print_exc(ferr)
        print("fire starter error")


# Init base class and run main loop
if __name__ == "__main__":
    # Init request class for communication
    req = Request()
    req.setup(unit, mode)
    device = Systemair(req, config_file)
    os.write(ferr, bytes("System started\t" + str(time.ctime()) + "\n", "utf8"))
    req.modbusregister(12543, 0)  # test for self.savecair extended address range
    if device.system_name == "VR400" and req.response != "no data":
        device.savecair = True
        device.system_name = "savecair"
        conversion_table = {}
        device.status_field[3] = "savecair"
        device.average_limit = 3400
        os.write(ferr, bytes("savecair unit set\n", "utf8"))
    monitoring = True
    reset_fans = False

    input_buffers = ""
    print("Going in for first PASS;")
    try:
        # First pass only
        system_start()
        # Main loop processing
        while Running:
            # do temps,energy and derivatives
            device.update_temps()
            device.update_xchanger()
            device.derivatives()
            # Execution tree, execution steps unique if prime
            # check states and flags
            if device.iter % 3 == 0:
                if "debug" in sys.argv:
                    os.system('echo "3" >./RAM/exec_tree')
                device.check_flags()
                if (
                    device.system_name == "VTR300"
                    or device.system_name == "VSR300"
                    or device.system_name == "savecair"
                    or device.use_calc_exhaust
                ):
                    device.calc_exhaust()
                device.check_ac_mode()
                if reset_fans:
                    device.set_fanspeed(reset_fans)
                    reset_fans = False
            # update moisture
            if device.iter % 5 == 0:
                if "debug" in sys.argv:
                    os.system('echo "5" >./RAM/exec_tree')
                if device.monitoring:
                    device.monitor()
                    device.shower_detect()
                device.print_json()  # Print to json

                if (
                    "humidity" in sys.argv
                    and (
                        device.system_name not in device.has_RH_sensor
                        or not device.RH_valid
                    )
                    or "debug" in sys.argv
                ):
                    device.moisture_calcs()
                if (
                    "humidity" in sys.argv
                    and device.system_name in device.has_RH_sensor
                ):
                    device.get_RH()  ## Read sensor humidity
            # update fans
            if device.iter % 7 == 0:
                if "debug" in sys.argv:
                    os.system('echo "7" >./RAM/exec_tree')
                device.update_fan_rpm()
                device.check_config()

            # debug specific sensors and temp probe status
            if device.iter % 11 == 0:
                if "debug" in sys.argv:
                    os.system('echo "11" >./RAM/exec_tree')
                device.get_rotor_state()
                device.update_fanspeed()
                if "debug" in sys.argv:
                    update_sensors()
                    device.get_temp_status()
                if device.coef_test_bool:
                    device.coef_debug()
                if "daemon" in sys.argv:
                    device.print_xchanger()  # Print to screen

            # refresh static humidity
            if device.iter % 79 == 0:
                if "debug" in sys.argv:
                    os.system('echo "79" >./RAM/exec_tree')
                device.update_airflow()
                device.check_flow_offset()
                device.get_heater()
            # if "humidity" in sys.argv and (device.system_name not in device.has_RH_sensor or not device.RH_valid):
            # calc local humidity and exec logger
            if device.iter % math.floor(120 / device.avg_frame_time) == 0:
                device.msg = ""
                logger()
            # send local tempt to temperatur.nu
            if device.iter % 251 == 0:
                if "debug" in sys.argv:
                    os.system('echo "251" >./RAM/exec_tree')
            # send ping status, generate graphs and refresh airdata instance.
            if device.iter % 563 == 0:
                if "debug" in sys.argv:
                    os.system('echo "563" >./RAM/exec_tree')
                device.update_airdata_instance()
                device.check_coef()
                if "debug" in sys.argv:
                    os.system("nice ./grapher.py debug moisture & >>/dev/null")
                elif device.has_RH_sensor:
                    os.system("nice ./grapher.py hasRH & >> /dev/null")
                else:
                    os.system("nice ./grapher.py  & >> /dev/null")
                if "ping" in sys.argv:
                    device.status_field[7] = round(device.inlet_ave, 2)
                    device.status_field[8] = round(device.extract_ave, 2)
                    device.status_field[9] = round(device.ef, 2)
                    device.status_field[10] = round(device.humidity, 2)
                    device.status_field[11] = device.monitoring
                    device.status_field[12] = device.cool_mode
                    device.status_field[13] = round(device.supply_ave, 2)
                    device.status_field[14] = round(device.exhaust_ave, 2)
                    device.status_field[15] = round(device.pressure_diff, 2)
                    device.status_field[16] = round(device.det_limit, 0)
                    report_alive()

                if "humidity" in sys.argv:
                    device.get_local()
                if "temperatur.nu" in sys.argv:
                    os.system(
                        "wget -q -O ./RAM/temperatur.nu  \
                        http://www.temperatur.nu/rapportera.php?hash=42bc157ea497be87b86e8269d8dc2d42\\&t="
                        + str(round(device.inlet_ave, 1))
                        + " &"
                    )

            # check for updates
            if device.iter % int(3600 / 0.2) == 0:
                if "debug" in sys.argv:
                    os.system('echo "7200s" >./RAM/exec_tree')
                os.system("./backup.py &")
                os.system("cp ./RAM/data.log ./data.save")
            # restart HTTP SERVER get filter status, reset IP on buttons page, update weather forecast
            if device.iter % (int(3600 * 2 / device.avg_frame_time)) == 0:
                device.get_filter_status()
                os.system("./http &")
                os.chdir("./public")
                os.system("./ip-replace.sh &")  # reset ip-addresses on buttons.html
                os.system("./ip-util.sh &")  # reset ip-addresses on buttons.html
                os.chdir("..")
                device.get_forecast()
                if device.status_field[0] > 0:
                    device.status_field[
                        0
                    ] -= 1  # remove one shower token from bucket every 2 hrs.
            device.iter += 1

            """Selection menu if not daemon"""
            if "daemon" not in sys.argv:
                device.print_xchanger()  # Print to screen
                timeout = 0.1
                print(
                    "\n"
                    "	CTRL-C to exit,\n"
                    "1: Toggle auto Monitoring	 6: Not implemented\n"
                    "2: Toggle fanspeed		 7: Set flow differential\n"
                    "3: Print all device attributes	 8: Run fans for 15min at Max\n"
                    "4: Display link settings	 9: Run the Firestarter mode\n"
                    "5: toggle flowOffset		 0: cycle winter/summer mode\n"
                    "10: Not implemented		11: Toggle electric heater\n"
                    "12: Start shower mode		13: Engage Cool mode\n"
                    "14: Enagage AI test\n"
                    "		enter commands:",
                    end=" ",
                )
            else:
                timeout = 0.05
            try:
                sys.stdout.flush()
            except IndexError:
                pass
            data = -1
            sender = ""
            input_buffers = select.select([sys.stdin, cmd_socket], [], [], timeout)[0]
            try:
                if cmd_socket in input_buffers:
                    try:
                        data, sender = cmd_socket.recvfrom(128)
                        data = int(data.decode("utf-8"))
                    except ValueError:
                        data = None
                        sender = "invalid"
                    except socket.error:
                        pass
                    try:
                        log = (
                            'echo "'
                            + str(time.ctime())
                            + ":"
                            + str(sender)
                            + ":"
                            + str(data)
                            + '" >> netlog.log &'
                        )
                        os.write(
                            ferr,
                            bytes(f"{sender}:{data} at\t{time.ctime()}\n", "utf-8"),
                        )
                        os.system(log)
                    except:
                        device.msg += "net log error\n"
                        traceback.print_exc()

                if "daemon" not in sys.argv and sys.stdin in input_buffers:
                    try:
                        data = sys.stdin.readline()
                        data = int(str(data))
                    except:
                        device.msg += "stdin error\n"
                        traceback.print_exc(ferr)

                if data != -1:
                    if data == 1:  # toggle auto monitor on/off
                        device.monitoring = (
                            not device.monitoring
                        )  # Toggle monitoring on / off
                        # Reset all automation modes.
                        device.inhibit = 0
                        device.press_inhibit = 0
                        device.coef_inhibit = 0
                        device.modetoken = 0
                        device.shower_mode = False
                        device.cooling = False
                    if data == 2:  # increment fanspeed
                        device.set_fanspeed(device.fanspeed + 1)
                        if "daemon" not in sys.argv:
                            print("set on 2")
                            input("press enter to resume")
                    if data == 3:  # print device attributes
                        clear_screen()
                        device.print_attributes()
                        sys.stdout.flush()
                        time.sleep(10)
                        if "daemon" not in sys.argv:
                            input("press enter to resume")
                    if data == 4:  # display modbus link settings
                        display_settings()
                        sys.stdout.flush()
                        time.sleep(10)
                        if "daemon" not in sys.argv:
                            input("press enter to resume")
                        else:
                            print("break")
                        recent = 4
                    if data == 5:
                        if device.flowOffset[0] == 0:
                            device.flowOffset[0] = 20
                        else:
                            device.flowOffset[0] = 0
                    if data == 6:  #
                        if "daemon" not in sys.argv:
                            input("press enter to resume")
                        else:
                            print("break")

                    if data == 7:  # set pressure differential
                        if "daemon" not in sys.argv:
                            inp = int(input("set differential pressure(-20% -> 20%):"))
                        else:
                            if device.ef == device.sf:
                                inp = 10
                            else:
                                inp = 0
                        device.set_differential(inp)

                    if data == 8:  # toggle forced vent timer
                        forced_ventilation(device)

                    if data == 9:  #
                        fireplace_mode(device)
                    if data == 0:  # cycle exchanger mode
                        device.cycle_exchanger(None)
                        device.modetoken = time.time()
                    if data == 96:
                        clear_screen()
                        device.msg += "Fanspeed to Off\n"
                        device.set_fanspeed(0)
                    if data == 97:  # set low fanspeed
                        clear_screen()
                        device.msg += "Fanspeed to Low\n"
                        device.set_fanspeed(1)
                    if data == 98:  # set mid fanspeed
                        device.set_fanspeed(2)
                        device.msg += "Fanspeed to Norm\n"
                    if data == 99:  # set high fanspeed
                        device.set_fanspeed(3)
                        # device.coef_debug()
                        device.msg += "Fanspeed to High\n"
                    if data == 11:  # Toggle electric heater
                        if device.heater == 0:
                            target = 2
                        else:
                            target = 0
                        device.set_heater(target)
                    if data == 12:  # toggle shower mode
                        device.shower = not device.shower
                        if device.shower:
                            device.initial_temp = device.extract_ave - 1
                            device.initial_fanspeed = 1
                            device.shower_initial = time.time()
                            device.showerRH = device.humidity - 10
                            device.set_fanspeed(2)
                    if data == 13:
                        device.cool_mode = not device.cool_mode
                    if data == 14:
                        device.set_fanspeed(3)
                        device.coef_debug()
            except TypeError as e:
                os.write(
                    ferr,
                    bytes(
                        "TypeError occurred at:\t" + str(time.ctime()) + "\n" + str(e),
                        encoding="utf8",
                    ),
                )
            except ValueError:
                os.write(
                    ferr,
                    bytes(
                        "ValueError occurred at:\t" + str(time.ctime()) + "\n",
                        encoding="utf8",
                    ),
                )
            except IOError:
                os.write(
                    ferr,
                    bytes(
                        "Connection to the systemAir unit has been lost at:\t"
                        + str(time.ctime())
                        + "\n",
                        encoding="utf8",
                    ),
                )
    except TypeError:
        traceback.print_exc(ferr)
    except ControlledExit:
        exit(0)
    except:  # noqa
        traceback.print_exc(ferr)
    syslog.syslog("Airiana-core not running, at end of line... this is bad")
