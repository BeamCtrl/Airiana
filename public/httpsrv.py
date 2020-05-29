#!/usr/bin/python3
import http.server
import socketserver,os,socket,struct,ssl
cert = "../keys/public.pem"
PORT = 80
dir= "./public/"
os.chdir(dir)

Handler = http.server.SimpleHTTPRequestHandler
Handler.server_version = "Airiana Web Server interface/2.5a"
class uServer(http.server.ThreadingHTTPServer):
	def run(self,server_class=http.server.ThreadingHTTPServer, handler_class=http.server.SimpleHTTPRequestHandler):
		server_address = ("",PORT)
		httpd = server_class(server_address,handler_class)
		httpd.socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
		httpd.serve_forever()

httpd = uServer(('',PORT),Handler)

#httpd.socket = ssl.wrap_socket(httpd.socket,certfile= cert,server_side=True)

print("serving at port", PORT)
try:
	httpd.serve_forever()
except:
	os.close(httpd.socket)
