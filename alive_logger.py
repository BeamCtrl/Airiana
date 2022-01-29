#!/usr/bin/python3

import socket
import select
import time
import os
import pathlib

path = pathlib.Path(__file__).parent.resolve()
os.chdir(path)
print ("started in", os.getcwd())
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
html = """ 
<html>
<meta http-equiv="refresh" content="0;url=http://[IP]">
[DA]

</html>
"""

sock.bind(("0.0.0.0", 59999))
while True:
    if sock in select.select([sock], [], [], 1)[0]:
        incomming_msg, addr = sock.recvfrom(37000)
        incomming_msg = incomming_msg.decode("utf-8")

        if incomming_msg.find("ether") > 0:
            ip = incomming_msg[61:75]
            mac = incomming_msg[14:31]
        else:
            mac = incomming_msg[38:55]
            ip = incomming_msg[58:72]
        print(time.ctime(), "MAC:", mac, "From:", addr)
        # print "active IP:",ip
        for_file = html.replace("[IP]", ip)
        for_file = html.replace("[DA]", incomming_msg)
        filename = "./public/local_links/" + mac + ".html"
        for_file += "\n" + "Source:" + str(addr)
        for_file.replace("\n", "<br>##")
        try:
            if len(mac) != 0:
                open(filename, "+").write(for_file)
        except IOError:
            print("file missing", filename)
