#!/usr/bin/python
# -*- coding: latin-1 -*-
import xml.parsers.expat
import os, time, sys,datetime
#print dir(os.stat("forecast.xml"))
#print os.stat("forecast.xml").st_ctime -time.time()
try:
	if os.stat("./RAM/forecast.xml").st_ctime -time.time() < -3600 or os.stat("./RAM/forecast.xml").st_size ==0:
		#print "Downloading updated forcast" 
		os.system("wget -q -O ./RAM/forecast.xml http://www.yr.no/sted/Sverige/V%C3%A4stmanland/V%C3%A4ster%C3%A5s-Barkar%C3%B6~2664448/forecast.xml")
except Exception as err:
		print "Error getting Forcast from YR.no"#os.system("sudo wget  -q -O forecast.xml http://www.yr.no/sted/Sverige/V%C3%A4stmanland/V%C3%A4ster%C3%A5s-Barkar%C3%B6~2664448/forecast.xml")
		print err
		os.system("touch ./RAM/forecast.xml")
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
	 	 return time.asctime(self.valid_from)+" "+str(self.temp)+"C "+str(self.pressure)+"hPa "+str(self.precipitation)+"mm "+str(self.wind_speed)+"m/s Weather type: "+str(self.weather_type)+" "
parser = xml.parsers.expat.ParserCreate()
fd = open('./RAM/forecast.xml','r')
forcasts = []
def start_element(name, attrs):
		#print name , attrs
		if name == 'time': 
			forcasts.append(Weather())
			forcasts[-1].valid_to =time.strptime(attrs['to'],"%Y-%m-%dT%H:%M:%S")
			forcasts[-1].valid_from =time.strptime(attrs['from'],"%Y-%m-%dT%H:%M:%S")
			forcasts[-1].period = attrs["period"]
                if name == 'temperature': 	forcasts[-1].temp       = (int(attrs[u'value']))
                if name == 'pressure': 		forcasts[-1].pressure   = (float(attrs[u'value']))
                if name == 'windSpeed': 	forcasts[-1].wind_speed = (float(attrs[u'mps']))
                if name == 'windDirection': 	forcasts[-1].wind_dir   =  (str(attrs[u'code']))
                if name == 'precipitation': 	forcasts[-1].precipitation   =  (str(attrs[u'value']))
                if name == 'symbol':
		 	forcasts[-1].symbolic   =  attrs
			forcasts[-1].weather_type = attrs["number"]

parser.StartElementHandler = start_element
xmldoc = parser.ParseFile(fd)

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
	print forcasts[0]
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
			print each.temp, each.weather_type
		
