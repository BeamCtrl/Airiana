#!/usr/bin/python

import os, time
import mail
mailer = mail.Smtp()
if  not os.path.lexists("/home/pi/airiana/RAM/status.html"):
	os.system("touch /home/pi/airiana/RAM/status.html" )
def init():
	from users import users
	global users
	global status
	global mail_sent
	status = {}
	mail_sent = {}

	for each in users.keys():
		status[each]= 0

	for each in users.keys():
		mail_sent[each] = False
init()
os.chdir("/home/pi/airiana")
os.system("./alive_logger.py &")
files = os.listdir("./public/local_links/")

#for each in users.keys():
#	print each, ": ",users[each]
while True:
    try:
		users_prev = users
		from users import users
		if len(users_prev) <> len(users):
			init()
		html = """<html>STATUS VIEW AIRIANA SYSTEMS<br>
			<meta http-equiv="refresh" content="5">
			<table><tr>
			<th>Name</th>
			<th>Ping</th>
			<th>Status</th>
			<th>Shr</th>
			<th>Ex</th>
			<th>tm</th>
			<th>Unit</th>
			<th>Vr</th>
			<th>hash</th>
			<th>uTm</th>
			<th>In</th>
			<th>Out</th>
			<th>flw</th>
			<th>RH</th>
			<th>Auto ON</th>
			<th>Cooling active</th>
			<th>Supply</th>
			<th>Exhaust</th>
			<th>P.diff</th>
			<th>detLimit</th>
			</tr>"""
		flag = "unknown"
		files = os.listdir("./public/local_links/")
		for each in files:
			try:
				mod = os.stat(str("./public/local_links/"+each)).st_mtime
				content = os.popen("cat ./public/local_links/"+each).read()
				content = content.replace("nan", " -1 ")
				stat_field = content.split("status:")[-1]
				try:
					#print stat_field
					if content.find("status")!=-1 :exec  ("lis ="+stat_field.split("\n")[0])
					else: lis =[]
				except:
					lis=["data error"]
				#print status[str(each.split(".")[0])], each
				if (time.time()-mod)/3600>status[str(each.split(".")[0])]:
					status[str(each.split(".")[0])] = round((time.time()-mod)/3600,2)
				status[str(each.split(".")[0])] =status[str(each.split(".")[0])]*0.99
				if (time.time()-mod)/3600<3:
					flag = "<font color=\"green\"> Alive </font>"
					if  mail_sent[each.split(".")[0]]:
                                                mail_sent[each.split(".")[0]] = False
                                                mailer.setup ("daniel.halling@outlook.com","airiana@abiding.se","Airiana user: "+str(users[str(each.split(".")[0])])+" has checked in and is now alive.")
                                                mailer.send()
				else: 
					flag = "<font color=\"red\"> Inactive </font>"
					if not mail_sent[each.split(".")[0]]:
						mail_sent[each.split(".")[0]] = True
						mailer.setup ("daniel.halling@outlook.com","airiana@outlook.com","Airiana user: "+str(users[str(each.split(".")[0])])+" has changed status to inactive.")
						mailer.send()
				status_table= ""
				for item in lis:
					status_table += str(item) +"</td><td>"
				html += "<tr><td><a href=\"/local_links/"\
					+each+"\">"+users[str(each.split(".")[0])]\
					+"</a></td><td>"+time.ctime(mod)+"</td><td>"+flag\
					+" "+str(round(status[str(each.split(".")[0])],2))+"</td><td> "\
					+status_table+" </td></tr>\n"
			except KeyError:
 				html += "<tr><td><a href=\"/local_links/"+each+"\">"+each+"</a></td><td>"+time.ctime(mod)+"</td><td>"+flag+" </td></tr>\n" 

		html +="<br></table></html>"
		file = open("/home/pi/airiana/RAM/status.html","w+")
		file.write(html)
		file.close()
		time.sleep(10)
    except KeyboardInterrupt: break 


