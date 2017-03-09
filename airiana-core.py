#!/usr/bin/python
import airdata
import serial, numpy, select, threading
import minimalmodbus, os, traceback
import time,struct,sys
import statistics
from mail import *
vers = "7.3h"
#exec util fnctns
os.chdir("/home/pi/airiana/public")
os.system("./ip-replace.sh")  # reset ip-addresses on buttons.html
os.chdir("/home/pi/airiana/")
os.system("./http &> /dev/null") ## START WEB SERVICE
os.system("./forcast.py &> /dev/null") ## Get forcast
if os.path.lexists("./RAM/data.log"): os.system("touch data.log")
if "debug" in sys.argv and not os.path.lexists("./sensors"): os.system("touch sensors")
if "debug" in sys.argv: os.system("./status.py &")
starttime=time.time()
#Setup deamon env
if "daemon" in sys.argv:
	fout = os.open("./RAM/out",os.O_WRONLY|os.O_CREAT)
	ferr = os.open("./RAM/err",os.O_WRONLY|os.O_CREAT)
	os.dup2(fout,sys.stdout.fileno())
	os.dup2(ferr,sys.stderr.fileno())
	print "Output redirected to file;"
# Setup serial, RS 485 to machine
if os.path.lexists("/dev/serial0"):
	print "Communication started on device Serial0;"
	unit = "/dev/serial0"
else :
	print "Communication started on device ttyAMA0;"
	unit = "/dev/ttyAMA0"
minimalmodbus.BAUDRATE = 19200
minimalmodbus.PARITY = serial.PARITY_NONE
minimalmodbus.BYTESIZE = 8
minimalmodbus.STOPBITS=1
client = minimalmodbus.Instrument(unit,1)
client.debug=False
client.precalculate_read_size=True
#############################################
wait_time = 0.1
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
		if time.time()-starttime> 60:break

########### global uty functions################
sensor_dict = {}

#SEND PING TO EPIC HEADMASTER
def report_alive():
	try:
		msg = os.popen("/sbin/ifconfig wlan0").readlines()
		for each in msg:
			if each.find("HWaddr") <> -1:
				message = each
				message += os.popen("hostname -I").read()
				#message += (time.time()-starttime)/device.iter
				#print message
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
		+str(round(device.local_humidity+device.humidity_comp,1))	\
		+":"				\
		+str(device.inside)		\
		+":"				\
		+str(round(device.energy_diff,2))\
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
		self.connect_errors= -1
		self.checksum_errors=0
		self.buff= ""
		self.counter = 0
	def modbusregisters(self,start,count):
		try:
			self.response= "no data"
			self.buff = ""
			self.buff += os.read(bus,1000) # purge content on bus
			time.sleep(wait_time)
			self.response = client.read_registers(start,count)
			self.buff += os.read(bus,1000) # re purge
			time.sleep(wait_time)
			self.response = client.read_registers(start,count)
		except ValueError as error:
			#print "checksum error,retry:",self.checksum_errors,error.message
			#print error.message.find("\x01\x83\x02\xc0\xf1")
			if  error.message.find("\x01\x83\x02\xc0\xf1")<>-1:
				print "address out of range"
				exit()
			self.checksum_errors +=1
			self.modbusregisters(start,count)
		except IOError:
			self.connect_errors += 1
			self.modbusregisters(start,count)
	def modbusregister (self,address,decimals):
		try:
			self.response = "no data"
			self.buff = ""
			time.sleep(wait_time)
                        self.response = client.read_register(address,decimals)
			time.sleep(wait_time)
			self.response = client.read_register(address,decimals)
		except IOError:
	 		self.connect_errors += 1
			#print "no response, retry:",self.connect_errors,address
			self.modbusregister(address,decimals)
		except ValueError:
			#print "checksum error,retry:",self.checksum_errors
			os.read(bus,1000) # bus purge
			self.checksum_errors +=1
			self.modbusregister(address,decimals)
	def write_register(self, reg, value):
		self.modbusregister(reg, 0)
		start = self.response
		if start == value: return 0
		try:
			#print "set", reg, "to",value
			resp = client.write_register(reg,value)
		except IOError as error:
			#print "ioerror",error,os.read(bus,100)
			#self.write_register(reg,value)
			pass
		except ValueError as error:
			#print "val error",error,os.read(bus,100)
			#self.write_register(reg,value)
			pass
		#print "buffer",os.read(bus,1000)
		time.sleep(wait_time)
		try:
			self.modbusregister(reg,0)
			#print "readback",self.response

			if self.response <> start or value == req.response:
				return True
			else :self.counter +=1
			self.response, start
			if self.counter < 10:self.write_register(reg, value)
			else:
				self.counter = 0
				return False
		except IOError as error:
			#print os.read(bus,100)
			#self.write_register(reg,value)
			#print error
			pass
		except ValueError as error:
			#print error, os.read(bus,100)
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
		self.press_inhibit = 0
		self.local_humidity = 0.0
		self.eff_ave=[90]
		self.diff_ave=[0]
		self.totalenergy = 0.0
		self.averagelimit = 300#min122
		self.sf = 34
		self.ef = 34
		self.ef_rpm = 1500
		self.sf_rpm = 1500
		self.inlet = []
		self.inlet_ave =0
		self.supply = []
		self.supply_ave=0
		self.extract = []
		self.extract_ave=0
		self.exhaust = []
		self.exhaust_ave=0
		self.supply_power=0
		self.extract_power=0
		self.extract_combined=0
		self.gain = 0
		self.loss=0
		self.register = {}
		self.starttime = time.time()
		self.timer = 0
		self.defrost = False
		self.current_mode=0
		self.extract_humidity=0.40 # relative humidity
		self.extract_humidity_comp=0.00 # relative humidity re compensated
		self.condensate_compensation =0
		self.cond_eff = 1
		self.dew_point=10
		self.dur=1.0
		self.extract_dt = 0.0
		self.update_airdata_instance()
		self.shower =False
		self.msg = ""
		self.inside =0
		self.inside_humid=0
		self.exchanger_mode=5
		self.rotor_state = 0
		self.rotor_active = "Yes"
		self.inhibit = time.time()
		self.sensor_temp = 0
		self.sensor_humid = 0
		self.modetoken = 0
		self.cooling = 0
		self.forcast = [-1,-1]
		self.extract_dt_log =[]
		self.dt_hold = 0
		self.dt_entries  =0
		self.extract_dt_long_time = time.time()
		self.iter=1
		self.extract_dt_long = 0
		self.cool_mode=0
		self.temps = []
		self.temp_state = 0
		self.condensate = 0
		self.coef = 0.12
		self.tcomp = 0
		self.inlet_coef = 0.1
		self.filter = 0
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
		self.new_humidity=0
		self.div =0

	def get_filter_status(self):
		req.modbusregister(601,0)
		self.filter = req.response

	def get_temp_status(self):
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

	def display_fanspeed(self):
		req.modbusregister(100,0)
		self.fanspeed = req.response
		if self.fanspeed >3: self.fanspeed=3
		print "Fan is now on:",self.speeds[self.fanspeed]

	def get_fanspeed(self):
		req.modbusregister(100,0)
		self.fanspeed =int(req.response)
		return self.fanspeed

	def update_temps(self):
		req.modbusregisters(213,5)# Tempsensors 1 -5
		self.time.insert(0,time.time())
		if len(self.time) > self.averagelimit: self.time.pop(-1)
		self.temps = req.response[:]
		#req.response[1] #EXTRACT
		#req.response[2] #EXHAUST
		#req.response[0] #Supply pre elec heater
		#req.response[3] #Supply post electric heater
		if self.rotor_active ==  "No" and self.coef <> 0.19+(float(self.fanspeed)/100):
			if self.coef-( 0.19+(float(self.fanspeed)/100))>0:self.coef -= 0.00035#0.04
                        else: self.coef += 0.0002
		if self.rotor_active == "Yes" and self.coef <> 0.07:
			if self.coef-( 0.07)>0:self.coef -= 0.00015#0.04
			else: self.coef += 0.0004
		# NEGATYIVE VAL sign bit compensation
		if req.response[4]>60000:
			req.response[4] -= 0xFFFF
		if self.sf <> 0:
			self.tcomp= ((req.response[1]-req.response[4])*self.coef)#float(7*34)/self.sf # compensation (heat transfer from duct) + (supply flow component)
			req.response[1] += self.tcomp
		if self.rotor_active =="No"  and self.inlet_coef <0.14:self.inlet_coef+= 0.00014 #OFF
		if self.rotor_active =="Yes" and self.inlet_coef >0.08:self.inlet_coef-= 0.00014 # ON
		req.response[4]  -= (req.response[1]-req.response[4])*self.inlet_coef #inlet compensation exchanger OFF/ON

		self.inlet.insert(0,float(req.response[4])/10)

		if req.response[2]>6000:
			req.response[2] -=0xFFFF
		if self.rotor_active =="No" :
			req.response[2]  -= (req.response[1]-req.response[4])*0.01  #exhaust compensation exch off
		else : 	req.response[2]  -= (req.response[1]-req.response[4])*0.06  #exhaust compensation exch ON
		self.exhaust.insert(0,float(req.response[2])/10)

      		#limit array size
		for each in [self.inlet,self.supply,self.extract,self.exhaust]:
			if len(each)>self.averagelimit: each.pop(-1)
		self.supply.insert(0,float(req.response[3])/10)
		self.extract.insert(0, float(req.response[1])/10)
		try:
			self.eff = (self.supply[0]-self.inlet[0])/(self.extract[0]-self.inlet[0])*100
		except ZeroDivisionError:self.eff = 100
		self.eff_ave.insert(0,self.eff)
		if len(self.eff_ave) >self.averagelimit: self.eff_ave.pop(-1)

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
				client.write_register(100,target)
	    			os.read(bus	,100)
	    			time.sleep(wait_time*50)
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
				os.read(bus,100)
				if self.fanspeed<>target:self.set_fanspeed(target)
			if "Check" == error.message[0:5]:
				os.read(bus,100)
				self.set_fanspeed(target)
    		except IOError as error:
    			#print "no response", "fanspeed:", self.speeds[self.fanspeed]
			os.read(bus,100)
			self.set_fanspeed(target)
		except: print "unhandled exception", sys.exc_info[0]
		self.update_airflow()


	def update_fan_rpm(self):
		req.modbusregisters(110,2)
		self.sf_rpm,self.ef_rpm=req.response[0],req.response[1]
		try:
			self.electric_power= (self.ef_rpm/(100/(float(float(self.ef_rpm)/1381)**1.89))+self.sf_rpm/(100/(float(float(self.sf_rpm)/1381)**1.89)))
		except ZeroDivisionError:self.electric_power=0
		if "Yes" in self.rotor_active :self.electric_power +=10 # rotor motor 10Watts
		self.electric_power+=5#controller power
	def update_fanspeed(self):
		req.modbusregister(100,0)
		self.fanspeed = req.response

	def update_airflow(self):
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

	def update_airdata_instance(self):
		self.airdata_inst= airdata.Energy()

	def update_xchanger(self):
		self.inlet_ave = numpy.average(self.inlet)
		self.supply_ave = numpy.average(self.supply)
		self.extract_ave = numpy.average(self.extract)
		self.exhaust_ave = numpy.average(self.exhaust)
		if self.fanspeed <> 0:
			#self.availible_energy =  self.airdata_inst.energy_flow(self.ef,self.extract_ave,self.inlet_ave)+self.airdata_inst.condensation_energy((self.airdata_inst.vapor_max(self.exhaust_ave)-self.airdata_inst.vapor_max(self.inlet_ave))*((self.ef)/1000))
			
			try:self.used_energy    = self.airdata_inst.energy_flow(self.sf,self.supply_ave,self.inlet_ave)
			except: self.used_energy = 0
			factor = 1 # casing transfer correction factor
			if   self.rotor_active=="Yes":
				if self.fanspeed ==3:
					factor = 3.3
				elif self.fanspeed ==1:
					if self.ef == self.sf: factor = 3.95 		 
					else : factor=2.9
				elif self.fanspeed ==2:
					factor = 6.25
			elif self.rotor_active =="No":
				if self.fanspeed == 1   :
					factor=3#  - 16 constant# red  from casing heat transfer
				elif self.fanspeed == 2 :
					factor = 1.9#  - 16 constant# red  from casing heat transfer
				elif self.fanspeed == 3 :
					factor = 5.5
			else: factor=1
 			if self.rotor_active == "Yes":
				self.supply_power   = self.used_energy-5-(self.extract_ave-self.inlet_ave)*factor#  constant# red  from casing heat transfer
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

			self.cond_data.append(-self.extract_power+self.used_energy)
			if len(self.cond_data)> 400:self.cond_data.pop(0)

	def get_rotor_state(self):
		req.modbusregister(206,0)
	        device.exchanger_mode= req.response
		req.modbusregisters(350,2)
                device.rotor_state = req.response[0]
                if req.response[1]:device.rotor_active = "Yes"
                else: device.rotor_active = "No"

	def moisture_calcs(self):## calculate moisure/humidities
		# Vh2o max extracted air
		if numpy.isnan(self.extract_humidity) and self.diff_ave[0]>0:
			pass#self.extract_humidity  = 0.10
			#self.dew_point = self.airdata_inst.dew_point(self.extract_humidity*100,self.extract_ave)
		try:
			#extract_vmax	   = self.airdata_inst.vapor_max(self.extract_ave)
			#moisture 		   = extract_vmax*self.extract_humidity
			#inlet_vmax  	   = self.airdata_inst.vapor_max(self.inlet_ave)
			self.dew_point 	   = self.airdata_inst.dew_point(self.extract_humidity*100,self.extract_ave)
			#dew_point_moisture = self.airdata_inst.vapor_max(self.dew_point) #dew point in extracted air
			#self.condensate    = (dew_point_moisture - inlet_vmax) #diff in moisture content between inlet max vapor and dewpoint extracted

		except:pass
		self.cond_eff=.20#  1 -((self.extract_ave-self.supply_ave)/35)#!abs(self.inlet_ave-self.exhaust_ave)/20
		######### SAT MOIST IPDATE ############
		if self.energy_diff > 0:
			try:
				#d_pw = (self.airdata_inst.energy_to_pwdiff(numpy.average(self.cond_data),self.extract_ave)/self.cond_eff)/(float(self.ef)/1000)
				d_pw = (self.airdata_inst.energy_to_pwdiff(self.energy_diff,self.extract_ave)/self.cond_eff)/(float(self.ef)/1000)
			except: d_pw=0
		else: d_pw = 0
		max_pw = self.airdata_inst.sat_vapor_press(self.extract_ave)
		#div = (self.inlet_ave+(self.prev_static_temp*2))/3
		self.div += (self.inlet_ave-self.div)*(0.00005*self.ef)
		low_pw = self.airdata_inst.sat_vapor_press(self.div)
		if "debug" in sys.argv:self.msg += str(round( max_pw,2))+"Pa "+str(round( low_pw,2))+"Pa "+str( round(d_pw,2))+"Pa "+str(round(d_pw/max_pw*100,2))+"% "+str(round(self.div,2))+"C "+str(round( self.energy_diff,2))+"W\n"
		if d_pw != 0:self.new_humidity = ((low_pw+d_pw) / max_pw) * 100
		else: self.new_humidity = self.airdata_inst.sat_vapor_press(self.prev_static_temp)/max_pw*100

		#####END
		"""if len(self.i_diff)>10 and (self.dew_point > self.inlet_ave) :
			self.extract_humidity +=0.00001*self.i_diff[-1]-0.00001*(self.i_diff[-1]-self.i_diff[-2])+0.000001*numpy.sum(self.i_diff)
		elif self.dew_point < self.inlet_ave: self.extract_humidity += (self.inlet_ave -self.dew_point)/float(100) +0.0001
		if self.extract_humidity>=1:self.extract_humidity = 1
		if self.extract_humidity<=0:self.extract_humidity = 0
		if self.condensate >0:
			self.condensate_compensation= (self.airdata_inst.condensation_energy(self.condensate)/1000)*self.ef*self.cond_eff

			self.extract_humidity_comp =self.extract_humidity#+abs((self.extract_humidity*( self.inlet_ave/(self.exhaust_ave-self.inlet_ave)*(1-0.87))))
			if self.extract_humidity==numpy.nan: self.extract_humidity=0
		else:
			self.extract_humidity_comp   = 0
			self.condensate_compensation = 0
			if self.diff_ave[0] <0:self.extract_humidity=numpy.nan
		"""
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

	# decect if shower is on
	def shower_detect(self):
		try: # SHOWER CONTROLLER (should be moved to monitor method)
			lim = 0.05
			if self.ef >50: lim = 0.07
			if self.extract_dt > lim and self.inhibit ==0 and numpy.average(self.extract_dt_list)*60>0.50:
				self.msg = "shower mode engaged\n"
				if self.shower==False:
					self.shower = True
					self.initial_temp = self.extract_ave
					self.initial_fanspeed= self.fanspeed
					self.set_fanspeed(3)
					#self.msg += str(self.initial_temp) +" "+ str(self.initial_fanspeed)
					#try:
					#	mail.setup("daniel.halling@outlook.com","daniel.halling@outlook.com","Shower mode engaged! " +str(self.initial_temp)+"C Humidity: "+str(self.extract_humidity)+"%")
                                	#	mail.send()
					#except: self.msg+= "mailing error"
					self.inhibit=time.time()
					self.shower_initial=self.inhibit
			if self.extract_dt <0.02 and self.shower==True:
				self.msg="shower wait state, "+str(round(self.extract_ave,2))+"C "+str(round(self.initial_temp+0.3,2))+"C\n"
				if self.extract_ave<=(self.initial_temp+0.3) or self.shower_initial -time.time() < -30*60:
					self.shower=False
					self.msg ="shower mode off, returning to "+str(self.speeds[self.initial_fanspeed])
					self.set_fanspeed(self.initial_fanspeed)

		except:
			print self.msg
			print traceback.print_exc()
			print "shower detect system error"
	# PRINT OUTPUT
	def print_xchanger(self):
		global monitoring,vers
		tmp =  "***"+time.ctime()+" status: "+str(int(time.time()-starttime))+'('+str(self.iter)+")"+str(round((time.time()-starttime)/self.iter,2))+" Vers. "+vers+" ***\n"
		if "debug" in sys.argv: tmp += str(sys.argv)+"\n"

		try:
			tmp += "Inlet: "+str(round(self.inlet_ave,2))+"C\t\tSupply: "+str(round(self.supply_ave,2))+"C\td_in : "+str(round(self.supply_ave,2)-round(self.inlet_ave,2))+"C"
			tmp += "\nExtract: "+str(round(self.extract_ave,2))+"C\tExhaust: "+str(round(self.exhaust_ave,2))+"C\td_out: "+str(round(self.extract_ave,2)-round(self.exhaust_ave,2))+"C\n"
			tmp += "Extract dT/dt: "+str(round(self.extract_dt,3))+"degC/min dT/dt: "+str(round(self.extract_dt_long,3))+"("+str(round(numpy.average(self.extract_dt_list)*60,3))+")degC/hr\n\n"
			if "debug" in sys.argv:
				tmp += "Tcomp:" + str(self.tcomp) + " at T1:"+str(self.temps[1])+" coef:"+str(round(self.coef,4))+" inlet coef:"+str(self.inlet_coef)+"\n"
				tmp +="Extract:"+str(self.temps[1])+ "\tInlet:"+str(self.temps[4])+"\tExhaust:"+str(self.temps[2])+"\tSupply,pre:"+str(self.temps[0])+"\tSupply,post:"+str(self.temps[3])+"\n"
		except:pass
		tmp += "Exchanger Setting: "+str(self.exchanger_mode)+" State: "+self.rotor_states[self.rotor_state]+", Rotor Active: "+self.rotor_active+"\n"
		if self.rotor_active=="Yes" or "debug" in sys.argv:
			tmp += "HeatExchange supply "+str(round(self.supply_power,1))+"W \n"
			tmp += "HeatExchange extract "+str(round(self.extract_power+self.condensate_compensation,1))+"W\n"
			if "debug" in sys.argv: tmp += "Diff:"+str(round(numpy.average(self.diff_ave),2))+"% "+str(round(self.supply_power-self.extract_combined,1))+"W\n"
			if "humidity" in sys.argv and "debug" in sys.argv : tmp +="\nCondensation  efficiency: " +str(round(self.cond_eff,2)*100)+"%\n"
		if "humidity" in sys.argv :
			if "debug" in sys.argv:
				#tmp += "Calculated humidity: "+str(round(self.extract_humidity*100,2))+"% at:"+str(round(self.extract_ave,1))+"C Dewpoint:"+str(round(self.dew_point,2))+"C\n"
				tmp += "Static: "+str(round(self.local_humidity+self.humidity_comp,2))+"% "+str(round(self.humidity_comp,2))+"\n"
			tmp += "Calculated Humidity: " + str(round (self.new_humidity,2))+"% Pressure limit: "+str(round(self.indoor_dewpoint,2))+"C\n"
		if "debug" in sys.argv:
			try:
				tmp += "Outdoor Sensor: "+str(self.sensor_temp)+"C "+str(self.sensor_humid)+"% Dewpoint: "+str(round(self.airdata_inst.dew_point(self.sensor_humid,self.sensor_temp),2))+"C\n"
				tmp += "Indoor Sensor: "+str(self.inside)+"C "+str(self.inside_humid)+"% Dewpoint: "+str(round(self.airdata_inst.dew_point(self.inside_humid,self.inside),2))+"C\n"
			except: pass
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
		tmp += "Filter has been installed for "+ str(self.filter)+" days.\n\n"
		tmp += "Ambient Pressure:"+ str(self.airdata_inst.press)+"hPa\n"
		if self.forcast[1]<>-1: tmp += "Weather forecast for tomorrow is: "+str(self.forcast[0])+"C "+self.weather_types[self.forcast[1]]+".\n\n"
		if "Timer" in threading.enumerate()[-1].name: tmp+= "Ventilation timer on: "+str((int(time.time())-int(device.timer))/60)+":"+str((int(time.time()-int(self.timer))%60))+"\n"
		#tmp+= str(threading.enumerate())+"\n"
		if self.shower : tmp += "Shower mode engaged at:" +time.ctime(self.shower_initial)+"\n"
		if self.inhibit>0:tmp+=  "Mode sensing inhibited "+"("+str(int((self.inhibit+600-time.time())/60+1))+"min)\n"
		if self.modetoken >=1 :tmp+= "Mode change inhibited at: "+time.ctime(self.modetoken)+"("+str(int((self.modetoken+3600-time.time())/60+1))+"min)\n"
		if self.cool_mode: tmp+= "Cooling mode is in effect, target is 20.7C extraction temperature\n"
		#tmp += "lower limit:22.0C, when cooling 21.0C, fans up2 22.01C, fans up3 22.5 or +0.5C/hr\nExchanger limits ON:21C OFF:22C\nWeather Data from YR.no\n"
		if not monitoring: tmp += "\nSystem Automation off\n"

		#CLEAR SCREEN AND REPRINT
		clear_screen()
		if self.iter %30==0 and "debug" in sys.argv :
			try:
				ave, dev = statistics.stddev(self.cond_data)
				self.msg += str(len(self.cond_data))+" mean:"+str(ave)+" stddev:"+str(dev)+" "+ str(dev/ave*100)+"%\n"
				#print self.msg
			except : print "mean error"
		tmp +=  self.msg+"\n"
		tmp = tmp.replace("\n",";\n")
		tmp = tmp.replace("\t","'\t")
		print tmp

	#Read all data registers
	def update_registers(self):
		for each in range(100,900,100):
			if   each == 100: addresses = 36
			elif each == 200: addresses = 21
			elif each == 300: addresses = 52
			elif each == 400: addresses = 59
			elif each == 500: addresses = 57
			elif each == 600: addresses = 72
			elif each == 700: addresses = 51
			elif each == 800: addresses = 2
			req.modbusregisters(each,addresses)
			time.sleep(0.1)
			print os.read(bus,200)
			for addr in  range(len(req.response)):
				self.register[str(each+addr+1)]=req.response[addr]
			print len(req.response),"entries recieved at address space:",each

	#print previously read modbus registers
	def print_registers(self):
		try:
			print "\n",
			for each in range(1,73):
				tmp=""
				for address in range(100,900,100):
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
	    def set_val(val):
		try:
			#self.msg += "\nwriting mode "+str(val)+"\n"
                        client.write_register(206,val,functioncode=6)
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
	    if self.press_inhibit < now-(60*3):self.press_inhibit = 0

	#Monitor Logical crits for state changes on exchanger, pressure, rpms, forcast
	def monitor(self):
	    #### FAN RPM MONITORING
	    if self.sf_rpm <1550 and self.fanspeed == 2 : self.inhibit = time.time()
	    if self.sf_rpm <1000 and self.fanspeed == 1 : self.inhibit = time.time()
	    #### EXCHANGER CONTROL
	    if self.forcast[0]< 10: self.target = 23
	    else: self.target = 22
	    if self.modetoken<=0 and self.cool_mode==0 :
		if self.extract_ave >self.target and self.exchanger_mode <> 0 and self.shower == False and self.inlet_ave >10:
			self.modetoken =time.time()
			self.cycle_exchanger(0)
		if self.supply_ave > self.target and self.exchanger_mode <> 0 and self.shower== False:
			self.cycle_exchanger(0)
			self.modetoken=time.time()
		if self.extract_ave < self.target-1 and self.exchanger_mode ==0 and not self.cool_mode :
			self.cycle_exchanger(5)
			self.modetoken=time.time()
		if self.supply_ave <10 and self.extract_ave < self.target and  self.exchanger_mode ==0 and not self.cool_mode :
			self.cycle_exchanger(5)
			self.modetoken=time.time()
		if self.exchanger_mode == 0 and self.inlet_ave < 10 and self.forcast[0] < 10 and self.forcast[1] <> -1 and self.fanspeed == 1 and not self.cool_mode and not self.shower:
			self.modetoken=time.time()
			self.cycle_exchanger(5)

	    #FORECAST RELATED COOLING
	    if self.forcast[0]>16 and self.forcast[1]<4 and self.cool_mode == False and self.extract_ave+0.1 > self.supply_ave and self.extract_ave>20.4:
		self.msg += "predictive Cooling enaged\n"
		if self.exchanger_mode <>0:self.cycle_exchanger(0)
		self.set_fanspeed(3)
		self.cool_mode = True

	    if self.cool_mode ==True:
		if (self.extract_ave <20.7 ) and self.fanspeed <> 1 :
			self.set_fanspeed(1)
			self.msg += "cooling complete\n"
		if self.fanspeed == 3 and self.supply_ave < 10:
			self.set_fanspeed(2)
		if self.fanspeed ==1 and self.extract_ave > 20.8 and self.extract_ave > self.supply_ave:
			self.set_fanspeed(3)
		if self.supply_ave>self.extract_ave+0.1 and self.fanspeed<>1:
			self.set_fanspeed(1)

			self.msg += "no cooling posible due to temperature conditions\n"
		if (self.forcast[0] <= 16 or self.forcast[1]>=4) and time.localtime().tm_hour >12: self.cool_mode=False
	    #DYNAMIC FANSPEED CONTROL

	    if self.fanspeed == 1 and self.extract_ave>self.target and self.extract_ave -self.supply_ave>0.1 and (self.extract_dt_long >= 0.2 and numpy.average(self.extract_dt_list) > 0.2)  and not self.shower and not self.cool_mode:
		 self.set_fanspeed(2)
		 self.msg += "Dynamic fanspeed 2\n"

	    if self.fanspeed <> 3 and self.extract_ave-0.1 > self.supply_ave and  self.inhibit==0 and (self.extract_ave >= 22.5 or (self.extract_dt_long >=0.7 and numpy.average(self.extract_dt_list)>0.7) and self.inlet_ave > 5 or self.extract_ave > 23.0 ) and not self.extract_dt_long < -0.2 and self.exchanger_mode <> 5 and not self.cool_mode and not self.shower:
		self.set_fanspeed(3)
		self.msg += "Dynamic fanspeed 3\n"

	    if self.fanspeed <>1 and self.extract_ave <self.target and self.inhibit == 0 and self.cool_mode == False and not self.shower:
		self.set_fanspeed(1)
		self.msg += "Dynamic fanspeed 1\n"

	    if self.extract_ave < self.supply_ave and self.fanspeed <> 1 and self.inhibit == 0 and self.cool_mode == False and not self.shower:
		self.set_fanspeed(1)
		self.msg += "Dynamic fanspeed, recover cool air\n"

	    if self.fanspeed== 3 and self.extract_ave < self.target+2 and self.extract_ave > self.target and self.exchanger_mode == 5 and not self.cool_mode and not self.inhibit and not self.shower:
		self.set_fanspeed(2)
		self.msg  +="Dynamic fanspeed 2\n"

	    # SHOWER MODE TIMEOUT #
	    if self.shower == True and self.shower_initial -time.time() < -30*60:
		self.shower = False

	    #Dynamic pressure control
	    if self.new_humidity > 20.0: #Low humidity limit, restriction to not set margin lower than 30%RH
		self.indoor_dewpoint = self.airdata_inst.dew_point(self.new_humidity+10,self.extract_ave)
	    else: 
		self.indoor_dewpoint = 5.0
	    if self.inlet_ave > self.indoor_dewpoint+0.1   and self.sf <> self.ef and not self.press_inhibit:
		self.set_differential(0)
		self.press_inhibit = time.time()
	    if self.inlet_ave < self.indoor_dewpoint-0.1  and self.sf == self.ef and self.inlet_ave < 15 and not self.press_inhibit:
		self.set_differential(10)
		self.press_inhibit = time.time()

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
		if percent>20:percent = 20
		if percent<-20:percent =-20
		req.modbusregister(103,0) #nominal supply flow
		#print "sf_nom is", req.response
		target = req.response + req.response * (float(percent)/100)
		#print "to set ef_no to",target
		req.write_register(104,target) # nominal extract flow
		#print "one down"
		high_flow = 107
		if percent < 0 :high_flow += 107*float(percent)/100
		if high_flow >107: high_flow= 107
		#print "high should be extract:", int(high_flow)
		req.write_register(106,int(high_flow)) # reset high extract
		#raw_input(" diff set done")

	#get and set the local low/static humidity
	def get_local(self):
		try:
			out = os.popen("./humid.py "+str(self.extract_ave)).readline()
			tmp = out.split(" ")
			self.local_humidity = float(tmp[0])
			temp = float(tmp[1])
			if temp <> self.prev_static_temp:
				self.prev_static_temp = temp
				self.humidity_comp = 0
			return self.local_humidity
		except:pass

## Init base class ##
if __name__:# not "__main__":
	device = Systemair()

###################################################################
############################ RUN MAIN loop ########################
if __name__:# not  "__main__":
	monitoring = True
	def set_monitoring(bool):
		global monitoring
		monitoring = bool
	input = ""
	try:
	    #FIRST PASS ONLY #
            clear_screen()
	    if "ping" in sys.argv:report_alive()
	    print "First PASS;\n updating fanspeeds;"
	    device.update_airflow()
	    sys.stdout.flush()
	    print "Updating fans rpms;"
	    device.update_fan_rpm()
	    sys.stdout.flush()
	    print "Reading Filter Status;"
	    device.get_filter_status()
	    sys.stdout.flush()
	    print "Retrieving weather forecast;"
	    device.get_forcast()
	    sys.stdout.flush()
	    print "Generating historical graphs;"
	    if "debug" in sys.argv:
		os.system("sudo nice ./grapher.py debug &")
	    else:
		os.system("sudo nice ./grapher.py humidities &")
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
		device.coef = 0.19+(float(device.fanspeed)/100)
		device.inlet_coef=0.14
	    else:
		device.coef= 0.07
		device.inlet_coef = 0.08
	    print "Read initial temperatures;"
	    device.update_temps()
	    device.update_xchanger()
	    device.get_local()
	    device.div = device.inlet_ave
	    starttime=time.time()
	    if "humidity" in sys.argv: 	
		device.moisture_calcs()

	    print "system started:",time.ctime(starttime),";"
	    sys.stdout.flush()
	    time.sleep(2)
	    while True:##### mainloop do each pass ###########
		timeout =0.5
		now = int(time.time()-starttime)
		#do temps,energy and derivatives
		device.update_temps()
		device.update_xchanger()
		device.derivatives()
		## EXEC TREE, exec ssteps need to be prime##
		#check states and flags
		if device.iter%3 ==0:
			device.check_flags()
			if monitoring:
				device.monitor()
				device.shower_detect()
		# update moisture and rotor/rpm
		if device.iter%5==0:
			if "humidity" in sys.argv:
				device.moisture_calcs()
			device.update_fan_rpm()
			device.get_rotor_state()
		#update fans
		if device.iter%7==0:
			device.update_fanspeed()
			device.update_airflow()
		#debug specific and static humidity gain updatade
		if device.iter%11==0:
			if "debug" in sys.argv:
				update_sensors()
				device.get_temp_status()
		#refresh airdata class
		if device.iter%79==0:
			device.update_airdata_instance()
		#calc local humidity and exec logger
		if device.iter%60==0:
			device.msg = ""
			device.get_local()
			logger()
		#send local tempt to temperatur.nu
		if device.iter%29==0 and "temperatur.nu" in sys.argv:
                        os.system("wget -q -O temperatur.nu  http://www.temperatur.nu/rapportera.php?hash=42bc157ea497be87b86e8269d8dc2d42\\&t="+str(round(device.inlet_ave,1))+" &")
		#genetarte graphs
		if device.iter%181==0:
			if "debug" in sys.argv:os.system("nice ./grapher.py debug & >>/dev/null")
			else : os.system("nice ./grapher.py humidities & >> /dev/null")
		# send alive packet to headmaster
		if device.iter%3600==0:
			if "ping" in sys.argv:
				report_alive()
		#restart HTTP SERVER
		if device.iter %(3600*2)==0:
			device.get_filter_status()
			os.system("./http")
			os.system("./ip-replace.sh")  # reset ip-addresses on buttons.html
			device.get_forcast()
		## PRINT TO DISPLAY ##
		device.print_xchanger()
		device.iter+=1
		########### Selection menu if not daemon######
		if "daemon" not in sys.argv:
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
		input = select.select([sys.stdin,cmd_socket],[],[],timeout)[0]
		try:
			if cmd_socket in input:
							sock = cmd_socket.recvfrom(128)
							input = sock[0]
							sender = sock[1]
							device.msg += "Network command recieved: Processing...\n"
							device.print_xchanger()
							sys.stdout.flush()
							log = "echo " + str(time.ctime())+":"+str(input)+str(sender)+">>netlog.log"
							print log
							os.system(log)
			elif sys.stdin in input: 	input = sys.stdin.readline()
		   	try:
				if int(input) ==1:monitoring = not monitoring # Toggle monitoring on / off

				elif int(input) == 2:
					device.set_fanspeed(device.fanspeed+1)
					if "daemon" not in sys.argv:raw_input("press enter to resume")
				elif int(input) == 3:
					clear_screen()
					device.print_attributes()
					sys.stdout.flush()
					time.sleep(10)
					if "daemon" not in sys.argv:raw_input("press enter to resume")
				elif int(input)== 4:
					display_settings()
					sys.stdout.flush()
					time.sleep(10)
					if "daemon" not in sys.argv:raw_input("press enter to resume")
					else: print "break"
					recent=4

				elif int(input)==6:
					device.update_registers()
					if "daemon" not in sys.argv:raw_input("press enter to resume")
					else:print "break"

				elif int(input)==7:
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
				elif int(input)== 8:
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
				elif int(input)== 9:
					device.print_registers()
					sys.stdout.flush()
					time.sleep(10)
					if "daemon" not in sys.argv:raw_input("press enter to resume")
					else: print "break"
				elif int(input)==0:
					device.cycle_exchanger(None)

				if int(input)==97:
					clear_screen()
					device.msg += "Fanspeed to Low\n"
					device.set_fanspeed(1)
				elif int (input)==98:
					device.set_fanspeed(2)
					device.msg += "Fanspeed to Norm\n"
				elif int(input)==99:
					device.set_fanspeed(3)
					device.msg += "fanspeed to High\n"

			except:pass# traceback.print_exc()
		except TypeError:pass
		except ValueError:
			pass
		except:
			error  = open("error.txt","w")
			traceback.print_tb(sys.exc_info()[-1],error)
			traceback.print_exc(error)
			error.close()
			traceback.print_exc()
			if "daemon" not in sys.argv:raw_input("press enter to resume")

	except KeyboardInterrupt:
		print "\nexiting..."
		if threading.enumerate()[-1].name=="Timer": threading.enumerate()[-1].cancel()
		cmd_socket.close()
