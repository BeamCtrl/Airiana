#!/usr/bin/python3
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
PORT = 505
minimalmodbus.BAUDRATE = 19200
minimalmodbus.PARITY = serial.PARITY_NONE
minimalmodbus.BYTESIZE = 8
minimalmodbus.STOPBITS = 1


#############################################


class Request:
    def __init__(self):
        self.client = None
        self.connect_errors = 0
        self.checksum_errors = 0
        self.multi_errors = 0
        self.write_errors = 0
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
        self.latest_request_address = 0
        self.latest_request_mode = "Single"
        self.latest_request_decimals = 0
        self.latest_request_count = 0
        self.connection_timeout = 0

    def setup(self, unit, mode):
        self.unit = unit
        self.mode = mode
        if self.mode == "TCP":
            print("Using TCP backend")
            # TCP auto connect on first modbus request
            try:
                config = open("ipconfig", "r").readline()
                print("Reading ip configuration file for IAM access", config[:-1])
                config = eval(config)
                self.client = pyModbusTCP.client.ModbusClient(
                    host=config["ip"], port=config["port"], auto_open=True
                )
            except:
                print(
                    "Fallback localhost:505 server there may be a problem with formating the ipconfig file or it may not exist"
                )  # noPEP8
                self.client = pyModbusTCP.client.ModbusClient(
                    host=IP, port=PORT, auto_open=True, auto_close=True
                )
        else:
            print("Using RTU backend;")
            ID = 1  # UNIT ID
            self.bus = os.open(
                self.unit, os.O_RDONLY | os.O_NONBLOCK
            )  # read bus file to drain buffers
            try:
                buf = os.read(
                    self.bus, 1000
                )  # read 1k chars to empty buffer before starting the instrument
            except OSError:
                pass  # the buffer is empty
            client = minimalmodbus.Instrument(
                self.unit, ID
            )  # setup the minimal modbus client
            client.debug = False
            client.precalculate_read_size = True
            client.timeout = 0.05
            self.client = client
            wait_time = 0.00

        print("request object created: ", self.mode, ";\n")
        test = self.comm_test()
        print("Comm test: ", test, ";\n")

    def close(self):
        self.client.serial.close()

    def comm_test(self):
        print("Running Comm test;")
        fd = os.open("RAM/request.log", os.O_WRONLY | os.O_CREAT)
        self.modbusregister(101, 0)  # Read non savecair flow address
        first = self.response
        os.write(
            fd, bytes("Testing Non-savecair address 101:" + str(first) + "\n", "utf-8")
        )
        print("Testing Non-savecair address 101:" + str(first) + ";")
        self.modbusregister(12543, 0)  # Read savecair address space
        second = self.response
        print("Testing savecair address 12543:" + str(second) + ";")
        os.write(
            fd, bytes("Testing savecair address 12543:" + str(second) + "\n", "utf-8")
        )
        if (
            (first == 0 and second == 0)
            or (first == "no data" and second == "no data")
            or (first == "" and second == "")
            or (first == 0 and second == "no data")
            or (first == "no data" and second == 0)
        ):
            os.write(fd, bytes("Request object Failed communications test.\n", "utf-8"))
            os.close(fd)
            return False
        os.write(fd, bytes("Request object Passed communications test.\n", "utf-8"))
        os.close(fd)
        return True

    def modbusregisters(self, start, count, signed=False):
        self.client.precalculate_read_size = True
        self.latest_request_address = start
        self.latest_request_mode = "Multi"
        self.latest_request_count = count
        self.iter += 1
        try:
            self.response = "no data"
            if self.mode == "RTU":
                self.response = self.client.read_registers(start, count)
            else:
                self.response = self.client.read_holding_registers(start, count)
            if signed:
                for each in self.response:
                    if each & 0x8000:
                        each -= 0xFFFF

        except ValueError as error:
            if -1 != error.message.find("\x01\x83\x02\xc0\xf1"):
                print("multi, address out of range;")
            # exit()
            self.checksum_errors += 1
            self.modbusregisters(start, count)
        except IOError:
            self.connect_errors += 1
            if self.connect_errors > 1000 or self.multi_errors > 1000:
                self.error_review()
            if self.rate < 0.99:
                self.modbusregisters(start, count)
        self.client.precalculate_read_size = False

    def error_review(self):
        delta = self.iter - self.error_time
        self.error_time = self.iter
        if delta != 0:
            rate = (
                float(
                    self.connect_errors
                    + self.checksum_errors
                    + self.write_errors
                    + self.multi_errors
                )
                / delta
            )
        else:
            rate = 0.0
        if rate >= 0.99:
            os.read(self.bus, 1000)
            self.connection_timeout += 1
            time.sleep(10)
            fd = os.open("RAM/err", os.O_WRONLY)
            os.lseek(fd, os.SEEK_SET, os.SEEK_END)
            os.write(
                fd,
                bytes(
                    """read error high rate,
            possible no communication with unit, error rate over 99%\n""",
                    "utf-8",
                ),
            )
            os.fsync(fd)
            os.close(fd)
            self.close()
            self.setup(self.unit, self.mode)
            # exit(-1)
        os.system("echo " + str(rate) + " " + str(self.wait_time) + " > RAM/error_rate")
        self.connect_errors = 0
        self.checksum_errors = 0
        self.write_errors = 0
        self.multi_errors = 0

    def modbusregister(self, address, decimals):
        """

        :type self: request Object for modbus comm
        """
        self.latest_request_address = address
        self.latest_request_mode = "Single"
        self.latest_request_decimals = decimals
        if self.mode == "RTU":
            self.iter += 1
            self.client.precalculate_read_size = True

            try:
                self.response = "no data"
                os.read(self.bus, 20)  # bus purge
                self.response = self.client.read_register(
                    address, decimals, signed=True
                )
            except (IOError, ValueError, TypeError):
                self.connect_errors += 1
                if self.connect_errors > 1000:
                    self.error_review()
                try:
                    os.read(self.bus, 20)  # bus purge
                except TypeError:
                    pass  # read should not typeError here, but does somehow.
                if address == 12543 and self.connect_errors >= 10:
                    return 0
                self.modbusregister(address, decimals)
        else:
            data = "noData"
            try:
                data = self.client.read_holding_registers(address, 1)
                self.response = data[0]
                if decimals != 0:
                    self.response /= decimals * 10
            except TypeError:
                print("TCP read error on address:", address, data)

        self.reset = 0  # set reset counter to 0

    def write_register(self, reg, value, tries=10):
        if self.mode == "RTU":
            self.iter += 1
            self.client.precalculate_read_size = True

            try:
                if tries > 0:
                    self.client.write_register(reg, value, 0, 6)
            except (IOError, ValueError):
                self.write_errors += 1
                if tries > 0:
                    self.write_register(reg, value, tries=tries - 1)

            self.modbusregister(reg, 0)
            if value != self.response and tries > 0:
                self.write_register(reg, value, tries=tries - 1)

            if tries == 0:
                fd = os.open("RAM/err", os.O_WRONLY)
                os.write(
                    fd,
                    bytes(
                        "Write error, no tries left on register:" + str(reg) + "\n",
                        "utf-8",
                    ),
                )
                os.close(fd)
        else:
            try:
                valid = self.client.write_single_register(reg, value)
                self.modbusregister(reg, 0)
                if value != self.response and tries > 0:
                    self.write_errors += 1
                    self.write_register(reg, value, tries=tries - 1)
                if tries == 0:
                    fd = os.open("RAM/err", os.O_WRONLY)
                    os.write(
                        fd,
                        bytes(
                            "Write error, no tries left on register:"
                            + str(reg)
                            + " "
                            + str(valid)
                            + "\n",
                            "utf-8",
                        ),
                    )
                    os.close(fd)

            except:
                with os.open("RAM/err", os.O_WRONLY) as fd:
                    os.write(
                        fd,
                        bytes("TCP write error on addrs:" + str(reg) + "\n", "utf-8"),
                    )


if "__main__" == __name__:
    # Setup serial, RS 485 to machine
    if os.path.lexists("/dev/ttyUSB0"):
        print("Communication started on device ttyUSB0;")
        unit = "/dev/ttyUSB0"

    elif os.path.lexists("/dev/serial0"):
        print("Communication started on device Serial0;")
        unit = "/dev/serial0"
    else:
        print("Communication started on device ttyAMA0;")
        unit = "/dev/ttyAMA0"

    req = Request()
    req.setup(unit, "RTU")
    req = Request()
    req.setup(unit, "TCP")
