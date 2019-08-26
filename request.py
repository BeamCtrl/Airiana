#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
import os
import sys

#######Request object for doing modbus comms##
class Request(object):
	def __init__(self,bus,client):
		self.connect_errors= 0
		self.checksum_errors = 0
		self.multi_errors = 0
		self.write_errors = 0
		self.buff= ""
		self.counter = 0
		self.error_time=time.time()
		self.wait_time =  0.01
		self.prev_rate = 0
		self.rate =0
		self.iter = 0
		self.bus = bus
		self.client = client
	def modbusregisters(self,start,count,signed=False):
		self.client.precalculate_read_size=True
		self.iter += 1
		try:
			self.response= "no data"
			try:
				pass#os.write(bus,"\0x01")
			except: pass
			self.response = self.client.read_registers(start,count)
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
			if self.rate < 0.9:
				self.modbusregisters(start,count)
		self.client.precalculate_read_size=False

	def error_review (self):
		delta = self.iter - self.error_time
		self.error_time = self.iter
		if delta <>0:
			rate = float(self.connect_errors+self.checksum_errors+self.write_errors+self.multi_errors) / delta
		else: rate=0.5
		if rate >= 0.9:
			os.read(self.bus,1000)
			time.sleep(1)
			os.write(ferr,"read error high rate, possible no comms with unit error rate over 90%\n")
			raise IOError
		os.system ("echo "+str(rate)+" "+ str(self.wait_time)+" > RAM/error_rate")
		self.connect_errors = 0
		self.checksum_errors = 0
		self.write_errors = 0
		self.multi_errors = 0

	def modbusregister (self,address,decimals):
		self.iter += 1
		self.client.precalculate_read_size=True

		try:
			self.response = "no data"
			self.buff += os.read(self.bus,20) # bus purge
                        self.response = self.client.read_register(address,decimals,signed=True)
		except IOError as error:
	 		self.connect_errors += 1
			if self.connect_errors > 100: self.error_review()
			self.buff += os.read(self.bus,20) # bus purge
			#print "single, no response, retry:",self.connect_errors,address,";"
			self.modbusregister(address,decimals)
		except ValueError as error:
			#print "single, checksum error,retry:",self.checksum_errors,error,";"
			#os.write(ferr,"read: "+str(error)+"\n")
			self.buff += os.read(self.bus,20) # bus purge
			self.checksum_errors +=1
			self.modbusregister(address,decimals)
		self.client.precalculate_read_size=False

	def write_register(self, reg, value,functioncode=6,tries=10):
		self.iter += 1
		self.client.precalculate_read_size=True
		#if start == value: return 0
		try:
			#print "set", reg, "to",value
			#time.sleep(self.wait_time)
			#print os.read(bus,20)
			if tries  > 0:
				resp = self.client.write_register(reg,value,0,6)
			#print tries,reg
			#sys.stdout.flush()
		except IOError as error:
			#print "write, ioerror",error,os.read(self.bus,20),";"
			#os.write(ferr,"write: "+str(error)+"\n")
			self.write_errors += 1
			self.write_register(reg,value,tries=tries-1)
			pass
		except ValueError as error:
			#print "write, val error",error,os.read(self.bus,20),"\n--",reg," ",value,";"
			#os.write(ferr,"write: "+str(error)+"\n")
			self.write_errors += 1
			self.write_register(reg,value,tries=tries-1)

			pass
		self.modbusregister(reg,0)
		if value <> self.response and tries>0:
			self.write_register(reg,value,tries=tries-1)
		if tries == 0:
			fd = os.open("RAM/err",os.WR_ONLY)
			os.write(fd,"Write error, no tries left on register:"+str(reg)+"\n")
			os.close(fd)

