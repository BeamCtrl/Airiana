#!/usr/bin/python3
# -*- coding: utf-8 -*-
###################IMPORTS
vers = "10.3"
import airdata
import numpy
import select
import threading
import os
import traceback
import time
import sys
import signal
import math
import pickle
import syslog
from request import Request


numpy.seterr('ignore')
#############################

Running = True
savecair = False
mode = "RTU"
holdoff_t = time.time()
if "TCP" in sys.argv:
    mode = "TCP"


# Register cleanup
def exit_callback(self, arg):
    print("Gracefull shutdown\nexiting on signal", self)
    sys.stdout.flush()
    now = device.iter
    shutdown = time.time()
    Running = False
    os.system("cp ./RAM/data.log ./data.save")
    if threading.enumerate()[-1].name == "Timer":
        threading.enumerate()[-1].cancel()
    cmd_socket.close()
    os.write(ferr, bytes("Exiting in a safe way" + "\n", encoding='utf8'))
    # Sleep untill one iteration has passed or we've been in shutdown for 3 sec.
    while  (device.iter < now) or (time.time() < shutdown + 3):
        time.sleep(0.1)
    sys.exit(0)

signal.signal(signal.SIGTERM, exit_callback)
signal.signal(signal.SIGINT, exit_callback)

try:

    syslog.syslog("file is " + __file__)
    path = os.path.abspath(__file__).replace("airiana-core.py", "")
    syslog.syslog("changing to " + path)
    os.chdir(path)

except:
    syslog.syslog("unable to chdir to: " + path)
    exit(22)

# exec util fnctns
os.chdir(path + "/public")
os.system("./ip-replace.sh")  # reset ip-addresses on buttons.html
os.chdir(path)
os.system("./http &> /dev/null")  ## START WEB SERVICE
listme = []
## cpy saved data to RAM ##
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
# Setup deamon env
ferr = os.open("./RAM/err", os.O_WRONLY | os.O_CREAT)
air_out = os.open("./RAM/air.out", os.O_WRONLY | os.O_CREAT)
if "daemon" in sys.argv:
    fout = os.open("./RAM/out", os.O_WRONLY | os.O_CREAT)
    os.dup2(fout, sys.stdout.fileno())
    print("Output redirected to file;")
    # if not "keep-log" in sys.argv:
    #	os.system("rm -f ./RAM/err")
    #	ferr = os.open("./RAM/err",os.O_WRONLY|os.O_CREAT)

    os.dup2(ferr, sys.stderr.fileno())
    os.lseek(ferr, 0, os.SEEK_END)

# Setup serial, RS 485 to machine
if os.path.lexists("/dev/ttyUSB0"):
    print("Communication started on device ttyUSB0;")
    unit = "/dev/ttyUSB0"
    os.write(ferr, bytes("\n\nUsing /dev/ttyUSB0" + "\n", encoding='utf8'))

elif os.path.lexists("/dev/serial0"):
    print("Communication started on device Serial0;")
    unit = "/dev/serial0"
    os.write(ferr, bytes("\n\nUsing /dev/serial0" + "\n", encoding='utf8'))
else:
    print("Communication started on device ttyAMA0;")
    unit = "/dev/ttyAMA0"
    os.write(ferr, bytes("\n\nUsing /dev/ttyAMA0" + "\n", encoding='utf8'))

################################# command socket setup
import socket

hostname = os.popen("hostname").read()[:-1]
print("Trying to Run on host:", hostname, ", for 60sec;")

while True:
    try:
        cmd_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        cmd_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        cmd_socket.bind(("0.0.0.0", 9876))
        break
    except:
        traceback.print_exc(ferr)
        os.system("sleep 1")
        print("sleeping;")
        if time.time() - starttime > 60: break

########### global uty functions################
sensor_dict = {}


def count_down(inhibit, target):
    inhibit = int(target - (time.time() - inhibit))
    if inhibit > 3600:
        hrs = math.floor(inhibit / 3600)
        inhibit = int(inhibit - (hrs * 3600))
        return str(hrs) + "h " + str(math.floor(inhibit / 60)) + "min " + str(inhibit % 60).zfill(2) + "s"
    if inhibit % 60 == 0:
        return str(math.floor(inhibit / 60)) + "min"
    if inhibit > 60:
        return str(math.floor(inhibit / 60)) + "min " + str(inhibit % 60).zfill(2) + "s"
    if inhibit < 60:
        return str(inhibit).zfill(2) + "s"


# SEND PING TO EPIC HEADMASTER
def report_alive():
    global holdoff_t
    try:
        msg = os.popen("/sbin/ifconfig wlan0").readlines()
        for each in msg:
            if each.find("HWaddr") != -1 or each.find("ether") != -1:
                message = each
                message += os.popen("hostname -I").read()
                hw_addr = str(each.split(" ")[9]).replace(":","_")
                try:
                    message += "\n###status:"+str(device.status_field)+"\n###<br>"
                except:
                    message += "\nstatus: initialization "+str(vers)+"\n\n<br>"
                try:
                    fd = os.open("RAM/err", os.O_RDONLY)
                    stats = os.stat("RAM/err")
                    sizeT = stats.st_size
                    if sizeT > 1024 * 5:
                        sizeT = 1024 * 5
                    os.lseek(fd, -sizeT, os.SEEK_END)
                    temp = os.read(fd, sizeT)
                    os.close(fd)
                    if sizeT == 5 * 1024 and not "keep-log" in sys.argv:
                        os.lseek(ferr, 0, os.SEEK_SET)
                        os.ftruncate(ferr, 0)
                        os.fsync(ferr)
                        os.write(ferr, temp)
                        os.fsync(ferr)
                    try:
                        if os.path.lexists("update.log"):
                            log = os.open("update.log", os.O_RDONLY)
                            logdata = os.read(log, 5000)
                            temp += bytes("\n\n", "utf-8")
                            temp += logdata
                            os.close(log)
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
                    if os.path.lexists("RAM/error_rate"): message += os.popen("cat RAM/error_rate").read() + "<br>"
                except:
                    os.write(ferr, bytes("Ping error " + str(traceback.print_exc()) + "\n", encoding='utf8'))
                    os.close(fd)
        # if "debug" in sys.argv: device.msg +=  message + "\n"
        html = """ <html>[DA]</html>"""
        if holdoff_t < (time.time() - 3600): # wait for one hour
            stat = open("RAM/"+hw_addr, "w")
            stat.write(html.replace(u"[DA]",message))
            #print(bytes(html.replace(u"[DA]",message), encoding = "utf-8"))
            os.system("curl -s -X DELETE \"https://filebin.net/airiana_ping_status_store/" + hw_addr + ".html\"")
            tmp = "-s -X POST \"https://filebin.net/airiana_ping_status_store/" + hw_addr + ".html\""
            tmp += " -d @RAM/" + hw_addr
            #os.write(ferr, "curl " + tmp + "\n")
            stat.close()
            res = os.popen("curl " + tmp).read()
            if res.find("Insufficient storage") != -1:
                os.write(ferr, b"Holdoff time in effect, will re-ping in one hour.\n")
            holdoff_t = time.time()

        #sock =  socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        #sock.sendto(message, (socket.gethostbyname("lappy.asuscomm.com"), 59999))
        ##sock.close()
    except NameError:
        os.write(ferr,"unable to ping, network error\t"+time.ctime() + "\n")
        traceback.print_exc(ferr)


# READ AVAIL SENSOR DATA
def update_sensors():
    try:
        with open("sensors", "r") as fd:
            for each in fd.readlines():
                unit = each.split(":")
                id = unit[0]
                unit.pop(0)
                tmp = {}
                for sensor in unit:
                    dat = sensor.split(";")
                    tmp[dat[0]] = dat[1]
                sensor_dict[id] = tmp
            try:
                device.sensor_temp = float(sensor_dict["91"]["temperature"])
                device.sensor_humid = int(sensor_dict["91"]["humidity"])
                device.airdata_inst.humid = float(device.sensor_humid) / 100
            except KeyError:
                pass  # device.msg +="\nerror on sensor 91"
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
            cmd = "" \
                  + str(time.time()) \
                  + ":" \
                  + str(device.sensor_temp) \
                  + ":" \
                  + str(round(device.extract_ave, 2)) \
                  + ":" \
                  + str(round(device.sensor_humid, 2)) \
                  + ":" \
                  + str(round(device.humidity, 2)) \
                  + ":" \
                  + str(round(device.inlet_ave, 2)) \
                  + ":" \
                  + str(round(device.exhaust_ave, 2)) \
                  + ":" \
                  + str(round(device.supply_ave, 2)) \
                  + ":" \
                  + str(round(device.local_humidity, 2)) \
                  + ":" \
                  + str(device.inside) \
                  + ":" \
                  + str(round(numpy.average(device.cond_data), 1)) \
                  + ":" + str(device.inside_humid) \
                  + ":" + str(device.moist_in) \
                  + ":" + str(device.moist_out) \
                  + ":" + str(device.humidity_diff)
            fdo.write(cmd + "\n")
    except:
        traceback.print_exc(ferr)
    if "homeAss" in sys.argv:
        os.system("./ha-httpsensor.py -n ftx_Indoor -u °C -d temperature -v " + str(
            round(device.extract_ave, 1)) + ">/dev/null &")
        os.system("./ha-httpsensor.py -n ftx_Outside -u °C -d temperature -v " + str(
            round(device.inlet_ave, 1)) + ">/dev/null &")
        try:
            os.system("./ha-httpsensor.py -n ftx_Efficiency -u % -d calculated -v " + str(
                round(numpy.average(device.eff_ave), 2)) + ">/dev/null &")
        except:
            traceback.print_exc(ferr)

        os.system(
            "./ha-httpsensor.py -n ftx_Humidity -d humidity -u % -v " + str(int(device.humidity)) + ">/dev/null &")
        os.system(
            "./ha-httpsensor.py -n ftx_ExtractFan -d fanspeed -u rpm -v " + str(int(device.ef_rpm)) + ">/dev/null &")


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


#################################################################################
start = time.time()  # START TIME
sys.stdout.flush()


############DEVICE CLASS FOR SYSTEMAIR VR400DCV#############################
class Systemair(object):
    def __init__(self):
        self.elec_now = 0
        self.showerRH = None
        self.initial_temp = None
        self.fanspeed = 1
        self.system_types = {0: "VR400", 1: "VR700", 2: "VR700DK", 3: "VR400DE", 4: "VTC300", 5: "VTC700",
                             12: "VTR150K", 13: "VTR200B", 14: "VSR300", 15: "VSR500", 16: "VSR150",
                             17: "VTR300", 18: "VTR500", 19: "VSR300DE", 20: "VTC200", 21: "VTC100"}
        self.has_RH_sensor = ("VTR300", "VSR300", "Savecair" )
        self.rotor_states = {0: "Normal", 1: "Rotor Fault", 2: "Rotor Fault Detected"
            , 3: "Summer Mode transitioning", 4: "Summer Mode"
            , 5: "Leaving Summer Mode", 6: "Manual Summer Mode"
            , 7: "Rotor Cleaning in Summer Mode", 8: "Rotor cleaning in manual summer mode"
            , 9: "Fans off", 10: "Rotor Cleaning during fans off", 11: "Rotor Fault, but conditions normal"}
        self.speeds = {0: "Off", 1: "Low", 2: "Normal", 3: "High", 4: "undefined"}
        self.weather_types = {
            1: "Clear skies", 2: "Fair weather", 3: "Partly cloudy",
            4: "Cloudy", 40: "Light showers", 41: "Heavy showers",
            5: "Rain", 24: "Light rain and thunder",
            6: "Rain and thunder", 25: "Heavy rain and thunder",
            42: "light sleet showers", 7: "Sleet showers",
            43: "Heavy sleet showers", 26: "Light sleet showers and thunder",
            20: "sleet showers and thunder", 27: "Heavy sleet showers and thunder",
            44: "Light snowfall", 8: "Snow",
            45: "Heavy snow showers", 28: "Light snow and thunder",
            29: "Heavy snow and thunder",
            21: "Snow showers and thunder", 46: "Light rain",
            9: "Rain", 10: "Heavy rain",
            30: "Light rain and thunder",
            22: "Rain and thunder",
            11: "Heavy rain and thunder",
            47: "Light sleet",
            12: "Sleet",
            48: "Heavy Sleet",
            31: "Light sleet and thunder",
            23: "Sleet and thunder",
            32: "Heavy sleet and thunder",
            49: "Light snow",
            13: "Snow",
            50: "Heavy snow",
            33: "Light snow and thunder",
            14: "Snow and thunder",
            34: "Heavy snow and thunder",
            15: "Fog", -1: "No weather data"}
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
        self.cooling_limit = 16
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
        self.house_heat_limit = 8
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
        self.rotor_state = 0
        self.rotor_active = "Yes"
        self.inhibit = time.time()
        self.integral_forcast = 0
        self.system_name = ""
        self.sensor_temp = 0
        self.sensor_humid = 0
        self.modetoken = 0
        self.cooling = 0
        self.forcast = [-1, -1, -1]
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
        self.div = 0
        self.set_system_name()
        self.RH_valid = 0
        self.hum_list = []
        self.status_field = [-1, self.exchanger_mode, 0, self.system_name, vers,
                             os.popen("git log --pretty=format:'%h' -n 1").read(), 0, self.inlet_ave, self.extract_ave,
                             self.ef, self.humidity, 0, self.cool_mode, self.supply_ave, self.exhaust_ave,
                             self.pressure_diff, self.det_limit]
        self.heater = 0
        self.exchanger_speed = 0
        self.unit_comp = []
        self.coef_dict = {0: {}, 1: {}, 2: {}, 3: {}}
        self.coef_test_bool = False
        self.coef_inhibit = time.time()
        self.sensor_exhaust = -60
        self.admin_password = ""
        self.electric_power_sum = 0.0

    def get_password(self):
        req.modbusregister(16000,0)
        self.admin_password = "{0}{1}{2}{3}".format(str(req.response & 0b1),
                                                    str(req.response & 0b1000 >> 3),
                                                    str(req.response & 0b10000000 >> 7),
                                                    str(req.response & 0b100000000000 >> 11))

    def system_setup(self):
        try:
            if os.path.isfile("coeficients.dat"):
                self.coef_dict = pickle.load(open("coeficients.dat", "rb"))
            else:
                pickle.dump(self.coef_dict, open("coeficients.dat", "wb"))
        except EOFError:
            traceback.print_exc(ferr)
            pickle.dump(self.coef_dict, open("coeficients.dat", "wb"))

        if savecair:
            self.get_password()
            req.write_register(1400, 16)
            req.write_register(1401, 16)
            req.write_register(1402, 20)
            req.write_register(1403, 20)
            req.write_register(1404, 50)
            req.write_register(1405, 50)
            req.write_register(1406, 90)
            req.write_register(1407, 90)
            req.write_register(1408, 100)
            req.write_register(1409, 100)
        else:
            self.get_heater()
            # make sure the electric heater is oFF
            if self.heater != 0:
                self.set_heater(0)
            # check if there is an RH sensor availible even though its not listed
            self.get_RH()
            if self.RH_valid and self.system_name not in self.has_RH_sensor:
                self.has_RH_sensor += (self.system_name)

            # setup airflow levels
            if self.system_name in ("VR400", "VTR300",):
                req.modbusregister(137, 0)
                if int(req.response) == 1:
                    req.write_register(137, 0)
                req.modbusregister(107, 0)
                if int(req.response) == 1:
                    req.write_register(107, 0)
                # SET BASE FLOW RATES
                # req.write_register(101,30) 	#read only
                req.write_register(102, 30)
                req.write_register(103, 50)
                req.write_register(104, 50)
                # req.write_register(105,107) 	#read only
                req.write_register(106, 107)
            if self.system_name in ("VSR300"):
                req.modbusregister(137, 0)
                if int(req.response) == 1:
                    req.write_register(137, 0)
                req.modbusregister(107, 0)
                if int(req.response) == 1:
                    req.write_register(107, 0)
                # SET BASE FLOW RATES
                # req.write_register(101,30) 	#read only
                req.write_register(102, 40)
                req.write_register(103, 60)
                req.write_register(104, 60)
                # req.write_register(105,107) 	#read only
                req.write_register(106, 107)
            if "VTR700" in self.system_name:
                req.modbusregister(137, 0)
                if int(req.response) == 1:
                    req.write_register(137, 0)
                req.modbusregister(107, 0)
                if int(req.response) == 1:
                    req.write_register(107, 0)
                # SET BASE FLOW RATES
                # req.write_register(101,50) 	#read only
                req.write_register(102, 50)
                req.write_register(103, 100)
                req.write_register(104, 100)
                # req.write_register(105,200) 	#read only
                req.write_register(106, 200)

    # get heater status
    def get_heater(self):
        if not savecair:
            req.modbusregister(200, 0)
            self.heater = int(req.response)
        else:
            self.heater = 0

    # set heater status
    def set_heater(self, heater):
        if not savecair:
            req.write_register(200, heater)

    # get and set the Unit System name, from system types dict
    def set_system_name(self):
        if not savecair:
            req.modbusregister(500, 0)
            self.system_name = self.system_types[req.response]

    # get the coef mode, for dict matching
    def get_coef_mode(self):
        mode = 0
        if self.exchanger_mode == 5 and self.exchanger_speed == 100:
            mode += 1
        if self.sf != self.ef:
            mode += 2
        return mode

    # calculate a new coef if fanspeed change renders high dt values  //UNused
    def coef_debug(self):
        if self.fanspeed == 3 and not self.coef_test_bool and self.inhibit and not self.shower:
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
        if (self.inhibit == 0 or self.fanspeed == 2) and self.coef_test_bool == True:
            temp = 0
            for each in self.rawdata:
                temp += float(each[1]) / 10
            temp = temp / len(self.rawdata)
            temp_diff = (float((self.rawdata[-1][1]) / 10) - self.coef_prev_inlet)
            delta = (self.coef_prev_temp - temp)
            new_coef = delta / temp_diff
            os.system("echo \"newCoef:" + str(new_coef) + "\nAmbientDiff:" + str(temp_diff) + "\" >> newCoef.txt")
            os.system("echo \"delta:" + str(delta) + " list:" + str(self.get_coef_mode()) + "\ntemp:" + str(
                temp) + " prev_tmp:" + str(self.coef_prev_temp) + "\n\" >> newCoef.txt")
            try:
                keys = list(self.coef_dict[self.get_coef_mode()].keys())
            except KeyError:
                keys = []
            if int(temp_diff) not in keys:
                self.coef_dict[self.get_coef_mode()][int(temp_diff)] = new_coef
            else:
                self.coef_dict[self.get_coef_mode()][int(temp_diff)] += (new_coef -
                                                    self.coef_dict[self.get_coef_mode()][
                                                    int(temp_diff)]) * 0.1  # add 10% of diff from new coef to dict
            if len(self.coef_dict) != 0:
                pickle.dump(self.coef_dict, open("coeficients.dat", "wb"))
            self.coef_test_bool = False
            self.set_fanspeed(1)

    # Get relative humidity from internal sensor, valid units in self.has_RH_sensor tuple
    def get_RH(self):
        if "noRH" in sys.argv:
            self.RH_valid = 0
            return 0
        if not savecair:
            req.modbusregister(382, 0)
            self.RH_valid = int(req.response)
            if self.RH_valid:
                req.modbusregister(380, 0)
                self.humidity = float(req.response)
        else:
            req.modbusregister(12135, 0)
            if req.response != 0:
                self.RH_valid = 1
                self.humidity = float(req.response)
        if self.RH_valid:
            self.hum_list.insert(0, self.humidity)
            if len(self.hum_list) > self.average_limit:
                self.hum_list.pop(-1)
            try:
                # if an update of the humidity value on the sensor exeeds 2points reuse last known value
                if abs(self.humidity - self.hum_list[1]) > 2:
                    self.humidity = self.hum_list[1]
                    self.hum_list[0] = self.humidity
            except IndexError:
                pass
            except:
                traceback.print_exc(ferr)

    # get the nr of days  used and alarm lvl for filters
    def get_filter_status(self):
        if not savecair:
            req.modbusregister(600, 0)
            self.filter_limit = int(req.response) * 31
            req.modbusregister(601, 0)
            self.filter = req.response
            try:
                self.filter_remaining = round(100 * (1 - (float(self.filter) / self.filter_limit)), 1)
            except:
                traceback.print_exc(ferr)

            if self.filter_remaining < 0: self.filter_remaining = 0
        else:
            req.modbusregister(7000, 0)
            self.filter_limit = int(req.response) * 30
            req.modbusregister(7004, 0)
            lowend = req.response
            req.modbusregister(7005, 0)
            highend = req.response << 16
            self.filter_raw = lowend + highend
            self.filter = self.filter_limit - (lowend + highend) / (3600 * 24)
            self.filter_remaining = round(100 * (1 - (float(self.filter) / self.filter_limit)), 1)
            if self.filter_remaining < 0: self.filter_remaining = 0

    # get status byte for temp probes
    def get_temp_status(self):
        if not savecair:
            req.modbusregister(218, 0)
            self.temp_state = req.response

    def print_attributes(self):
        for each in dir(self):
            obj = None
            exec(str("obj = self." + each))
            if isinstance(obj, (int, float, str, list)) or True:
                exec(str("print (each,  self." + each + ")"))
        if not "daemon" in sys.argv:
            input("press enter to resume")
        else:
            print("break")
            os.system("sleep 2")

    def get_fanspeed(self):
        if not savecair:
            req.modbusregister(100, 0)
            self.fanspeed = int(req.response)
            return self.fanspeed
        else:
            req.modbusregister(1130, 0)
            if req.response <= 0:
                self.fanspeed = 0
            else:
                self.fanspeed = req.response - 1
            return self.fanspeed

    def update_temps(self):
        if not savecair:
            req.modbusregisters(213, 5)  # Tempsensors 1 -5
            self.time.insert(0, time.time())
            if len(self.time) > self.average_limit: self.time.pop(-1)

            # NEGATYIVE VAL sign bit twos complement
            if req.response[4] > 6000:
                req.response[4] -= 0xFFFF
            if req.response[2] > 6000:
                req.response[2] -= 0xFFFF

            self.temps = req.response[:]
            self.rawdata.insert(0, self.temps)
            if len(self.rawdata) > self.average_limit: self.rawdata.pop(-1)

            # req.response[1] #EXTRACT
            # req.response[2] #EXHAUST
            # req.response[0] #Supply pre elec heater
            # req.response[3] #Supply post electric heater
            # req.response[4] Inlet

            # update [4] with inlet coef
            req.response[4] -= (req.response[1] - req.response[
                4]) * self.inlet_coef  # inlet compensation exchanger OFF/ON
            # update [1] with tcomp, after calc of [4]
            self.tcomp = 10 * self.get_tcomp(float(req.response[1]) / 10, float(req.response[4]) / 10)
            req.response[1] += self.tcomp

            self.extract.insert(0, float(req.response[1]) / 10)
            self.exhaust.insert(0, float(req.response[2]) / 10)
            self.supply.insert(0, float(req.response[3]) / 10)
            self.inlet.insert(0, float(req.response[4]) / 10)

            # limit array size
            for each in [self.inlet, self.supply, self.extract, self.exhaust]:
                if len(each) > self.average_limit: each.pop(-1)
        else:  # SAVECAIR SECTION
            self.time.insert(0, time.time())

            ##EXTRACT
            extract = "no data"
            cnt = 0
            while extract == "no data" and cnt < 10:
                req.modbusregister(12543, 1)
                extract = req.response
            try:  # replace erronous data input when temp diff exceeds 1C between samples
                if extract - self.rawdata[0][1] > 50 and (extract != 0.0 or self.rawdata[1][1] != 0.0):
                    os.write(ferr, bytes("temp read error at: " + str(extract) + "C \t" + str(time.ctime()) + "\n",
                                     encoding='utf8'))
                    extract = self.rawdata[1][1]
            except IndexError:
                pass
            except TypeError:
                os.write(ferr, bytes("temp read type error at: " + str(extract) + "C \t" + str(time.ctime()) + "\n",
                                     encoding='utf8'))
                traceback.print_exc(ferr)
                extract = self.rawdata[1][1]
                pass
            except:
                traceback.print_exc(ferr)

            req.modbusregister(12102, 1)
            supply = req.response
            req.modbusregister(12101, 1)
            inlet = req.response
            # req.response[1] #EXTRACT
            # req.response[2] #EXHAUST
            # req.response[0] #Supply pre elec heater
            # req.response[3] #Supply post electric heater
            # req.response[4] Inlet
            self.rawdata.insert(0, (0, extract * 10, 0, supply * 10, inlet * 10))
            if len(self.rawdata) > self.average_limit:
                self.rawdata.pop(-1)
            self.tcomp = self.get_tcomp(extract, inlet)
            self.extract.insert(0, float(extract + self.tcomp))
            ## SUPPLY
            self.supply.insert(0, float(supply))
            ### INLET
            # if self.rotor_active =="No"  and self.inlet_coef <0.03:self.inlet_coef+= 0.0001 #OFF
            # if self.rotor_active =="Yes" and self.inlet_coef >0.00:self.inlet_coef-= 0.0001 # ON
            tweak = 0
            try:
                inlet_comp = ((float(3200) / self.sf_rpm) - 1) * 0.01
                tweak = (extract - inlet) * inlet_comp  # inlet compensation exchanger OFF/ON
            except ZeroDivisionError:
                pass
            self.inlet.insert(0, float(inlet - tweak))

            if len(self.extract) > self.average_limit: self.extract.pop(-1)
            if len(self.exhaust) > self.average_limit: self.exhaust.pop(-1)
            if len(self.supply) > self.average_limit: self.supply.pop(-1)
            if len(self.inlet) > self.average_limit: self.inlet.pop(-1)
            if len(self.time) > self.average_limit: self.time.pop(-1)
        try:
            self.eff = (self.supply_ave - self.inlet_ave) / (self.extract_ave - self.inlet_ave) * 100
        except ZeroDivisionError:
            self.eff = 100
        self.eff_ave.insert(0, self.eff)
        if len(self.eff_ave) > self.average_limit: self.eff_ave.pop(-1)

    # Return the Tcomp temperature offset for extraction temps
    def get_tcomp(self, extract, inlet):
        tcomp = 0
        try:
            diff = extract - inlet
            dyn_coef = 0
            try:
                if self.fanspeed and len(self.coef_dict) != 0:
                    dyn_coef = numpy.median(list(self.coef_dict[self.get_coef_mode()].values())) * float(1) / (
                        self.fanspeed)  # self.dyn_coef #float(7*34)/self.sf # compensation (heat transfer from duct) + (supply flow component)
                if self.fanspeed == 3:
                    dyn_coef = 0
            except KeyError:
                dyn_coef = numpy.average(list(self.coef_dict[self.get_coef_mode()].values()))
                if numpy.isnan(dyn_coef):
                    dyn_coef = 0
            except:
                traceback.print_exc(ferr)
            try:
                if dyn_coef != self.new_coef:
                    self.new_coef += 0.0001 * (dyn_coef - self.new_coef)
                    if abs(dyn_coef - self.new_coef) < 0.001:
                        self.new_coef = dyn_coef
            except:
                traceback.print_exc(ferr)
            tcomp = (
                        diff) * -self.new_coef  # self.dyn_coef #float(7*34)/self.sf # compensation (heat transfer from duct) + (supply flow component)
        except ZeroDivisionError:
            pass
        if numpy.isnan(tcomp):
            return 0
        return tcomp

    def set_fanspeed(self, target):
        self.inhibit = time.time()
        self.coef_inhibit = time.time()
        if target != self.fanspeed:  # add one to bucket
            self.status_field[0] += 1
            os.write(ferr,
                     bytes("Changing fanspeed to:" + str(target) + " \t\t" + str(time.ctime()) + "\n", encoding='utf8'))
        # print actual,"->",target
        if target >= 4: target = 0
        if target < 0: target = 0
        # print "write to device", target
        if not savecair:
            req.write_register(100, target)
        else:
            if target == 0:
                req.write_register(1130, target)
            else:
                req.write_register(1130, target + 1)
        if self.get_fanspeed() != target:
            os.write(ferr,
                     bytes("Incorrectly set fanspeed " + str(self.get_fanspeed()) + " to " + str(target) + " \t" + str(
                         time.ctime()) + "\n", encoding='utf8'))
        self.update_airflow()

    def update_fan_rpm(self):
        if not savecair:
            req.modbusregisters(110, 2)
            self.sf_rpm, self.ef_rpm = req.response[0], req.response[1]
            try:
                if self.system_name in ("VR400"):
                    self.electric_power = (
                            self.ef_rpm / (100 / (float(float(self.ef_rpm) / 1381) ** 1.89)) + self.sf_rpm / (
                            100 / (float(float(self.sf_rpm) / 1381) ** 1.89)))
                if self.system_name in ("VSR300"):
                    self.electric_power = 0.2 * (
                            self.ef_rpm / (100 / (float(float(self.ef_rpm) / 1381) ** 1.89)) + self.sf_rpm / (
                            100 / (float(float(self.sf_rpm) / 1381) ** 1.89)))
                if self.system_name in ("VTR300"):
                    self.electric_power = 0.2 * (
                            self.ef_rpm / (100 / (float(float(self.ef_rpm) / 1381) ** 1.89)) + self.sf_rpm / (
                            100 / (float(float(self.sf_rpm) / 1381) ** 1.89)))

            except ZeroDivisionError:
                self.electric_power = 0
            if "Yes" in self.rotor_active: self.electric_power += 10  # rotor motor 10Watts
            self.electric_power += 5  # controller power

        else:
            req.modbusregister(12400, 0)
            self.sf_rpm = req.response
            req.modbusregister(12401, 0)
            self.ef_rpm = req.response
            try:
                self.electric_power = 3.404 * math.exp(0.001 * self.ef_rpm) + 3.404 * math.exp(0.001 * self.sf_rpm)
            except ZeroDivisionError:
                self.electric_power = 0
            if "Yes" in self.rotor_active: self.electric_power += 10  # rotor motor 10Watts
            self.electric_power += 5  # controller board power
        if self.elec_now != 0:  # integral of the electric power used by fans and controller
            self.electric_power_sum += (self.electric_power * (time.time() - self.elec_now)) / 3600
        self.elec_now = time.time()

    def update_fanspeed(self):
        self.fanspeed = self.get_fanspeed()

    def update_airflow(self):
        if not savecair:
            req.modbusregisters(101, 6)
            sf = [req.response[0], req.response[2], req.response[4]]
            ef = [req.response[1], req.response[3], req.response[5]]
            tmp = self.fanspeed  # self.get_fanspeed()
            if tmp <= 0: tmp = 1
            self.sf = sf[tmp - 1]
            self.ef = ef[tmp - 1]
            if self.fanspeed == 0:
                self.ef = 0
                self.sf = 0
        else:
            req.modbusregister(14000, 0)
            self.sf = int(req.response)
            req.modbusregister(14001, 0)
            self.ef = int(req.response)

    def update_airdata_instance(self):
        self.airdata_inst = airdata.Energy()

    def update_xchanger(self):
        if len(self.inlet):
            self.inlet_ave = numpy.average(self.inlet)
            self.supply_ave = numpy.average(self.supply)
            self.extract_ave = numpy.average(self.extract)
            if self.system_name == "VR400":
                self.exhaust_ave = numpy.average(self.exhaust)
        else:
            self.inlet_ave = self.inlet[0]
            self.supply_ave = self.supply[0]
            self.extract_ave = self.extract[0]
            if self.system_name == "VR400":
                self.exhaust_ave = self.exhaust[0]

        if self.fanspeed != 0:
            # self.availible_energy =  self.airdata_inst.energy_flow(self.ef,self.extract_ave,self.inlet_ave)+self.airdata_inst.condensation_energy((self.airdata_inst.vapor_max(self.exhaust_ave)-self.airdata_inst.vapor_max(self.inlet_ave))*((self.ef)/1000))

            try:
                self.used_energy = self.airdata_inst.energy_flow(self.sf, self.supply_ave, self.inlet_ave)
            except:
                traceback.print_exc(ferr)
                self.used_energy = 0
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
                self.supply_power = self.used_energy - 00 - (
                        self.extract_ave - self.inlet_ave) * factor  # constant# red  from casing heat transfer
            else:
                self.supply_power = self.used_energy - 0 - (
                        self.extract_ave - self.inlet_ave) * factor  # constant# red  from casing heat transfer

            try:
                self.extract_exchanger = self.airdata_inst.energy_flow(self.ef, self.extract_ave, self.exhaust_ave)
            except:
                self.extract_exchanger = 0
            self.extract_offset = 0  # float(8)*(self.extract_ave-self.supply_ave)# + 20Watt/degC transfer after exchanger unit
            self.extract_power = self.extract_exchanger + self.extract_offset
            self.extract_combined = self.extract_power + self.condensate_compensation
            self.energy_diff = self.supply_power - self.extract_power
            try:
                self.loss = self.airdata_inst.energy_flow(self.ef, self.exhaust_ave,
                                                          self.inlet_ave) + self.airdata_inst.energy_flow(self.sf,
                                                                                                          self.extract_ave,
                                                                                                          self.supply_ave)
            except:
                self.loss = 0
            try:
                self.diff_ave.insert(0, (-1 * (self.extract_combined - self.supply_power) / (
                        (self.supply_power + self.extract_combined) / 2)) * 100)
            except ZeroDivisionError:
                pass

            if len(self.diff_ave) > self.average_limit: self.diff_ave.pop(-1)
            self.i_diff.append((self.extract_combined - self.supply_power) * -1)
            if len(self.i_diff) > 15: self.i_diff.pop(0)
            try:
                self.dur = self.time[0] - self.time[1]
                if self.rotor_active == "Yes":
                    self.total_energy += (self.loss * self.dur) / 3600
                elif self.exhaust_ave > self.extract_ave and self.exhaust_ave > self.inlet_ave and self.ac_active:
                    self.AC_energy += self.airdata_inst.energy_flow(self.ef, self.exhaust_ave,
                                                                    self.inlet_ave) * self.dur / 3600
                elif self.extract_ave > self.supply_ave:
                    self.cooling += (self.loss * self.dur) / 3600
                else:
                    self.gain += (self.loss * self.dur) / 3600
            except IndexError:
                pass
            except:
                traceback.print_exc(ferr)

            self.cond_data.append(self.energy_diff)
            if len(self.cond_data) > self.average_limit + 5000: self.cond_data.pop(0)

    # test if exhaust temperatures are indicative of ac hot flow connected to cooker exhaust line
    def check_ac_mode(self):
        # use external exhaust sensor if it measures more 30C, airCond mode.
        if (self.sensor_exhaust >= 30 or (
                self.exhaust_ave - self.inlet_ave > 5 and self.exhaust_ave > 30)) and not self.ac_active:
            self.ac_active = True
            os.write(ferr, bytes("A/C mode engaged. Detected high exhaust temperatures at \t" + time.ctime() + "\n",
                                 encoding='utf8'))
            if self.fanspeed != 3:
                self.set_fanspeed(3)
        if self.ac_active and (self.sensor_exhaust <= 30 or (
                self.exhaust_ave - self.extract_ave < 5 and self.exhaust_ave < 30 and self.sensor_exhaust <= 30)):
            self.ac_active = False
            os.write(ferr, bytes("A/C mode disengaged. no AC conditions detected at \t" + time.ctime() + "\n",
                                 encoding='utf8'))
        if "sensors" in sys.argv and self.ac_active:
            self.exhaust_ave = self.sensor_exhaust

    # For units whithout exhaust temp sensor calc expected exhaust temp based on transfered energy in supply
    def calc_exhaust(self):
        if self.supply_power and self.ef and not self.ac_active:
            if self.supply_ave > self.inlet_ave:
                exhaust = self.extract_ave - self.airdata_inst.temp_diff(self.supply_power, self.extract_ave, self.ef)
            else:
                exhaust = self.extract_ave + self.airdata_inst.temp_diff(-1 * self.supply_power, self.extract_ave,
                                                                         self.ef)
            self.exhaust_ave = exhaust

    # Retrieve the rotor state from the unit
    def get_rotor_state(self):
        if not savecair:
            req.modbusregister(206, 0)
            self.exchanger_mode = req.response
            req.modbusregisters(350, 2)
            self.rotor_state = req.response[0]
            if req.response[1]:
                self.rotor_active = "Yes"
                self.exchanger_speed = 100
            else:
                self.rotor_active = "No"
        else:
            req.modbusregister(2140, 0)
            if req.response:
                self.rotor_active = "Yes"
                self.exchanger_mode = 5
            else:
                self.exchanger_mode = 0
                self.rotor_active = "No"
            self.rotor_state = 0
            self.exchanger_speed = req.response
        self.status_field[1] = self.exchanger_mode

    # do moisture calculations
    def moisture_calcs(self, data=None):  ## calculate moisure/humidities
        self.moist_in = 1000 * self.airdata_inst.sat_vapor_press(
            self.airdata_inst.dew_point(self.humidity, self.extract_ave))
        self.moist_out = 1000 * self.airdata_inst.sat_vapor_press(
            self.airdata_inst.dew_point(self.local_humidity, self.extract_ave))
        self.humidity_diff = self.moist_in - self.moist_out
        self.cond_eff = 1.0  # 1 -((self.extract_ave-self.supply_ave)/35)#!abs(self.inlet_ave-self.exhaust_ave)/20
        ######### SAT MOIST UPDATE ############
        if self.energy_diff > 0 and self.rotor_active == "Yes":
            try:
                d_pw = (self.airdata_inst.energy_to_pwdiff(self.energy_diff, self.extract_ave) / self.cond_eff) / (
                        float(self.ef) / 1000)
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
            tmp_RH = ((low_pw + d_pw) / max_pw) * 100
            self.humidity += (tmp_RH - self.humidity) * 0.001
            self.hum_list.insert(0, self.humidity)
            if len(self.hum_list) > self.average_limit:
                self.hum_list.pop(-1)
        # if "debug" in sys.argv:
        #	self.msg += str(self.new_humidity)+"  "+str( self.local_humidity)+"\n"
        # query for a ref humidity at temp
        if data != None:
            max_pw = self.airdata_inst.sat_vapor_press(self.extract_ave)
            low_pw = self.airdata_inst.sat_vapor_press(data)
        return ((low_pw) / max_pw) * 100

    #####END

    # calc long and short derivatives
    def derivatives(self):
        # SHORT
        if len(self.extract) > self.average_limit - 1:
            self.extract_dt = (numpy.average(self.extract[0:14]) - numpy.average(
                self.extract[self.average_limit - 15:self.average_limit - 1]))
            self.extract_dt = self.extract_dt / ((self.time[0] - self.time[self.average_limit - 1]) / 60)
            self.extract_dt_list.append(self.extract_dt)
            if len(self.extract_dt_list) > 500: self.extract_dt_list.pop(0)
        # LONG
        if self.iter % round(360 / self.avg_frame_time, -2) == 0:
            if self.dt_hold == 0: self.dt_hold = self.extract_ave
            self.extract_dt_long = float((self.extract_ave - self.dt_hold)) / (
                    (time.time() - self.extract_dt_long_time) / 360)
            self.extract_dt_long_time = time.time()
            self.dt_hold = self.extract_ave
            self.avg_frame_time = (time.time() - starttime) / self.iter

    # decect if shower is on
    def shower_detect(self):
        def turnoff(self):
            if savecair:
                req.write_register(1161, 2)
            else:
                self.set_fanspeed(self.initial_fanspeed)

        if "debug" in sys.argv and self.shower and self.RH_valid:
            self.msg = "Shower wait state, " + str(round(self.extract_ave, 2)) + "C " + str(
                round(self.initial_temp + 0.3, 2)) + "C RH: " + str(self.showerRH + 5) + "\n"
        if self.RH_valid == 1 and not self.shower:  # Shower humidity sensor control
            try:
                if self.hum_list[0] - self.hum_list[-1] > 8 and \
                        numpy.average(self.extract_dt_list) * 60 > 0.0:
                    self.shower = True
                    self.initial_temp = self.extract_ave
                    self.initial_fanspeed = self.fanspeed
                    if savecair:
                        req.write_register(1103, 45)
                        req.write_register(1161, 4)
                    else:
                        self.set_fanspeed(3)
                    if self.RH_valid:
                        self.showerRH = self.hum_list[-1]
                    self.inhibit = time.time()
                    self.coef_inhibit = time.time()
                    self.shower_initial = self.inhibit
                    self.msg = "Shower mode engaged\n"
                    os.write(ferr, bytes("Engaged Shower mode at\t" + str(time.ctime()) + "\n", encoding='utf8'))
                    self.status_field[0] += 1
            except IndexError:
                pass
        elif not self.shower and not self.RH_valid:
            # SHOWER derivative CONTROLER
            lim = 0.07
            if self.ef > 50: lim = 0.07
            if len(self.extract_dt_list) and self.extract_dt > lim + float(
                    self.det_limit) / 100 and self.inhibit == 0 and numpy.average(self.extract_dt_list) * 60 > 1.40:
                self.msg = "Shower mode engaged\n"
                if self.shower == False:
                    self.shower = True
                    self.initial_temp = self.extract_ave
                    self.initial_fanspeed = self.fanspeed
                    self.set_fanspeed(3)
                    self.humidity += 30
                    self.inhibit = time.time()
                    self.coef_inhibit = time.time()
                    self.shower_initial = self.inhibit
                    self.status_field[0] += 1
                    os.write(ferr, bytes("Engaged Shower mode at \t" + str(time.ctime()) + "\n", encoding='utf8'))

        if len(self.extract_dt_list) != 0 and numpy.average(self.extract_dt_list) * 60 < 0.25 \
                and self.shower == True \
                and self.shower_initial - time.time() < -60:
            state = False
            if not self.RH_valid and self.extract_ave <= (self.initial_temp + 0.3):
                state = True
            if self.RH_valid and self.showerRH + 5 > self.humidity:
                if "debug" in sys.argv:
                    self.msg += "RH after shower now OK\n"
                    os.write(ferr, bytes("Shower mode off RH is ok \t" + str(time.ctime()) + "\n", encoding='utf8'))
                state = True
            if state == True:
                if self.shower_initial - time.time() > -120:
                    self.det_limit += 1
                try:
                    os.write(ferr, bytes("Leaving Shower mode dT: " + str(
                        numpy.max(self.extract) - numpy.min(self.extract)) + " \t" + str(time.ctime()) + "\n",
                                         encoding='utf8'))
                    self.msg = "Shower mode off, returning to " + str(self.speeds[self.initial_fanspeed] + "\n")
                except IOError:
                    pass
                self.shower = False
                self.shower_initial = 0
                turnoff(self)
        # SHOWER MODEwTIMEOUT #
        if self.shower == True and self.shower_initial - time.time() < -45 * 60:
            self.shower = False
            os.write(ferr, bytes("Shower mode ended on timeout at:\t" + str(time.ctime()) + "\n", encoding='utf8'))
            turnoff(self)

    # PRINT OUTPUT
    def print_xchanger(self):
        global monitoring, vers
        tmp = self.system_name
        if savecair:
            tmp += " SavecAir"
        tmp += " " + time.ctime() + " status: " + str(int(time.time() - starttime)) + '(' + str(self.iter) + ")" + str(
            round((time.time() - starttime) / self.iter, 2)) + " Vers. " + vers + " ***\n"
        if "debug" in sys.argv:
            try:
                tmp += "Errors -- Connect: " + str(req.connect_errors) + " Checksum: " + str(
                    req.checksum_errors) + " Write: " + str(req.write_errors) + " drain: " + str(
                    len(req.buff)) + " Multi: " + str(req.multi_errors) + "\n"
                tmp += "temp sensor state: " + str(bin(self.temp_state)) + " Heater:" + str(self.heater) + "\n"
                tmp += "Unit admin password: " + self.admin_password + "\n"
                if len(req.buff) > 50: req.buff = ""
                tmp += str(sys.argv) + "\n"
            except:
                pass
        try:
            if len(self.extract_dt_list):
                tmp += "Inlet: <b>" + str("%.2f" % self.inlet_ave) + "C</b>\t\tSupply: " + str(
                    "%.2f" % self.supply_ave) + "C\td_in : " + str(
                    round(self.supply_ave - self.inlet_ave, 2)) + "C"
                tmp += "\nExtract: <b>" + str("%.2f" % self.extract_ave) + "C</b>\tExhaust: " + str(
                    "%.2f" % self.exhaust_ave) + "C\td_out: " + str(
                    round(self.extract_ave - self.exhaust_ave, 2)) + "C\n"
                tmp += "Extract dT/dt: " + str(round(self.extract_dt, 3)) + "degC/min dT/dt: " + str(
                    round(numpy.average(self.extract_dt_list) * 60, 3)) + "degC/hr\n\n"
                if "debug" in sys.argv:
                    tmp += "Tcomp:" + str(self.tcomp) + " at T1:" + str(self.rawdata[0][1]) + " coef:" + str(
                        round(self.coef, 4)) + " inlet coef:" + str(self.inlet_coef) + " dyn:" + str(
                        self.new_coef) + "\n"
                    tmp += "Extract:" + str(self.rawdata[0][1]) + "\tInlet:" + str(
                        self.rawdata[0][4]) + "\tExhaust:" + str(self.rawdata[0][2]) + "\tSupply,pre:" + str(
                        self.rawdata[0][0]) + "\tSupply,post:" + str(self.rawdata[0][3]) + "\n"
        except:
            pass
        # req.response[1] #EXTRACT
        # req.response[2] #EXHAUST
        # req.response[0] #Supply pre elec heater
        # req.response[3] #Supply post electric heater
        # req.response[4] Inlet
        if not savecair:
            tmp += "Exchanger Setting: " + str(self.exchanger_mode) + " State: " + self.rotor_states[
                self.rotor_state] + ", Rotor Active: " + self.rotor_active + "\n"
        else:
            tmp += "Exchanger Rotor speed: " + str(self.exchanger_speed) + "% set target:" + str(
                self.target) + "C exchanger setting: " + str(self.exchanger_mode) + "\n"
        if self.rotor_active == "Yes" or "debug" in sys.argv:
            tmp += "HeatExchange supply " + str(round(self.supply_power, 1)) + "W \n"
            tmp += "HeatExchange extract " + str(round(self.extract_power + self.condensate_compensation, 1)) + "W\n"
            if "debug" in sys.argv: tmp += "Diff:" + str(round(numpy.average(self.diff_ave), 2)) + "% " + str(
                round(self.energy_diff, 1)) + "W\n"
            if "humidity" in sys.argv and "debug" in sys.argv: tmp += "\nCondensation  efficiency: " + str(
                round(self.cond_eff, 2) * 100) + "%\n"
        if "humidity" in sys.argv:
            if "debug" in sys.argv:
                tmp += "Static RH low: " + str(round(self.local_humidity, 2)) + "% " + str(
                    round(self.prev_static_temp - self.kinetic_compensation, 2)) + "C\n"
                if self.RH_valid:
                    tmp += "Humidity d/dt:" + str(self.hum_list[0] - self.hum_list[-1]) + "%\n"
            if self.RH_valid:
                tmp += "Relative humidity: " + str(round(self.humidity, 2)) + "% Dewpoint: " + str(
                    round(self.airdata_inst.dew_point(self.humidity, float(self.rawdata[0][1]) / 10), 2)) + "C\n"
        if "sensors" in sys.argv:
            tmp += "Outdoor Sensor:\t " + str(self.sensor_temp) + "C " + str(self.sensor_humid) + "% Dewpoint: " + str(
                round(self.airdata_inst.dew_point(self.sensor_humid, self.sensor_temp), 2)) + "C\n"
            tmp += "Indoor Sensor:\t " + str(self.inside) + "C " + str(self.inside_humid) + "% Dewpoint: " + str(
                round(self.airdata_inst.dew_point(self.inside_humid, self.inside), 2)) + "C\n"
            tmp += "Sensor exhaust:\t" + str(self.sensor_exhaust) + "\n"
        if "debug" in sys.argv:
            try:
                tmp += "Fanspeed level: " + str(self.fanspeed) + "\n"
                tmp += "Long dt: " + str(self.extract_dt_long) + "\n"
                # tmp += "Current Coef: "+ str(self.get_coef_mode()) + str(self.coef_dict[self.get_coef_mode()])+"\n"
                if self.coef_test_bool:
                    tmp += "In Test:" + str(time.ctime(self.coef_inhibit + 3600)) + "\n"

            except:
                pass
            tmp += "diff. humidity partial pressure in-out: " + str(int(round(self.humidity_diff, 0))) + "Pa\n"

        if "humidity" in sys.argv:
            tmp += "Pressure limit: " + str(round(self.indoor_dewpoint, 2)) + "C\n"

        if self.rotor_active == "Yes":
            tmp += "\nElectric power:" + str(round(self.electric_power, 0)) + "W COP:" + str(
                round(self.supply_power / self.electric_power, 1)) + "\n"
        else:
            tmp += "\nElectric power:" + str(round(self.electric_power, 0)) + "W COP:" + str(
                round(self.loss / self.electric_power, 1)) + "\n"
        if self.supply_ave < self.extract_ave:
            tmp += "Energy Loss: " + str(round(self.loss, 1)) + "W\n"
        else:
            tmp += "Energy gain: " + str(round(self.loss, 1)) + "W\n"
        tmp += "Loss total: " + str(round(self.total_energy / 1000, 3)) + "kWh Average:" + str(
            round((self.total_energy) / (((time.time() - starttime) / 3600)), 1)) + "W\n"
        tmp += "Cooling total: " + str(round(self.cooling / 1000, 3)) + "kWh\n"
        tmp += "Heat gain total: " + str(round(self.gain / 1000, 3)) + "kWh\n"
        tmp += "Unit electric total: " + str(round(self.electric_power_sum/1000, 3)) + "kWh\n"
        tmp += "Supply:" + str(self.sf) + " l/s," + str(self.sf_rpm) + "rpm\tExtract:" + str(self.ef) + " l/s," + str(
            self.ef_rpm) + "rpm\n"
        if self.ac_active:
            tmp += "AirCondition unit detected ON\n"
        if self.AC_energy:
            tmp += "AC-energy: " + str(round(self.AC_energy / 1000, 3)) + "kWh\n"
        if self.rotor_active == "Yes" or "debug" in sys.argv:
            tmp += "Temperature Efficiency: " + str(round(numpy.average(self.eff_ave), 2)) + "%\n"
        tmp += "Filter has been installed for " + str(math.ceil(self.filter)) + " days ," + str(
            self.filter_remaining) + "% remaining. \n\n"
        tmp += "Ambient Pressure:" + str(round(self.airdata_inst.press, 2)) + "hPa\n"
        if self.forcast[1] != -1: tmp += "Weather forecast: " + str(self.forcast[0]) + "C " + str(
            self.forcast[1] / 8 * 100) + "% cloud cover RH:" + str(self.forcast[2]) + "%\n\n"
        if "Timer" in threading.enumerate()[-1].name:
           tmp += "Ventilation timer on: " + count_down(self.timer, 120 * 60) + "\n"
        if self.shower: tmp += "Shower mode engaged at:" + time.ctime(self.shower_initial) + "\n"
        if self.inhibit > 0: tmp += "Status change inhibited (" + count_down(self.inhibit, 600) + ")\n"
        if self.press_inhibit > 0: tmp += "Pressure change inhibited (" + count_down(self.press_inhibit, 1800) + ")\n"
        if self.modetoken >= 1: tmp += "Exchanger mode change inhibited (" + count_down(self.modetoken, 3600) + ")\n"
        if self.cool_mode: tmp += "Cooling mode is in effect, target is 20.7C extraction temperature\n"
        if not monitoring: tmp += "\nSystem Automation off\n"

        self.status_field[2] = round((time.time() - starttime) / self.iter, 2)
        self.status_field[6] = round((time.time() - starttime) / 3600, 1)
        tmp += self.msg + "\n"
        tmp = tmp.replace("\n", ";\n")
        tmp = tmp.replace("\t", "'\t")
        # CLEAR SCREEN AND REPRINT
        clear_screen()
        print(tmp)

    # change exchanger mode to to, if no to flip 0 or 5
    def cycle_exchanger(self, to):
        os.write(ferr, bytes("cycle exchanger to: " + str(to) + "\t" + str(time.ctime()) + "\n", encoding='utf8'))
        if not savecair:
            def set_val(val):
                try:
                    # self.msg += "\nwriting mode "+str(val)+"\n"
                    req.write_register(206, val)
                    return 1
                except:
                    return 0

            def get_val():
                try:
                    req.modbusregister(206, 0)
                    self.current_mode = req.response
                    return self.current_mode
                except:
                    pass  # print "read error"

            ### SET FUNCTIONS ####
            try:
                if to is None:
                    self.msg += "manual state change\n"
                    self.current_mode = get_val()
                i = 0
                if self.current_mode != 0 or to == 0:
                    while not set_val(0):
                        # self.msg += "\nwrite error"
                        time.sleep(0.2)  # set summer mode
                        i += 1
                        if i > 10:
                            os.write(ferr, bytes("Exchanger write failed\n"))
                else:
                    while not set_val(5):
                        # self.msg +="\nwrite error"
                        time.sleep(0.2)  # set winter mode
                        i += 1
                        if i > 10:
                            os.write(ferr, bytes("Exchanger write failed\n"))
                self.modetoken = time.time()
                self.inhibit = time.time()  # set inhibit time to prevent derivatives sensing when returning
            except:
                # self.msg +=  "\nexit due to error"
                traceback.print_exc(ferr)
            finally:
                self.exchanger_mode = get_val()
        else:
            if to == 0:
                req.write_register(2000, 120)
                self.exchanger_mode = 0
            if to == 5:
                self.exchanger_mode = 5
                if not self.cool_mode:
                    req.write_register(2000, self.target * 10)
                else:
                    req.write_register(2000, 300)

            if to == None:
                req.modbusregister(2000, 0)
                if int(req.response) == 120:
                    if not self.cool_mode:
                        req.write_register(2000, self.target * 10)
                    else:
                        req.write_register(2000, 300)
                    self.exchanger_mode = 5
                else:
                    req.write_register(2000, 120)
                    self.exchanger_mode = 0
        self.coef_inhibit = time.time()  # set inhibit time to prevent derivatives sensing when returning

    # clear flags as timeouts occur
    def check_flags(self):
        global monitoring
        #### INHIBITS AND LIMITERS
        now = time.time()
        if self.inhibit < now - (60 * 10): self.inhibit = 0
        if self.modetoken < now - (60 * 60): self.modetoken = 0
        if self.press_inhibit < now - (60 * 30): self.press_inhibit = 0
        if self.coef_inhibit < now - (60 * 60): self.coef_inhibit = 0
        if self.flowOffset[1] - time.time() < -3600 \
                and self.flowOffset[0] > 0 \
                and self.humidity_diff < 350:
            self.flowOffset[0] -= 1
            self.flowOffset[1] = time.time()

    # Monitor Logical crits for state changes on exchanger, pressure, rpms, forcast
    def monitor(self):
        if "VTR400" in self.system_name:
            #### FAN RPM MONITORING
            if self.sf_rpm < 1550 and self.fanspeed == 2:
                self.inhibit = time.time()
                self.coef_inhibit = time.time()
            if self.sf_rpm < 1000 and self.fanspeed == 1:
                self.coef_inhibit = time.time()
                self.inhibit = time.time()
        if True:
            #### EXCHANGER CONTROL
            self.house_heat_limit = 7  # daily low limit on cooling
            if self.inlet_ave < 13:
                self.target = 24
            else:
                self.target = 23
            if self.cool_mode:
                self.target = 20.7
            if self.modetoken <= 0 and self.cool_mode == 0:

                if self.extract_ave > self.target \
                        and self.exchanger_mode != 0 \
                        and self.shower == False \
                        and self.inlet_ave > 10:
                    self.cycle_exchanger(0)
                    self.modetoken = time.time()
                    os.write(ferr,
                             bytes("Exchange set to 0 inlet>10C and extr above target \t" + str(time.ctime()) + "\n",
                                   encoding='utf8'))

                if self.supply_ave > self.target \
                        and self.exchanger_mode != 0 \
                        and self.shower == False:
                    self.cycle_exchanger(0)
                    self.modetoken = time.time()
                    os.write(ferr,
                             bytes("Exchange set to 0 supply>target \t" + str(time.ctime()) + "\n", encoding='utf8'))

                if self.extract_ave < self.target - 1 \
                        and self.exchanger_mode != 5 \
                        and not self.cool_mode:
                    self.cycle_exchanger(5)
                    self.modetoken = time.time()
                    os.write(ferr,
                             bytes("1.Exchange set to 5. extract is less than target-1C \t" + str(time.ctime()) + "\n",
                                   encoding='utf8'))

                if self.supply_ave < 10 \
                        and self.extract_ave < self.target \
                        and self.exchanger_mode != 5 \
                        and not self.cool_mode:
                    self.cycle_exchanger(5)
                    os.write(ferr,
                             bytes("2.Exchange set to 5 supply<10C and extract< target \t" + str(time.ctime()) + "\n",
                                   encoding='utf8'))
                    self.modetoken = time.time()
                if self.exchanger_mode != 5 \
                        and self.inlet_ave < 10 \
                        and self.forcast[0] <= 10 \
                        and self.forcast[1] > -1 \
                        and self.fanspeed == 1 \
                        and not self.cool_mode \
                        and not self.shower:
                    self.modetoken = time.time()
                    self.cycle_exchanger(5)
                    os.write(ferr,
                             bytes("3.Exchange set to 5 inlet<10C \t" + str(time.ctime()) + "\n", encoding='utf8'))

            # FORECAST RELATED COOLING
            try:
                if self.forcast[0] > self.cooling_limit and self.tomorrows_low[0] > self.house_heat_limit \
                        and self.integral_forcast > 0 \
                        and self.cool_mode == False \
                        and self.extract_ave > 20.7 \
                        or self.inlet_ave > 25.0 and not self.cool_mode:
                    self.msg += "Predictive Cooling enaged\n"
                    if self.pressure_diff != 0:
                        self.set_differential(0)
                    if savecair:
                        req.write_register(1407, 100)
                        req.write_register(1406, 100)
                    if self.exchanger_mode != 0:
                        self.cycle_exchanger(0)
                    self.set_differential(0)
                    self.cool_mode = True
                    os.write(ferr, bytes("Cooling activated \t" + str(time.ctime()) + "\n", encoding='utf8'))

            except:
                os.write(ferr,
                         bytes("Forecast cooling error " + str(self.integral_forcast) + ' ' + str(time.ctime()) + "\n",
                               encoding='utf8'))

            if self.cool_mode and not self.inhibit and not self.shower and not self.ac_active:
                if (self.extract_ave < 20.7) and self.fanspeed != 1:
                    self.set_fanspeed(1)
                    self.msg += "Cooling complete\n"
                    os.write(ferr,
                             bytes("Cooling complete 20.7C reached \t" + str(time.ctime()) + "\n", encoding='utf8'))

                if self.fanspeed == 3 and (self.supply_ave < 12 and self.extract_ave < 22):
                    self.set_fanspeed(2)
                    self.msg += "Cooling reduced\n"
                    os.write(ferr, bytes("Cooling reduced to medium, supply below 12C \t" + str(time.ctime()) + "\n",
                                         encoding='utf8'))

                if self.fanspeed == 2 and self.supply_ave > 13:
                    self.set_fanspeed(3)
                    self.msg += "Cooling returned to High.\n"
                    os.write(ferr,
                             bytes(
                                 "Cooling returned to high from medium, supply above 13C \t" + str(time.ctime()) + "\n",
                                 encoding='utf8'))

                if self.fanspeed == 1 and self.extract_ave > 21 and self.extract_ave + 0.1 > self.inlet_ave:
                    self.set_fanspeed(3)
                    self.msg += "Cooling returned to High, indoor is hotter than outside.\n"
                    os.write(ferr, bytes("Cooling returned to high, indoor is hotter than outside. " + str(
                        time.ctime()) + " " + str(self.fanspeed) + " " + str(self.extract_ave) + " " + str(
                        self.inlet_ave) + "\n", encoding='utf8'))

                if self.inlet_ave + 0.1 > self.extract_ave and self.fanspeed != 1 and self.extract_ave > 21:
                    self.set_fanspeed(1)
                    self.msg += "No cooling posible due to temperature conditions\n"
                    os.write(ferr, bytes("Cooling will wait, will try to recycle cold air by low fanspeed \t" + str(
                        time.ctime()) + "\n", "utf-8"))

                try:
                    if self.integral_forcast < 0 and time.localtime().tm_hour > 12 and self.inlet_ave < 24.9:
                        self.cool_mode = False
                        os.write(ferr, bytes("Cooling mode turned off " + str(time.ctime()) + "\n", encoding='utf8'))
                        if savecair and self.ef == 100:
                            req.write_register(1407, 90)
                            req.write_register(1406, 90)
                except ValueError:
                    os.write(ferr, bytes("forcast error  " + str(time.ctime()) + "\n", encoding='utf8'))

            # DYNAMIC FANSPEED CONTROL
            if not self.inhibit and not self.shower and not self.cool_mode:
                # dynamic with RHsensor
                if self.RH_valid:
                    if self.fanspeed == 1 \
                            and ((self.extract_ave > self.target + 0.6
                                  and self.extract_ave - self.supply_ave > 0.1)
                                 or self.humidity_diff > 500):
                        self.set_fanspeed(2)
                        self.msg += "Dynamic fanspeed 2\n"
                        if self.humidity_diff > 500:
                            self.flowOffset = [self.flowOffset[0] + 5, time.time()]
                            os.write(ferr,
                                     bytes("Dynamic fanspeed 2 with RH \t" + str(time.ctime()) + "\n", encoding='utf8'))
                        else:
                            os.write(ferr,
                                     bytes("Dynamic fanspeed 2 no RH\t" + str(time.ctime()) + "\n", encoding='utf8'))
                    if self.fanspeed == 2 \
                            and ((self.extract_ave < self.target + 0.5
                                  and self.extract_ave - self.supply_ave > 0.1
                                  and self.humidity_diff < 400
                                  or (self.humidity_diff < 350
                                      and not self.extract_ave > self.target + 0.5))):
                        self.set_fanspeed(1)
                        if self.humidity_diff < 350:
                            self.msg += "Dynamic fanspeed 1, Air quality Good\n"
                            os.write(ferr,
                                     bytes("Dynamic fanspeed 1 with RH\t" + str(time.ctime()) + "\n", encoding='utf8'))
                        else:
                            self.msg += "Dynamic fanspeed 1\n"
                            os.write(ferr,
                                     bytes("Dynamic fanspeed 1 no RH\t" + str(time.ctime()) + "\n", encoding='utf8'))
                # dynamic without Rhsensor
                else:
                    if self.fanspeed == 2 \
                            and self.extract_ave < self.target + 0.5 \
                            and self.extract_ave - self.supply_ave > 0.1:
                        self.set_fanspeed(1)
                        self.msg += "Dynamic fanspeed 1\n"
                        os.write(ferr,
                                 bytes("Dynamic fanspeed 1 without RH\t" + str(time.ctime()) + "\n", encoding='utf8'))

                    if self.fanspeed == 1 \
                            and (self.extract_ave > self.target + 0.6
                                 and self.extract_ave - self.supply_ave > 0.1):
                        self.set_fanspeed(2)
                        self.msg += "Dynamic fanspeed 2\n"
                        os.write(ferr,
                                 bytes("Dynamic fanspeed 2 extr > target +0.5C without RH\t" + str(time.ctime()) + "\n",
                                       encoding='utf8'))
                # dynamic 3 if temp is climbing and exchanger is off, and extract is above target +1.2C
                if self.fanspeed == 2 \
                        and self.extract_ave - 0.1 > self.supply_ave \
                        and (self.extract_ave >= self.target + 1.2
                             or (self.extract_dt_long >= 0.7 and self.inlet_ave > 5)) \
                        and self.exchanger_mode != 5 \
                        and not self.extract_dt_long < -0.2:
                    self.set_fanspeed(3)
                    self.msg += "Dynamic fanspeed 3\n"
                    os.write(ferr, bytes("Dynamic fanspeed 3 target+1.2C or dt long > 0.7C/h (" + str(
                        self.extract_dt_long) + ")\t" + str(time.ctime()) + "\n", encoding='utf8'))

                # Recover cold air if outside is hotter
                if self.extract_ave < self.supply_ave and self.fanspeed != 1 and self.cool_mode:
                    self.set_fanspeed(1)
                    self.msg += "Dynamic fanspeed, recover cool air\n"
                    os.write(ferr, bytes("Dynamic fanspeed 1 recover cool air " + str(time.ctime()) + "\n" + str(
                        self.extract_ave) + ' ' + str(self.supply_ave) + '\n', encoding='utf8'))

                # Lower to fanspeed 2 if long dt is less than -0.5 and outside is less than 12C
                # also lower from 3 when below target+0.8 and not rising above 0.7C/hr
                if (self.fanspeed == 3
                    and self.extract_ave < self.target + 0.8
                    and not self.extract_dt_long > 0.7) \
                        or (self.supply_ave < 12
                            and self.extract_dt_long < -0.5):
                    self.set_fanspeed(2)
                    self.msg += "Dynamic fanspeed 2 with long dt\n"
                    os.write(ferr, bytes("Dynamic fanspeed 2 with long dt from 3\t" + str(time.ctime()) + "\n",
                                         encoding='utf8'))

            # Dynamic pressure control
            if not self.shower:
                if self.humidity > 20.0:  # Low humidity limit, restriction to not set margin lower than 20%RH
                    if savecair or self.RH_valid:
                        self.indoor_dewpoint = self.airdata_inst.dew_point(self.humidity + 5, self.extract_ave)
                    else:
                        self.indoor_dewpoint = self.airdata_inst.dew_point(self.humidity + 10, self.extract_ave)
                else:
                    self.indoor_dewpoint = 5.0
                if not self.cool_mode:
                    if self.inlet_ave > self.indoor_dewpoint + 0.2 and self.pressure_diff != 0 and not self.press_inhibit and not \
                            self.forcast[1] == -1:
                        self.set_differential(0)
                        if "debug" in sys.argv: self.msg += "\nPressure diff to 0%"
                    if (
                            self.inlet_ave < self.indoor_dewpoint - 0.1 and self.pressure_diff != 10 and self.inlet_ave < 15 and not self.press_inhibit) or (
                            self.forcast[-1] == -1 and self.sf == self.ef):
                        self.set_differential(10)
                        if "debug" in sys.argv: self.msg += "\nPressure diff to +10%"
        # if "debug" in sys.argv: print "Pressure inhibit = " , str(time.ctime(self.press_inhibit))

    # Get the active forcast
    def get_forcast(self):
        ###### WEATHER FORCAST MODES
        forcast = [-1, -1]
        try:
            forcast = os.popen("./forcast2.0.py tomorrow").readlines()
            self.forcast[2] = float(forcast[1])
            forcast = forcast[0].split(" ")
            self.forcast[0] = float(forcast[0])
            self.forcast[1] = float(forcast[1])
            # get tomorrows-low values
            tomorrows_low = os.popen("./forcast2.0.py tomorrows-low").read()[:-1].split(" ")
            for index in range(len(tomorrows_low)):
                self.tomorrows_low[index] = float(tomorrows_low[index])
            # print self.tomorrows_low
            # get integral for comming days
            self.integral_forcast = float(os.popen("./forcast2.0.py integral " + str(self.cooling_limit)).read())
            # print self.integral_forcast
            if os.stat("./RAM/forecast.json").st_ctime < time.time() - 3600 * 24: raise Exception(
                "FileError: file too old")
        except IOError:
            traceback.print_exc(ferr)
            self.msg += "error getting forecast.(io error)\n" + str(forcast)
            self.forcast = [-1, -1]
        except IndexError:
            traceback.print_exc(ferr)
            self.msg += "error getting forecast.(index error)\n" + str(forcast)
        # self.forcast=[-1,-1]
        except FileError:
            traceback.print_exc(ferr)
            self.msg += "error getting forecast.(file too old)\n" + str(forcast)

    # set the fan pressure diff
    def set_differential(self, percent):
        os.write(ferr, bytes("Pressure difference set to: " + str(percent) + "%\t" + str(time.ctime()) + "\n",
                             encoding='utf8'))
        self.coef_inhibit = time.time()
        if percent > 20: percent = 20
        if percent < -20: percent = -20
        if not savecair and not self.shower:
            if "debug" in sys.argv: self.msg += "start pressure change " + str(percent) + "\n"
            req.modbusregister(103, 0)  # nominal supply flow
            # print "sf_nom is", req.response
            target = int(req.response + req.response * (float(percent) / 100))
            # print "to set ef_no to",target
            req.write_register(104, target)  # nominal extract flow
            req.modbusregister(104, 0)  # nominal supply flow
            if req.response == target:
                self.press_inhibit = time.time()
            if "debug" in sys.argv:
                if req.response == target: self.msg += "supply flow change completed \n"
            high_flow = 107
            if percent < 0: high_flow += 107 * float(percent) / 100
            if high_flow > 107: high_flow = 107
            # print "high should be extract:", int(high_flow)
            req.write_register(106, int(high_flow))  # reset high extract
            # raw_input(" diff set done")
            if "debug" in sys.argv: self.msg += "change completed\n"
            self.press_inhibit = time.time()

        elif savecair and not self.shower:
            self.press_inhibit = time.time()

            for each in range(1400, 1408, 2):
                req.modbusregister(each, 0)
                # raw_input(str(percent)+"% "+str(each)+"-"+str(int(req.response*(1+(float(percent)/100)))))
                req.write_register(each + 1, int(req.response + percent))
        if not savecair and not self.shower and self.system_name == "VTR300":
            if "debug" in sys.argv: self.msg += "start pressure change " + str(percent) + "\n"

            req.modbusregister(101, 0)  # LOW supply flow
            target = int(req.response + req.response * (float(percent) / 100))
            req.write_register(102, target)  # LOW extract flow

            req.modbusregister(103, 0)  # nominal supply flow
            target = int(req.response + req.response * (float(percent) / 100))
            req.write_register(104, target)  # nominal extract flow

            req.modbusregister(106, 0)  # nominal supply flow
            target = int(req.response - req.response * abs(float(percent) / 100))
            req.write_register(105, target)  # nominal extract flow

            if req.response == target:
                self.press_inhibit = time.time()
            if "debug" in sys.argv: self.msg += "change completed\n"
        self.pressure_diff = percent
        self.update_airflow()

    # Set base flow rate with an offset to regulate humidity in a more clever manner.
    def check_flow_offset(self):
        if self.flowOffset[0] > 20:  # Maximum offset allowed
            self.flowOffset[0] = 20
        if savecair:
            base = self.ef_base + self.pressure_diff
            req.modbusregister(1403, 0)
            ef = int(req.response)
            if self.fanspeed == 1 and ef != base + self.flowOffset[0] and not self.shower and not self.cool_mode:
                req.write_register(1403, base + self.flowOffset[0])
                req.write_register(1402, self.sf_base + self.flowOffset[0])
                os.write(ferr,
                         bytes("Extract flow offset to: " + str(ef)
                               + "/" + str(self.flowOffset[0])
                               + "/" + str(base)
                               + "\t" + str(time.ctime())
                               + "\n", encoding='utf8'))
                self.ef = base + self.flowOffset[0]
                self.sf = self.sf_base + self.flowOffset[0]
        if self.has_RH_sensor and not savecair:
            base = 30 + self.pressure_diff
            if self.fanspeed == 1 and self.ef != base + self.flowOffset[0] and not self.shower:
                req.write_register(102, base + self.flowOffset[0])
                req.write_register(101, 30 + self.flowOffset[0])
                # self.msg += "Updated base extract flow to: "+str(base+self.flowOffset[0])+"\n"
                os.write(ferr,
                        bytes("Updated extract flow offset to: " +
                              str(self.flowOffset[0]) + "\t" + str(time.ctime()) + "\n", 'utf8'))
                self.ef = base + self.flowOffset[0]
                self.sf = 30 + self.flowOffset[0]

    # get and set the local low/static humidity
    def get_local(self):
        if self.prev_static_temp == 8:
            if os.path.lexists("RAM/latest_static"):
                try:
                    self.prev_static_temp = float(os.popen("cat RAM/latest_static").readline().split("\n")[0])
                except:
                    self.prev_static_temp = self.inlet_ave
                    os.write(ferr,
                             bytes("Unable to load latest_static temp\t" + str(time.ctime()) + "\n", encoding='utf8'))
            else:
                fd = os.open("RAM/latest_static", os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
                os.write(fd, bytes(str(self.prev_static_temp), encoding='utf8'))
                os.close(fd)

        out = os.popen("./humid.py " + str(self.extract_ave)).readline()
        tmp = out.split(" ")
        wthr = [-1, -1]
        comp = 0
        try:
            saturation_point = float(tmp[1])
        except:
            os.write(ferr, bytes("Unable to cast 24h low temp " + "\t" + str(time.ctime()) + "\n", encoding='utf8'))
            os.system("echo 8 > ./RAM/latest_static")
            saturation_point = self.inlet_ave
        # if no forcast is avail
        if self.forcast[1] != -1:
            try:
                # wthr = os.popen("./forcast2.0.py tomorrows-low").read().split(" ")
                sun = int(os.popen("./forcast2.0.py sun").readlines()[0].split(":")[0])
            # comp = float(wthr[0])-(float(wthr[2])/8) # tomorrows low temp +1C(5%RH) - Windspeed(m/s)/8
            except ValueError:
                sun = 7
                os.write(ferr,
                         bytes("Unable set weather or sunrise " + "\t" + str(time.ctime()) + "\n", encoding='utf8'))
            # wthr = [self.prev_static_temp, 0, 0,100]
            # comp = float(wthr[0])-(float(wthr[2])/8) # tomorrows low temp +1C(5%RH) - Windspeed(m/s)/8
            except IndexError:
                os.write(ferr, bytes("Forcast does not return proper data." + " " + str(time.ctime()) + "\n",
                                     encoding='utf8'))

        else:
            os.write(ferr, bytes("forcast unavailible. " + " " + str(self.forcast) + str(time.ctime()) + "\n",
                                 encoding='utf8'))
            sun = 7
            comp = 0
        try:
            # comp = (self.airdata_inst.dew_point(wthr[0],float(wthr[3]))-self.airdata_inst.dew_point (self.extract_ave,self.local_humidity))/(24*50) # new comp calc with humidity forcast
            pass
        except OverflowError:
            pass
        # comp = (comp - (self.prev_static_temp-self.kinetic_compensation))/(24*3)
        self.kinetic_compensation -= comp * self.avg_frame_time
        # if prev static is above saturation point
        # if self.prev_static_temp >= saturation_point:
        if self.prev_static_temp >= self.inlet_ave:
            self.local_humidity = self.moisture_calcs(
                saturation_point - self.kinetic_compensation)  # if 24hr low is higher than current temp
        else:
            self.local_humidity = self.moisture_calcs(
                self.prev_static_temp - self.kinetic_compensation)  # if 24hr low is lower than current temp

        if self.prev_static_temp - self.kinetic_compensation > self.inlet_ave:
            # self.prev_static_temp = self.inlet_ave+self.kinetic_compensation
            self.kinetic_compensation = self.kinetic_compensation * 0.98
        # if "debug" in sys.argv:
        #    self.msg += "Comp set to: " + str(round(comp, 4)) + " Calc RH%: " + str(
        #        self.local_humidity) + "% prev_static: " + str(self.prev_static_temp) + "C 24h-low: " + str(
        #        saturation_point) + "C tomorrows low: " + str(wthr[0]) + "c\n"
        # nightly refresh
        if time.localtime().tm_hour == sun and time.localtime().tm_min < 5 or self.prev_static_temp == 8:
            self.prev_static_temp = saturation_point
            self.kinetic_compensation = 0
            if self.forcast[1] != -1:
                try:
                    weather = os.popen("./forcast2.0.py -f wind/fog ").read().split(" ")
                    fog_cover = float(weather[-1])
                    wind = float(weather[-2])
                    if wind > 2:  # compensate for windy conditions
                        self.kinetic_compensation += wind / 16
                    if fog_cover > 75:  # if fog over 75%
                        self.kinetic_compensation = 0
                except:
                    os.write(ferr, bytes("Unable to update morning low with wind/fog compensation" + "\t" + str(
                        time.ctime()) + "\n", "utf-8"))

            self.prev_static_temp -= self.kinetic_compensation
            fd = os.open("RAM/latest_static", os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
            os.write(fd, bytes(str(self.prev_static_temp - self.kinetic_compensation), encoding='utf8'))
            os.close(fd)

    # print Json data to air.out for thrid party processing
    def print_json(self):
        global monitoring
        tmp = ""
        try:
            json_vars = {
                         "extract": self.extract_ave, "coolingMode": str(self.cool_mode).lower(),
                         "supply": self.supply_ave, "sf": self.sf, "ef": self.ef,
                         "exhaust": self.exhaust_ave, "autoON": str(monitoring).lower(),
                         "shower": str(self.shower).lower(), "rotorSpeed": self.exchanger_speed,
                         "sfRPM": self.sf_rpm, "energyXfer": self.loss, "efficiency": self.eff,
                         "efRPM": self.ef_rpm, "name": self.system_name,
                         "filterPercentRemaining": self.filter_remaining,
                         "pressure": self.airdata_inst.press, "filterInstalledDays": self.filter,
                         "rotorActive": str(self.rotor_active).lower(), "elecHeater": self.heater,
                         "inlet": self.inlet_ave,
                         "electricPower": self.electric_power, "electricPowerTotal": round(self.electric_power_sum, 2),
                         "referenceHumidity": round(self.local_humidity, 1)}
            if len(self.hum_list) and self.RH_valid:
                json_vars.update({"measuredHumidity": round(self.hum_list[0],1)})
            else:
                json_vars.update({"calculatedHumidity": round(self.hum_list[0],1)})
            tmp = str(json_vars).replace("'", "\"")
        except IndexError:
            os.write(ferr, bytes(f"json-writer humidity IndexError {self.hum_list}\n", "utf-8"))
        os.ftruncate(air_out, 0)
        os.lseek(air_out, 0, os.SEEK_SET)
        os.write(air_out, bytes(tmp, encoding='utf8'))

    def check_coef(self):
        """ CHECK IF COEF IS AVAILABLE AND IF NOT in inhibit and current fans are at 1 ,
            run a set of max speed fans to generate new coef data
        """
        try:
            self.coef_dict[int(self.get_coef_mode())][int(self.extract_ave - self.inlet_ave)]
        except KeyError:
            if self.get_fanspeed() == 1 and not self.inhibit \
                    and not self.coef_inhibit and self.monitor and not self.cool_mode:
                os.write(ferr,
                         bytes("Starting coefAI test @  " + str(int(self.extract_ave - self.inlet_ave)) + "C\t" + str(
                             time.ctime()) + "\n", "utf-8"))
                self.set_fanspeed(3)
                self.coef_debug()


# Init base class
if __name__ == "__main__":
    print("Reporting system start;")
    report_alive()
    # init request class for communication
    req = Request()
    req.setup(unit, mode)

    os.write(ferr, bytes("System started\t" + str(time.ctime()) + "\n", 'utf8'))

    device = Systemair()
    req.modbusregister(12543, 0)  # test for savecair extended address range
    if device.system_name == "VR400" and req.response != "no data":
        savecair = True
        device.system_name = "Savecair"
        conversion_table = {}
        device.status_field[3] = "Savecair"
        device.average_limit = 3400
        os.write(ferr, bytes("Savecair unit set\n", 'utf8'))


#  RUN MAIN loop
if __name__ == "__main__":
    monitoring = True
    reset_fans = False


    def set_monitoring(bool):
        global monitoring
        monitoring = bool


    def reset_fanspeed(speed):
        global reset_fans
        reset_fans = speed


    input_buffers = ""
    print("Going in for first PASS;")
    try:
        # FIRST PASS ONLY #
        clear_screen()
        print("First PASS;")
        print("Updating fanspeeds;")
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
        device.get_forcast()
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
        print("Setting up coeficients;")
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
        device.div = device.inlet_ave
        if "humidity" in sys.argv:
            device.humidity = device.moisture_calcs(10.0)
            device.get_local()
        sys.stdout.flush()
        if "ping" in sys.argv: report_alive()
        starttime = time.time()
        print("System started:", time.ctime(starttime), ";")

        while Running:  ##### mainloop do each pass ###########
            # do temps,energy and derivatives
            device.update_temps()
            device.update_xchanger()
            device.derivatives()
            ## EXEC TREE, exec steps uniqe if prime##
            # check states and flags
            if device.iter % 3 == 0:
                if "debug" in sys.argv:
                    os.system("echo \"3\" >./RAM/exec_tree")
                device.check_flags()
                if device.system_name == "VTR300" or device.system_name == "VSR300" or device.system_name == "Savecair":
                    device.calc_exhaust()
                device.check_ac_mode()
                if reset_fans:
                    device.set_fanspeed(reset_fans)
                    reset_fans = 0
            # update moisture
            if device.iter % 5 == 0:
                if "debug" in sys.argv:
                    os.system("echo \"5\" >./RAM/exec_tree")
                if monitoring:
                    device.monitor()
                    device.shower_detect()
                device.print_json()  # Print to json

                if "humidity" in sys.argv and (
                        device.system_name not in device.has_RH_sensor or not device.RH_valid) or "debug" in sys.argv:
                    device.moisture_calcs()
                if "humidity" in sys.argv and device.system_name in device.has_RH_sensor:
                    device.get_RH()  ## Read sensor humidity
            # update fans
            if device.iter % 7 == 0:
                if "debug" in sys.argv:
                    os.system("echo \"7\" >./RAM/exec_tree")
                device.update_fan_rpm()

            # debug specific sensors and temp probe status
            if device.iter % 11 == 0:
                if "debug" in sys.argv:
                    os.system("echo \"11\" >./RAM/exec_tree")
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
                    os.system("echo \"79\" >./RAM/exec_tree")
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
                    os.system("echo \"251\" >./RAM/exec_tree")
            # send ping status, generate graphs and refresh airdata instance.
            if device.iter % 563 == 0:
                if "debug" in sys.argv:
                    os.system("echo \"563\" >./RAM/exec_tree")
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
                    device.status_field[11] = monitoring
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
                        "wget -q -O ./RAM/temperatur.nu  http://www.temperatur.nu/rapportera.php?hash=42bc157ea497be87b86e8269d8dc2d42\\&t=" + str(
                            round(device.inlet_ave, 1)) + " &")

            # check for updates
            if device.iter % int(3600 / 0.2) == 0:
                if "debug" in sys.argv:
                    os.system("echo \"7200s\" >./RAM/exec_tree")
                os.system("./backup.py &")
                os.system("cp ./RAM/data.log ./data.save")
            # restart HTTP SERVER get filterstatus, reset IP on buttons page, update weather forcast
            if device.iter % (int(3600 * 2 / device.avg_frame_time)) == 0:
                device.get_filter_status()
                os.system("./http &")
                os.system("./public/ip-replace.sh &")  # reset ip-addresses on buttons.html
                os.system("./public/ip-util.sh &")  # reset ip-addresses on buttons.html
                device.get_forcast()
                if device.status_field[0] > 0: device.status_field[
                    0] -= 1  # remove one shower token from bucket every 2 hrs.
            device.iter += 1
            ########### Selection menu if not daemon######
            if "daemon" not in sys.argv:
                device.print_xchanger()  # Print to screen
                timeout = 0.1
                print("""
	CTRL-C to exit,
1: Toggle auto Monitoring	 6: Not implemented
2: Toggle fanspeed		 7: Set flow differential
3: Print all device attributes	 8: Run fans for 15min at Max
4: Display link settings	 9: Run the Firestarter mode
5: toggle flowOffset		 0: cycle winter/summer mode
10: Not implemented		11: Toggle electric heater
12: Start shower mode		13: Engage Cool mode
14: Enagage AI test
		enter commands:""", end=' ')
            else:
                timeout = 0.05
            try:
                sys.stdout.flush()
            except IndexError:
                pass
            data = -1
            input_buffers = select.select([sys.stdin, cmd_socket], [], [], timeout)[0]
            try:
                if cmd_socket in input_buffers:
                    try:
                        sock = cmd_socket.recvfrom(128)
                        data = sock[0]
                        data = int(data.decode("utf-8"))
                        sender = sock[1]
                    except:
                        pass
                    try:
                        #device.msg += "\nNetwork command recieved: Processing... " + str(data) + "\n"
                        log = "echo \"" + str(time.ctime()) + ":" + str(sender) + ":" + str(data) + "\" >> netlog.log &"
                        os.write(ferr, bytes(f"{sender}:{data} at\t{time.ctime()}\n", "utf-8"))
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
                        monitoring = not monitoring  # Toggle monitoring on / off
                        device.inhibit = 0
                        device.press_inhibit = 0
                        device.coef_inhibit = 0
                        device.modetoken = 0
                        device.shower_mode = 0
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
                        try:
                            if "daemon" not in sys.argv:
                                inp = int(input("set differential pressure(-20% -> 20%):"))
                            else:
                                if device.ef == device.sf:
                                    inp = 10
                                else:
                                    inp = 0
                            device.set_differential(inp)
                        except IOError:
                            print("not used")
                        except:
                            traceback.print_exc(ferr)

                    if data == 8:  # toggle forced vent timer
                        try:
                            if threading.enumerate()[-1].name == "Timer":
                                if tim.name == "Timer": tim.cancel()
                                if tim2.name == "Timer": tim2.cancel()
                                device.msg += "Removed Forced ventilation timer\n"
                                os.write(ferr, bytes(
                                    bytes("Vent Timer canceled at:\t" + str(time.ctime()) + "\n", encoding='utf8')))
                                monitoring = True
                                device.timer = False

                            if threading.enumerate()[-1].name != "Timer":
                                os.write(ferr,
                                         bytes("Vent timer started at:\t" + str(time.ctime()) + "\n", encoding='utf8'))
                                prev = device.fanspeed
                                device.set_fanspeed(3)
                                monitoring = False
                                device.msg += "Forced Ventilation on timer\n"
                                tim2 = threading.Timer(60.0 * 120 + 2, set_monitoring, [True])
                                tim2.start()
                                tim = threading.Timer(60.0 * 120, reset_fanspeed, [prev])
                                tim.setName("Timer")
                                device.timer = time.time()
                                tim.start()
                        except:
                            traceback.print_exc(ferr)
                            print("force vent error")

                    if data == 9:  #
                        try:
                            if threading.enumerate()[-1].name == "fire":
                                if tim.name == "fire": tim.cancel()
                                if tim2.name == "fire": tim2.cancel()
                                device.msg += "Removed fire starter ventilation timer\n"
                                os.write(ferr, bytes(
                                    bytes("Fire timer canceled at:\t" + str(time.ctime()) + "\n", encoding='utf8')))
                                device.press_inhibit = 0
                                monitoring = True

                            if threading.enumerate()[-1].name != "fire":
                                os.write(ferr,
                                         bytes("Fire start at:\t" + str(time.ctime()) + "\n", encoding='utf8'))
                                monitoring = False
                                prev = device.fanspeed
                                device.set_differential(-10)
                                device.press_inhibit = 0
                                device.set_fanspeed(3)
                                device.msg += "Fire start Ventilation on timer\n"
                                tim2 = threading.Timer(60.0 * 10 + 2, set_monitoring, [True])
                                tim2.start()
                                tim = threading.Timer(60.0 * 10, reset_fanspeed, [prev])
                                tim.setName("fire")
                                tim.start()
                        except:
                            traceback.print_exc(ferr)
                            print("fire starter error")
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
                    if data == 11:  ## toggle electric heater set
                        if device.heater == 0:
                            set = 2
                        else:
                            set = 0
                        device.set_heater(set)
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
                os.write(ferr, bytes("TypeError occured at:\t" + str(time.ctime()) + "\n" + str(e), encoding='utf8'))
            except ValueError:
                os.write(ferr, bytes("ValueError occured at:\t" + str(time.ctime()) + "\n", encoding='utf8'))
            except IOError:
                os.write(ferr, bytes("Connection to the systemAir unit has been lost at:\t" + str(time.ctime()) + "\n",
                                     encoding='utf8'))
    except TypeError:
        pass
    except KeyboardInterrupt:
        exit_callback(2, None)
    except:
        traceback.print_exc(ferr)
