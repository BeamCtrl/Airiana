#! /usr/bin/python3

import socketserver
import socket
import os
import traceback
import time
import sys
hostname = os.popen("hostname").read()[:-1]


class MyHandler(socketserver.BaseRequestHandler):
    def send_ok(self):
        self.request.send(bytes(
            "HTTP/1.1 200 OK\n\n<html><head><meta http-equiv=\"refresh\" content=\"0; url=http://"
            + self.ip + "/\" /></head></html> \n\r", "utf-8"))
    def send_home(self):
        self.request.send(bytes("HTTP/1.1 302 Found\r\nLocation: http://airiana.local/\r\n\r\n", "utf-8"))

    def handle(self):
        self.ip = os.popen("hostname -I").readline().split(" ")[0]
        data = str(self.request.recv(1024), "utf-8").strip().split("\r\n")
        print(data[0])
        sys.stdout.flush()
        if "GET" in data[0]:
            if "command" in data[0]:
                req = data[0].split(" ")
                command = req[1]
                command = command.split("?")
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.sendto(bytes(command[-1], "utf-8"), ("127.0.0.1", 9876))
                s.close()
                self.send_ok()

        if "POST" in data[0]:
            if "setup" in data[0]:
                print(data)
                network = ""
                password = ""
                data = data[-1]
                command = data.split("?")
                data = command[-1].split("&")
                print(data)
                if data[0].find("network") != -1:
                    network = data[0].split("=")[-1]
                if data[1].find("Password") != -1:
                    password = data[1].split("=")[-1]
                if password != "" and network != "":
                    os.system(f"echo {network}:{password} >> ./wifi.dat")
                print("Wificonfig:", network, password)
                network_conf = \
                f"""
[connection]
id=preconfigured
uuid=6bd00b15-baac-4fb7-ab8a-1cf655aaa60a
type=wifi
[wifi]
mode=infrastructure
ssid={network}
hidden=false
[ipv4]
method=auto
[ipv6]
addr-gen-mode=default
method=auto
[proxy]
[wifi-security]
key-mgmt=wpa-psk
psk={password}
                """
                wpa = "country=se\nupdate_config=1\nctrl_interface=/var/run/wpa_supplicant\nnetwork={"
                wpa += f"\n scan_ssid=1\n ssid=\"{network}\"\n psk=\"{password}\""
                wpa += "\n}\n\n"
                os.system(f"echo '{network_conf}'"
                          "| sudo tee /etc/NetworkManager/system-connections/preconfigured.nmconnection"
                          " > /dev/null")
                os.chdir("/home/pi/Airiana/public/")
                self.send_home()
                os.system('echo "<br>Rebooting system due to updated WiFi configuration, please wait...<br>" >> out.txt')
                os.system("sleep 10 && sudo reboot &")

            if "command" in data[0]:
                req = data[0].split(" ")
                command = req[1]
                command = command.split("?")
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.sendto(bytes(command[-1], "utf-8"), ("127.0.0.1", 9876))
                s.close()
                # self.request.send("HTTP/1.1 HTTP/1.1 303 See Other Location: buttons.html \n\r")
                self.send_ok()

            if "utility" in data[0]:
                print(data[0])
                os.chdir("/home/pi/Airiana/")
                if "shutdown" in data[0]:
                    self.send_ok()
                    os.system("sudo shutdown")
                if "reboot" in data[0]:
                    self.send_ok()
                    os.system("sudo reboot &")
                if "update" in data[0]:
                    self.send_ok()
                    os.system("sudo ./update")
                    if os.path.lexists("/dev/ttyAMA0"):
                        os.system("./restart &")
                    else:
                        os.system("sudo systemctl restart airiana.service controller.service &")
                if "restart" in data[0]:
                    self.send_ok()
                    os.system("./restart airiana-core.py controller &")

                if "coffee" in data[0]:
                    self.request.send(bytes(
                        "HTTP/1.1 200 OK\n\n<html><head><meta http-equiv=\"refresh\" content=\"0; url=http://" + str(
                            self.ip) + "/coffee.txt\" /></head></html> \n\r", "utf-8"))
                    return 0
                os.chdir("/home/pi/Airiana/public/")


socketserver.TCPServer.allow_reuse_address = True

while True:
    try:
        srv = socketserver.TCPServer(("0.0.0.0", 8000), MyHandler)
        srv.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        print()
        break
    except KeyboardInterrupt:
        exit()
    except IOError:
        print("error binding to socket")
        traceback.print_exc()
        os.system("sleep 1")

srv.serve_forever()
