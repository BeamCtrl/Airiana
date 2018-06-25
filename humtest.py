#!/usr/bin/python
import numpy as np
import os, traceback, sys
import time as tm
os.chdir("/home/pi/airiana/")
if len(sys.argv)==1:
	fil = os.popen("cat ./RAM/data.log")
else: 
	fil= os.popen("cat "+sys.argv[-1])
data = fil.readlines()
#print data[-1], tm.time()
sen_hum = []
sen_temp = []
extract =[]
calc_hum = []
inlet = []
exhaust=[]
time =[]
supply=[]
supply_humid=[]
outside = []
cond_comp=[]
inside_hum=[]
diff = []
#data.pop(0)
#print "Processing line: ",
try:
	#i=0
	for each in data:
	    try: 
	     #i+=1
	     #print i,
	     #print(chr(27)+"["+str(len(str(i))+2)+"D"),
	     sys.stdout.flush()
	     tmp =each.split(":")
	     for entry in tmp: 
		if entry==np.nan: entry=0
	     #temp = (tm.time()-day)-((tm.time()-day)%(3600))	
	     if float(tmp[0]) > 0: #temp:	
		sen_hum.append(float(tmp[3]))
		sen_temp.append(float(tmp[1]))
		extract.append(float(tmp[2]))
		calc_hum.append(float(tmp[4]))
		inlet.append(float(tmp[5]))
		exhaust.append(float(tmp[6]))
		time.append(tm.time()-float(tmp[0]))
		supply.append(float(tmp[7]))
		supply_humid.append(float(tmp[8]))
		outside.append(float(tmp[9]))
		cond_comp.append(float(tmp[10]))
		inside_hum.append(int(tmp[11]))
		diff.append (round(calc_hum[-1]-supply_humid[-1] ,3)) 
	    except IndexError:inside_hum.append(0)
	    except ValueError: pass#print tmp[0]
	    except: traceback.print_exc() 	
except:traceback.print_exc()
red_hum = []
red_time=[]
i=0
for each in calc_hum:
	i+=1
	if float(each) <> 0.0: 
		try:
			red_time.append(time[i])
			red_hum.append(each)
			#print each, time[i]
		except:pass
#for each in diff: print each
import statistics as stat
print "\n",tm.ctime()
print "Start: " + tm.ctime(float(-red_time[0]+tm.time()))
print "max",max(diff),"%  min",min(diff),"%"
ave, stddev = stat.stddev(diff)
tmp = "stddev: "+"+-"+ str(round(stddev,2))+ "% ave:"+str(round(ave,2))+"%\n"
#tmp = "stddev: "+u"\u00B1"+ str(round(stddev,2))+ "% ave:"+str(round(ave,2))+"%"
tmp +=  "Last: "+ str(calc_hum[-1]-supply_humid[-1])+'%'
print tmp
print "End: " + tm.ctime(float(-red_time[-1]+tm.time()))+"\n"
