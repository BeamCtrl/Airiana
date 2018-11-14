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
if "data.log" in sys.argv:
	data+=	os.popen("cat ./RAM/data.log").readlines()

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
try:
	#i=0
	if len(sys.argv)>1:
		init = float(data[0].split(":")[0])
		day =  tm.time()-init
		print "start time", tm.ctime(init)
		print "Will process ",len (data), "data points"
	else:
		day = 60*60*24
	i = 0
	for each in data:
	    i+=1
	    if round(float(i)/len(data)*100,3)%20==0 and day <> 60*60*24: print str(round(float(i)/len(data)*100,3))+"%",
	    try: 
	     #i+=1
	     #print i,
	     #print(chr(27)+"["+str(len(str(i))+2)+"D"),
	     sys.stdout.flush()
	     tmp =each.split(":")

	     #temp = (tm.time()-day)-((tm.time()-day)%(3600))	
	     for entry in tmp: 
		if entry==np.nan: entry=0
	     if float(tmp[0]) > 0 and float(tmp[0]) > tm.time()-(day): #temp:	
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
import statistics as stat
#print "\n",tm.ctime()
print "\nStart: " + tm.ctime(float(-time[0]+tm.time()))
print "max",max(diff),"%  min",min(diff),"%"
ave, stddev = stat.stddev(diff)
tmp = "stddev: "+"+-"+ str(round(stddev,2))+ "% ave:"+str(round(ave,2))+"%\n"
#tmp = "stddev: "+u"\u00B1"+ str(round(stddev,2))+ "% ave:"+str(round(ave,2))+"%"
tmp +=  "Last: "+ str(calc_hum[-1]-supply_humid[-1])+'%'
print tmp
print "End: " + tm.ctime(float(-time[-1]+tm.time()))+"\n"
