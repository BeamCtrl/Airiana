#!/usr/bin/python
#################################################################
#								#
#	Installation script for airiana system			#
#								#
#								#
#								#
#################################################################
#
#
# INSTALL BY CLONING#
# git clone https://github.com/beamctrl/airiana/
#
#################################################################
import os, sys
print "Installing the AirianaCores"
reboot = False
os.system("apt-get update")
dir = os.getcwd()

# INSTALL DEPS#
os.system("apt-get -y install python-matplotlib")
os.system("pip install  minimalmodbus")
os.system("pip install  progressbar")
os.system("pip install requests")
os.system("pip install pyModbusTCP")
os.system("pip install pyephem")
os.system("apt-get -y install ntp")

# NEED TO SET LOCALE
os.system("cp ./systemfiles/timezone /etc/")

#Enable UART for RS485 HAT
boot_cmd="enable_uart=1\n"
boot_file = open("/boot/config.txt","rw+")
lines=boot_file.readlines()
if boot_cmd in lines:
	print "uart_enabled" 
else:
	print "Enabling uart"
	boot_file.write(boot_cmd)
	boot_file.close()
	reboot = True

#MAKE RAM DRIVE IN FSTAB#
fstab_comment = "#temp filesystem only in RAM for use on Airiana tempfiles.\n"
fstab_cmd = "tmpfs "+dir+"/RAM tmpfs defaults,noatime,nosuid,mode=0755,size=50m 0 0\n"
# MAKE RAM DRIve for linux logs var/logs
fstab_cmd += "tmpfs /home/pi/airiana/RAM tmpfs defaults,noatime,nosuid,mode=0755,uid=pi,gid=pi,size=50m 0 0"
fstab_file = open("/etc/fstab","rw+")
lines=fstab_file.readlines()
## write RAM tmpfs's to fstab
if fstab_comment in lines: print "fstab installed" 
else:
	for each in lines:
		if "/RAM/" in each: lines.pop(lines.index(each))
		if "/var/" in each: lines.pop(lines.index(each))
		if "filesystem only in RAM" in each: lines.pop(lines.index(each))
	print "Setting up Ram drive"
	lines.append(fstab_comment)
	lines.append(fstab_cmd)
	fstab_file.seek(0,0)
	fstab_file.writelines(lines)
	fstab_file.close()
	reboot = True

#install system services for airaina and controller
if not os.path.lexists("/etc/systemd/system/airiana.service") or "update" in sys.argv:
	os.system("cp ./systemfiles/airiana.service /etc/systemd/system/")
if not os.path.lexists("/etc/systemd/system/controller.service") or "update" in sys.argv:
	os.system("cp ./systemfiles/controller.service /etc/systemd/system/")

os.system("systemctl enable airiana.service")
os.system("systemctl enable controller.service")

# redir console from uart
boot_cmd= "dwc_otg.lpm_enable=0 console=tty1 root=/dev/mmcblk0p2 rootfstype=ext4 elevator=deadline fsck.repair=yes rootwait"
if boot_cmd not in open("/boot/cmdline.txt").read():
	print "adding boot cmdline config"
	os.system("echo " +boot_cmd+"> /boot/cmdline.txt" )
	reboot = True
##
## setup airiana as host#
os.system ("cp ./systemfiles/hosts /etc/")

#Touch a data log file
os.system ("touch data.log")
os.chdir("./public/")

# link files to RAM-disk
os.system("ln -s ../RAM/out out.txt")
os.system("ln -s ../RAM/history.png history.png")
os.system("ln -s ../RAM/status.html status.html")
os.system("echo airiana > /etc/hostname")
os.system("chown pi:pi ../RAM/")
os.system("chown pi:pi ../RAM/*")

# setup updater.py for auto update
if  "/updater.py" not in os.popen("crontab -u pi -l").read():
	tmp  =os.popen("crontab -u pi -l").read()
	os.system("echo \"" + tmp+ "0 */4 * * * sudo /usr/bin/python "+dir+"/updater.py\"|crontab -u pi -")

#reboot if needed
if not "update" in sys.argv or reboot:
	#Reboot after installation
	print "Installation completed, reboot in 15 sec"
	os.system("sleep 15")
	os.system("reboot")
