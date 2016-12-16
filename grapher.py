#!/usr/bin/python
import numpy as np
#import matplotlib.pyplot as plt
import matplotlib, sys , os, traceback, subprocess
import time as tm
matplotlib.use('Agg')
from pylab import *
ioff()
## make backup of datafile if large##
rev = 1
if int(os.stat("./RAM/data.log").st_size) > 1024000:
	while os.path.isfile("data.log."+str(rev)): rev += 1
	os.system("mv ./RAM/data.log ./data.log."+str(rev))
	os.system("tail -n "+str(60*24)+" data.log."+str(rev)+" > ./RAM/data.log")
	lines= int(subprocess.check_output(["wc", "-l", "data.log."+str(rev)]).split(" ")[0])
	os.system("head -n "+str(lines-60*24)+" data.log."+str(rev) +" > tmp.log")
	os.system("mv tmp.log data.log."+str(rev))
######################
if len(sys.argv) >=2  and "debug" not in sys.argv[1] :day= int(sys.argv[1])
else:day = int(float(3600*24))
fil = os.popen("tail -"+str(day/60)+" ./RAM/data.log")
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
	     if float(tmp[0]) > tm.time()-(day):	
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
		#print len(red_time) ,len(red_hum), i
			

#fig, ax = subplots()
#print fig.properties()
fig=figure(1,figsize=(7,15),dpi=20)

s1=subplot(211)
s1.set_title("Temperatures")
if "debug" in sys.argv: plot(time[-day:-1],sen_temp[-day:-1], '-', linewidth=1,label="outdoor sensor temperature")
plot(time[-day:-1],extract[-day:-1], '-', linewidth=1,label="extract temperature")
plot(time[-day:-1],inlet[-day:-1], '-', linewidth=1,label="inlet temperature")
plot(time[-day:-1],exhaust[-day:-1], '-', linewidth=1,label="exhaust temperature")
plot(time[-day:-1],supply[-day:-1],'-',linewidth=1,label="supply temperature")
if "debug" in sys.argv:plot(time[-day:-1],outside[-day:-1],'-',linewidth=1,label="indoor sensor temperature")
grid(True)
ax = gca()
ax.set_ylim(int(min(inlet))-1, int(max(max(extract),max(inlet)))+1)
low, high = ax.get_ylim()
ax.yaxis.set_ticks(np.arange(int(low),int(high+1)))
ax.set_xlim(min(time[-day:-1]),max(time[-day:-1]))
ax.xaxis.set_ticks(np.arange(tm.time()%3600,max(time[-day:-1])+4*3600,4*3600))
ax.set_xticklabels(np.arange(tm.time()%3600,max(time[-day:-1])+4*3600,4*3600))
ax.invert_xaxis()
if "debug" in sys.argv:
	s2=subplot(212)
	s2.set_title("Humidities")
	plot(red_time,red_hum, '-', linewidth=1,label="calculated humidity")
	plot(time,cond_comp,'-',linewidth=1,label="condensation power")
	plot(time[-day:-1],sen_hum[-day:-1], '-', linewidth=1,label="outdoor sensor humidity")
	plot(time[-day:-1],supply_humid[-day:-1],'-',linewidth=1,label="supply estimate humidity")
	plot(time,inside_hum,'-',linewidth=1,label="inside sensor humidity")
	
	subplots_adjust( hspace=0.75 )
	ax = gca()
	ax.set_ylim(-30, int(max(sen_hum))+10)
	low,high = ax.get_ylim()
	ax.yaxis.set_ticks(np.arange(low,high+10,10))
	ax.set_xlim(min(time[-day:-1]),max(time[-day:-1]))
	ax.xaxis.set_ticks(np.arange(tm.time()%3600,max(time[-day:-1])+4*3600+1,4*3600))
	ax.set_xticklabels(np.arange(tm.time()%3600,max(time[-day:-1])+4*3600+1,4*3600))
	fig.canvas.draw()
	subplot(211)
	lgd =legend(bbox_to_anchor=(0.5, -0.3), loc=0, ncol=2, mode="expand", borderaxespad=.0)

#s2.set_position([0.1,0.8, 0.5, 0.5])
labels = [item.get_text() for item in s1.get_xticklabels()]
for i in range(len(labels)):
	try:
        	if not tm.localtime().tm_isdst: labels[i]=tm.strftime("%H:%M - %a",tm.gmtime(tm.time() -(float(labels[i]))-(tm.altzone)-3600))
        	else:labels[i]=tm.strftime("%H:%M - %a",tm.gmtime(tm.time() -(float(labels[i]))-(tm.altzone)))
	except:pass#print "label error"
s1.set_xticklabels(labels)
setp(s1.get_xticklabels(), rotation=45)

if "debug" in sys.argv:
	subplot(212)
	gca().set_xlim(min(time[-day:-1]),max(time[-day:-1]))
	labels = [item.get_text() for item in s2.get_xticklabels()]
	
	for i in range(len(labels)):
		try:
			if not tm.localtime().tm_isdst:labels[i]=tm.strftime("%H:%M - %a",tm.gmtime(tm.time() -(float(labels[i]))-(tm.altzone)-3600))	
			else:labels[i]=tm.strftime("%H:%M - %a",tm.gmtime(tm.time() -(float(labels[i])-(tm.altzone))))	
		except : pass#print "label error"
		s2.set_xticklabels(labels)
		setp(s2.get_xticklabels(), rotation=45)

	ax = gca()
	ax.invert_xaxis()
	
lgd = legend(bbox_to_anchor=(0.5, -0.3), loc=1, ncol=2, mode="expand", borderaxespad=.0)
grid(True)
	


fig.subplots_adjust(right=0.90)


savefig("./RAM/history.png",bbox_extra_artists=(lgd,),bbox_inches='tight')
