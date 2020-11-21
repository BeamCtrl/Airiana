#!/usr/bin/python
# -*- coding: latin-1 -*-
import xml.parsers.expat
import os, time, sys,datetime,json
import traceback
#print dir(os.stat("forecast.xml"))
#print os.stat("forecast.xml").st_ctime -time.time()
loc = os.popen("cat location").read()
"""try:
	with open("latlong.json") as file:
		latlong=json.load(file)
	#print latlong["lat"], latlong["long"]
except IOError:
	print "legacy parsing"
"""
sun ={}
weather_types= {\
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
				15:"Fog",0:"No weather data"}
try:
	try:
		if type(latlong) is dict:
			if os.stat("/home/pi/airiana/RAM/forecast.xml").st_ctime -time.time() < -3600 or os.stat("/home/pi/airiana/RAM/forecast.xml").st_size ==0 or "-f" in sys.argv:
	  			loc = "\"https://api.met.no/weatherapi/locationforecast/2.0/classic?lat="+str(latlong["lat"])+"&lon="+str(latlong["long"])+"\""
				os.system("wget -q -U \"Airiana-forecast-agent\" -O /home/pi/airiana/RAM/forecast.xml "+loc)
	except NameError:
		if os.stat("/home/pi/airiana/RAM/forecast.xml").st_ctime -time.time() < -3600 or os.stat("/home/pi/airiana/RAM/forecast.xml").st_size ==0 or "-f" in sys.argv:
			print "Downloading updated forcast"
			os.system("wget -q -O /home/pi/airiana/RAM/forecast.xml "+loc)

except Exception as err:
		#print "Error getting Forcast from YR.no" #os.system("sudo wget  -q -O forecast.xml http://www.yr.no/sted/Sverige/V%C3%A4stmanland/V%C3%A4ster%C3%A5s-Barkar%C3%B6~2664448/forecast.xml")
		#print err
		print -1, -1
		os.system("touch /home/pi/airiana/RAM/forecast.xml")
		exit()
class Weather():
	def __init__(self):
		self.wind_speed = 0
		self.wind_dir = 0
		self.weather_type =0 
		self.valid_from =0
		self.valid_to =0
		self.period  = -1
		self.temp =0
		self.precipitation =0
		self.pressure =0
		self.symbolic ={}
	def __str__(self):
	 	 return time.asctime(self.valid_from)+" "+str(self.temp)+"C "+str(self.pressure)+"hPa "+str(self.precipitation)+"mm "+str(self.wind_speed)+"m/s Weather type: "+str(weather_types[int(self.weather_type)])+" "
parser = xml.parsers.expat.ParserCreate()
fd = open('/home/pi/airiana/RAM/forecast.xml','r')
forcasts = []
prev_time = 0

def start_element(name, attrs):
	try:
		global prev_time
		#print name, attrs
		if name == 'sun':
			global sun
			sun = attrs
		if name == 'time' and prev_time  != time.strptime(attrs[u'to'],"%Y-%m-%dT%H:%M:%SZ"):
			forcasts.append(Weather())
			forcasts[-1].valid_to =time.strptime(attrs[u'to'],"%Y-%m-%dT%H:%M:%SZ")
			prev_time = forcasts[-1].valid_to
			forcasts[-1].valid_from =time.strptime(attrs['from'],"%Y-%m-%dT%H:%M:%SZ")
			forcasts[-1].period = attrs["period"]
                if name == 'temperature': 	forcasts[-1].temp       = (attrs[u'value'])
                if name == 'pressure': 		forcasts[-1].pressure   = (float(attrs[u'value']))
                if name == 'windSpeed': 	forcasts[-1].wind_speed = (float(attrs[u'mps']))
                if name == 'windDirection': 	forcasts[-1].wind_dir   =  (float(attrs[u'deg']))
                if name == 'precipitation': 	forcasts[-1].precipitation   =  (str(attrs[u'value']))
                if name == 'symbol':
		 	forcasts[-1].symbolic   =  attrs
			forcasts[-1].weather_type = attrs["number"]
	except KeyError:
		pass
		#print name, attrs
parser.StartElementHandler = start_element
try:
	xmldoc = parser.ParseFile(fd)
except :
	traceback.print_exc()
	print "file error, unable to parse xml"
	#print fd.read()
	#os.system("rm -f RAM/forecast.xml")
	exit()
#for each in forcasts: print each

now = time.gmtime()

if len(sys.argv)<2:
	for each in forcasts:
		#print each.symbolic
		if each.period == "2":
			print time.asctime(each.valid_from),
			print each.symbolic["name"].encode("ascii","ignore"),
			print each.temp,"C",
			print each.pressure,"hPa",
			print each.wind_speed,"m/s",
			print "weather type",each.weather_type
			#break
if "now" in sys.argv:
	print time.asctime(forcasts[0].valid_from)+" "+str(forcasts[0].temp)+"C "+str(forcasts[0].pressure)+"hPa "+str(forcasts[0].precipitation)+"mm "+str(forcasts[0].wind_speed)+"m/s Weather type: "+str(int(forcasts[0].weather_type))+" "

if "all" in sys.argv:
	for each in forcasts: print each

if "pressure" in sys.argv:
	print forcasts[0].pressure

tomorrow = datetime.date.today() + datetime.timedelta(days=1)
tomorrow = tomorrow.timetuple()
if "tomorrow" in sys.argv:
	for each in forcasts:
		if each.valid_from.tm_mday==tomorrow.tm_mday and each.period == "2":
			print each.temp,each.weather_type
if "tomorrows-low" in sys.argv:
	tomorrow = datetime.date.today() + datetime.timedelta(days=1)
	tomorrow = tomorrow.timetuple()
	for each in forcasts:
		if each.valid_from.tm_mday==tomorrow.tm_mday and each.period == "1":
			print each.temp, each.weather_type,each.wind_speed


if "sun" in sys.argv and len(sun)<>0:
	print sun['rise'].split("T")[1]
	print sun['set'].split("T")[1]

if "sun" in sys.argv and len(sun)==0:
	print "07:00:00"
	print "19:00:00"

