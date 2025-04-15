#!/usr/bin/python3
import time as tm
import matplotlib, traceback
import airdata
import sys
import numpy as np

air_obj = airdata.Energy()


class Sensor:
    def __init__(self):
        self.sensor_temp = 0
        self.sensor_humid = 0


device = Sensor()
matplotlib.use("Agg")

import pylab

pylab.ioff()

if len(sys.argv) > 1:
    log = sys.argv[1]
else:
    log = "151"


def update_sensors():
    global device
    try:
        fd = open("sensors")
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
            device.sensor_temp = float(sensor_dict[log]["temperature"])
            device.sensor_humid = int(sensor_dict[log]["humidity"])
        except:
            pass
        if device.sensor_temp != 0.0 and device.sensor_humid != 0:
            temp.append(device.sensor_temp)
            humid.append(device.sensor_humid)
            dewpoint.append(air_obj.dew_point(humid[-1], temp[-1]))
            time.append(tm.time())
    except:
        print("new sensor data error")
        traceback.print_exc()
    finally:
        fd.close()


sensor_dict = {}
time = []
temp = []
humid = []
dewpoint = []

fd = open(str(log) + ".log", "a+")
fd.seek(0)
for each in fd.readlines():
    data = each.split(":")
    if float(data[0]) > tm.time() - 3600 * 24 * 30 * 3:
        time.append(float(data[0]))
        temp.append(float(data[1]))
        humid.append(int(data[2][0:-1]))
        dewpoint.append(air_obj.dew_point(float(data[2][0:-1]), float(data[1])))
fig = pylab.figure(1, figsize=(11, 8), dpi=250)

while True:
    update_sensors()
    if device.sensor_temp != 0 and device.sensor_humid != 0:
        fd.write(
            str(tm.time())
            + ":"
            + str(device.sensor_temp)
            + ":"
            + str(device.sensor_humid)
            + "\n"
        )
        fd.flush()
    pylab.clf()

    s1 = pylab.subplot(111)
    s1.set_title("Sensor: " + str(log))
    fig.subplots_adjust(bottom=0.2, top=0.95, hspace=0.7, wspace=0.7)
    ax = pylab.gca()
    low, high = -20, 100
    ax.yaxis.set_ticks(np.arange(int(low), int(high + 1), 5))
    pylab.gca().set_autoscalex_on(True)
    pylab.gca().set_autoscaley_on(True)
    pylab.gca().set_xlim(min(time), max(time))
    hum_line = pylab.plot(time, humid, "-")[0]
    temp_line = pylab.plot(time, temp, "-")[0]
    dewpoint_line = pylab.plot(time[0 : len(dewpoint)], dewpoint, "-")[0]
    pylab.grid(True)
    pylab.draw()

    labels = [item.get_text() for item in s1.get_xticklabels()]
    num = len(labels) - 1
    pos = 0
    for each in pylab.gca().get_xticks():
        try:
            print(float(each))
            labels[pos] = tm.strftime("%H:%M - %d/%m - %Y", tm.localtime(float(each)))
            pos += 1
        except:
            pos += 1
    s1.set_xticklabels(labels)
    pylab.setp(s1.get_xticklabels(), rotation=45)
    pylab.draw()

    pylab.savefig("./RAM/" + str(log) + ".png")
    tm.sleep(600)
    sys.stdout.flush()
