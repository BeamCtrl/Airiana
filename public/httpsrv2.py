#!/usr/bin/python
import SimpleHTTPServer
import SocketServer, os, socket, struct, ssl

cert = "../keys/public.pem"
PORT = 80
dir = "./public/"
os.chdir(dir)

Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
Handler.server_version = "Airiana Web Server interface/2.3e"


class myServer(SocketServer.TCPServer):
    def server_bind(self):
        while True:
            try:
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.socket.setsockopt(
                    socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 2)
                )
                self.socket.bind(self.server_address)
                break
            except:
                os.system("sleep 1")


httpd = myServer(("", PORT), Handler)
# httpd.socket = ssl.wrap_socket(httpd.socket,certfile= cert,server_side=True)

print("serving at port", PORT)
try:
    httpd.serve_forever()
except:
    pass
