#!/usr/bin/python
import airdata,os,time,sys
import numpy, traceback
airdata_inst = airdata.Energy()
extract = float(sys.argv[1])
def get_humidity():
		global airdata_inst,extract
                day = 60*22
                templist = []
                data = os.popen("tail -n "+str(int(day))+" ./RAM/data.log")
		try:
			sunrise = int(os.popen ("sudo ./forcast2.0.py sun").readlines()[0].split(":")[0])
		except: sunrise = 6
                for each in data.readlines():
                         tmp = each.split(":")
			 try:
				 if time.localtime(float(tmp[0]))[3] >=sunrise - 1 and time.localtime(float(tmp[0]))[3] <= sunrise + 1 and float(tmp[0])>time.time()-(3*3600):
						templist.append (float(tmp[5]))
				 else:
					#print time.localtime(float(tmp[0]))[3]
				 	pass
			 except: print "error getting sunrise temp ranges"
		#print templist
                if len(templist)>0:inlet_min = numpy.average(templist)
		else:
			try:
				inlet_min = float(open("RAM/latest_static",'r').read())
			except:
				traceback.print_exc()
				raise IndexError
		airdata_inst.sat_vapor_press(extract)
		bottom = airdata_inst.pw
		airdata_inst.sat_vapor_press(inlet_min)
		top = airdata_inst.pw

		# adjustmet to closer match RHwmo below zero saturations
		if inlet_min < 0:
			top  = airdata_inst.pw + bottom*(float(inlet_min*-1.05)/100)

		print top/bottom*100, inlet_min

#input : indoor temp
#output: relative humidity as expressed by indoortemp last 24hrs min temp

try:
	get_humidity()
except:
	print -60, -1
	traceback.print_exc()
##############
