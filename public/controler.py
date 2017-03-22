#! /usr/bin/python


import SocketServer
import socket, os, traceback
hostname = os.popen("hostname").read()[:-1]
ip = os.popen("hostname -I").readline()[:-2]
class myHandler (SocketServer.BaseRequestHandler):
	def handle(self):
	
		data = self.request.recv(1024).strip().split("\r\n")
		#print data
		if "GET" in data[0]:
			if "command" in data[0]:
				req = data[0].split(" ")
				command=req[1]
				command=command.split("?")
				s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
                        	s.sendto(str(command[-1]),("127.0.0.1",9876))
                        	s.close()
                        	self.request.send("HTTP/1.1 200 OK\n\n<html><head><meta http-equiv=\"refresh\" content=\"0; url=/buttons.html\" /></head></html> \n\r")
                        	#self.request.send("HTTP/1.1 200 OK\n\n<html><head><script type=\"text/javascript\">function return(){window.history.back();}setTimeout(\'return()\',1);</script></head><body></body></html>")
		if "POST" in data[0]:
			if "command" in data[0]:
                                req = data[0].split(" ")
                                command=req[1]
                                command=command.split("?")
                                s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
                                s.sendto(str(command[-1]),("127.0.0.1",9876))
                                s.close()
                        	#self.request.send("HTTP/1.1 HTTP/1.1 303 See Other Location: buttons.html \n\r")
                        	self.request.send("HTTP/1.1 200 OK\n\n<html><head><meta http-equiv=\"refresh\" content=\"0; url=http://"+str(ip)+"/buttons.html\" /></head></html> \n\r")

			if "utility" in data[0]:
				os.chdir("..")
				if "reboot" in data[0]:
					os.system("sudo reboot")
				if "update" in data[0]:
					os.system("git pull")
					os.system("./restart")
				if "restart" in data[0]:
					os.system("./restart")
				if "coffee" in data[0]:
			 	     	self.request.send("HTTP/1.1 200 OK\n\n<html><head><meta http-equiv=\"refresh\" content=\"0; url=http://"+str(ip)+"/coffee.txt\" /></head></html> \n\r")
			      	else:
					self.request.send("HTTP/1.1 200 OK\n\n<html><head><meta http-equiv=\"refresh\" content=\"0; url=http://"+str(ip)+"/util.html\" /></head></html> \n\r")


SocketServer.TCPServer.allow_reuse_address = True

while True:
	try:
		srv = SocketServer.TCPServer(("0.0.0.0",8000),myHandler)
		srv.socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)	
		break
	except KeyboardInterrupt:
		exit() 
	except: 
		print "error binding to socket"
		traceback.print_exc()
		os.system("sleep 1")

srv.serve_forever()
