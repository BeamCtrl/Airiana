#!/usr/bin/python
import time as tm
import os
## make backup of datafile if large##
logfile = open("./RAM/data.log","r")
loglines = logfile.readlines()
buffer = []
buffer_len = -1
while buffer_len <> len(buffer) :
	buffer_len = len(buffer)
	for each in loglines:
		line = each.split(":")
		if float(line[0]) < (tm.time()-(60*24*60)):
			os.system("echo -n \""+each +"\">> ./data.log")
			buffer.append (loglines.pop(loglines.index(each)))
			#print "removed:",tm.ctime(float(line[0]))

os.system("rm -f ./RAM/data.log")
targetfile = open("./RAM/data.log","w+")
for each in loglines:
	targetfile.write(each)
targetfile.close()
logfile.close()
