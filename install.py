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
if "clean" in sys.argv:
    os.system("systemctl disable controller.service")
    os.system("systemctl disable airiana.service")
    os.system("rm /etc/systemd/airiana.service /etc/systemd/system/controller.service")

# INSTALL DEPS#
os.system("apt-get -y install python-pip")
os.system("apt-get -y install python-dev")
os.system("apt-get -y install python3-dev")
os.system("apt-get -y install python-matplotlib")
os.system("pip install minimalmodbus")
os.system("pip install progressbar")
os.system("pip install requests")
os.system("pip install pyModbusTCP")
os.system("pip install setuptools")
os.system("pip install pyephem")
os.system("apt-get -y install ntp")
os.system("apt-get -y upgrade")
# NEED TO SET LOCALE
os.system("cp ./systemfiles/timezone /etc/")

#Enable UART for RS485 HAT
boot_cmd="enable_uart=1\n"
boot_file = open("/boot/config.txt","rw+")
lines=boot_file.readlines()
if boot_cmd in lines:
	print "Uart already enabled" 
else:
	print "Enabling uart"
	boot_file.write(boot_cmd)
	boot_file.close()
	reboot = True
sys.stdout.flush()

#replace static paths with install path
os.system("sed -i 's-/home/pi/airiana/-"+dir+"/-g' airiana-core.py")
os.system("sed -i 's-/home/pi/airiana/-"+dir+"/-g' public/ip-replace.sh")
os.system("sed -i 's-/home/pi/airiana/-"+dir+"/-g' public/controler.py")
os.system("sed -i 's-/home/pi/airiana/-"+dir+"/-g' forcast2.0.py")
os.system("sed -i 's-/home/pi/airiana/-"+dir+"/-g' humtest.py")
os.system("sed -i 's-/home/pi/airiana/-"+dir+"/-g' updater.py")
os.system("sed -i 's-/home/pi/airiana/-"+dir+"/-g' systemfiles/controller.service")
os.system("sed -i 's-/home/pi/airiana/-"+dir+"/-g' systemfiles/airiana.service")
os.system("sed -i 's-/home/pi/airiana/-"+dir+"/-g' public/ip-util.sh")

#MAKE RAM DRIVE IN FSTAB#
fstab_comment = "#temp filesystem only in RAM for use on Airiana tempfiles.\n"
fstab_RAM = "tmpfs "+dir+"/RAM tmpfs defaults,noatime,nosuid,mode=0755,size=50m 0 0\n"
# MAKE RAM DRIve for linux logs var/logs
fstab_var = "tmpfs /var/log tmpfs defaults,noatime,nosuid,mode=0755,size=75m 0 0"
fstab_file = open("/etc/fstab","rw+")
lines=fstab_file.readlines()
## write RAM tmpfs's to fstab
if fstab_var not in lines or fstab_RAM not in lines:
	 for each in lines:
		if "/RAM" in each: 
			print "Found RAM drive setup"
			lines.pop(lines.index(each))
		if "/var" in each:
			print "Found /var/log partition setup"
			lines.pop(lines.index(each))
		if "filesystem only in RAM" in each:
			print "Found fstab comment"
			lines.pop(lines.index(each))
	 print "Setting up Ram drive"
	 lines.append(fstab_comment)
	 lines.append(fstab_RAM)
	 lines.append(fstab_var)
	 fstab_file.seek(0,0)
	 fstab_file.writelines(lines)
	 fstab_file.close()
	 reboot = True
else:
	 print "fstab  already installed" 
sys.stdout.flush()

#install system services for airaina and controller
if not os.path.lexists("/etc/systemd/system/airiana.service"):
	print "setup autostart for airiana.service"
	os.system("cp ./systemfiles/airiana.service /etc/systemd/system/")
	os.system("systemctl enable airiana.service")

if not os.path.lexists("/etc/systemd/system/controller.service"):
	print "setup autostart for controller.service"
	os.system("cp ./systemfiles/controller.service /etc/systemd/system/")
	os.system("systemctl enable controller.service")
sys.stdout.flush()

# redir console from uart
boot_cmd= "dwc_otg.lpm_enable=0 console=tty1 root=/dev/mmcblk0p2 rootfstype=ext4 elevator=deadline fsck.repair=yes rootwait"
if boot_cmd not in open("/boot/cmdline.txt").read():
	print "adding boot cmdline config"
	os.system("echo " +boot_cmd+"> /boot/cmdline.txt" )
	reboot = True
##
## setup airiana as host#
print "Copy hosts file"
os.system ("cp ./systemfiles/hosts /etc/")
sys.stdout.flush()

#Touch a data log file
print "Touch data.log"
os.system ("touch data.log")
os.chdir("./public/")
sys.stdout.flush()

# link files to RAM-disk
print "setup symlinkts between RAM and ./public"
sys.stdout.flush()
os.system("ln -s ../RAM/out out.txt")
os.system("ln -s ../RAM/history.png history.png")
os.system("ln -s ../RAM/air.out air.out")
os.system("ln -s ../RAM/status.html status.html")
os.system("echo airiana > /etc/hostname")
os.system("chown pi:pi ../RAM/")
os.system("chown pi:pi ../RAM/*")

# setup updater.py for auto update
print "setup auto update from airiana repo."
cron =  os.popen("crontab -u pi -l").readlines()
crontab = ""
updated = False
for line in cron:
	if  line.find("updater.py") >0 :
		line = "0 */4 * * * sudo /usr/bin/python "+dir+"/updater.py\n"
		updated = True
	crontab += line
if not updated:
	crontab +=  "0 */4 * * * sudo /usr/bin/python "+dir+"/updater.py\n"
os.system("echo \"" + crontab +"\" | crontab -u pi -")
sys.stdout.flush()

#reboot if needed
if not "update" in sys.argv or reboot or "reboot" in sys.argv:
	#Reboot after installation
	print "Installation completed, reboot in 15 sec"
	sys.stdout.flush()
	os.system("sleep 15")
	os.system("reboot")

if "update" in sys.argv:
	print "System update sucessfull"
