#!/usr/bin/python
import airdata,os,time,sys
import numpy
airdata_inst = airdata.Energy()
extract = float(sys.argv[1])
def get_humidity():
		global airdata_inst,extract
                day = 60*24
                templist = []
                data = os.popen("tail -n "+str(int(day))+" ./RAM/data.log")
                for each in data.readlines():
                         tmp = each.split(":")
			 try:
				 if time.localtime(float(tmp[0]))[3] >5 and time.localtime(float(tmp[0]))[3] <9 and float(tmp[0])>time.time()-(day*60):
	                         	#if float(tmp[0])<time.time()-(24*3600):
					templist.append (float(tmp[5]))
				 else:
					#print time.localtime(float(tmp[0]))[3]
				 	pass
			 except: pass
		#print templist
                inlet_min = numpy.average(templist)
		airdata_inst.vapor_max(inlet_min+1)
		top = airdata_inst.pw
		if inlet_min < 0:
			top = airdata_inst.pw*(1+((inlet_min*-2)/100)) # to translate into RHwmo
		airdata_inst.vapor_max(extract)
		bottom = airdata_inst.pw
		print top/bottom*100, inlet_min+1

#input : indoor temp
#output: relative humidity as expressed by indoortemp last 24hrs min temp

try:
	get_humidity()
except: print -1, -1
##############
