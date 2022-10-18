#! /usr/bin/python3

import socketserver
import socket
import os
import traceback

hostname = os.popen("hostname").read()[:-1]


class MyHandler(socketserver.BaseRequestHandler):
    def send_ok(self):
        self.request.send(bytes(
            "HTTP/1.1 200 OK\n\n<html><head><meta http-equiv=\"refresh\" content=\"0; url=http://"
            + self.ip + "/\" /></head></html> \n\r", "utf-8"))
    def handle(self):
        self.ip = os.popen("hostname -I").readline().split(" ")[0]
        data = str(self.request.recv(1024), "utf-8").strip().split("\r\n")
        print(data[0])
        if "GET" in data[0]:
            if "command" in data[0]:
                req = data[0].split(" ")
                command = req[1]
                command = command.split("?")
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.sendto(bytes(command[-1],"utf-8"), ("127.0.0.1", 9876))
                s.close()
                self.send_ok()
        if "POST" in data[0]:
            if "setup" in data[0]:
                req = data[0].split(" ")
                command = req[1]
                command = command.split("?")
                password = data[1]
            if "command" in data[0]:
                req = data[0].split(" ")
                command = req[1]
                command = command.split("?")
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.sendto(bytes(command[-1],"utf-8"), ("127.0.0.1", 9876))
                s.close()
                # self.request.send("HTTP/1.1 HTTP/1.1 303 See Other Location: buttons.html \n\r")
                self.send_ok()
            if "utility" in data[0]:
                print(data[0])
                os.chdir("/home/pi/airiana/")
                if "shutdown" in data[0]:
                    self.send_ok()
                    os.system("sudo shutdown")
                if "reboot" in data[0]:
                    self.send_ok()
                    os.system(" sudo reboot &")
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
                            ip) + "/coffee.txt\" /></head></html> \n\r", "utf-8"))
                    return 0
                os.chdir("/home/pi/airiana/public/")


socketserver.TCPServer.allow_reuse_address = True

while True:
    try:
        srv = socketserver.TCPServer(("0.0.0.0", 8000), MyHandler)
        srv.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        break
    except KeyboardInterrupt:
        exit()
    except IOError:
        print("error binding to socket")
        traceback.print_exc()
        os.system("sleep 1")

srv.serve_forever()
