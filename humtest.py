#!/usr/bin/python3
import numpy as np
import os
import traceback
import sys
import time as tm
import statistics as stat
import progressbar
import pathlib

path = pathlib.Path(__file__).parent.resolve()
os.chdir(path)
if len(sys.argv) == 1:
    fil = os.popen("cat ./RAM/data.log")
else:
    for each in sys.argv[1:]:
        if not each.isdigit():
            print("File:", each)
            fil = open(each, "r")
    if len(sys.argv[1:]) == 1 and sys.argv[-1].isdigit():
        print("Single file: data.log")
        fil = open("data.log", "r")

data = fil.readlines()
if "data.log" in sys.argv or "cat data.log" in fil.name:
    print("Adding current data from RAM")
    data += os.popen("cat ./RAM/data.log").readlines()

sen_hum = []
sen_temp = []
extract = []
calc_hum = []
inlet = []
exhaust = []
time = []
supply = []
supply_humid = []
outside = []
cond_comp = []
inside_hum = []
diff = []
mdP = []
cdP = []

try:
    # i=0
    if len(sys.argv) > 1:
        init = float(data[0].split(":")[0])
        day = tm.time() - init
        for each in sys.argv:
            if each.isdigit():
                day = 60 * 60 * 24 * int(each)
                break
        print("start time", tm.ctime(init))
        print("Will process ", len(data), "data points")
    else:
        day = 60 * 60 * 24
    i = 0
    x = []
    y = []
    l = len(data)
    widgets = [progressbar.Bar('>'), ' ', progressbar.ETA(), ' ', progressbar.ReverseBar('<')]
    pbar = progressbar.ProgressBar(widgets=widgets)
    for each in pbar(data):
        i += 1

        try:
            sys.stdout.flush()
            tmp = each.split(":")
            for entry in tmp:
                if entry == np.nan or entry == "nan" or float(tmp[4]) > 100 or float(tmp[4]) < 0:
                    raise ZeroDivisionError
            if float(tmp[0]) > 0 and float(tmp[0]) > tm.time() - (day):  # temp:
                sen_hum.append(float(tmp[3]))
                sen_temp.append(float(tmp[1]))
                extract.append(float(tmp[2]))
                calc_hum.append(float(tmp[4]))
                inlet.append(float(tmp[5]))
                exhaust.append(float(tmp[6]))
                time.append(tm.time() - float(tmp[0]))
                supply.append(float(tmp[7]))
                supply_humid.append(float(tmp[8]))
                outside.append(float(tmp[9]))
                cond_comp.append(float(tmp[10]))
                inside_hum.append(int(tmp[11]))
                cdP.append(float(tmp[13]))
                mdP.append(float(tmp[12]))
                x.append(calc_hum[-1])
                y.append(supply_humid[-1])
                diff.append(round(calc_hum[-1] - supply_humid[-1], 3))
                if diff[-1] < -35: pass  # print tmp[0]
        except IndexError:
            inside_hum.append(0)
        except ValueError:
            pass
        except ZeroDivisionError:
            pass
        except:
            traceback.print_exc()
except:
    traceback.print_exc()
print("\nStart: " + tm.ctime(float(-time[0] + tm.time())))
print("max", max(diff), "%  min", min(diff), "%")
ave = stat.mean(diff)
ave, stddev = stat.stddev(diff)
tmp = "Differential stddev: " + "+-" + str(round(stddev, 2)) + "% Differential mean:" + str(round(ave, 2)) + "%\n"
tmp += "Last: " + str(calc_hum[-1] - supply_humid[-1]) + '%'
print(tmp)
print("\nRelative Humidity (%)")
print("Measured:")
mave, mstddev = stat.stddev(x)
print("Mean:", mave, "Stddev:", mstddev)
ave, stddev = stat.stddev(y)
rmsError = stat.rmsError(x, y)
mae = stat.meanAbsError(x, y)
print("Calculated:")
print("Mean:", ave, "Stddev:", stddev)
print("\nCorrelation coeficient\t", round(stat.correlation(x, y), 2))
print("RootMeanSquaredError\t", rmsError, "\t", round(rmsError / mstddev, 2), "stdDev")
print("MeanAbsoluteError\t", mae, "\t", round(mae / mstddev, 2), "stdDev")

print("\nPartial pressures (Pa)")
print("Measured:")
mave, mstddev = stat.stddev(mdP)
print("Mean:", mave, "Stddev:", mstddev)
ave, stddev = stat.stddev(cdP)
rmsError = stat.rmsError(mdP, cdP)
mae = stat.meanAbsError(mdP, cdP)
print("Calculated:")
print("Mean:", ave, "Stddev:", stddev)
print("\nCorrelation coeficient\t", round(stat.correlation(mdP, cdP), 2))
# print "MeanErrorSquared", stat.meanErrorSq(mdP,cdP)
print("RootMeanSquaredError\t", rmsError, round(rmsError / mstddev, 2), "stdDev")
print("MeanAbsoluteError\t", mae, round(mae / mstddev, 2), "stdDev")
print("End: " + tm.ctime(float(-time[-1] + tm.time())) + "\n")
