#!/usr/bin/python
import os, time
import mail
import sys
mailer = mail.Smtp()
if not os.path.lexists("/home/pi/airiana/RAM/status.html"):
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
os.system("./alive_logger.py > /dev/null &")
files = os.listdir("./public/local_links/")
data = dict(enumerate(["token","exchanger","exectime","name","version","hash","uptime","inlet","extract","extractflow","rh","auto","cooling","supply","exhaust","pdiff","detlimit"]))
data = {value : key for (key, value) in data.items()}

#print data
#for each in users.keys():
#	print each, ": ",users[each]
stat_dict = {}
location= dict()
def checkLocation(user):
	try:
		#print location
		if len(location[user]) <>0:
			#print "user known",user, location[user]
			return None
	except KeyError:
		with open("./public/local_links/"+user+".html") as log:
			ip = log.read().split("Source:('")[-1].split("\'")[0]
		#print "checking ip:",ip
		loc = os.popen("/home/pi/airiana/geoloc.py " + ip ).read()
		location.update( {user:loc})
		#print "got new location", loc
def analyse_stat(status,user):
	#if "debug" in sys.argv:
	#	print "Analyze", status, users[user]
	# Store Warnings in the stat_dict as {"user-MAC":{"alarmType":INT}}
	# check if winter mode is on and exhaust is higher than supply
	if len(status) > 1:
		#print status[data["exchanger"]],status[data["exhaust"]], status[data["supply"] ]
		if int(status[data["exchanger"]])==5 and float(status[data["exhaust"]])>float(status[data["supply"]]) and float(status[data["intlet"]])< 10:
			#print users[user], "Exchanger problem\n"
			try:
				stat_dict[user]={"ExchangerProblem":True}
			except: pass #print "there is en error in dictsetting"
			#print stat_dict[user]
		# TODO: check exhaust is higher than extract while inlet is lower than extract

starttime = time.time()
while True:
    try:
		users_prev = users
		from users import users
		if len(users_prev) <> len(users):
			init()
		html = """<html>STATUS VIEW AIRIANA SYSTEMS<br>
			<meta http-equiv="refresh" content="5" charset="UTF-8">
			<table style="width: 100%;"><tr>
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
		html2 = ""
		for each in files:
			try:
				mod = os.stat(str("./public/local_links/"+each)).st_mtime
				content = os.popen("cat ./public/local_links/"+each).readlines()
				stat_field = ""
				for line in content:
					if "status:" in line:
						stat_field = line
						break
				content = stat_field.replace("nan", " -1 ")
				#print content
				user =str(each.split(".")[0])
				checkLocation(user)
				#try: print "userID",user,"location:", location[user]
				#except:
				#	print "\n"
				lis=[]
				try:
					if content.find("status")!=-1 :
						exec ("lis ="+stat_field.split(":")[-1])
						#print lis
					else: lis =["no data"]
				except:
					lis=["data error"]
				# CHECK IF USER REGISTERED #
				if user in users.keys():
					#print "Checking status of user ", users[user],"\n"
					if int(time.time()-starttime)%1 == 0:
						try:
							analyse_stat(lis,user)
						except IOError: print "analysis error"
					#print status[str(each.split(".")[0])], each
					if (time.time()-mod)/3600>status[user]:
						status[user] = round((time.time()-mod)/3600,2)
					status[user] =status[user]*0.99
					if (time.time()-mod)/3600<3:
						flag = "<font color=\"green\"> Alive </font>"
						if  mail_sent[user] == True:
	                                                mail_sent[user] = False
	                                                mailer.setup ("daniel.halling@outlook.com","airiana@outlook.com","Airiana user: "+str(users[user])+" has checked in and is now alive.")
	                                                mailer.send()
					else:
						flag = "<font color=\"red\"> Inactive </font>"
						if not mail_sent[user]:
							mail_sent[user] = True
							mailer.setup ("daniel.halling@outlook.com","airiana@outlook.com","Airiana user: "+str(users[user])+" has changed status to inactive.")
							mailer.send()
					status_table= ""
					for item in lis:
						status_table += str(item) +"</td><td>"
					if (time.time()-mod)/3600<3:
						html += "<tr><td><a href=\"/local_links/"\
							+each+"\">"+users[user]\
							+"</a></td><td>"+time.strftime("%d/%m %H:%M:%S",time.localtime(mod))+"</td><td>"+flag\
							+"</td><td> "\
							+status_table
					else:
						html += "<tr style=\"font-style:italic\" ><td><a href=\"/local_links/"\
							+each+"\">"+users[user]\
							+"</a></td><td>"+time.strftime("%d/%m %H:%M:%S",time.localtime(mod))+"</td><td>"+flag\
							+"</td><td> "\
							+status_table

					try:
						html += " " +str(stat_dict[user])
					except KeyError: pass #print "No error state"
					try:
						html += " </td><td>"+location[user]+"</td></tr>\n"
					except:
						html += "</td></tr>\n"

				else:
					if (time.time()-mod)/3600<3:
						flag = "<font color=\"green\"> Alive </font>"
					else:
						flag = "<font color=\"red\"> Inactive </font>"

					status_table= ""
					for item in lis:
						status_table += str(item) +"</td><td>"
					html2 += "<tr><td><a href=\"/local_links/"\
						+each+"\">"+user\
						+"</a></td><td>"+time.strftime("%d/%m %H:%M:%S",time.localtime(mod))+"</td><td>"+flag\
						+"</td><td> "\
						+status_table
					try:
						html2 += " </td><td>"+location[user]+"</td></tr>\n"
					except:
						html2 += "</td></tr>\n"

					if (time.time()-mod)/3600 > 24:
						os.system("rm -f ./public/local_links/"+each)
			except KeyError:
				print "Trying to look up unknown user error"
				pass

		html +="<br></table><br>"
		html += """	<table style="width: 100%">
			<caption style="text-align:left"><strong>Not registered users:</strong></caption>
			<tr>
			<th style="text-align:left">Name</th>
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

		html += html2
		html +="<br></table></html>"

		file = open("/home/pi/airiana/RAM/status.html","w+")
		file.write(html)
		file.close()
		time.sleep(10)
    except KeyboardInterrupt: break 

