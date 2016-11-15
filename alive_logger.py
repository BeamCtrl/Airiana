#!/usr/bin/python

import socket
import select
import os
import time
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
html = """ 
<html>
<meta http-equiv="refresh" content="0;url=http://[IP]">


</html>
"""

sock.bind(("0.0.0.0",59999))
while True:
	if sock in select.select( [sock], [], [], 1)[0]:
		incomming_msg, addr=sock.recvfrom(1024)
		mac =incomming_msg[38:55]
		ip = incomming_msg[58:]
		#print time.ctime(), "MAC:", mac, "From:",addr
		#print "active IP:",ip
		for_file= html.replace("[IP]",ip)
		filename = "./public/local_links/"+mac+".html"
		#print "filename:",filename
		#print for_file
		open(filename,"w+").write(for_file)
