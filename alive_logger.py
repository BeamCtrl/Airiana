#!/usr/bin/python

import socket
import select
import time
import os
os.chdir("/home/pi/airiana")
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
html = """ 
<html>
<meta http-equiv="refresh" content="0;url=http://[IP]">
[DA]

</html>
"""

sock.bind(("0.0.0.0",59999))
while True:
	if sock in select.select( [sock], [], [], 1)[0]:
		incomming_msg, addr=sock.recvfrom(37000)
		#print "***", incomming_msg, "***"
	 	#print incomming_msg.find("ether")

		if incomming_msg.find("ether") > 0:
			print "ether"
			ip = incomming_msg[61:75]
			mac =incomming_msg[14:31]
		else:
			print "hwadddr"
			mac =incomming_msg[38:55]
			ip = incomming_msg[58:72]
		print time.ctime(), "MAC:", mac, "From:",addr
		print "active IP:",ip
		for_file= html.replace("[IP]",ip)
		for_file= html.replace("[DA]",incomming_msg)
		#for_file += "\n"+incomming_msg
		filename = "./public/local_links/"+mac+".html"
		for_file += "\n"+"Source:"+str(addr)
		#print "filename:",filename
		#print for_file
		for_file.replace("\n","<br>##")
		open(filename,"w+").write(for_file)
