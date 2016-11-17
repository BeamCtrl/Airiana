#!/usr/bin/python
#################################################################
#								#
#	Installation script for airiana system			#
#								#
#								#
#								#
#################################################################



import os, sys
print "Upgrading Raspbian OS"
os.system("rpi-update")
os.system("apt-get update")
os.system("apt-get install python-matplotlib")
fstab_comment = "#temp filesystem only in RAM for use on Airiana tempfiles.\n"
fstab_cmd = "tmpfs /home/pi/airiana/RAM tmpfs defaults,noatime,nosuid,mode=0755,size=50m 0 0\n"

#os.system("mkdir airiana")
#os.chdir("./airiana")
os.system("mkdir RAM public systemfiles")
os.system("chmod 766 RAM public systemfiles")
#os.system("wget -O update http://lappy.asuscomm.com:443/update")
#os.system("chmod 755 update")
#os.system("./update")
os.system("git clone https://github.com/beamctrl/airiana/")
os.system("pip install minimalmodbus")
os.system("apt-get install ntp")
# NEED TO SET LOCALE


boot_cmd="enable_uart=1\n"
boot_file = open("/boot/config.txt","rw+")
lines=boot_file.readlines()
if boot_cmd in lines: print "uart_enabled" 
else: 
	print "Enabling uart"
	boot_file.write(boot_cmd)
	boot_file.close()

fstab_file = open("/etc/fstab","rw+")
lines=fstab_file.readlines()
if fstab_cmd in lines: print "fstab installed" 
else:
	 print "Setting up Ram drive"
	 fstab_file.write(fstab_comment)
	 fstab_file.write(fstab_cmd)
	 fstab_file.close()

os.system("cp ./systemfiles/airiana.service /etc/systemd/system/")
os.system("cp ./systemfiles/controller.service /etc/systemd/system/")

os.system("systemctl enable airiana.service")
os.system("systemctl enable controller.service")

boot_cmd= "dwc_otg.lpm_enable=0 console=tty1 root=/dev/mmcblk0p2 rootfstype=ext4 elevator=deadline fsck.repair=yes rootwait"

os.system("echo " +boot_cmd+"> /boot/cmdline.txt" )

os.system ("cp ./systemfiles/hosts /etc/")

os.chdir("./public/")
os.system("ln -s ../RAM/out out.txt")
os.system("ln -s ../RAM/history.png history.png")
os.system("echo airiana > /etc/hostname")
print "Installation completed, reboot in 15 sec"
os.system("sleep 15")
os.system("reboot")
