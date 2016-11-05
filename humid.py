#!/usr/bin/python
import airdata,os,time,sys
airdata_inst = airdata.Energy()
extract = float(sys.argv[1])
def get_humidity():
		global airdata_inst,extract
                day = 60*24
                templist = []
                data = os.popen("tail -n "+str(day/1)+" data.log")
                for each in data.readlines():
                         tmp = each.split(":")
                         if float(tmp[0])<time.time()-(24*3600):
			 	pass
			 else:                    
				templist.append (float(tmp[5]))

                inlet_min = min(templist)
		airdata_inst.vapor_max(inlet_min)
		top = airdata_inst.pw
		airdata_inst.vapor_max(extract)
		bottom = airdata_inst.pw
		print top/bottom*100, inlet_min


get_humidity()

