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
[DA]
</html>
"""

sock.bind(("0.0.0.0", 59999))
while True:
        print(int(time.time()%60))
        if int(time.time()) % 120 == 0:
            print ("unpacking")
            os.system("curl -s -X GET \"https://filebin.net/archive/airiana_ping_status_store/zip\" --output ./RAM/filebin.zip")
            os.system("unzip -o RAM/filebin.zip -d public/local_links/ 2> RAM/unzip.out")
        os.system("rm RAM/filebin.zip")
        os.system("rm RAM/unzip.out")
        if sock in select.select( [sock], [], [], 1)[0]:
            incomming_msg, addr=sock.recvfrom(37000)
            #print "***", incomming_msg, "***"
	 	    #print incomming_msg.find("ether")

        if incomming_msg.find("ether") > 0:
            #print "ether"
            ip = incomming_msg[61:75]
            mac =incomming_msg[14:31]
        else:
            #print "hwadddr"
            mac =incomming_msg[38:55]
            ip = incomming_msg[58:72]
        print (time.ctime(), "MAC:", mac, "From:",addr)
        #print "active IP:",ip
        for_file= html.replace("[IP]",ip)
        for_file= html.replace("[DA]",incomming_msg)
        #for_file += "\n"+incomming_msg
        filename = "./public/local_links/"+mac+".html"
        for_file += "\n"+"Source:"+str(addr)
        #print "filename:",filename
        #print for_file
        #location = os.popen("/home/pi/airiana/geoloc.py "+addr[0]).read()
        #for_file += "\nlocation:"+ location+"\n"
        for_file.replace("\n","<br>##")
        try:
            if len(mac)!=0:
                open(filename,"w+").write(for_file)
        except IOError:
            print ("file missing",filename)
