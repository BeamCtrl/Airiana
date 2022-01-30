#!/usr/bin/python3
import time as tm
import os
# make backup of datafile if large##
logfile = ""
try:
	logfile = open("./RAM/data.log", "r")
except FileNotFoundError:
	print("no datafile found, creating")
	os.system("touch ./RAM/data.log")
	exit(0)
loglines = logfile.readlines()
buffer = []
buffer_len = -1
while buffer_len != len(buffer):
	buffer_len = len(buffer)
	for each in loglines:
		line = each.split(":")
		if float(line[0]) < (tm.time()-(25*60*60)):
			os.system("echo -n \"" + each + "\">> ./data.log")
			buffer.append(loglines.pop(loglines.index(each)))

os.system("rm -f ./RAM/data.log")
targetfile = open("./RAM/data.log", "w")
for each in loglines:
	targetfile.write(each)
targetfile.close()
logfile.close()
