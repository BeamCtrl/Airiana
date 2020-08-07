#!/usr/bin/python
import requests
import sys
import os
value=  	sys.argv[sys.argv.index("-v")+1]
unit =  	sys.argv[sys.argv.index("-u")+1]
sensor_name = 	sys.argv[sys.argv.index("-n")+1]
device_class =	sys.argv[sys.argv.index("-d")+1]
conf = open("ha-token", "r")
server = eval( conf.readline())
bearer = conf.readline()
url = "http://"+server["ip"]+":"+str(server["port"])+"/api/states/sensor."+sensor_name
#bearer= "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiI3Y2I3ZjhiMWU3NjU0ZjczOWRlYzgwZDUyN2E3YzFjMyIsImV4cCI6MTg2MTU2NTU3MCwiaWF0IjoxNTQ2MjA1NTcwfQ.a7r2UjyzbA43N6RHJn3tV5SGc4CXMeABrPFrbG8MOhE"


try:
	#headers={"Authorization" :"Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiI3YmQ3OGM1OGIzYTg0MzhlOWU0MDc3NGEzZDk3MjMwNCIsImV4cCI6MTg2MTU2MzYyMywiaWF0IjoxNTQ2MjAzNjIzfQ.vEsVkJdqEKyirCpferhDylBzOPL6q7GVl6JoAh3uxz8a"} 
	headers={"Content-Type":"application/json","Authorization" :"Bearer "+bearer} 
	data= "{\"state\":"+ value+", \"attributes\": {\"unit_of_measurement\":\"" + unit+"\", \"friendly_name\": \""+sensor_name+"\",\"device_class\":\""+device_class+"\",\"default_visibility\":\"visible\"}}"
	response = requests.request('POST', url, data=data,headers=headers)
	print(data,response.text)
except:pass

