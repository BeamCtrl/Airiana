#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
import os
import minimalmodbus
import serial

try:
	import pyModbusTCP.client
except:
	pass
"""#######Request object for doing modbus coms##
"""
IP = "localhost"
PORT = "505"
minimalmodbus.BAUDRATE = 19200
minimalmodbus.PARITY = serial.PARITY_NONE
minimalmodbus.BYTESIZE = 8
minimalmodbus.STOPBITS=1
#############################################

class Request:
    def __init__(self):
        self.connect_errors = 0
        self.checksum_errors = 0
    	self.multi_errors = 0
    	self.write_errors = 0
    	self.buff = ""
    	self.counter = 0
    	self.error_time = time.time()
    	self.wait_time = 0.01
    	self.prev_rate = 0
    	self.rate = 0
    	self.iter = 0
    	self.bus = 0
    	self.fclient = ""
    	self.response = ""
    	self.mode = "RTU"
    	self.unit = ""
	self.reset = 0

    def setup(self, unit, mode):
        self.unit = unit
        self.mode = mode
	if self.mode == "TCP":
		print "Using TCP backend\n"
		# TCP auto connect on first modbus request
		try:
			config = open("ipconfig","r").readline()
			print "Reading ip configuration file for IAM access", config
			config = eval(config)
			self.client = pyModbusTCP.client.ModbusClient(host=config["ip"], port=config["port"], auto_open=True)
		except:
			print "Fallback localhost:505 server there may be a problem with formating the ipconfig file or it may not exist"
			self.client = pyModbusTCP.client.ModbusClient(host=IP, port=PORT, auto_open=True)
	else:
		print "Using RTU backend;"
		ID = 1 # UNIT ID
                self.bus = os.open(self.unit,os.O_RDONLY|os.O_NONBLOCK)  # read bus file to drain buffers
                try:
			buf  = os.read(self.bus,1000) # read 1k chars to empty buffer before starting the instrument
		except OSError: pass # the buffer is empty
		client = minimalmodbus.Instrument(self.unit,ID) # setup the minimal modbus client
		client.debug=False
		client.precalculate_read_size=True
 		client.timeout= 0.05
                self.client = client
                wait_time = 0.00

        print "request object created: ",self.mode,";\n"
	test = self.comm_test()
	print "Comm test: ", test, ";\n"

    def comm_test(self):
		print "Running Comm test"
	        fd = os.open("RAM/request.log", os.O_WRONLY|os.O_CREAT)
		self.modbusregister(101,0) # Read non savecair flow address
		first = self.response
            	os.write(fd, "Testing Non-savecair address 101:" +str(first)+"\n")
            	print "Testing Non-savecair address 101:" +str(first)
		self.modbusregister(12543,0) # Read savecair address space
		seccond = self.response
		print "Testing savecair address 12543:" +str(seccond)
            	os.write(fd, "Testing savecair address 12543:" +str(seccond)+"\n")
		if first == 0 and seccond == 0 or (first =="no data" and seccond=="no data"):
            		os.write(fd, "Request object Failed communications test.\n")
            		os.close(fd)
			return False
		os.write(fd, "Request object Passed communications test.\n")
          	os.close(fd)
		return True

    def modbusregisters(self, start, count, signed=False):
        self.client.precalculate_read_size = True
        self.iter += 1
        try:
            self.response = "no data"
	    if self.mode== "RTU":
                self.response = self.client.read_registers(start, count)
            else:
                self.response = self.client.read_holding_registers(start, count)
            if signed:
                for each in self.response:
                    if each & 0x8000:
                        each -= 0xFFFF

        except ValueError as error:
            if -1 != error.message.find("\x01\x83\x02\xc0\xf1"):
                print "multi, address out of range;"
            # exit()
            self.checksum_errors += 1
            self.modbusregisters(start, count)
        except IOError:
            self.connect_errors += 1
            if self.connect_errors > 100 or self.multi_errors > 100:
                self.error_review()
            if self.rate < 0.9:
                self.modbusregisters(start, count)
        self.client.precalculate_read_size = False

    def error_review(self):
        delta = self.iter - self.error_time
        self.error_time = self.iter
        if delta != 0:
            rate = float(self.connect_errors +
                         self.checksum_errors +
                         self.write_errors +
                         self.multi_errors) / delta
        else:
            rate = 0.0
        if rate >= 0.9:
            os.read(self.bus, 1000)
            time.sleep(1)
            fd = os.open("RAM/err", os.O_WRONLY)
	    os.lseek(fd, os.SEEK_SET, os.SEEK_END)
            os.write(fd, """read error high rate,
            possible no comms with unit error rate over 90%\n""")
            os.close(fd)
	    exit(-1)
        os.system("echo " + str(rate)
                  + " "
                  + str(self.wait_time)
                  + " > RAM/error_rate")
        self.connect_errors = 0
        self.checksum_errors = 0
        self.write_errors = 0
        self.multi_errors = 0

    def modbusregister(self, address, decimals):
        """

        :type self: request Object for modbus comm
        """
        if self.mode == "RTU":
	    self.iter += 1
            self.client.precalculate_read_size = True

            try:
        	self.response = "no data"
        	self.buff += os.read(self.bus, 20)  # bus purge
        	self.response = self.client.read_register(
        	        address, decimals,
        	        signed=True)
       	    except IOError:
        	self.connect_errors += 1
            	if self.connect_errors > 100:
                	self.error_review()
            	self.buff += os.read(self.bus, 20)  # bus purge
		if address == 12543 and self.connect_errors >= 10: return 0
            	self.modbusregister(address, decimals)
            except ValueError:
            	self.buff += os.read(self.bus, 20)  # bus purge
            	self.checksum_errors += 1
		if address == 12543 and self.checksum_errors >= 10: return 0
            	self.modbusregister(address, decimals)
        	#self.client.precalculate_read_size = False
		#print "request om address ", address, "returned", self.response
        else:
            try:
                self.response = self.client.read_holding_registers(address, 1)[0]
                if decimals != 0:
                    self.response/=(decimals*10)
            except: print "TCP read error on addrs:",address

	self.reset = 0 #set reset counter to 0
    def write_register(self, reg, value, tries=10):
	if self.mode == "RTU":
	        self.iter += 1
	        self.client.precalculate_read_size = True

	        try:
	            if tries > 0:
	                self.client.write_register(reg, value, 0, 6)
	        except IOError:

	            self.write_errors += 1
	            if tries > 0:
	                self.write_register(reg, value, tries=tries - 1)

	        except ValueError:
	            self.write_errors += 1
	            if tries > 0:
	                self.write_register(reg, value, tries=tries - 1)

	        self.modbusregister(reg, 0)
	        if value != self.response and tries > 0:
	            self.write_register(reg, value, tries=tries - 1)

	        if tries == 0:
	            fd = os.open("RAM/err", os.O_WRONLY)
	            os.write(fd,
	                     "Write error, no tries left on register:"
	                     + str(reg) + "\n")
	            os.close(fd)
	else:
		try:
			self.response = self.client.write_single_register(address, 1)
		except:  
			with os.open("RAM/err","w") as fd:
				os.write(fd, "TCP write error on addrs:" + str(address) + "\n")
