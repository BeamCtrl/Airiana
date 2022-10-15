#!/usr/bin/python
#################################################################
#   	                                 						#
#  Installation script for airiana system            			#
#   							                                #
#   							                                #
#   							                                #
#################################################################
#
#
# INSTALL BY CLONING#
# git clone https://github.com/beamctrl/airiana/
#
#################################################################
import os
import sys
osname = os.popen("./osname.py").read()
def setUart():
    global boot_cmd, lines, reboot
    # Enable UART for RS485 HAT
    boot_cmd = "enable_uart=1\n"
    boot_file = open("/boot/config.txt", "r+")
    lines = boot_file.readlines()
    if boot_cmd in lines:
        print("Uart already enabled")
    else:
        print("Enabling uart")
        boot_file.write(boot_cmd)
        boot_file.close()
        reboot = True
    #sys.stdout.flush()



# INSTALL DEPS #
def install_deps():
    os.system("sudo apt-get update")
    os.system("sudo apt-get -y --force-yes install python3-pip")
    os.system("sudo apt-get -y --force-yes install python3-dev")
    os.system("sudo apt-get -y --force-yes install python3-matplotlib")
    os.system("sudo apt-get -y --force-yes install python3-numpy")
    os.system("pip3 install minimalmodbus --user")
    os.system("pip3 install progressbar --user")
    os.system("pip3 install requests --user")
    os.system("pip3 install pyModbusTCP --user")
    os.system("pip3 install setuptools --user")
    os.system("pip3 install pyephem --user")
    os.system("sudo apt-get -y --force-yes install libatlas-dev")
    os.system("sudo apt-get -y --force-yes install ntp")
    os.system("sudo apt-get -y --force-yes install hostapd")
    os.system("sudo apt-get -y --force-yes install dnsmasq")
    #os.system("sudo apt-get -yq --force-yes -o \"Dpkg::Options::=--force-confdef\"  upgrade")

def disable_auto_connect_services():
    os.system("sudo systemctl unmask hostapd")
    os.system("sudo systemctl disable hostapd")
    os.system("sudo systemctl disable dnsmasq")

def add_dnsmasq_conf():
    conf = "#AutoHotspot Config\n#stop DNSmasq from using resolv.conf\nno-resolv\n#Interface to use\n"
    conf += "interface=wlan0\nbind-interfaces\ndhcp-range=10.0.0.50,10.0.0.150,12h\n"
    with  open("/etc/dnsmasq.conf","r") as dnsmasq:
      if dnsmasq.read().find(conf) == -1:
          os.system("sudo echo \"" + conf + "\" >> /etc/dnsmasq.conf")
      else:
          print("Dnsmasq already has AutoHotspot configured")

def add_dhcpcd_conf():
    conf = "nohook wpa_supplicant\n"
    with  open("/etc/dhcpcd.conf","r") as dhcpcd:
          if dhcpcd.read().find(conf) == -1:
              os.system("sudo echo \"" + conf + "\" >> /etc/dhcpcd.conf")
          else:
              print("dhcpcd already has AutoHotspot configured")

def add_sudoer_conf():
    conf = "username ALL= NOPASSWD: /home/pi/Airiana/systemfiles/autohotspot.sh\n"
    with  open("/etc/dhcpcd.conf","r") as dhcpcd:
          if dhcpcd.read().find(conf) == -1:
              os.system("sudo echo \"" + conf + "\" >> /etc/dhcpcd.conf")
          else:
              print("sudoers already has AutoHotspot configured")
def set_fstab():
    global lines, reboot, user_id, group_id
    # MAKE RAM DRIVE IN FSTAB#
    fstab_comment = "#temp filesystem only in RAM for use on Airiana tempfiles.\n"
    fstab_RAM = "tmpfs " + path + "/RAM tmpfs defaults,noatime,nosuid,uid=" + user_id + ",gid=" + group_id + ",mode=0755,size=50m 0 0\n"
    # MAKE RAM DRIve for linux logs var/logs
    fstab_var = "tmpfs /var/log tmpfs defaults,noatime,nosuid,mode=0755,size=75m 0 0"
    fstab_file = open("/etc/fstab", "r+")
    lines = fstab_file.readlines()
    # Write RAM tmpfs's to fstab
    if fstab_var not in lines or fstab_RAM not in lines:
        for each in lines:
            if "/RAM" in each:
                print("Found RAM drive setup")
                lines.pop(lines.index(each))
            if "/var" in each:
                print("Found /var/log partition setup")
                lines.pop(lines.index(each))
            if "filesystem only in RAM" in each:
                print("Found fstab comment")
                lines.pop(lines.index(each))
        print("Setting up Ram drive")
        lines.append(fstab_comment)
        lines.append(fstab_RAM)
        lines.append(fstab_var)
        fstab_file.seek(0, 0)
        fstab_file.writelines(lines)
        fstab_file.close()
        reboot = True
    else:
        print("fstab  already installed")
    #sys.stdout.flush()


def clean_paths():
    # replace static paths with install path
    os.system("sed -i 's-/home/pi/airiana/-" + path + "/-g' airiana-core.py")
    os.system("sed -i 's-/home/pi/airiana/-" + path + "/-g' public/ip-replace.sh")
    os.system("sed -i 's-/home/pi/airiana/-" + path + "/-g' public/controller.py")
    os.system("sed -i 's-/home/pi/airiana/-" + path + "/-g' forcast2.0.py")
    os.system("sed -i 's-/home/pi/airiana/-" + path + "/-g' humtest.py")
    os.system("sed -i 's-/home/pi/airiana/-" + path + "/-g' updater.py")
    os.system("sed -i 's-/home/pi/airiana/-" + path + "/-g' systemfiles/controller.service")
    os.system("sed -i 's-/home/pi/airiana/-" + path + "/-g' systemfiles/airiana.service")
    os.system("sed -i 's-/home/pi/airiana/-" + path + "/-g' systemfiles/autohotspot.service")
    os.system("sed -i 's-/home/pi/airiana/-" + path + "/-g' public/ip-util.sh")


user_name = os.getlogin()
user_id = os.getuid()
group_id = os.getgid()

if len(sys.argv) < 2:
    print("Installing the AirianaCores")
reboot = False

path = os.getcwd()

if "clean" in sys.argv:
    os.system("sudo systemctl disable controller.service")
    os.system("sudo systemctl disable airiana.service")
    os.system("sudo rm /etc/systemd/system/airiana.service /etc/systemd/system/controller.service")
    sys.exit()

if user_id != 0:
    install_deps()

# Auto hotspot configuration
if user_id != 0 and osname in ("buster", "bullseye"):
    try:
        disable_auto_connect_services()
        add_dnsmasq_conf()
        add_dhcpcd_conf()
        add_sudoer_conf()
        if not os.path.lexists("/etc/systemd/system/autohotspot.service"):
            print("setup autostart for autohotspot.service")
            os.system("sudo cp ./systemfiles/autohotspot.service /etc/systemd/system/")
            os.system("sudo systemctl enable autohotspot.service")
         #update sudoers to allow no password wificonf

    except:
        print("Auto hotspot config had an error")


# NEED TO SET LOCALE
# os.system("cp ./systemfiles/timezone /etc/")

if user_id == 0 and "--set-uart" in sys.argv:
    setUart()
    sys.exit()
else:
    os.popen("sudo python3 ./install.py --set-uart")
# Fix static paths
clean_paths()

# update the fstab file with RAM-drives for /var/log and ~/airiana/RAM
if user_id == 0 and "--set-fstab" in sys.argv:
    user_id = sys.argv[-2]
    group_id = sys.argv[-1]
    set_fstab()
    sys.exit()
else:
    os.popen("sudo python3 ./install.py --set-fstab " + str(user_id) + " " + str(group_id))

# install system services for airaina and controller
if not os.path.lexists("/etc/systemd/system/airiana.service"):
    print("setup autostart for airiana.service")
    os.system("sudo cp ./systemfiles/airiana.service /etc/systemd/system/")
    os.system("sudo systemctl enable airiana.service")

if not os.path.lexists("/etc/systemd/system/controller.service"):
    print("setup autostart for controller.service")
    os.system("sudo cp ./systemfiles/controller.service /etc/systemd/system/")
    os.system("sudo systemctl enable controller.service")
sys.stdout.flush()



# redir console from uart
def redirectConsole(boot_cmd):
    os.system("echo " + boot_cmd + "> /boot/cmdline.txt")

boot_cmd = "dwc_otg.lpm_enable=0 console=tty1 root=/dev/mmcblk0p2 rootfstype=ext4 elevator=deadline fsck.repair=yes rootwait"
if boot_cmd not in open("/boot/cmdline.txt").read():
    reboot = True
    print("Cmdline is invalid")
    if user_id == 0 and "--redirect-console" in sys.argv:
        print("Redirecting console")
        redirectConsole(boot_cmd)
        sys.exit()
    else:
        print("Sudo console redirect")
        os.popen("sudo python3 ./install.py --redirect-console")
# setup airiana as host#
print("Copy hosts file and set hostname")
os.system("sudo cp ./systemfiles/hosts /etc/")
os.system("echo airiana |sudo tee /etc/hostname")

sys.stdout.flush()

# Touch a data log file
print("Touch data.log")
os.system("touch data.log")

# move to public folder for symlink setup
os.chdir("./public/")
sys.stdout.flush()

# link files to RAM-disk
print("setup symlinks between RAM and ./public")
sys.stdout.flush()
os.system("ln -s ../RAM/out out.txt")
os.system("ln -s ../RAM/history.png history.png")
os.system("ln -s ../RAM/air.out air.out")
os.system("ln -s ../RAM/status.html status.html")

# setup updater.py for auto update
print("setup auto update from airiana repo.")
cron = os.popen("crontab -u pi -l").readlines()
if "no crontab for user pi" in cron:
    cron = ""
crontab = ""
updated = False
for line in cron: # this will update an existing airiana conf
    if line.find("updater.py") > 0:
        line = "0 */4 * * * /usr/bin/python " + path + "/updater.py\n"
        updated = True
    if line.find("autohotspot.sh") > 0:
        line += "*/5 * * * * sudo /home/pi/Airiana/systemfiles/autohotspot.sh\n"
        updated = True
    crontab += line
if not updated: # this is for new installations
    crontab += "0 */4 * * * /usr/bin/python " + path + "/updater.py\n"
    crontab += "*/5 * * * * sudo /home/pi/Airiana/systemfiles/autohotspot.sh\n"
os.system("echo \"" + crontab + "\" | crontab -u pi -")
sys.stdout.flush()

# reboot if needed
if "update" not in sys.argv or reboot or "reboot" in sys.argv:
    # Reboot after installation
    print("Installation completed, reboot in 15 sec")
    sys.stdout.flush()
    os.system("sleep 15")
    os.system("sudo reboot")

if "update" in sys.argv:
    os.system("sudo systemctl daemon-reload")
    print("System update successful,restarting services")
    os.system("sudo systemctl restart airiana.service controller.service")
