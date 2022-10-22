#!/usr/bin/python3
import sys, os, time

version = sys.version_info[0:2]
print("running on version", version)
if version[0] == 3 and version[1] < 7:
    os.system("python2.7 public/httpsrv2.py&")
    exit()
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer, SimpleHTTPRequestHandler
import socketserver, os, socket, struct, ssl

print("running python3")
cert = "../keys/public.pem"
PORT = 80
dirs = "./public/"
os.chdir(dirs)


def get_ssids():
    ssid_list = []
    ssids = os.popen("sudo iwlist scan |grep SSID").readlines()
    for each in ssids:
        each = each.replace("ESSID:", "")
        each = each.replace(" ", "")
        each = each.replace("\n", "")
        each = each.replace("\"", "")
        ssid_list.append(each)
    return ssid_list


class ExtendedHandler(SimpleHTTPRequestHandler):
    def __init__(self, request, server, handler):
        super().__init__(request, server, handler)

    def finish(self):
        req = self.request
        if self.requestline.find("wifi.html") != -1:
            os.system("sudo iwlist scan |tr '\n' ',' >> ./SSID")
        ip = self.request.getpeername()[0]
        if self.requestline.find("current_version") != -1:
            os.system("echo " + str(ip) + " " + self.requestline + " " + str(time.ctime()) + " >> ../checks.txt")
        SimpleHTTPRequestHandler.finish(self)


class uServer(ThreadingHTTPServer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


Handler = ExtendedHandler
Handler.server_version = "Airiana Web Server interface/2.5a"
Handler.ssids = get_ssids()
httpd = uServer(('', PORT), Handler)

# httpd.socket = ssl.wrap_socket(httpd.socket,certfile= cert,server_side=True)
print("serving at port", PORT)
try:
    httpd.serve_forever()
    pass
except:
    httpd.socket.close()
