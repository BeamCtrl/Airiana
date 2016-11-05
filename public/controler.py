#! /usr/bin/python


import SocketServer
import socket, os
hostname = os.popen("hostname").read()[:-1]
class myHandler (SocketServer.BaseRequestHandler):
	
	def handle(self):
		data = self.request.recv(1024).strip().split("\r\n")
		if "GET" in data[0]:
			if "command" in data[0]:
				req = data[0].split(" ")
				command=req[1]
				command=command.split("?")
				s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
                        	s.sendto(str(command[-1]),("127.0.0.1",9876))
                        	s.close()
                        	self.request.send("HTTP/1.1 200 OK\n\n<html><head><script type=\"text/javascript\">function retur(){window.history.back();}setTimeout(\'retur()\',50);</script></head><body></body></html>")


	
SocketServer.TCPServer.allow_reuse_address = True
try:
	srv = SocketServer.TCPServer(("0.0.0.0",8000),myHandler)
except: os.system("sleep 1")

srv.serve_forever()
