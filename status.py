#!/usr/bin/python3
import os
import sys
import time
import mail
import traceback
mailer = mail.Smtp()


path = os.path.abspath(__file__).replace("status.py", "")
os.chdir(path)
if not os.path.lexists("./RAM/status.html"):
	os.system("touch ./RAM/status.html" )
def init():
	from users import users
	global users
	global status
	global mail_sent
	status = {}
	mail_sent = {}
	for each in list(users.keys()):
		print (users[each], each)
		users[each.replace(":","_")] = users[each]

	for each in list(users.keys()):
		status[each]= 0

	for each in list(users.keys()):
		mail_sent[each] = False
init()

os.chdir("/home/pi/airiana")
os.system("./alive_logger.py > /dev/null &")
files = os.listdir("./public/local_links/")
data = dict(enumerate(["token","exchanger","exectime","name","version","hash","uptime","inlet","extract","extractflow","rh","auto","cooling","supply","exhaust","pdiff","detlimit","Location"]))
data = {value : key for (key, value) in list(data.items())}

print(data)
#for each in users.keys():
#	print each, ": ",users[each]
stat_dict = {}
location= dict()
def checkLocation(user):
	try:
		#print location
		if len(location[user]) !=0:
			#print "user known",user, location[user]
			return None
	except KeyError:
		with open("./public/local_links/"+user+".html") as log:
			ip = log.read().split("Source:('")[-1].split("\'")[0]
		#print "checking ip:",ip
		loc = os.popen("./geoloc.py " + ip ).read()
		location.update( {user:loc})
		#print "got new location", loc
def analyse_stat(status,user):
	# if "debug" in sys.argv:
	# print "Analyze", status, users[user]
	# Store Warnings in the stat_dict as {"user-MAC":{"alarmType":INT}}
	# check if winter mode is on and exhaust is higher than supply
	if len(status) > 1:
		#print status[data["exchanger"]],status[data["exhaust"]], status[data["supply"] ]
		if int(status[data["exchanger"]])==5 and float(status[data["exhaust"]])>float(status[data["supply"]]) and float(status[data["inlet"]])< 10:
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
		if len(users_prev) != len(users):
			init()
		headers = """<html>STATUS VIEW AIRIANA SYSTEMS<br>
			<meta http-equiv="refresh" content="5" charset="UTF-8">
			<table style="width: 100%;"><tr>
			<th style="text-align:left;">Name&emsp;&emsp;&emsp;&emsp;&emsp;</th>
			<th style="text-align:left">Ping</th>
			<th style="text-align:left">Status</th>
			<th style="text-align:left">  </th>
			<th style="text-align:left">Shr</th>
			<th style="text-align:left">Ex</th>
			<th style="text-align:left">tm</th>
			<th style="text-align:left">Unit</th>
			<th style="text-align:left">Vr</th>
			<th style="text-align:left">hash</th>
			<th style="text-align:left">uTm</th>
			<th style="text-align:left">In</th>
			<th style="text-align:left">Out</th>
			<th style="text-align:left">flw</th>
			<th style="text-align:left">RH</th>
			<th style="text-align:left">Auto ON</th>
			<th style="text-align:left">Cooling active</th>
			<th style="text-align:left">Supply</th>
			<th style="text-align:left">Exhaust</th>
			<th style="text-align:left">P.diff</th>
			<th style="text-align:left">DetLimit</th>
			<th style="text-align:left">Active error</th>
			<th style="text-align:left">Location</th>
			</tr>"""
		html = "" + headers
		flag = "unknown"
		files = os.listdir("./public/local_links/")
		html2 = ""
		for each in files:
			try:
				mod = os.stat(str("./public/local_links/"+each)).st_mtime
				data_file = open("./public/local_links/"+each, "r")
				content = data_file.readlines()
				stat_field = ""
				for line in content:
					if "status:" in line:
						stat_field = line
						break
				content = stat_field.replace("nan", " -1 ")
				#print content
				user = str(each.split(".")[0])
				#checkLocation(user)
				#try: print "userID",user,"location:", location[user]
				#except:
				#	print "\n"
				lis=[]
				try:
					if content.find("status")!=-1 :
						exec ("lis ="+stat_field.split(":")[-1])
					else:
						lis =["no data"]
				except:
					lis=["-1","-1","-1","-1","-1","-1","-1","-1","-1","-1","-1","-1","-1","-1","-1","-1","data error"]
					try:
						st = content.split("###")
						exec ("lis =" + st[1].replace("status:", ""))
					except:
						lis = ["data error"]
				# CHECK IF USER REGISTERED #
				if user in list(users.keys()):
					#print "Checking status of user ", users[user],"\n"
					if int(time.time()-starttime)%1 == 0:
						try:
							analyse_stat(lis,user)
						except IOError: print("analysis error")
					#print status[str(each.split(".")[0])], each
					if (time.time()-mod)/3600 > status[user]:
						status[user] = round((time.time() - mod) / 3600, 2)
					status[user] = status[user] * 0.99
					if (time.time()-mod)/3600<3:
						flag = "<font color=\"green\">Alive  </font>"
						if  mail_sent[user] == True:
													mail_sent[user] = False
													mailer.setup ("daniel.halling@outlook.com","airiana@outlook.com","Airiana user: "+str(users[user])+" has checked in and is now alive.")
													mailer.send()
					else:
						flag = "<font color=\"red\">Inactive</font>"
						if not mail_sent[user] and not "no-mail" in sys.argv:
							mail_sent[user] = True
							mailer.setup ("daniel.halling@outlook.com","airiana@outlook.com","Airiana user: "+str(users[user])+" has changed status to inactive.")
							#mailer.send()
					status_table= ""
					for item in lis:
						status_table += str(item) +"</td><td nowrap>"
					if (time.time()-mod)/3600<3:
						html += "<tr><td nowrap><a href=\"/local_links/"\
							+each+"\">"+users[user]\
							+"</a></td><td nowrap>"+time.strftime("%d/%m %H:%M:%S",time.localtime(mod))+"</td><td nowrap>"+flag\
							+"</td><td nowrap>"\
							+status_table
					else:
						html += "<tr style=\"font-style:italic\"><td nowrap><a href=\"/local_links/"\
							+each+"\">"+users[user]\
							+"</a></td><td nowrap>"+time.strftime("%d/%m %H:%M:%S",time.localtime(mod))+"</td><td nowrap>"+flag\
							+"</td><td nowrap>"\
							+status_table

					try:
						html += " " +str(stat_dict[user])
					except KeyError: pass #print "No error state"
					try:
						html += " </td><td nowrap>"+location[user]+"</td></tr>\n"
					except:
						html += "</td></tr>\n"

				else:
					if (time.time()-mod)/3600<3:
						flag = "<font color=\"green\">Alive  </font>"
					else:
						flag = "<font color=\"red\">Inactive</font>"

					status_table = "<td nowrap>"
					for item in lis:
						status_table += str(item) +"</td><td nowrap>"
					html2 += "<tr><td><a href=\"/local_links/"\
						+each+"\">"+user\
						+"</a></td><td nowrap>"+time.strftime("%d/%m %H:%M:%S", time.localtime(mod))+"</td><td nowrap>"+flag\
						+"</td><td nowrap>"\
						+status_table
					if len(lis) == 1:
						html2 += 16 * "<td nowrap></td>"
					try:
						html2 += "</td><td nowrap>"+location[user]+"</td></tr>\n"
					except:
						html2 += "</td></tr>\n"

					if (time.time()-mod)/3600 > 24:
						os.system("rm -f ./public/local_links/"+each)
			except KeyError:
				print("Trying to look up unknown user error", user)
				traceback.print_exc()
				pass

		html +="<br></table><br>"
		html += headers

		html += html2
		html +="<br></table></html>"

		file = open("./RAM/status.html", "w+")
		file.write(html)
		file.close()
		time.sleep(10)
	except KeyboardInterrupt: break

