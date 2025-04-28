#!/usr/bin/python3
import sys, os, time

version = sys.version_info[0:2]
print("running on version", version)
if version[0] == 3 and version[1] < 7:
    os.system("python2.7 public/httpsrv2.py&")
    exit()
from http.server import (
    BaseHTTPRequestHandler,
    ThreadingHTTPServer,
    SimpleHTTPRequestHandler,
)
import socketserver, os, socket, struct, ssl

print("running python3")
cert = "../keys/public.pem"
PORT = 80
dirs = "./public/"
os.chdir(dirs)


def get_ssids():
    SSID_data = (
        os.popen("sudo iwlist scan 2>/dev/null |grep ESSID|xargs").read().split(" ")
    )
    SSID_data = list(set(SSID_data))
    SSID_data = [ssid for ssid in SSID_data if ssid.find("x00") == -1]
    with open("SSID", "w") as file:
        file.write(" ".join(SSID_data))


class ExtendedHandler(SimpleHTTPRequestHandler):
    def __init__(self, request, server, handler):
        super().__init__(request, server, handler)

    def finish(self):
        req = self.request
        if (
            self.requestline.find("wifi.html") != -1
            or self.requestline.find("SSID") != -1
        ):
            get_ssids()
        ip = self.request.getpeername()[0]
        if self.requestline.find("current_version") != -1:
            os.system(
                "echo "
                + str(ip)
                + " "
                + self.requestline
                + " "
                + str(time.ctime())
                + " >> ../checks.txt"
            )
        SimpleHTTPRequestHandler.finish(self)

    def do_OPTIONS(self):
        print("sending options")
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "http://192.168.1.61")
        self.send_header("Access-Control-Allow-Methods", "PUT, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


class uServer(ThreadingHTTPServer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


Handler = ExtendedHandler
Handler.server_version = "Airiana Web Server interface/2.5a"
Handler.ssids = get_ssids()
httpd = uServer(("", PORT), Handler)

# httpd.socket = ssl.wrap_socket(httpd.socket,certfile= cert,server_side=True)
print("serving at port", PORT)
try:
    httpd.serve_forever()
    pass
except:
    httpd.socket.close()
