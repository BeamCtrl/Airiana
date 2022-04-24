#!/usr/bin/python3
import socket
import time
import select
import sys
import os
sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

def cmds ():
        now = time.ctime(time.time())
        print("""
        CTRL-C to exit,
1: Toggle auto Monitoring        6: Not implemented
2: Toggle fanspeed               7: Set flow differential
3: Print all device attributes   8: Run fans for 15min at Max
4: Display link settings         9: Run the Firestarter mode
5: toggle flowOffset             0: cycle winter/summer mode
10: Not implemented             11: Toggle electric heater
12: Start shower mode           13: Engage Cool mode
14: Enagage AI test
                enter commands:""", end=' ')
print(chr(27)+"[2J")
#cmds()
try:
	while True:
		incomming = select.select([sys.stdin],[],[],2)
		if sys.stdin in incomming[0]:
			cmd = sys.stdin.read(2)
			print(cmd+chr(27)+"[2J")
			sock.sendto(cmd.encode("utf-8"),("127.0.0.1",9876))
		print(chr(27) +"\x1b[H")
		# chr(27) +"[2J\x1b[H"
		page = open("./RAM/out").read()
		if page.find("break")>=0:
			os.system("clear")
			print(page)
			input("press enter to resume")
			print(chr(27) +"[2J\x1b[H")
		else:
			os.system("clear")
			print(page)
			cmds()
except KeyboardInterrupt: exit()
