#!/usr/bin/python3
import socket
import time
import select
import sys
import os
sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

def cmds ():
	now = time.ctime(time.time())
	print(f"""{now}        CTRL-C to exit,
1: Toggle Auto Monitoring        6:
2: Toggle fanspeed               7: Toggle pressure diff
3: Print all device attributes   8: Run fans for 120min at Max
4: Display link settings         9:
5: show/update values           10: Toggle shower mode
                enter commands:""")
print(chr(27)+"[2J")
#cmds()
try:
	while True:
		input= select.select([sys.stdin],[],[],2)
		if sys.stdin in input[0]:
			cmd = sys.stdin.read(2)
			print(cmd+chr(27)+"[2J")
			sock.sendto(cmd.encode("utf-8"),("127.0.0.1",9876))
		print(chr(27) +"\x1b[H")
		#chr(27) +"[2J\x1b[H"
		page = open("./RAM/out").read()
		if page.find("break")>=0:
			os.system("clear")
			print(page)
			raw_input("press enter to resume") 
			print(chr(27) +"[2J\x1b[H")
		else:
			os.system("clear")
			print(page)
			cmds()
except KeyboardInterrupt: exit()
