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
import pwd

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
    sys.stdout.flush()
    exit(0)


# INSTALL DEPS #
def install_deps():
    os.system("apt-get update")
    os.system("sudo apt-get -y install python3-pip")
    os.system("sudo apt-get -y install python3-dev")
    os.system("sudo apt-get -y install python3-matplotlib")
    os.system("pip3 install minimalmodbus")
    os.system("pip3 install progressbar")
    os.system("pip3 install requests")
    os.system("pip3 install pyModbusTCP")
    os.system("pip3 install setuptools")
    os.system("pip3 install pyephem")
    os.system("pip3 install numpy")
    os.system("sudo apt-get -y install ntp")
    os.system("sudo apt-get -yq --force-yes -o \"Dpkg::Options::=--force-confdef\"  upgrade")


def setFstab():
    global lines, reboot, user_id, group_id
    # MAKE RAM DRIVE IN FSTAB#
    fstab_comment = "#temp filesystem only in RAM for use on Airiana tempfiles.\n"
    fstab_RAM = "tmpfs " + path + "/RAM tmpfs defaults, noatime, nosuid, uid=" + user_id + ", gid=" + group_id + ", mode=0755, size=50m 0 0\n"
    # MAKE RAM DRIve for linux logs var/logs
    fstab_var = "tmpfs /var/log tmpfs defaults, noatime, nosuid, mode=0755, size=75m 0 0"
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
    sys.stdout.flush()
    exit(0)


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
    os.system("sed -i 's-/home/pi/airiana/-" + path + "/-g' public/ip-util.sh")


user_name = os.getlogin()
user_id = os.getuid()
group_id = os.getgid()

print("Installing the AirianaCores")
reboot = False

path = os.getcwd()

if "clean" in sys.argv:
    os.system("sudo systemctl disable controller.service")
    os.system("sudo systemctl disable airiana.service")
    os.system("sudo rm /etc/systemd/airiana.service /etc/systemd/system/controller.service")
    exit(0)

if len(sys.argv) == 1:
    install_deps()

# NEED TO SET LOCALE
# os.system("cp ./systemfiles/timezone /etc/")

if user_id == 0 and "--set-uart" in sys.argv:
    setUart()
else:
    os.popen("sudo python3 ./install.py --set-uart")
# Fix static paths
clean_paths()

# update the fstab file with RAM-drives for /var/log and ~/airiana/RAM
if user_id == 0 and "--set-fstab" in sys.argv():
    user_id = sys.argv[-2]
    group_id = sys.argv[-1]
    setFstab()
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


boot_cmd = "dwc_otg.lpm_enable=0 console=tty1 root=/dev/mmcblk0p2 rootfstype=ext4 elevator=deadline fsck.repair=yes rootwait"
# redir console from uart
def redirectConsole(boot_cmd):
    print("adding boot cmdline config")
    os.system("echo " + boot_cmd + "> /boot/cmdline.txt")


if boot_cmd not in open("/boot/cmdline.txt").read():
    if user_id == 0 and "--redirect-console" in sys.argv:
        redirectConsole(boot_cmd)
        reboot = True

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
print("setup symlinkts between RAM and ./public")
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
for line in cron:
    if line.find("updater.py") > 0:
        line = "0 */4 * * * sudo /usr/bin/python " + path + "/updater.py\n"
        updated = True
    crontab += line
if not updated:
    crontab += "0 */4 * * * sudo /usr/bin/python " + path + "/updater.py\n"
os.system("echo \"" + crontab + "\" | crontab -u pi -")
sys.stdout.flush()

# reboot if needed
if "update" not in sys.argv or reboot or "reboot" in sys.argv:
    # Reboot after installation
    print("Installation completed, reboot in 15 sec")
    sys.stdout.flush()
    os.system("sleep 15")
    os.system("reboot")

if "update" in sys.argv:
    print("System update sucessfull")
