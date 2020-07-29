#!/usr/bin/python
import os,sys
import time as tm
import matplotlib,traceback
import airdata
air_obj=airdata.Energy()
from matplotlib import gridspec
class sensor ():
	def __init__(self):
		self.sensor_temp=0
		self.sensor_humid=0
device= sensor()
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pylab import *
ioff()
if len(sys.argv)>1:log=sys.argv[1]
else: log="151"
#print "logging sensor" , log
import random as rndm
#tm.sleep(rndm.randint(90,300))
def update_sensors():
	global device
	try:
		fd=open ("sensors")
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
			device.sensor_temp =float(sensor_dict[log]["temperature"])
			device.sensor_humid =int(sensor_dict[log]["humidity"])
		except: pass
		if device.sensor_temp<>0.0 and device.sensor_humid <>0:
			temp.append(device.sensor_temp)
			humid.append(device.sensor_humid)
			dewpoint.append(air_obj.dew_point(humid[-1],temp[-1]))
			time.append(tm.time())  
	except : 
		print "new sensor data error"
		traceback.print_exc()
	finally: fd.close()
sensor_dict = {}
time=[]
temp=[]
humid=[]
dewpoint=[]
#hum_line=plot(time,humid)[0]
#print temp_line

fd = open(str(log)+".log","a+")
fd.seek(0)
for each in fd.readlines():
	data = each.split(":")
	if float(data[0]) > tm.time()-3600*24*1000:
		#print data
		time.append(float(data[0]))
		temp.append(float(data[1]))
		humid.append(int(data[2][0:-1]))
		dewpoint.append(air_obj.dew_point(humid[-1],temp[-1]))
fig=figure(1,figsize=(11,8),dpi=250)
#s1=subplot("111")
#temp_line=plot(time,temp)[0]
#hum_line=plot(time,humid)[0]
#grid(True)

while True:
	update_sensors()
	if device.sensor_temp <>0 and device.sensor_humid <>0:
		fd.write(str(tm.time())+":"+str(device.sensor_temp)+":"+str(device.sensor_humid)+"\n")	
		fd.flush()
		#print device.sensor_temp,"C",device.sensor_humid,"%", len(humid),len(time)
	clf()

	s1=subplot("111")
	s1.set_title("Sensor: "+str(log))
	fig.subplots_adjust(bottom=0.2, top=0.95,
                    hspace=0.7, wspace=0.7)
	#print max(time),min(time)
	ax = gca()
	#low, high = ax.get_ylim()
	low, high = -20,100
	ax.yaxis.set_ticks(np.arange(int(low),int(high+1),5))
	gca().set_autoscalex_on(True)
	gca().set_xlim(min(time),max(time))
	hum_line=plot(time,humid,"-")[0]
	temp_line=plot(time,temp,"-")[0]
	dewpoint_line=plot(time[0:len(dewpoint)],dewpoint,"-")[0]
	grid(True)
	draw()
	
	labels = [item.get_text() for item in s1.get_xticklabels()]
	num = len(labels)-1
	pos=0
	#print labels
	try:
		#for i in range(int(min(time)),int(max(time)),int((max(time)-min(time))/num+1)):
		for each in  gca().get_xticks():
			labels[pos]=tm.strftime("%H:%M - %d/%m - %Y",tm.localtime(float(each)))
			pos+=1
	except:pos+=1
	print labels
	s1.set_xticklabels(labels)
	setp(s1.get_xticklabels(), rotation=45)
	draw()

	savefig("./RAM/"+str(log)+".png")
	#tm.sleep((60*60*12)+rndm.randint(0,30))
	tm.sleep(120)
	sys.stdout.flush()
