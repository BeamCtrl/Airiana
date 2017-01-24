#!/usr/bin/python

import os, time
html = "<html>STATUS VIEW AIRIANA SYSTEMS<br><table><tr><th>Name</th><th>Ping</th><th>Status</th></tr>"
users = {\
	"7c:dd:90:42:61:6f":"Halling", \
	"48:ee:0c:f2:ca:b7":"Broden",\
	"b8:27:eb:57:ef:d9":"Dev.",\
	"b8:27:eb:dc:38:7b":"Malmstrom",\
	"b8:27:eb:1d:ed:11":"Fransson"}

files = os.listdir("./public/local_links/")
#for each in users.keys():
#	print each, ": ",users[each]
while True:
    try:
		for each in files:
			try:
				mod = os.stat(str("./public/local_links/"+each)).st_mtime
				#print users[str(each.split(".")[0])], "latest ping:",time.ctime(mod),round((time.time()-mod)/3600,2), "hrs"
				if (time.time()-mod)/3600 < 1.5: flag = "<font color=\"green\"> Alive </font>"
				else: flag = "<font color=\"red\"> Inactive </font>"
				html += "<tr><td>"+users[str(each.split(".")[0])]+"</td><td>"+time.ctime(mod)+"</td><td>"+flag+str(round((time.time()-mod)/3600,2))+"</td></tr>" 
			except KeyError: print "no hit on:",each
		html +="</table></html>"
		file = open("./public/status.html","w")
		file.write(html)
		file.close()
		time.sleep(60)
    except KeyboardInterrupt: break 
