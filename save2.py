#!/usr/bin/python 
import minimalmodbus,traceback,time,serial
unit = "/dev/serial0"

speeds = (1200,2400,4800,9600,19200,28800,38400,57600,115200)
minimalmodbus.BAUDRATE = 19200
minimalmodbus.PARITY   = serial.PARITY_NONE
minimalmodbus.BYTESIZE = 8
minimalmodbus.STOPBITS = 1		
minimalmodbus.CLOSE_PORT_AFTER_EACH_CALL=True
client = minimalmodbus.Instrument(unit,1)
client.debug=False
client.precalculate_read_size=True
#12100,12101,12102,12103,12104,12105,12106,12107,12108,12109
import sys
if "list" in sys.argv:
	for each in range(21000):
		res= client.read_register(each,0,signed=True)
		if res <>0: print each,":",res
		#if int(res) == 25:
		#	raw_input()

first = {}
second= {}
if "diff" in sys.argv:
   for each in (1,2):
	start =time.time()
	for address in range(1000,21000):
		if address%1000 == 0:
			print "Pass:",each, " Gatherd:",address,"rate: ",1000/(time.time()-start),"reqs/sec"
			start = time.time()
		if each == 1:
			try:
				first[address]= client.read_register(address,0,signed=True)
			except : pass
		else:
			try:
				second[address]= client.read_register(address,0,signed=True)
				if second[address]<>first[address]:  print "Address:",address,"-",first[address],":",second[address]
			except:pass
	#raw_input("press enter to resume diff")

while True:
	   target = raw_input("addrs:")
	   if "w" in target:
		inp =raw_input("data:")
		res = client.write_register(int(target[1:]),int(inp))
   		res = int(client.read_register(int(target[1:]),0,functioncode=4,signed=True))
		print "target:",target[1:],res
	   else:
		target = int(target)
   		res = int(client.read_register(target,0,functioncode=3,signed=True))
		print "target:",target,res

