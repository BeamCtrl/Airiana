#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
import os

try:
	import pyModbusTCP.client
except:
	pass
"""#######Request object for doing modbus coms##
"""
IP = "localhost"
PORT = "505"
class Request:
    connect_errors = 0
    checksum_errors = 0
    multi_errors = 0
    write_errors = 0
    buff = ""
    counter = 0
    error_time = time.time()
    wait_time = 0.01
    prev_rate = 0
    rate = 0
    iter = 0
    bus = 0
    client = ""
    response = ""
    mode = "RTU"
    def __init__(self, bus, client, mode):
        self.client = client
        self.bus = bus
	self.mode = mode
	if self.mode == "TCP":
		print "using TCP backend"
		# TCP auto connect on first modbus request
		try:
			config = eval (open("ipconfig","r").read())
			self.client = pyModbusTCP.client.ModbusClient(host=config["ip"], port=config["port"], auto_open=True)
		except:
			self.client = pyModbusTCP.client.ModbusClient(host=IP, port=PORT, auto_open=True)
	else:
		print "using RTU backend"
        print "request object created",self.mode

    def modbusregisters(self, start, count, signed=False):
        self.client.precalculate_read_size = True
        self.iter += 1
        try:
            self.response = "no data"
            self.response = self.client.read_registers(start, count)
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
            rate = 0.5
        if rate >= 0.9:
            os.read(self.bus, 1000)
            time.sleep(1)
            fd = os.open("RAM/err", os.O_WRONLY)
            os.write(fd, """read error high rate,
            possible no comms with unit error rate over 90%\n""")
            os.close(fd)
            raise IOError
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
            	self.modbusregister(address, decimals)
            except ValueError:
            	self.buff += os.read(self.bus, 20)  # bus purge
            	self.checksum_errors += 1
            	self.modbusregister(address, decimals)
        	self.client.precalculate_read_size = False
		#print "request om address ", address, "returned", self.response
	else:
		try:
			self.response = self.client.read_input_registers(address, 1)
		except: print "TCP read error on addrs:",address
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
	            pass
	        except ValueError:

	            self.write_errors += 1
	            if tries > 0:
	                self.write_register(reg, value, tries=tries - 1)

	            pass
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
			self.response = self.client.write_input_registers(address, 1)
		except: print "TCP write error on addrs:",address
