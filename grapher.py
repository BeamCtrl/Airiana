#!/usr/bin/python3
import traceback
import time as tm
import os
import math
import warnings
from pylab import *

matplotlib.use("Agg")

ioff()
warnings.filterwarnings("ignore", module="matplotlib\..*")  # noqa

if len(sys.argv) >= 2:
    try:
        day = int(float(sys.argv[1]) * 3600 * 24)
        print("day set to", day)
    except:
        day = 3600 * 24
else:
    day = 3600 * 24
lines = int(math.ceil(day / 5))
seconds_remainder = tm.time() % 3600
quarter_day = day / 24 * 4
if day > 3600 * 24:
    fil = os.popen("tail -n " + str(lines) + " ./data.log")
    data = fil.readlines()
    fil = os.popen("tail -n " + str(lines) + " ./RAM/data.log")
    data += fil.readlines()
else:
    fil = os.popen("tail -n " + str(lines) + " ./RAM/data.log")
    data = fil.readlines()


sen_hum = []
sen_temp = []
extract = []
measured_hum = []
inlet = []
exhaust = []
time = []
supply = []
supply_humid = []
outside = []
cond_comp = []
inside_hum = []
moist_in = []
moist_out = []
humdiff = []
# data.pop(0)
# print "Processing line: ",
try:
    i = 0
    for each in data:
        i += 1
        c = day / (24 * 60 * 60)
        if c >= 1 and i % (3 * c) > 0:
            pass
        else:
            try:
                # i+=1
                # print i,
                # print chr(27)+"["+str(len(str(i))+2)+"D",
                sys.stdout.flush()
                tmp = each.split(":")
                for entry in tmp:
                    if entry == np.nan:
                        entry = 0

                temp = (tm.time() - day) - ((tm.time() - day) % (3600))
                if float(tmp[0]) > temp:
                    sen_hum.append(float(tmp[3]))
                    sen_temp.append(float(tmp[1]))
                    extract.append(float(tmp[2]))
                    measured_hum.append(float(tmp[4]))
                    inlet.append(float(tmp[5]))
                    exhaust.append(float(tmp[6]))
                    time.append(tm.time() - float(tmp[0]))
                    supply.append(float(tmp[7]))
                    supply_humid.append(float(tmp[8]))
                    outside.append(float(tmp[9]))
                    cond_comp.append(float(tmp[10]))
                    try:
                        inside_hum.append(float(tmp[11]))
                    except IndexError:
                        inside_hum.append(0)
                    except ValueError:
                        inside_hum.append(0)
                    moist_in.append(float(tmp[12]))
                    moist_out.append(float(tmp[13]))
                    humdiff.append(float(tmp[14]))

            except IndexError as error:
                moist_in.append(0)
                moist_out.append(0)
                humdiff.append(0)
                pass  # print error
            except ValueError as error:
                moist_in.append(0)
                moist_out.append(0)
                humdiff.append(0)
                print(error)
            except:
                traceback.print_exc()
except:
    traceback.print_exc()
red_hum = []
red_time = []
i = 0
max_time = max(time[-day:-1]) + 4 * 3600
for each in measured_hum:
    i += 1
    if float(each) != 0.0:
        try:
            red_time.append(time[i])
            red_hum.append(each)
        # print each, time[i]
        except:
            pass
    # print len(red_time) ,len(red_hum), i

# create figure
fig = figure(1, figsize=(7, 15), dpi=100)
# add subplot 211 Temps to figure
s1 = subplot(211)
s1.set_title("Temperatures")
plot(time[-day:-1], extract[-day:-1], "-", linewidth=1, label="extract temperature")
plot(time[-day:-1], inlet[-day:-1], "-", linewidth=1, label="inlet temperature")
plot(time[-day:-1], exhaust[-day:-1], "-", linewidth=1, label="exhaust temperature")
plot(time[-day:-1], supply[-day:-1], "-", linewidth=1, label="supply temperature")
if "debug" in sys.argv:
    plot(
        time[-day:-1],
        sen_temp[-day:-1],
        "-",
        linewidth=1,
        label="outdoor sensor temperature",
    )
    plot(
        time[-day:-1],
        outside[-day:-1],
        "-",
        linewidth=1,
        label="indoor sensor temperature",
    )
    try:
        ob = axhline(y=float(os.popen("cat RAM/latest_static").read()))
    except:
        ob = axhline(y=0.0)
grid(True)
ax = gca()
try:
    ax.set_ylim(
        int(min(inlet)) - 1, int(max(extract + inlet + exhaust + supply + outside)) + 2
    )
except ValueError:
    exit(0)
low, high = ax.get_ylim()
step = floor((high - low) / 30) + 1
ax.yaxis.set_ticks(np.arange(int(low), int(high + 1), 1))
try:
    ax.set_xlim(min(time[-day:-1]), max(time[-day:-1]))
except ValueError:
    sys.exit(0)
ax.xaxis.set_ticks(np.arange(seconds_remainder, max_time, quarter_day))
ax.set_xticklabels(np.arange(seconds_remainder, max_time, quarter_day))
ax.invert_xaxis()
lgd = legend(
    bbox_to_anchor=(0.5, -0.3), loc=1, ncol=2, mode="expand", borderaxespad=0.0
)

# add subplot 212 humidity to figure
if "debug" in sys.argv or "hasRH" in sys.argv:
    s2 = subplot(212)
    s2.set_title("Humidity")
    grid(True)
    plot(
        red_time[-day:-1], red_hum[-day:-1], "-", linewidth=1, label="Relative humidity"
    )
    plot(
        time[-day:-1],
        supply_humid[-day:-1],
        "-",
        linewidth=1,
        label="Calculated outside humidity",
    )
    if "debug" in sys.argv:
        plot(time, cond_comp, "-", linewidth=1, label="Condensation power")
        plot(time, inside_hum, "-", linewidth=1, label="Inside sensor humidity")
        plot(
            time[-day:-1],
            sen_hum[-day:-1],
            "-",
            linewidth=1,
            label="Outdoor sensor humidity",
        )
    subplots_adjust(hspace=0.75)
    ax = gca()
    ax.set_ylim(-30, 100 + 10)
    low, high = ax.get_ylim()
    ax.yaxis.set_ticks(np.arange(low, high, 10))
    ax.set_xlim(min(time[-day:-1]), max(time[-day:-1]))

    ax.xaxis.set_ticks(np.arange(seconds_remainder, max_time, quarter_day))
    ax.set_xticklabels(np.arange(seconds_remainder, max_time, quarter_day))
    ax.invert_xaxis()
    lgd = legend(
        bbox_to_anchor=(0.5, -0.3), loc=2, ncol=2, mode="expand", borderaxespad=0.0
    )

# add subplot 213 moisture to figure
if "moisture" in sys.argv:
    s3 = subplot(312)
    grid(True)
    s3.set_title("Moistures (Pa)")
    plot(time, moist_in, "-", linewidth=1, label="Indoor H20 part.press")
    plot(time, moist_out, "-", linewidth=1, label="Outdoor H20 part.press")
    plot(time, humdiff, "-", linewidth=1, label="Differential H20 part.press")
    subplots_adjust(hspace=1.75)
    ax = gca()
    ax.set_ylim(
        round(min(humdiff + moist_out + moist_in), -2) - 100,
        round(max(moist_in + moist_out + humdiff), -2) + 100,
    )
    low, high = ax.get_ylim()
    ax.yaxis.set_ticks(np.arange(low, high, 200))
    ax.set_xlim(min(time[-day:-1]), max(time[-day:-1]))
    ax.xaxis.set_ticks(np.arange(seconds_remainder, max_time, quarter_day))
    ax.set_xticklabels(np.arange(seconds_remainder, max_time, quarter_day))
    lgd = legend(
        bbox_to_anchor=(0.5, -0.5), loc=0, ncol=2, mode="expand", borderaxespad=0.0
    )
    ax.invert_xaxis()

# create the pretty labels for the graphs
labels = [item.get_text() for item in s1.get_xticklabels()]
for i in range(len(labels)):
    try:
        if not tm.localtime().tm_isdst:
            labels[i] = tm.strftime(
                "%H:%M - %a",
                tm.gmtime(tm.time() - (float(labels[i])) - (tm.altzone) - 3600),
            )
        else:
            labels[i] = tm.strftime(
                "%H:%M - %a", tm.gmtime(tm.time() - (float(labels[i])) - (tm.altzone))
            )
    except:
        pass  # print "label error"
# Temperatures
if len(labels) < len(s1.get_xticklabels()):
    labels.append("")
s1.set_xticklabels(labels)
setp(s1.get_xticklabels(), rotation=45)
# Humidities
if "debug" in sys.argv or "hasRH" in sys.argv:
    if len(labels) < len(s2.get_xticklabels()):
        labels.append("")
    s2.set_xticklabels(labels)
    setp(s2.get_xticklabels(), rotation=45)
# Partial Pressures
if "moisture" in sys.argv:
    try:
        if len(labels) < len(s3.get_xticklabels()):
            labels.append("")
        s3.set_xticklabels(labels)
        setp(s3.get_xticklabels(), rotation=45)
    except ValueError:
        os.system('echo "Tick Error in grapher" >> RAM/err')
grid(True)
# move to the right
fig.subplots_adjust(right=0.90)
# draw the image
fig.canvas.draw()
# save to file
savefig(
    "./RAM/history.png", bbox_extra_artists=(lgd,), bbox_inches="tight", pad_inches=1
)
