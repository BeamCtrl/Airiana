#!/usr/bin/python

### density -50C: 1.534 kg/m3  +40C:1.127kg/m3
### specifc heat capacity -50C:1.005KJ/kg*K +40:1.005 KJ/kg*K
### roh = p/RT pressure / 287058 *  273,15+T isa press 101325Pa
import os,time,sys,math
class Energy(object):
	def __init__(self):
		try:
			#GET AMBIENT PRESURE##
			self.press= float(os.popen("./forcast.py pressure").read())
			self.press = self.press -2 # 15m Above sea lvl
		except ValueError:
			 self.press=1013.25-2
			 print "value error for pressure"
		except:
			print "error occured getting current pressure ISA assumed"
		        self.press = 1013.25-2  #hPa Barkaro 15meters above sea level
			err = open("airdata_error.log","w")
			err.write( "Airdata.py pressure error: "+str(sys.exc_info()))
			err.close()
		#print"Ambient air pressure used:",self.press,"hPa"
		self.T=273.15 #K  Zero Celcius in Kelvin
		self.R=287.058 #   GAS CONSTANT for dry air for pressures in Pa 
		self.density= lambda t: (self.press*100)/(self.R*(self.T+t))
		self.specific_heat = 1.005  #J/g*K
		self.humid = .50
		self.mass_const = 0.62198

	#CALCULATE AIR DENSITY AT A GIVEN TEMPERATURE
	def get_mass(self,temp):
		return (self.density(temp)) #kg/m3
	def temp_diff(self,energy, extract_temp,extract_flow):
		d_W = energy
		d_T = 0.1
		d_temp = 0.0
		while d_W >0:
			density = self.density(extract_temp+d_temp)
			mass = density * extract_flow
			energy = mass * self.specific_heat*d_T
			d_W -=  energy
			d_temp += d_T
		return d_temp
		
	#CALCULATE THE ENERGY REQUIRED TO SENSIBLY RAISE OR LOWER TEMPERATURE FOR A GIVVEN VOLUME
	def energy_flow(self,litres,high,low):
		total=0
		step =1
		if low < high:step=-1
		for each in range(int(high*100),int(low*100),step):
			density = self.density(float(each)/100) # kg/m3
			volume  = float(litres)/1000 #m3
			d_T= 0.01  # K
			mass = density*volume #kg/m3 * m3 = kg
			energy = mass * self.specific_heat*d_T #kg  * J/gK  * K  = J
			#print energy, float(each)/100,"C", total,"W"
			total += energy*1000
		#print "high",high,"low",low,"litres",litres,round(self.get_mass(high/10),2),round(self.get_mass(low/10),2), "energy", int(total)
		return total

	#RETURN MAXIMUM VAPOR CONTENT BY MASS
	def vapor_max(self,T):
		self.pw = 6.1121*math.exp( (18.678-T/234.5) * (T/(T+257.14))  )
		self.abs=(self.pw*2.16679)/(self.T+T)   *100 #### BUG WHY FACTOR 100//solved convertsion from hPa
		#print self.abs,"g/m3 vapor_max"," temp:",T," sat. pressure:",self.pw
		return self.abs
	def sat_vapor_press (self,T):
		self.pw = 6.1121*math.exp( (18.678-T/234.5) * (T/(T+257.14))  ) * 100
		return self.pw
	def vapor_mass(self,pw): #return vapor mass from vapor partial pressure
		return (self.mass_const*pw)/(self.press-pw)

	def energy_to_pwdiff(self, energy, temp):
		mass_quiv = self.condensation_mass(energy) # grams condensate per kilogram air
		#d_pw = self.press*100*(float(mass_quiv*0.001)/self.mass_const)
		d_pw = (mass_quiv/1000 * self.press*100)/(self.mass_const+mass_quiv)#/(self.get_mass(temp)*1000)
		return d_pw

	def condensation_mass(self,energy):
		return float(energy) / 2490  # (g) 2490kJ/kg latent heat convertsion

	def xchange_humid(self,T):
		content = (self.abs*self.humid)/100
		rel = float(content / self.vapor_max(T))*100
		#print "extraction relative humidity:", round(rel,0), "% ", "vapor content is:",round(content,2), "grams per cubic meter"

	#Return latent energy in a givven mas of condensing water vapor
	def condensation_energy (self, grams):
		return float(grams*(2490)) # 2490 kJ/Kg consensated water

	# CALCULATE DEWPOINT FROM temperature and relative humidity
	def dew_point(self,RH,temp):
		#Constants used acc NOAA std#
		a=6.1121 #mBar
		b=18.678
		c=234.5 # C
		d=257.14 #acc ardon buck (1996)
		def gamma(RH,temp):
			Ps = math.log((float(RH)/100)*math.exp( ((b-(temp/d))*(temp/(c+temp))) )  )
			return Ps
		return (c*gamma(RH,temp))/(b-gamma(RH,temp))


# Abs_hum  = C * Pw/T  C = 2.16679 gK/J Pw vapor press T temp in Kelvin
#Pw = A*10^(mT/T+Tn)  -->A=6.116441 m=7.591386 Tn=240.7263   vl -20C ->+50C
#ref Vaisala.comhumidity conversion formulas
if  "__main__" in __name__:
	air =Energy()
	#print air.energy_to_pwdiff(25,22)
	#print air.energy_to_pwdiff(12,22)/(0.0034)
	#print air.sat_vapor_press(10)
	#print air.sat_vapor_press(20)
	#print air.sat_vapor_press(100)
	#for each in range(-60,121):
	#	print air.density(each),"kg/m3",each, "C", air.sat_vapor_press(each),"Pa"
	#print air.dew_point(30,22.0)		
	print air.energy_flow(34,18.29,21.73)
	print air.energy_flow(34,21.58,17.73)
