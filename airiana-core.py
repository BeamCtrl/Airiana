#!/usr/bin/python
import airdata
import serial, numpy, select, threading
import minimalmodbus, os, traceback
import time,struct,sys
import statistics
import signal
#from mail import *
vers = "7.7"
Running =True
savecair=False
# Register cleanup
def exit_callback(self, arg):
		print "Gracefull shutdown\nexiting on signal",self
		sys.stdout.flush()
		Running = False
		time.sleep(3)
                os.system("cp ./RAM/data.log ./data.save")
                if threading.enumerate()[-1].name=="Timer": threading.enumerate()[-1].cancel()
                cmd_socket.close()
		sys.exit()

signal.signal(signal.SIGTERM, exit_callback)
signal.signal(signal.SIGINT , exit_callback)

#exec util fnctns
os.chdir("/home/pi/airiana/public")
os.system("./ip-replace.sh")  # reset ip-addresses on buttons.html
os.chdir("/home/pi/airiana/")
os.system("./http &> /dev/null") ## START WEB SERVICE
#os.system("./forcast.py &> /dev/null") ## Get forcast
listme=[]
## cpy saved data to RAM ##
if  not os.path.lexists("./data.save"):
	os.system("touch data.save")
else:
	os.system("cp data.save ./RAM/data.log")
#################################
if  not os.path.lexists("./RAM/forecast.txt"):
	os.system("touch ./RAM/forecast.txt")
#################################
if "debug" in sys.argv and not os.path.lexists("./sensors"):
	os.system("touch sensors")
#################################
starttime=time.time()
#Setup deamon env
if "daemon" in sys.argv:
	fout = os.open("./RAM/out",os.O_WRONLY|os.O_CREAT)
	os.dup2(fout,sys.stdout.fileno())
	print "Output redirected to file;"
	#os.system("rm -f ./RAM/err")
	ferr = os.open("./RAM/err",os.O_WRONLY|os.O_CREAT)
	os.dup2(ferr,sys.stderr.fileno())

# Setup serial, RS 485 to machine
if os.path.lexists("/dev/serial0"):
	print "Communication started on device Serial0;"
	unit = "/dev/serial0"
	#os.system("sleep 2")
else :
	print "Communication started on device ttyAMA0;"
	unit = "/dev/ttyAMA0"
minimalmodbus.BAUDRATE = 19200
minimalmodbus.PARITY = serial.PARITY_NONE
minimalmodbus.BYTESIZE = 8
minimalmodbus.STOPBITS=1
client = minimalmodbus.Instrument(unit,1)
client.debug=False
client.precalculate_read_size=False
client.timeout= 0.05
#############################################
wait_time = 0.00
bus=os.open(unit,os.O_RDONLY)
################################# command socket setup
import socket
hostname =os.popen("hostname").read()[:-1]
print "Trying to Run on host:",hostname,", for 60sec;"

while True:
	try:
		cmd_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
		cmd_socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
		cmd_socket.bind(("0.0.0.0",9876))
		break
	except:
		os.system("sleep 1")
		print "sleeping"
		if time.time()-starttime> 60:break

########### global uty functions################
sensor_dict = {}

#SEND PING TO EPIC HEADMASTER
def report_alive():
	try:
		msg = os.popen("/sbin/ifconfig wlan0").readlines()
		for each in msg:
			if each.find("HWaddr") <> -1 or each.find("ether")<>-1:
				message = each
				message += os.popen("hostname -I").read()
				try:
					message += "\nstatus:"+str(device.status_field)+"\n"
				except: pass
				if "debug" in sys.argv: device.msg +=  message + "\n"

		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
		sock.sendto(message, (socket.gethostbyname("lappy.asuscomm.com"), 59999))
	except: pass

#READ AVAIL SENSOR DATA
def update_sensors():
	try:
		fd=open ("sensors","r")
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
			device.sensor_temp =float(sensor_dict["91"]["temperature"])
			device.sensor_humid =int(sensor_dict["91"]["humidity"])
			device.airdata_inst.humid = float(device.sensor_humid)/100
		except KeyError: pass#device.msg +="\nerror on sensor 91"
		try:
			device.inside =float(sensor_dict["92"]["temperature"])
			device.inside_humid =int(sensor_dict["92"]["humidity"])
		except KeyError: pass#device.msg +="\nerror on sensor 92"

	except IndexError:
		device.msg += "\nnew sensor data error"
		traceback.print_exc()
#Auto updater
def update():
	os.system("wget -q -O ./RAM/VERS http://lappy.asuscomm.com:443/current_version")
	ver = os.popen("cat ./RAM/VERS").read()
	ver = ver.split(" ")
	
	if "debug" in sys.argv:
		print vers, "->", ver
	if vers not in ver[0] and "Valid" in ver[1]:
		print "Updating Airiana system software to",ver[0]
		os.system("./update&")	
	
#WRITE TO DATA.LOG
def logger ():
	try:
		fdo = open("./RAM/data.log","a+")
		#+str(device.extract_humidity*100)\
		cmd = ""   		\
		+str(time.time()) 		\
		+":"				\
		+str(device.sensor_temp)	\
		+":"				\
		+str(round(device.extract_ave,2))	\
		+":"				\
		+str(round(device.sensor_humid,2))	\
		+":"				\
		+str(round(device.new_humidity,2))\
		+":"				\
		+str(round(device.inlet_ave,2))		\
		+":"				\
		+str(round(device.exhaust_ave,2))	\
		+":"				\
		+str(round(device.supply_ave,2))		\
		+":"				\
		+str(round(device.humidity_target,2))	\
		+":"				\
		+str(device.inside)		\
		+":"				\
		+str(round(numpy.average(device.cond_data),1))\
		+":"+str(device.inside_humid)
		fdo.write(cmd+"\n")
		fdo.close()
	except:traceback.print_exc()

#PRINT COMM SETTING
def display_settings():
        clear_screen()
        print str(client).replace(",","\n")

#CLEAR WHATS ON SCREEN AND RETURN TO UPPER LEFT
def clear_screen():
        if "daemon" in sys.argv:
                os.lseek(fout,0,0)
                os.ftruncate(fout,0)
                os.fsync(fout)
        else:print chr(27) +"[2J\x1b[H"
##############################################
#######Request object for doing modbus comms##
class Request(object):
	def __init__(self):
		self.connect_errors= 0
		self.checksum_errors = 0
		self.multi_errors = 0
		self.write_errors = 0
		self.buff= ""
		self.counter = 0
		self.error_time=time.time()
		self.wait_time =  wait_time
		self.prev_rate = 0
		self.iter = 0
	def modbusregisters(self,start,count,signed=False):
		client.precalculate_read_size=True
		self.iter += 1
		try:
			self.response= "no data"
			try:
				pass#os.write(bus,"\0x01")
			except: pass
			self.response = client.read_registers(start,count)
			if signed:
				for each in self.response:
					if each & 0x8000: each -= 0xFFFF
		except ValueError as error:
			#print "multi, checksum error,retry:",self.checksum_errors,error.message,";"
			#os.write(ferr,"read many: "+str(error)+"\n")
			#print error.message.find("\x01\x83\x02\xc0\xf1")
			if  error.message.find("\x01\x83\x02\xc0\xf1")<>-1:
				print "multi, address out of range;"
				#exit()
			self.checksum_errors +=1
			self.modbusregisters(start,count)
		except IOError as error:
			self.connect_errors += 1
			if self.connect_errors > 100 or self.multi_errors >100:
				self.error_review()
				#os.write(ferr,"read many: "+str(error)+"\n")
			#if self.connect_errors > 200: exit_callback(self,None)
			self.modbusregisters(start,count)
		client.precalculate_read_size=False

	def error_review (self):
		delta = self.iter - self.error_time
		self.error_time = self.iter
		rate = float(self.connect_errors+self.checksum_errors+self.write_errors+self.multi_errors) / delta
		if rate >= 0.9:
			os.read(bus,1000)
			time.sleep(1)
		os.system ("echo "+str(rate)+" "+ str(self.wait_time)+" > RAM/error_rate")
		self.connect_errors = 0
		self.checksum_errors = 0
		self.write_errors = 0
		self.multi_errors = 0
		#self.prev_rate = rate

	def modbusregister (self,address,decimals):
		self.iter += 1
		client.precalculate_read_size=True

		try:
			self.response = "no data"
			self.buff += os.read(bus,20) # bus purge
                        self.response = client.read_register(address,decimals,signed=True)
		except IOError as error:
	 		self.connect_errors += 1
			if self.connect_errors > 100: self.error_review()
			self.buff += os.read(bus,20) # bus purge
			#print "single, no response, retry:",self.connect_errors,address,";"
			self.modbusregister(address,decimals)
		except ValueError as error:
			#print "single, checksum error,retry:",self.checksum_errors,error,";"
			#os.write(ferr,"read: "+str(error)+"\n")
			self.buff += os.read(bus,20) # bus purge
			self.checksum_errors +=1
			self.modbusregister(address,decimals)
		client.precalculate_read_size=False

	def write_register(self, reg, value,functioncode=6):
		self.iter += 1
		client.precalculate_read_size=True
		if start == value: return 0
		try:
			#print "set", reg, "to",value
			#time.sleep(self.wait_time)
			#print os.read(bus,20)
			resp = client.write_register(reg,value,0,6)
		except IOError as error:
			#print "write, ioerror",error,os.read(bus,20),";"
			#os.write(ferr,"write: "+str(error)+"\n")
			self.write_errors += 1
			#self.write_register(reg,value)
			pass
		except ValueError as error:
			#print "write, val error",error,os.read(bus,20),"\n--",reg," ",value,";"
			#os.write(ferr,"write: "+str(error)+"\n")
			self.write_errors += 1
			#self.write_register(reg,value)
			pass


#################################################################################
start = time.time() # START TIME
# init request class for communication
req = Request()
############DEVICE CLASS FOR SYSTEMAIR VR400DCV#############################
class Systemair(object):
	def __init__(self):
		self.fanspeed=1
		self.system_types = {0:"VR400",1:"VR700",2:"VR700DK",3:"VR400DE",4:"VTC300",5:"VTC700",
					12:"VTR150K",13:"VTR200B",14:"VSR300",15:"VSR500",16:"VSR150",
					17:"VTR300",18:"VTR500",19:"VSR300DE",20:"VTC200",21:"VTC100"}
		self.has_RH_sensor = ("VTR300")
		self.rotor_states={0:"Normal",1:"Rotor Fault",2:"Rotor Fault Detected"
				,3:"Summer Mode transitioning",4:"Summer Mode"
				,5:"Leaving Summer Mode",6:"Manual Summer Mode"
				, 7:"Rotor Cleaning in Summer Mode",8:"Rotor cleaning in manual summer mode"
				,9:"Fans off",10:"Rotor Cleaning during fans off", 11:"Rotor Fault, but conditions normal"}
		self.speeds= {0:"Off",1:"Low",2:"Normal",3:"High",4:"undefined"}
		self.weather_types= {\
				1:"Clear skies",2:"Fair weather",3:"Partly cloudy",\
				4:"Cloudy",40:"Light showers",41:"Heavy showers",\
				5:"Rain",24:"Light rain and thunder",\
				6:"Rain and thunder",25:"Heavy rain and thunder",\
				42:"light sleet showers",7:"Sleet showers",\
				43:"Heavy sleet showers",26:"Light sleet showers and thunder",\
				20:"sleet showers and thunder",27:"Heavy sleet showers and thunder",\
				44:"Light snowfall",8:"Snow",\
				45:"Heavy snow showers",28:"Light snow and thunder",\
				29:"Heavy snow and thunder",\
				21:"Snow showers and thunder",46:"Light rain",\
				9:"Rain",10:"Heavy rain",\
				30:"Light rain and thunder",\
				22:"Rain and thunder",\
				11:"Heavy rain and thunder",\
				47:"Light sleet",\
				12:"Sleet",\
				48:"Heavy Sleet",\
				31:"Light sleet and thunder",\
				23:"Sleet and thunder",\
				32:"Heavy sleet and thunder",\
				49:"Light snow",\
				13:"Snow",\
				50:"Heavy snow",\
				33:"Light snow and thunder",\
				14:"Snow and thunder",\
				34:"Heavy snow and thunder",\
				15:"Fog",-1:"No weather data"}
		self.avg_frame_time = 1
		self.rawdata = []
		self.press_inhibit = 0
		self.local_humidity = 0.0
		self.eff_ave=[90]
		self.diff_ave=[0]
		self.totalenergy = 0.0
		self.averagelimit = 1800#min122
		self.sf = 18
		self.ef = 23
		self.ef_rpm = 1500
		self.sf_rpm = 1500
		self.inlet = []
		self.inlet_ave =0
		self.supply = []
		self.supply_ave=0
		self.extract = []
		self.extract_ave=0
		self.electric_power = 1
		self.house_heat_limit = 8
		self.humidity_target =0
		self.exhaust = []
		self.exhaust_ave=0
		self.supply_power=0
		self.extract_power=0
		self.extract_combined=0
		self.gain = 0
		self.loss=0
		self.register = {}
		self.kinetic_compensation = 0
		self.starttime = time.time()
		self.timer = 0
		self.defrost = False
		self.current_mode=0
		self.extract_humidity=0.40 # relative humidity
		self.extract_humidity_comp=0.00 # relative humidity re compensated
		self.condensate_compensation =0
		self.filter_remaining = 0
		self.cond_eff = 1
		self.dur=1.0
		self.extract_dt = 0.0
		self.update_airdata_instance()
		self.shower =False
		self.dyn_coef = 0
		self.msg = ""
		self.inside =0
		self.inside_humid=0
		self.exchanger_mode=5
		self.rotor_state = 0
		self.rotor_active = "Yes"
		self.inhibit = time.time()
		self.system_name = ""
		self.sensor_temp = 0
		self.sensor_humid = 0
		self.modetoken = 0
		self.cooling = 0
		self.forcast = [-1,-1]
		self.dt_hold = 0
		self.dt_entries  =0
		self.extract_dt_long_time = time.time()
		self.iter=1
		self.extract_dt_long = 0
		self.cool_mode=0
		self.temps = []
		self.temp_state = 0
		self.condensate = 0
		self.coef = 0.17
		self.tcomp = 0
		self.inlet_coef = 0.1
		self.filter = 0
		self.filter_limit = 0
		self.cond_data = []
		self.cond_valid = False
		self.cond_dev= 0
		self.i_diff = []
		self.time = []
		self.extract_dt_list = []
		self.humidity_comp = 0
		self.prev_static_temp = 0
		self.indoor_dewpoint = 0
		self.target = 22
		self.energy_diff=0
		self.new_humidity=40
		self.div =0
		self.set_system_name()
		self.RH_valid = 0
		self.hum_list = []
		self.status_field = [-1,0,0,self.system_name,vers,os.popen("git log --pretty=format:'%h' -n 1").read()]
		self.heater = 0
		self.exchanger_speed = 0
	#get heater status
	def get_heater(self):
		if not savecair:
			req.modbusregister(200,0)
	                self.heater = int(req.response)
		else: self.heater = 0
		
	#set heater status
	def set_heater(self,heater):
		req.write_register(200,heater)
	
	#get and set the Unit System name, from system types dict
	def set_system_name(self):
		req.modbusregister(500,0)
		self.system_name = self.system_types[req.response]

	#Get relative humidity from internal sensor, valid units in self.has_RH_sensor tuple
	def get_RH (self):
	    if not savecair:
		req.modbusregister(382,0)
		self.RH_valid = int(req.response)
		req.modbusregister(380,0)
		if self.RH_valid:
			self.new_humidity = int(req.response)
			self.hum_list.insert(0,self.new_humidity)
			if len(self.hum_list)>300:
				self.hum_list.pop(-1)
	    else:
		req.modbusregister(12135,0)
		if req.response <> 0:
			self.RH_valid = 1
			self.new_humidity = int(req.response)
			self.hum_list.insert(0,self.new_humidity)
			if len(self.hum_list)>self.averagelimit:
				self.hum_list.pop(-1)

	#get the nr of days  used and alarm lvl for filters
	def get_filter_status(self):
	    if not savecair:
		req.modbusregister(600,0)
		self.filter_limit = int(req.response)*31
		req.modbusregister(601,0)
		self.filter = req.response
		self.filter_remaining = round(100*(1 - (float(self.filter)/self.filter_limit)),1)
		if self.filter_remaining <0: self.filter_remaining = 0
	    else:
		req.modbusregister(7000,0)
		self.filter_limit = int(req.response)*31
		req.modbusregister(7004,0)
		lowend = req.response
		req.modbusregister(7005,0)
		highend= req.response<<16
		self.filter = self.filter_limit- (lowend+highend) / (3600*24)
		self.filter_remaining = round(100*(1 - (float(self.filter)/self.filter_limit)),1)
		if self.filter_remaining <0: self.filter_remaining = 0

	#get status byte for temp probes
	def get_temp_status(self):
	    if not savecair:
		req.modbusregister(218,0)
		self.temp_state= req.response

	def print_attributes(self):
		for each in dir(self):
			exec str( "obj= self."+each)
			if isinstance(obj, (int,float,str,list)): exec str( "print each,  self."+each)
		if not "daemon" in sys.argv : raw_input("press enter to resume")
		else:
			print "break"
			os.system("sleep 2")


	def get_fanspeed(self):
	    if not savecair:
		req.modbusregister(100,0)
		self.fanspeed =int(req.response)
		return self.fanspeed

	def update_temps(self):
	    if not savecair:
		req.modbusregisters(213,5)# Tempsensors 1 -5
		self.time.insert(0,time.time())
		if len(self.time) > self.averagelimit: self.time.pop(-1)


		if req.response[2]>6000:
			req.response[2] -=0xFFFF

		self.temps = req.response[:]
		self.rawdata.insert(0,self.temps)

		# NEGATYIVE VAL sign bit twos complement
		if req.response[4]>6000:
			req.response[4] -= 0xFFFF

		if len(self.rawdata)>self.averagelimit:self.rawdata.pop(-1)
		#req.response[1] #EXTRACTreq.BBresponse[2] #EXHAUST req.response[0] #Supply pre elec heater
		#req.response[3] #Supply post electric heater req.response[4] Inlet
		if self.system_name=="VR400":
			if self.rotor_active == "No" and self.coef <> 0.10:
				if self.coef-0.10>0:self.coef -= 0.0001
                        	else: self.coef += 0.0001
				self.coef=round(self.coef,5)
			if self.rotor_active == "Yes" and self.coef <> 0.10:
				if self.coef-0.10>0:self.coef -= 0.0001
				else: self.coef += 0.0001
				self.coef=round(self.coef,5)
			
			self.dyn_coef = self.fanspeed * 1.5
			"""if self.inhibit and self.extract_dt>0.1 and not self.shower:
					self.dyn_coef +=0.1
			if self.inhibit and self.extract_dt<-0.1 and not self.shower:
					self.dyn_coef -=0.1
			if abs(self.dyn_coef) > 10:
				self.dyn_coef = self.dyn_coef/2"""
			if self.sf <> 0:
				self.tcomp= ((req.response[1]-req.response[4])*self.coef)-self.dyn_coef #float(7*34)/self.sf # compensation (heat transfer from duct) + (supply flow component)
			else:
				self.tcomp = 0
			if self.rotor_active =="No"  and self.inlet_coef <0.14:self.inlet_coef+= 0.0001 #OFF
			if self.rotor_active =="Yes" and self.inlet_coef >0.07:self.inlet_coef-= 0.0001 # ON
		
		#update [4] with inlet coef
		req.response[4]  -= (req.response[1]-req.response[4])*self.inlet_coef #inlet compensation exchanger OFF/ON
		#update [1] with tcomp, after calc of [4]
		req.response[1] += self.tcomp

		#DO CALC FOR REQ[2] exhaust temp expectancy for VR300 machines as they have no exhust temp sensor:
		#########
		###########################################
		if self.system_name=="VTR300":
			#req.response[2] = req.response[4]
			pass
		#if self.rotor_active =="No" :
		#	req.response[2]  -= (req.response[1]-req.response[4])*0.01  #exhaust compensation exch off
		#else : 	req.response[2]  -= (req.response[1]-req.response[4])*0.06  #exhaust compensation exch ON
		
		self.extract.insert(0, float(req.response[1])/10)
		self.exhaust.insert(0, float(req.response[2])/10)
		self.supply.insert (0, float(req.response[3])/10)
		self.inlet.insert  (0, float(req.response[4])/10)
		
      		#limit array size
		for each in [self.inlet,self.supply,self.extract,self.exhaust]:
			if len(each)>self.averagelimit: each.pop(-1)
	    else:
		self.time.insert(0,time.time())

		##EXTRACT
		req.modbusregister(12543,1)
		extract = req.response
		req.modbusregister(12102,1)
		supply = req.response
		req.modbusregister(12101,1)
		inlet = req.response
		self.rawdata.insert(0,(inlet,supply,extract))
		if len(self.rawdata)>self.averagelimit:
			self.rawdata.pop(-1)
		self.dyn_coef = float(3200)/self.ef_rpm *0.1
		self.tcomp= ((extract-inlet)*0.00)+self.dyn_coef #float(7*34)/self.sf # compensation (heat transfer from duct) + (supply flow component)

		self.extract.insert(0,float(extract+self.tcomp))
		## SUPPLY
		self.supply.insert(0,float(supply))
		### INLET
		#if self.rotor_active =="No"  and self.inlet_coef <0.03:self.inlet_coef+= 0.0001 #OFF
		#if self.rotor_active =="Yes" and self.inlet_coef >0.00:self.inlet_coef-= 0.0001 # ON
		inlet_comp = ((float(3200)/self.sf_rpm)-1)*0.01
		tweak  = (extract-inlet)*inlet_comp #inlet compensation exchanger OFF/ON
		self.inlet.insert(0,float(inlet-tweak))


		if len(self.extract)>self.averagelimit: self.extract.pop(-1)
		if len(self.exhaust)>self.averagelimit: self.exhaust.pop(-1)
		if len(self.supply)>self.averagelimit: self.supply.pop(-1)
		if len(self.inlet)>self.averagelimit: self.inlet.pop(-1)
		if len(self.time)>self.averagelimit: self.time.pop(-1)
	    try:
		self.eff = (self.supply_ave-self.inlet_ave)/(self.extract_ave-self.inlet_ave)*100
	    except ZeroDivisionError:
		self.eff = 100
	    self.eff_ave.insert(0,self.eff)
	    if len(self.eff_ave) >self.averagelimit: self.eff_ave.pop(-1)

	def flow_calcs(self):
		extr_vol = self.ef
		supp_vol = self.sf
		inlet_T  = 0
		extract_T= 0
		exhaust_T= 0
		supply_T = 0
		for each in self.rawdata:
			inlet_T   += float(each[4])/10
			extract_T += float(each[1])/10
			exhaust_T += float(each[2])/10
			supply_T  += float(each[3])/10
		inlet_T   = inlet_T/len(self.rawdata)
		extract_T = extract_T/len(self.rawdata)
		exhaust_T = exhaust_T/len(self.rawdata)
		supply_T  = supply_T/len(self.rawdata)

		ener_in = 0
		ener_out = 0

		casing_diff = extract_T - inlet_T
		in_ave = supply_T - inlet_T
		out_ave = extract_T - exhaust_T
		duct_diff = out_ave - in_ave

		ener_in  = self.airdata_inst.energy_flow(supp_vol,inlet_T,supply_T)
		ener_out = self.airdata_inst.energy_flow(extr_vol,exhaust_T,extract_T)

		ener_diff = ener_out - ener_in
		try:
			diff_deg = ener_diff / casing_diff
		except ZeroDivisionError: pass
		if self.iter % 100 == 0:
			self.msg += "\Energ.flow Differential: "+str(diff_deg)+"W/deg\nin: "+str(int(ener_in))+" out: "+str(int(ener_out))\
				+" casing_diff"+str(int(casing_diff))+"C\n"
		#self.msg += "inlet\tsupply\textract\texhaust\n"+str(inlet_T)+"\t"+str(supply_T)+"\t"\
		#		+str(extract_T)+"\t"+str(exhaust_T)+"\n"

	def set_fanspeed(self,target):
		self.inhibit = time.time()
		actual = self.fanspeed
		#print actual,"->",target
	    	if target>=4: target=0
		if target<0: target=0
   		try:
	    		if actual == target:
				pass
				#print "done"
	    		else:
				#print "write to device", target
				if not savecair:
					req.write_register(100,target)
				else:
					req.write_register(1130,target+1)
	    			#time.sleep(wait_time*50)
			if int(self.get_fanspeed()) == target :
				#print "succsess", target
				self.fanspeed=target
			else:
				#print "error setting speed"
				self.set_fanspeed(target)
		except ValueError as error:
			#print error
			if "Wrong" == error.message[0:5]:
				self.get_fanspeed()
				if self.fanspeed<>target:self.set_fanspeed(target)
			if "Check" == error.message[0:5]:
				self.set_fanspeed(target)
    		except IOError as error:
    			#print "no response", "fanspeed:", self.speeds[self.fanspeed]
			self.set_fanspeed(target)
		except: print "unhandled exception", sys.exc_info[0]
		self.update_airflow()


	def update_fan_rpm(self):
	    if not savecair:
		req.modbusregisters(110,2)
		self.sf_rpm,self.ef_rpm=req.response[0],req.response[1]
		try:
			self.electric_power= (self.ef_rpm/(100/(float(float(self.ef_rpm)/1381)**1.89))+self.sf_rpm/(100/(float(float(self.sf_rpm)/1381)**1.89)))
		except ZeroDivisionError:self.electric_power=0
		if "Yes" in self.rotor_active :self.electric_power +=10 # rotor motor 10Watts
		self.electric_power+=5#controller power

	    else:
		req.modbusregisters(12400,2)
		self.sf_rpm ,self.ef_rpm = req.response[0],req.response[1]
		try:
			self.electric_power= (self.ef_rpm/(100/(float(float(self.ef_rpm)/1381)**1.89))+self.sf_rpm/(100/(float(float(self.sf_rpm)/1381)**1.89)))
		except ZeroDivisionError:self.electric_power=0

	def update_fanspeed(self):
	    if not savecair:
		req.modbusregister(100,0)
		self.fanspeed = req.response
	    else:
		req.modbusregister(1200,0)
		self.fanspeed = req.response-1
		
	def update_airflow(self):
	    if not savecair:
		req.modbusregisters(101,6)
		sf=[req.response[0],req.response[2],req.response[4]]
		ef=[req.response[1],req.response[3],req.response[5]]
		tmp=self.fanspeed#self.get_fanspeed()
		if tmp<=0: tmp=1
		self.sf= sf[tmp-1]
		self.ef= ef[tmp-1]
		if self.fanspeed == 0 :
			self.ef=0
			self.sf=0
	    else:
		req.modbusregisters(14000,2)
		self.sf,self.ef = req.response[0],req.response[1]


	def update_airdata_instance(self):
		self.airdata_inst= airdata.Energy()

	def update_xchanger(self):
		self.inlet_ave = numpy.average(self.inlet)
		self.supply_ave = numpy.average(self.supply)
		self.extract_ave = numpy.average(self.extract)
		if self.system_name == "VR400":
			self.exhaust_ave = numpy.average(self.exhaust)
		if self.fanspeed <> 0:
			#self.availible_energy =  self.airdata_inst.energy_flow(self.ef,self.extract_ave,self.inlet_ave)+self.airdata_inst.condensation_energy((self.airdata_inst.vapor_max(self.exhaust_ave)-self.airdata_inst.vapor_max(self.inlet_ave))*((self.ef)/1000))

			try:self.used_energy    = self.airdata_inst.energy_flow(self.sf,self.supply_ave,self.inlet_ave)
			except: self.used_energy = 0
			factor = 1 # casing transfer correction factor
			if   self.rotor_active=="Yes":
				if self.fanspeed ==3:
					factor =0 # 3.3
				elif self.fanspeed ==1:
					if self.ef == self.sf: factor = 0#3.95
					else : factor=0#2.9
				elif self.fanspeed ==2: # corrective factors W/deg
					factor =0 # 5.65
			elif self.rotor_active =="No":
				if self.fanspeed == 1   :
					factor= 0 # 3#  - 16 constant# red  from casing heat transfer
				elif self.fanspeed == 2 :
					factor = 0 # 1.9#  - 16 constant# red  from casing heat transfer
				elif self.fanspeed == 3 :
					factor = 0
			else: factor=1
 			if self.rotor_active == "Yes":
				self.supply_power   = self.used_energy-00-(self.extract_ave-self.inlet_ave)*factor#  constant# red  from casing heat transfer
 			else: self.supply_power   = self.used_energy-0-(self.extract_ave-self.inlet_ave)*factor#  constant# red  from casing heat transfer

			try:self.extract_exchanger  = self.airdata_inst.energy_flow(self.ef,self.extract_ave,self.exhaust_ave)
			except: self.extract_exchanger = 0
			self.extract_offset =0 #float(8)*(self.extract_ave-self.supply_ave)# + 20Watt/degC transfer after exchanger unit
			self.extract_power = self.extract_exchanger+self.extract_offset
			self.extract_combined = self.extract_power + self.condensate_compensation
			self.energy_diff = self.supply_power-self.extract_power
			try:self.loss = self.airdata_inst.energy_flow(self.ef,self.exhaust_ave,self.inlet_ave)+self.airdata_inst.energy_flow(self.sf,self.extract_ave,self.supply_ave)
			except: self.loss =0
			try:self.diff_ave.insert(0,(-1*(self.extract_combined-self.supply_power)/((self.supply_power+self.extract_combined)/2))*100)
			except ZeroDivisionError:pass
			if len (self.diff_ave) > self.averagelimit: self.diff_ave.pop(-1)
			self.i_diff.append((self.extract_combined-self.supply_power)*-1)
			if len(self.i_diff) > 15: self.i_diff.pop(0)
			try:
				self.dur = self.time[0]-self.time[1]
				if self.rotor_active =="Yes": self.totalenergy+=(self.loss*self.dur)/3600
				elif self.extract_ave > self.supply_ave: self.cooling += (self.loss*self.dur)/3600
				else: self.gain += (self.loss*self.dur)/3600
			except: pass

			self.cond_data.append(self.energy_diff)
			if len(self.cond_data)> self.averagelimit+5000:self.cond_data.pop(0)
	# For units whithout exhaust temp sensor calc expected exhaust temp based on transfered energy in supply
	def calc_exhaust(self):
		exhaust = self.extract_ave- self.airdata_inst.temp_diff(self.supply_power,self.extract_ave,self.ef)*0.94
		self.exhaust_ave=exhaust

	def get_rotor_state(self):
	    if not savecair:
		req.modbusregister(206,0)
	        self.exchanger_mode= req.response
		req.modbusregisters(350,2)
                self.rotor_state = req.response[0]
                if req.response[1]:self.rotor_active = "Yes"
                else: self.rotor_active = "No"
		self.status_field[1] = self.exchanger_mode
	    else:
		req.modbusregister(2140,0)
		if req.response:
			self.rotor_active = "Yes"
                else:
			self.rotor_active = "No"
		self.rotor_state = 0
		self.exchanger_speed = req.response

	def moisture_calcs(self):## calculate moisure/humidities

		self.cond_eff=.60 #  1 -((self.extract_ave-self.supply_ave)/35)#!abs(self.inlet_ave-self.exhaust_ave)/20
		######### SAT MOIST UPDATE ############
		if self.energy_diff > 0 and self.rotor_active=="Yes":
			try:
				d_pw = (self.airdata_inst.energy_to_pwdiff(self.energy_diff,self.extract_ave)/self.cond_eff)/(float(self.ef)/1000)
			except: d_pw=0
		else: d_pw = 0
		max_pw = self.airdata_inst.sat_vapor_press(self.extract_ave)

		self.div = self.prev_static_temp-self.kinetic_compensation 
		low_pw = self.airdata_inst.sat_vapor_press(self.div)


		#if "debug" in sys.argv:self.msg += str(round( max_pw,2))+ \
		#			"Pa "+str(round( low_pw,2))+"Pa "+\
		#			str( round(d_pw,2))+"Pa "+\
		#			str(round(d_pw/max_pw*100,2))+"% "+\
		#			str(round( self.energy_diff,2))+\
		#			"W kinetic_comp:"+str(round(self.kinetic_compensation,3))+\
		#			"C target:"+str(round((( low_pw+d_pw ) / max_pw ) * 100,2))+ "%\n"

		self.new_humidity += (((( low_pw+d_pw ) / max_pw ) * 100 )-self.new_humidity) *0.0001
		if self.iter %30 == 0 and "debug" in sys.argv:
			self.msg += "Humidity target: "+str((( low_pw+d_pw ) / max_pw ) * 100 )+"\n"	
			self.humidity_target =(( low_pw+d_pw ) / max_pw ) * 100 	
		return (( low_pw+d_pw ) / max_pw ) * 100 
		#####END

	#calc long and short derivatives
	def derivatives(self):
		#SHORT
		if len(self.extract)>self.averagelimit-1:
			self.extract_dt = (numpy.average(self.extract[0:14])-numpy.average(self.extract[self.averagelimit-15:self.averagelimit-1]))
			self.extract_dt = self.extract_dt/((self.time[0]-self.time[self.averagelimit-1])/60)
			self.extract_dt_list.append(self.extract_dt)
			if len(self.extract_dt_list)>500: self.extract_dt_list.pop(0)
		#LONG
		if self.iter %1500 == 0:
			if self.dt_hold == 0: self.dt_hold = self.extract_ave
			self.extract_dt_long= float((self.extract_ave-self.dt_hold))/((time.time()-self.extract_dt_long_time)/3600)
			self.extract_dt_long_time=time.time()
			self.dt_hold= self.extract_ave
			self.avg_frame_time=(time.time()-starttime)/self.iter
	# decect if shower is on
	def shower_detect(self):
		if self.RH_valid == 1 and not self.shower: # Shower humidity sensor control
			try:
				if self.hum_list[0]-self.hum_list[-1] > 8  and \
				numpy.average(self.extract_dt_list)*60 > 0.5:
					self.shower = True
                                        self.initial_temp = self.extract_ave
                                        self.initial_fanspeed= self.fanspeed
					if savecair:
						req.write_register(1103,45)
						req.write_register(1161,4)
					else:
	                                        self.set_fanspeed(3)
                                        self.inhibit=time.time()
                                        self.shower_initial=self.inhibit
					self.msg = "Shower mode engaged\n"
					self.status_field[0] += 1
			except IndexError: pass
		elif not self.shower and not self.RH_valid:
			# SHOWER derivative CONTROLER
			lim = 0.08
			if self.ef >50: lim = 0.10
			if self.extract_dt > lim and self.inhibit == 0 and numpy.average(self.extract_dt_list)*60>1.60:
				self.msg = "Shower mode engaged\n"
				if self.shower==False:
					self.shower = True
					self.initial_temp = self.extract_ave
					self.initial_fanspeed= self.fanspeed
					self.set_fanspeed(3)

					self.inhibit=time.time()
					self.shower_initial=self.inhibit
					self.status_field[0] += 1

		if numpy.average(self.extract_dt_list)*60 < 0		\
			and self.shower==True 				\
			and self.shower_initial - time.time()<-60:
			if "debug" in sys.argv:
				self.msg="Shower wait state, "+str(round(self.extract_ave,2))+"C "+str(round(self.initial_temp+0.3,2))+"C\n"
			if self.extract_ave<=(self.initial_temp+0.3) or self.shower_initial -time.time() < -30*60:
				self.shower=False
				try:
					self.msg ="Shower mode off, returning to "+str(self.speeds[self.initial_fanspeed]+"\n")
				except KeyError: pass
				if savecair:
					req.write_register(1161,2)
				else:
					self.set_fanspeed(self.initial_fanspeed)

	# PRINT OUTPUT
	def print_xchanger(self):
		global monitoring,vers
		tmp =  self.system_name
		if savecair:
			tmp += " SavecAir"
		tmp += " "+time.ctime()+" status: "+str(int(time.time()-starttime))+'('+str(self.iter)+")"+str(round((time.time()-starttime)/self.iter,2))+" Vers. "+vers+" ***\n"
		if "debug" in sys.argv:
			 try:
				tmp += "Errors -- Connect: "+str( req.connect_errors )+" Checksum: "+str(req.checksum_errors)+ " Write: "+str(req.write_errors)+" drain: "+str(len(req.buff))+" Multi: "+str(req.multi_errors) +"\n"
				tmp += "temp sensor state: "+str(bin(self.temp_state))+" Heater:"+str(self.heater)+"\n"
				if len(req.buff) > 50: req.buff = ""
				tmp += str(sys.argv)+"\n"
			 except: pass
		try:
			tmp += "Inlet: "+str("%.2f" % self.inlet_ave)+"C\t\tSupply: "+str("%.2f" % self.supply_ave)+"C\td_in : "+str(round(self.supply_ave,2)-round(self.inlet_ave,2))+"C"
			tmp += "\nExtract: "+str("%.2f" % self.extract_ave)+"C\tExhaust: "+str("%.2f" % self.exhaust_ave)+"C\td_out: "+str(round(self.extract_ave,2)-round(self.exhaust_ave,2))+"C\n"
			tmp += "Extract dT/dt: "+str(round(self.extract_dt,3))+"degC/min dT/dt: "+str(round(numpy.average(self.extract_dt_list)*60,3))+"degC/hr\n\n"
			if "debug" in sys.argv:
				tmp += "Tcomp:" + str(self.tcomp) + " at T1:"+str(self.rawdata[0][0])+" coef:"+str(round(self.coef,4))+" inlet coef:"+str(self.inlet_coef)+" dyn:"+str(self.dyn_coef)+"\n"
				if not savecair:
					tmp +="Extract:"+str(self.rawdata[0][2])+ "\tInlet:"+str(self.rawdata[0][1])+"\tExhaust:"+str(self.temps[2])+"\tSupply,pre:"+str(self.temps[0])+"\tSupply,post:"+str(self.temps[3])+"\n"
				else:
					tmp +="Extract:"+str(self.rawdata[0][2])+ "\tInlet:"+str(self.rawdata[0][0])+"\tSupply,post:"+str(self.rawdata[0][1])+"\n"
		except:pass
		if not savecair:
			tmp += "Exchanger Setting: "+str(self.exchanger_mode)+" State: "+self.rotor_states[self.rotor_state]+", Rotor Active: "+self.rotor_active+"\n"
		else:
			tmp += "Exchanger Rotor speed: "+str(self.exchanger_speed)+"%\n"
		if self.rotor_active=="Yes" or "debug" in sys.argv:
			tmp += "HeatExchange supply "+str(round(self.supply_power,1))+"W \n"
			tmp += "HeatExchange extract "+str(round(self.extract_power+self.condensate_compensation,1))+"W\n"
			if "debug" in sys.argv: tmp += "Diff:"+str(round(numpy.average(self.diff_ave),2))+"% "+str(round(self.energy_diff,1))+"W\n"
			if "humidity" in sys.argv and "debug" in sys.argv : tmp +="\nCondensation  efficiency: " +str(round(self.cond_eff,2)*100)+"%\n"
		if "humidity" in sys.argv :
			if "debug" in sys.argv:
				tmp += "Static: "+str(round(self.local_humidity+self.humidity_comp,2))+"%\n"
				if self.RH_valid:
					try:
						tmp+= "Valid RH "+str(self.RH_valid)+" "+str(self.hum_list[0]-self.hum_list[-1])+"d%\n"
					except:
						tmp+= "RH calcerror\n"
						traceback.print_exc()
				tmp += "Calculated humidity:\t " +str(round(self.rawdata[0][2],1))+"C "+ str(round (self.new_humidity,2))+"% Dewpoint: "+str(round(self.airdata_inst.dew_point(self.new_humidity,self.rawdata[0][2]),2))+"C\n" 
		if "debug" in sys.argv:
			try:
				tmp += "Outdoor Sensor:\t "+str(self.sensor_temp)+"C "+str(self.sensor_humid)+"% Dewpoint: "+str(round(self.airdata_inst.dew_point(self.sensor_humid,self.sensor_temp),2))+"C\n"
				tmp += "Indoor Sensor:\t "+str(self.inside)+"C "+str(self.inside_humid)+"% Dewpoint: "+str(round(self.airdata_inst.dew_point(self.inside_humid,self.inside),2))+"C\n"
			except: pass
		if "humidity" in sys.argv:
			tmp+= "Pressure limit: "+str(round(self.indoor_dewpoint,2))+"C\n"

		if self.rotor_active=="Yes":
			tmp += "\nElectric power:"+str(round(self.electric_power,0))+"W COP:"+ str(round(self.supply_power/self.electric_power,1))+"\n"
		else :  tmp += "\nElectric power:"+str(round(self.electric_power,0))+"W COP:"+ str(round(self.loss/self.electric_power,1))+"\n"
		if self.supply_ave < self.extract_ave:
			tmp += "Energy Loss: "+str(round(self.loss,1))+"W\n"
		else:
			tmp += "Energy Gain: "+str(round(self.loss,1))+"W\n"
		tmp += "Loss Total: "+str(round(self.totalenergy/1000,3))+"kWh Average:"+str(round((self.totalenergy)/(((time.time()-starttime)/3600)),1))+"W\n"
		tmp += "Cooling Total: "+str(round(self.cooling/1000,3))+"kWh\n"
		tmp += "Heat Gain Total: "+ str(round(self.gain/1000,3))+"kWh\n"
		tmp += "Supply:"+str(self.sf)+" l/s,"+str(self.sf_rpm)+"rpm\tExtract:"+str(self.ef)+" l/s,"+str(self.ef_rpm)+"rpm\n"
		if self.rotor_active == "Yes" or "debug" in sys.argv:
			tmp += "Temperature Efficiency: "+str(round(numpy.average(self.eff_ave),2))+"%\n"
			#tmp += "Energy efficiency:"+str(str(round((self.used_energy/self.availible_energy)*100,3))+"%\n")
		tmp += "Filter has been installed for "+ str(self.filter)+" days ,"+str(self.filter_remaining)+"% remaining.\n\n"
		tmp += "Ambient Pressure:"+ str(self.airdata_inst.press)+"hPa\n"
		if self.forcast[1]<>-1: tmp += "Weather forecast for tomorrow is: "+str(self.forcast[0])+"C "+self.weather_types[self.forcast[1]]+".\n\n"
		if "Timer" in threading.enumerate()[-1].name: tmp+= "Ventilation timer on: "+str((int(time.time())-int(device.timer))/60)+":"+str((int(time.time()-int(self.timer))%60))+"\n"
		#tmp+= str(threading.enumerate())+"\n"
		if self.shower : tmp += "Shower mode engaged at:" +time.ctime(self.shower_initial)+"\n"
		if self.inhibit>0:tmp+=  "Mode sensing inhibited "+"("+str(int((self.inhibit+600-time.time())/60+1))+"min)\n"
		if self.press_inhibit>0:tmp+=  "Pressure change inhibited "+"("+str(int((self.press_inhibit+1800-time.time())/60+1))+"min)\n"
		if self.modetoken >=1 :tmp+= "Mode change inhibited at: "+time.ctime(self.modetoken)+"("+str(int((self.modetoken+3600-time.time())/60+1))+"min)\n"
		if self.cool_mode: tmp+= "Cooling mode is in effect, target is 20.7C extraction temperature\n"
		#tmp += "lower limit:22.0C, when cooling 21.0C, fans up2 22.01C, fans up3 22.5 or +0.5C/hr\nExchanger limits ON:21C OFF:22C\nWeather Data from YR.no\n"
		if not monitoring: tmp += "\nSystem Automation off\n"

		self.status_field[2] = round((time.time()-starttime)/self.iter,2)
		if self.iter %60==0 and "debug" in sys.argv :
			try:
				ave, dev = statistics.stddev(self.cond_data)
				self.msg += str(len(self.cond_data))+" mean:"+str(ave)+" stddev:"+str(dev)+"\n"
				#print self.msg
			except : print "mean error"
		tmp +=  self.msg+"\n"
		tmp = tmp.replace("\n",";\n")
		tmp = tmp.replace("\t","'\t")
		#CLEAR SCREEN AND REPRINT
		clear_screen()
		print tmp

	#Read all data registers
	def update_registers(self):
		for each in range(100,900,100):
			print "Get series",each
			if   each == 100: addresses = 84#36
			elif each == 200: addresses = 84#21
			elif each == 300: addresses = 84
			elif each == 400: addresses = 85
			elif each == 500: addresses = 85
			elif each == 600: addresses = 85
			elif each == 700: addresses = 85
			elif each == 800: addresses = 85
			elif each == 900: addresses = 85
			elif each == 1000: addresses = 85
			for i in range(addresses):
				try:
					req.modbusregister(each+i,0)
				except:
					pass # print "error reading address",each+i
				self.register[str(each+i)]=req.response
				#print traceback.print_exc()
				#print "entries recieved at address:",each+i,req.response


	#print previously read modbus registers
	def print_registers(self):
	    if not savecair:
		try:
			print "\n",
			for each in range(1,84):
				tmp=""
				for address in range(100,1100,100):
				    try:
					pos = address+each
					tmp+= str(address+each)+":"+str( self.register[str(pos)])+" "+str( hex(self.register[str(pos)]))+"\t"
				    except KeyError: tmp+= str(pos)+":\t\t"
				print tmp
			if "daemon" not in sys.argv :raw_input("enter to resume")
			print "break"
		except:traceback.print_exc()

	#change exchanger mode to to, if no to flip 0 or 5
	def cycle_exchanger(self,to):
	  if not savecair:
	    def set_val(val):
		try:
			#self.msg += "\nwriting mode "+str(val)+"\n"
                        req.write_register(206,val,functioncode=6)
			return 1
		except: return 0
	    def get_val():
		try:
			req.modbusregister(206,0)
	               	self.current_mode = req.response
			return self.current_mode
		except:pass #print "read error"
	    ### SET FUNCTIONS ####
	    try:
		if to == None:
			self.msg+= "manual state change\n"
			self.current_mode = get_val()
		i=0
		if self.current_mode <>0 or to ==0:
			while set_val(0) == False:
				#self.msg += "\nwrite error"
				time.sleep(0.2)	#set summer mode
				i+=1
				if i>10: break
		else:
			while set_val(5) == False:
				#self.msg +="\nwrite error"
				time.sleep(0.2)	#set winter mode
				i+=1
				if i>10: break
		self.modetoken=time.time()
		self.inhibit= time.time()  # set inhibit time to prevent derivatives sensing when returning
	    except:
		#self.msg +=  "\nexit due to error"
		traceback.print_exc()
	    finally:
		self.exchanger_mode=get_val()

	#clear flags as timeouts occur
	def check_flags(self):
	    global monitoring
	    #### INHIBITS AND LIMITERS
	    now = time.time()
	    if self.inhibit < now-(60*10):self.inhibit = 0
    	    if self.modetoken < now-(60*60): self.modetoken=0
	    if self.press_inhibit < now-(60*30):self.press_inhibit = 0

	#Monitor Logical crits for state changes on exchanger, pressure, rpms, forcast
	def monitor(self):
	  if "VTR300" not in self.system_name :
	    #### FAN RPM MONITORING
	    if self.sf_rpm <1550 and self.fanspeed == 2 : self.inhibit = time.time()
	    if self.sf_rpm <1000 and self.fanspeed == 1 : self.inhibit = time.time()
	  else:
	    #### EXCHANGER CONTROL
	    self.house_heat_limit = 7  # daily low limit on cooling
	    if self.forcast[0]< 10: self.target = 23
	    else: self.target = 22
	    if self.modetoken<=0 and self.cool_mode==0 :

		if self.extract_ave >self.target 		\
			and self.exchanger_mode <> 0 		\
			and self.shower == False 		\
			and self.inlet_ave >10:
				self.modetoken =time.time()
				self.cycle_exchanger(0)
		if self.supply_ave > self.target 		\
			and self.exchanger_mode <> 0 		\
			and self.shower== False:
				self.cycle_exchanger(0)
				self.modetoken=time.time()
		if self.extract_ave < self.target-1 		\
			and self.exchanger_mode <> 5 		\
			and not self.cool_mode :
				self.cycle_exchanger(5)
				self.modetoken=time.time()
		if self.supply_ave <10 				\
			and self.extract_ave < self.target+1 	\
			and  self.exchanger_mode <> 5 		\
			and not self.cool_mode :
				self.cycle_exchanger(5)
				self.modetoken=time.time()
		if self.exchanger_mode <> 5 			\
			and self.inlet_ave < 10 		\
			and self.forcast[0] < 10		\
			and self.forcast[1] <> -1 		\
			and self.fanspeed == 1 			\
			and not self.cool_mode 			\
			and not self.shower:
				self.modetoken=time.time()
				self.cycle_exchanger(5)

	    #FORECAST RELATED COOLING
	    try:
		if self.forcast[0] > 16 and int(os.popen("./forcast.py tomorrows-low").read().split(" ")[0]) > self.house_heat_limit	\
			and self.forcast[1] < 4 				\
			and self.cool_mode == False 				\
			and self.extract_ave+0.1 > self.supply_ave 		\
			and self.extract_ave>20.7:
				self.msg += "predictive Cooling enaged\n"
				if self.exchanger_mode <>0:	self.cycle_exchanger(0)
				self.set_fanspeed(3)
				self.cool_mode = True
	    except: os.write(ferr, "Forcast cooling error")

	    if self.cool_mode and not self.inhibit and not self.shower:
		if (self.extract_ave <20.7 ) and self.fanspeed <> 1 :
			self.set_fanspeed(1)
			self.msg += "cooling complete\n"

		if self.fanspeed == 3 and self.supply_ave < 10:
			self.set_fanspeed(2)
			self.msg = "cooling reduced\n"

		if self.fanspeed ==1 and self.extract_ave > 20.8 and self.extract_ave > self.supply_ave:
			self.set_fanspeed(3)

		if self.supply_ave>self.extract_ave+0.1 and self.fanspeed<>1:
			self.set_fanspeed(1)
			self.msg += "no cooling posible due to temperature conditions\n"

		if (self.forcast[0] <= 16 or self.forcast[1]>=4) and time.localtime().tm_hour >12: self.cool_mode=False
	    #DYNAMIC FANSPEED CONTROL

	    if self.fanspeed < 2 				\
		and self.extract_ave > self.target 		\
		and self.extract_ave < self.target + 0.5 	\
		and self.extract_ave - self.supply_ave>0.1 	\
		and numpy.average(self.extract_dt_list) >= 0.2	\
		and not self.shower 				\
		and not self.inhibit 				\
		and not self.cool_mode:
		 	self.set_fanspeed(2)
		 	self.msg += "Dynamic fanspeed 2\n"

	    if self.fanspeed <> 3 													\
		and self.extract_ave-0.1 > self.supply_ave 										\
		and (self.extract_ave >= self.target+1 or (self.extract_dt_long >=0.7 and numpy.average(self.extract_dt_list)>0.7)	\
		and self.inlet_ave > 5 or self.extract_ave > self.target+2 )								\
		and self.exchanger_mode <> 5 												\
		and not self.extract_dt_long < -0.2 											\
		and not self.inhibit 													\
		and not self.cool_mode 													\
		and not self.shower:
			self.set_fanspeed(3)
			self.msg += "Dynamic fanspeed 3\n"

	    if self.fanspeed <> 1 				\
		and ((self.extract_ave < self.target		\
		and not self.inhibit				\
		and not self.cool_mode	 			\
		and not self.shower)				\
		or (self.extract_ave < self.target + 1.0 	\
		and numpy.average(self.extract_dt_list)<-.5 	\
		and not self.inhibit				\
		and not self.cool_mode				\
		and not self.shower)) :
			self.set_fanspeed(1)
			self.msg += "Dynamic fanspeed 1\n"

	    if self.extract_ave < self.supply_ave 	\
		and self.fanspeed <> 1 			\
		and not self.cool_mode	 		\
		and not self.inhibit			\
		and not self.shower:
			self.set_fanspeed(1)
			self.msg += "Dynamic fanspeed, recover cool air\n"

	    if (self.fanspeed== 3			\
 		and self.extract_ave < self.target + 1 	\
		and self.extract_ave > self.target	\
		and not self.shower			\
		and not self.inhibit			\
		and not self.cool_mode)		 	\
		or  (self.supply_ave < 10		\
		and numpy.average(self.extract_dt_list)<-.5 \
		and not self.cool_mode 			\
		and not self.inhibit 			\
		and not self.shower):
			self.set_fanspeed(2)
			self.msg  +="Dynamic fanspeed 2\n"

	    # SHOWER MODEwTIMEOUT #
	    if self.shower == True and self.shower_initial -time.time() < -45*60:
		self.shower = False

	    #Dynamic pressure control
	    if self.new_humidity > 20.0: #Low humidity limit, restriction to not set margin lower than 20%RH
		if savecair or self.RH_valid:
			self.indoor_dewpoint = self.airdata_inst.dew_point(self.new_humidity+5,self.extract_ave)
		else:
			self.indoor_dewpoint = self.airdata_inst.dew_point(self.new_humidity+10,self.extract_ave)
	    else:
		self.indoor_dewpoint = 5.0
	    if self.inlet_ave > self.indoor_dewpoint+0.2   and self.sf <> self.ef and not self.press_inhibit and not self.forcast[1] == -1 :
		self.set_differential(0)
		if "debug" in sys.argv: self.msg += "\nPressure diff to 0%"
	    if (self.inlet_ave < self.indoor_dewpoint-0.1  and self.sf == self.ef and self.inlet_ave < 15 and not self.press_inhibit) or (self.forcast[-1] == -1 and self.sf == self.ef):
		self.set_differential(10)
		if "debug" in sys.argv: self.msg += "\nPressure diff to +10%"
    	    #if "debug" in sys.argv: print "Pressure inhibit = " , str(time.ctime(self.press_inhibit))

	#Get the active forcast
	def get_forcast (self):
		###### WEATHER FORCAST MODES
	    try:
	    	forcast = os.popen("./forcast.py tomorrow")
	    	forcast = forcast.readlines()[0]
	    	self.forcast = forcast.split(" ")
		self.forcast[0]=int(self.forcast[0])
		self.forcast[1]=int(self.forcast[1])
		#print self.forcast[0],self.forcast[1]
		if os.stat("./RAM/forecast.xml").st_ctime < time.time()-3600*24 :raise Exception("FileError")
	    except:
		self.msg+= "error getting forecast\n"
		self.forcast=[-1,-1]
	#set the fan pressure diff
	def set_differential(self, percent):
	    if not savecair:
		if "debug" in sys.argv: self.msg += "start pressure change " +str( percent)+"\n"
		if percent>20:percent = 20
		if percent<-20:percent =-20
		req.modbusregister(103,0) #nominal supply flow
		#print "sf_nom is", req.response
		target = int(req.response + req.response * (float(percent)/100))
		#print "to set ef_no to",target
		req.write_register(104,target) # nominal extract flow
		req.modbusregister(104,0) #nominal supply flow
		if req.response == target:
			self.press_inhibit = time.time()
		if "debug" in sys.argv: 
			if req.response == target :self.msg+= "supply flow change completed \n"
		high_flow = 107
		if percent < 0 :high_flow += 107*float(percent)/100
		if high_flow >107: high_flow= 107
		#print "high should be extract:", int(high_flow)
		req.write_register(106,int(high_flow)) # reset high extract
		#raw_input(" diff set done")
		if "debug" in sys.argv: self.msg += "change completed\n"
	    else:
		self.press_inhibit = time.time()

		for each in range(1400,1408,2):
			req.modbusregister(each,0)
			#raw_input(str(percent)+"% "+str(each)+"-"+str(int(req.response*(1+(float(percent)/100)))))
			req.write_register(each+1,int(req.response+percent))
	#get and set the local low/static humidity
	def get_local(self):
		try:
			out = os.popen("./humid.py "+str(self.extract_ave)).readline()
			tmp = out.split(" ")
			temp = float(tmp[1])
			self.local_humidity = float(tmp[0])
			comp = float(os.popen("./forcast.py tomorrows-low").read().split(" ")[0])
			comp = float(comp - temp)/1500
			self.kinetic_compensation -= comp * self.avg_frame_time
			weather = int(os.popen("./forcast.py now").read().split(" ")[-2])
			if weather == 9 or weather == 10 or weather == 15:
				self.kinetic_compensation = 0

			if "debug" in sys.argv:
				self.msg += "Comp set to: " +str(round(comp,4))+" Static offset:"+str(round(self.kinetic_compensation,2))+"\n"
			if temp <> self.prev_static_temp:
				self.prev_static_temp = temp
				self.kinetic_compensation = (-1+float(os.popen("./forcast.py now").read().split(" ")[-5][:-3]))/3
				temp = weather
				if temp >=3:
					self.kinetic_compensation += 0.5
				elif temp == 15 or temp == 9 or temp == 10:
					self.kinetic_compensation = 0
				self.humidity_comp = 0
			#if self.kinetic_compensation <0: self.kinetic_compensation = 0
		except: print "dayliy low calc error"

## Init base class ##
if __name__  ==  "__main__":
	print "Reporting system start;"
	#print os.read(bus,10000)
	
	device = Systemair()

	try:
		if device.system_name =="VR400" and client.read_register(12543,0):
			savecair=True
			device.system_name="VTR300"
			conversion_table ={}
			device.status_field[3]="VTR300/savecair"
			device.averagelimit=1400
	except:pass
################
###################################################
############################ RUN MAIN loop ########################
if __name__  ==  "__main__":
	monitoring = True
	def set_monitoring(bool):
		global monitoring
		monitoring = bool
	input = ""
	print "Going in for first PASS;"
	try:
	    #FIRST PASS ONLY #
            clear_screen()
	    print "First PASS;\n updating fanspeeds;"
	    device.update_airflow()
	    sys.stdout.flush()
	    print "Updating fans rpms;"
	    device.update_fan_rpm()
	    sys.stdout.flush()
	    print "Reading Filter Status;"
	    device.get_filter_status()
	    sys.stdout.flush()
	    print "Reading internal heater state;"
	    device.get_heater()
	    sys.stdout.flush()
	    print "Retrieving weather forecast;"
	    device.get_forcast()
	    sys.stdout.flush()
	    print "Generating historical graphs;"
	    if "debug" in sys.argv:
		os.system("sudo nice ./grapher.py debug &")
	    else:
		os.system("sudo nice ./grapher.py &")
	    sys.stdout.flush()
	    if "debug" in sys.argv:
		print "checking for sensor data;"
		update_sensors()
	    	sys.stdout.flush()
	    print "Updating current rotor status;"
	    device.get_rotor_state()
	    print "Setting up coeficients;"
	    sys.stdout.flush()
	    if device.rotor_active == "No":
		device.coef = 0.09
		device.inlet_coef=0.07
	    else:
		device.coef= 0.09
		device.inlet_coef = 0.07
	    print "Read initial temperatures;"
	    device.update_temps()
	    device.update_xchanger()
	    device.div = device.inlet_ave
	    if "humidity" in sys.argv:
		device.get_local()
		device.new_humidity = device.moisture_calcs()
	    starttime=time.time()
	    print "system started:",time.ctime(starttime),";"
	    sys.stdout.flush()
	    if "ping" in sys.argv:report_alive()
	    time.sleep(2)
	    starttime=time.time()
	    while Running:##### mainloop do each pass ###########
		#do temps,energy and derivatives
		device.update_temps()
		device.update_xchanger()
		device.derivatives()
                if "raw_debug" in sys.argv:
                        device.flow_calcs()
		## EXEC TREE, exec steps uniqe if prime##
		#check states and flags
		if device.iter%3 ==0:
			device.check_flags()
			if device.system_name == "VTR300":
				device.calc_exhaust()
		# update moisture
		if device.iter%5==0:
			if monitoring:
				device.monitor()
				device.shower_detect()

			if "humidity" in sys.argv and (device.system_name not in device.has_RH_sensor or not device.RH_valid):
				device.moisture_calcs()
			if "humidity" in sys.argv and device.system_name in device.has_RH_sensor:
				device.get_RH() ## Read sensor humidity
		#update fans
		if device.iter%7==0:
			device.update_fan_rpm()
		#debug specific sensors and temp probe status
		if device.iter%11==0:
			device.get_rotor_state()
			device.update_fanspeed()
			if "debug" in sys.argv:
				update_sensors()
				device.get_temp_status()
				device.get_filter_status()

		#refresh static humidity
		if device.iter%79==0:
			device.update_airflow()
			device.get_heater()
			device.msg = ""
			#if "humidity" in sys.argv and (device.system_name not in device.has_RH_sensor or not device.RH_valid):
			device.get_local()
		#calc local humidity and exec logger
		if device.iter%int(float(120)/device.avg_frame_time)==0:
			logger()
		#send local tempt to temperatur.nu
		if device.iter%251==0 and "temperatur.nu" in sys.argv:
                        os.system("wget -q -O temperatur.nu  http://www.temperatur.nu/rapportera.php?hash=42bc157ea497be87b86e8269d8dc2d42\\&t="+str(round(device.inlet_ave,1))+" &")
		#generarte graphs and refresh airdata instance.
		if device.iter%563==0:
			device.update_airdata_instance()
			if "debug" in sys.argv:os.system("nice ./grapher.py debug & >>/dev/null")
			else : os.system("nice ./grapher.py  & >> /dev/null")
		# send alive packet to headmaster and check for updates
		if device.iter % int(3600/0.2)==0:
			os.system("./backup.py &")
			os.system("cp ./RAM/data.log ./data.save")
			if "ping" in sys.argv:
				report_alive()
			update()
		#restart HTTP SERVER get filterstatus, reset IP on buttons page, update weather forcast
		if device.iter %(int(3600*2 /device.avg_frame_time))==0:
			device.get_filter_status()
			os.system("./http &")
			os.system("./public/ip-replace.sh &")  # reset ip-addresses on buttons.html
			os.system("./public/ip-util.sh &")  # reset ip-addresses on buttons.html
			device.get_forcast()
			if device.status_field[0]>0:device.status_field[0] -= 1 # remove one shower token from bucket every 2 hrs.
		## PRINT TO DISPLAY ##
		device.print_xchanger()
		device.iter+=1
		########### Selection menu if not daemon######
		if "daemon" not in sys.argv:
			timeout = 0.01
			print """
	CTRL-C to exit,
1: Toggle auto Monitoring	 6: Retrive all Modbus Registers
2: Toggle fanspeed		 7: Set flow differential
3: Print all device attributes	 8: Run fans for 15min at Max
4: Display link settings	 9: Display availible Modbus Registers
5: show/update values		 0: cycle winter/summer mode
		enter commands:""",
		else: timeout=0.05
		try:sys.stdout.flush()
		except:pass
		data = -1
		input = select.select([sys.stdin,cmd_socket],[],[],timeout)[0]
		try:
			if cmd_socket in input:
				try:
					sock = cmd_socket.recvfrom(128)
					data = sock[0]
					data = int(str(data))
					sender = sock[1]
				except: pass 
				try:	
					device.msg += "Network command recieved: Processing... "+str(data)+"\n"
					log = "echo \"" + str(time.ctime()) +":" +str(sender) +":" +str(data) +"\" >> netlog.log &"
					os.system(log)
					#device.msg += log+"\n"+str(data)+" "+str(type(data))+" "+str(len(data))+"\n"
				except:	
					device.msg += "net log error\n"
					traceback.print_exc()


			if "daemon" not in sys.argv and sys.stdin in input:
				try:
					data = sys.stdin.readline()
					data = int(str(data))
				except: 
					device.msg += "stdin error\n"
					traceback.print_exc()

			if data <> -1:
				if data == 1:	
					monitoring = not monitoring # Toggle monitoring on / off
					device.inhibit = 0
				if data == 2:
					device.set_fanspeed(device.fanspeed+1)
					if "daemon" not in sys.argv:raw_input("press enter to resume")
				if data == 3:
					clear_screen()
					device.print_attributes()
					sys.stdout.flush()
					time.sleep(10)
					if "daemon" not in sys.argv:raw_input("press enter to resume")
				if data == 4:
					display_settings()
					sys.stdout.flush()
					time.sleep(10)
					if "daemon" not in sys.argv:raw_input("press enter to resume")
					else: print "break"
					recent=4

				if data ==6:
					device.update_registers()
					if "daemon" not in sys.argv:raw_input("press enter to resume")
					else:print "break"

				if data ==7:
					try:
						if "daemon" not in sys.argv :inp =int( raw_input("set differential pressure(-20% -> 20%):"))
						else:
							if device.ef == device.sf :inp =10
							else : inp =0
						device.set_differential(inp)
					except IOError:print "not used"
					except:
						traceback.print_exc()
						#raw_input("break")
				if data == 8:
					device.msg += "Forced Ventilation on timer\n"
					prev = device.fanspeed
					device.set_fanspeed(3)
					monitoring = not monitoring
					try:
						if threading.enumerate()[-1].name != "Timer":
							tim2 = threading.Timer(60.0*120,set_monitoring,[True] )
							tim2.start()
							tim = threading.Timer(60.0*120,device.set_fanspeed,[prev])
							tim.setName("Timer")
							device.timer=time.time()
							tim.start()
					except:
						traceback.print_exc()
						print "force vent error"
				if data == 9:
					device.print_registers()
					sys.stdout.flush()
					time.sleep(10)
					if "daemon" not in sys.argv:raw_input("press enter to resume")
					else: print "break"
				if data == 0:
					device.cycle_exchanger(None)

				if data == 97:
					clear_screen()
					device.msg += "Fanspeed to Low\n"
					device.set_fanspeed(1)
				if data == 98:
					device.set_fanspeed(2)
					device.msg += "Fanspeed to Norm\n"
				if data == 99:
					device.set_fanspeed(3)
					device.msg += "fanspeed to High\n"
				if data == 11:
					if device.heater ==0:
						set = 2
					else: set = 0
					device.set_heater(set)
				if data == 12:
					device.shower = not device.shower
					if device.shower:
						device.initial_temp=device.extract_ave + 1
						device.initial_fanspeed = 1
						device.shower_initial = time.time()
		except TypeError:pass
		except ValueError:pass
		#except:
		#	error  = open("error.txt","w")
		#	traceback.print_tb(sys.exc_info()[-1],error)
		#	traceback.print_exc(error)
		#	error.close()
		#	traceback.print_exc()
		#	if "daemon" not in sys.argv:raw_input("press enter to resume")

	except KeyboardInterrupt:
		exit_callback(2,None)


