#!/usr/bin/python3
# FOR TESTING use ./save2.py dev /dev/[your_device] test
# to manually read an address use ./save2.py
# to manually write to an address put a w before the address input "w1234"
# to list a range of addresses use ./save2.py list
# to diff two passes to see changes in the addresses use ./save2.py diff
#
# if your unit is a non savecair use address 101
# if you have a savecair use 1333
# as the savecair units have a different address space.
#

import minimalmodbus
import traceback
import time
import serial
import sys, os

for each in sys.argv:
    if not each.find("dev") == -1:
        print("Using: " + each)
        unit = each
try:
    if not unit: pass
except:
    print("using default: serial0")
    unit = "/dev/serial0"
i = 0
target = None
speeds = (1200, 2400, 4800, 9600, 19200, 28800, 38400, 57600, 115200)
# print speeds[i]
# 12100,12101,12102,12103,12104,12105,12106,12107,12108,12109
import sys

if "test" in sys.argv:
    import minimalmodbus

    addrs = 1333
    for speed in speeds:
        try:
            minimalmodbus.BAUDRATE = speed
            minimalmodbus.PARITY = serial.PARITY_NONE
            minimalmodbus.BYTESIZE = 8
            minimalmodbus.STOPBITS = 1
            minimalmodbus.CLOSE_PORT_AFTER_EACH_CALL = True
            client = minimalmodbus.Instrument(unit, 1)
            client.serial.baudrate = speed
            client.debug = False
            client.precalculate_read_size = True
            res = client.read_register(addrs, 0, signed=True)
            print(addrs, ":", res, "@", speed)
            print(os.popen("stty -F -a /dev/serial0").read())
            sys.stdout.flush()
        except minimalmodbus.NoResponseError:
            print("no response from unit")
        except:
            print("break at ", speed, traceback.print_exc())
    exit()
minimalmodbus.BAUDRATE = 19200  # speeds[i]
minimalmodbus.PARITY = serial.PARITY_NONE
minimalmodbus.BYTESIZE = 8
minimalmodbus.STOPBITS = 1
minimalmodbus.CLOSE_PORT_AFTER_EACH_CALL = True
client = minimalmodbus.Instrument(unit, 1)
client.debug = False
client.precalculate_read_size = True

if "list" in sys.argv:
    for each in range(1000, 21000):
        res = client.read_register(each, 0, signed=True)
        if res:
            print(each+1, ":", res)
            sys.stdout.flush()
    # else: print each
    # if int(res) == 25:
    #	raw_input()

first = {}
second = {}
if "diff" in sys.argv:
    for each in (1, 2):
        start = time.time()
        for address in range(1000, 21000):
            if address % 1000 == 0:
                print("Pass:", each, " Gatherd:", address, "rate: ", 1000 / (time.time() - start), "reqs/sec")
                start = time.time()
            if each == 1:
                try:
                    first[address] = client.read_register(address, 0, signed=True)
                except:
                    pass
            else:
                try:
                    second[address] = client.read_register(address, 0, signed=True)
                    if second[address] != first[address]:  print("Address:", address, "-", first[address], ":",
                                                                 second[address])
                except:
                    pass

while True:
    try:
        if target == None: target = input("addrs:")
        if "w" in target:
            inp = input("data:")
            res = client.write_register(int(target[1:]), int(inp))
            res = int(client.read_register(int(target[1:]), 0, functioncode=4, signed=True))
            print("target:", target[1:], res)
        else:
            target = int(target)
            res = int(client.read_register(target, 0, functioncode=3, signed=True))
            print("target:", target, res)
    except IndexError:
        i = 0
    except KeyboardInterrupt:
        exit(2)
    target = None
