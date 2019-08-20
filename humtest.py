#!/usr/bin/python
import numpy as np
import os, traceback, sys
import time as tm
import statistics as stat
os.chdir("/home/pi/airiana/")
if len(sys.argv)==1:
	fil = os.popen("cat ./RAM/data.log")
else :
	for each in sys.argv[1:]:
		if not each.isdigit():
			print "File:",each
			fil= open(each,"r")
	if len(sys.argv[1:])==1 and sys.argv[-1].isdigit():
		print "Single file: data.log"
		fil = open("data.log","r")

data = fil.readlines()
if "data.log" in sys.argv or  "cat data.log" in fil.name:
	print "Adding current data from RAM"
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
		for each in sys.argv:
			if each.isdigit():
				day= 60*60*24*int(each)
				break
		print "start time", tm.ctime(init)
		print "Will process ",len (data), "data points"
	else:
		day = 60*60*24
	i = 0
	x=[]
	y=[]
	l=len(data)
	for each in data:
	    i+=1
	    if round(float(i)/l*100,3)%1==0 and day <> 60*60*24:
		print "loading-"+str(int(float(i)/l*100))+"%"+str(int(float(i)/l*40)*"-"),
		print(chr(27)+"["+str(14+int(float(i)/l*40))+"D"),

	    try: 
	     #i+=1
	     #print i,
	     sys.stdout.flush()
	     tmp =each.split(":")
	     #temp = (tm.time()-day)-((tm.time()-day)%(3600))	
	     for entry in tmp: 
		if entry==np.nan or entry == "nan" or float(tmp[4])>100 or float(tmp[4])<0 : 
			#print float(tmp[4]),tmp[8]
			raise ZeroDivisionError
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
		x.append (calc_hum[-1])
		y.append (supply_humid[-1])
		diff.append (round(calc_hum[-1]-supply_humid[-1] ,3)) 
		if diff[-1]< -30: print tmp[0]
	    except IndexError:inside_hum.append(0)
	    except ValueError: pass#print tmp[0]
	    except ZeroDivisionError:pass
	    except: traceback.print_exc() 	
except:traceback.print_exc()
#print "\n",tm.ctime()
print "\nStart: " + tm.ctime(float(-time[0]+tm.time()))
print "max",max(diff),"%  min",min(diff),"%"
ave= stat.mean(diff)
ave ,stddev = stat.stddev(diff)
tmp = "Differential stddev: "+"+-"+ str(round(stddev,2))+ "% Differential mean:"+str(round(ave,2))+"%\n"
#tmp = "stddev: "+u"\u00B1"+ str(round(stddev,2))+ "% ave:"+str(round(ave,2))+"%"
tmp +=  "Last: "+ str(calc_hum[-1]-supply_humid[-1])+'%'
print tmp
print "Measured:"
ave, stddev = stat.stddev(x)
print "Mean:",ave,"Stddev:",stddev
ave, stddev = stat.stddev(y)
print "Calculated:"
print "Mean:",ave,"Stddev:",stddev
print "Correlation coeficient",stat.correlation(x,y)
print "Z test", stat.z_test(x,y)
print "End: " + tm.ctime(float(-time[-1]+tm.time()))+"\n"
