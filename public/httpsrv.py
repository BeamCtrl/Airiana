#!/usr/bin/python3
import sys, os, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer, SimpleHTTPRequestHandler

version = sys.version_info[0:2]
print("running on version", version)
if version[0] == 3 and version[1] < 7:
    os.system("python2.7 public/httpsrv2.py&")
    exit()

import socketserver, socket, struct, ssl

print("running python3")
cert = "../keys/public.pem"
PORT = 80
dirs = "./public/"
os.chdir(dirs)
SSID_data = []

def get_ssids():
    global SSID_data
    # check if SSID file has been updated (20s) recently or if no SSIDs are present
    print(f"SSID age: {time.time() - os.path.getmtime('SSID')} size:{os.path.getsize('SSID')}")
    if (not os.path.isfile("SSID")
        or time.time() - os.path.getmtime("SSID") > 20
        or os.path.getsize("SSID") == 0):
        print("Updating SSIDs")
        SSID_data = os.popen("sudo iwlist scan 2>/dev/null |grep ESSID").readlines()
        SSID_data = list(set(SSID_data))
        SSID_data = [ssid for ssid in SSID_data if ssid.find("x00") == -1]
        SSID_data = [ssid for ssid in SSID_data if len(ssid) != 0]
        with open("SSID", "w") as file:
            file.write(" ".join(SSID_data))
    print(SSID_data)


class ExtendedHandler(SimpleHTTPRequestHandler):
    def __init__(self, request, server, handler):
        super().__init__(request, server, handler)

    # Intercept captive portal detection URLs
    def do_GET(self):
        captive_urls = [
            "/hotspot-detect.html",                # iOS
            "/library/test/success.html",          # iOS older
            "/success.txt",                        # Android / Chrome
        ]
        print(f"GET {self.path}")
        if any(url in self.path for url in captive_urls):
            self.send_response(302)  # redirect
            self.send_header("Location", "/index.html")
            self.end_headers()
            return

        if "wifi.html" in self.path or "SSID" in self.path:
            get_ssids()
        ip = self.client_address[0]
        if "current_version" in self.path:
            with open("../checks.txt", "a") as f:
                f.write(f"{ip} {self.path} {time.ctime()}\n")
        super().do_GET()

    # CORS OPTIONS
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
Handler.ssids = get_ssids
httpd = uServer(("", PORT), Handler)

# Uncomment for HTTPS
# httpd.socket = ssl.wrap_socket(httpd.socket, certfile=cert, server_side=True)

print("serving at port", PORT)
try:
    httpd.serve_forever()
except KeyboardInterrupt:
    httpd.socket.close()
