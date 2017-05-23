#!/usr/bin/python
import smtplib,sys
from  email.mime.text import MIMEText
arg = sys.argv

server = "mail2.bahnhof.se"

class Smtp(object):
	def setup(self,to,fr,message):
		self.content = message
		self.to = to
		self.fr = fr
		self.mail = MIMEText (self.content)
		self.mail["Subject"]="Self generated mail"
		self.mail["From"]=self.fr
		self.mail["To"]=self.to
	def send (self):
		print "sending mail to:",self.to, "doing it from", self.fr
                print self.content
		socket = smtplib.SMTP_SSL(server)
		socket.login("mb299291", "Klinten1")
		socket.sendmail(self.fr,self.to,self.mail.as_string())
		socket.quit()
if __name__ == "__main__":
	mail = Smtp()
	if len(arg) >2 :
		to = arg[1]
		fr=arg[2]
		content=arg[3]
		mail.setup(to,fr,content)
		mail.send()

