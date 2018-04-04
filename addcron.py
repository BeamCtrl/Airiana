#!/usr/bin/python
import os
tmp  =os.popen("crontab -l").read()
os.system("echo \"" + tmp+ "0 */4 * * * sudo /usr/bin/python /home/pi/airiana/updater.py\" |crontab -u pi -")

