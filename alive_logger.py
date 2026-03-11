#!/usr/bin/python3

import socket
import select
import time
import os
import pathlib
import time


path = pathlib.Path(__file__).parent.resolve()
os.chdir(path)
print("started in", os.getcwd())
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
html = """
<html>
[DA]
</html>
"""

sock.bind(("0.0.0.0", 59999))
while True:
    if sock in select.select( [sock], [], [], 1)[0]:
            incoming_msg, addr=sock.recvfrom(37000)
            incoming_msg = incoming_msg.decode("utf-8")
            #print ("***", incoming_msg, "***")
            #print (incoming_msg.find("ether"))
            if incoming_msg.find("ether") > 0:
                ip = incoming_msg[61:75]
                mac = incoming_msg[14:31]
            else:
                mac = incoming_msg[38:55]
                ip = incoming_msg[58:72]
            print (time.ctime(), "MAC:", mac, "From:",addr)
            # print "active IP:",ip
            for_file = html.replace("[IP]",str(ip))
            for_file += html.replace("[DA]", str(incoming_msg))
            # for_file += "\n"+incomming_msg
            filename = "./public/local_links/"+mac+".html"
            for_file += "\n"+"Source:"+str(addr)
            # print "filename:",filename
            # print for_file
            for_file.replace("\n", "<br>##")
            try:
                if len(mac) != 0:
                    open(filename, "w+").write(for_file)
            except IOError:
                print ("file missing", filename)
