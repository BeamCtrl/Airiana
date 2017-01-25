#!/usr/bin/python

import os, time
users = {\
	"7c:dd:90:42:61:6f":"Halling", \
	"48:ee:0c:f2:ca:b7":"Broden",\
	"b8:27:eb:57:ef:d9":"Dev.",\
	"b8:27:eb:dc:38:7b":"Malmstrom",\
	"b8:27:eb:1d:ed:11":"Fransson"}
status = {}
for each in users.keys():
	status[each]= 0
files = os.listdir("./public/local_links/")
#for each in users.keys():
#	print each, ": ",users[each]
while True:
    try:
		html = "<html>STATUS VIEW AIRIANA SYSTEMS<br><table><tr><th>Name</th><th>Ping</th><th>Status</th></tr>"

		for each in files:
			try:
				mod = os.stat(str("./public/local_links/"+each)).st_mtime
				#print status[str(each.split(".")[0])], each
				if (time.time()-mod)/3600>status[str(each.split(".")[0])]:
					status[str(each.split(".")[0])] = round((time.time()-mod)/3600,2)
				status[str(each.split(".")[0])] =status[str(each.split(".")[0])]*0.99
				if (time.time()-mod)/3600<2:
					flag = "<font color=\"green\"> Alive </font>"
				else: flag = "<font color=\"red\"> Inactive </font>"
				html += "<tr><td>"+users[str(each.split(".")[0])]+"</td><td>"+time.ctime(mod)+"</td><td>"+flag+" "+str(status[str(each.split(".")[0])])+" </td></tr>\n" 
			except KeyError: print "no hit on:",each
		html +="<br></table></html>"
		file = open("./public/status.html","w")
		file.write(html)		
		file.close()
		time.sleep(60)
    except KeyboardInterrupt: break 
