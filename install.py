#!/usr/bin/python
#################################################################
#                                                               #
#  Installation script for airiana system                       #
#                                                               #
#################################################################
import os
import sys
import subprocess
import venv
import time

path = os.getcwd()
user_name = os.getlogin()
user_id = os.getuid()
group_id = os.getgid()

def run_command(command, check=True):
    try:
        result = subprocess.run(command, shell=True, check=check, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.stdout.decode().strip(), result.stderr.decode().strip()
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {command}\nError: {e.stderr.decode().strip()}")
        sys.exit(1)

def setUart():
    print("Checking UART settings...")
    boot_cmd = "enable_uart=1\n"
    with open("/boot/firmware/config.txt", "r+") as boot_file:
        lines = boot_file.readlines()
        if boot_cmd in lines:
            print("UART already enabled")
        else:
            print("Enabling UART")
            boot_file.write(boot_cmd)
            global reboot
            reboot = True

def create_virtual_env(path):
    print("Creating virtual environment...")
    venv_path = os.path.join(path, "venv")
    venv.EnvBuilder(with_pip=True).create(venv_path)
    return venv_path

def install_deps(venv_path):
    print("Installing dependencies in virtual environment...")
    pip_executable = os.path.join(venv_path, "bin", "pip")
    deps = [
        "minimalmodbus", "progressbar", "requests", "pyModbusTCP", 
        "setuptools", "pytest", "pyephem", "numpy"
    ]
    run_command(f"{pip_executable} install --upgrade pip")
    run_command(f"{pip_executable} install " + " ".join(deps))
    apt_executable = os.path.join("/usr", "bin", "apt")
    apt_deps = ["dhcpcd", "hostapd", "dnsmasq",
                "iptables", "libopenblas-dev", "python3-numpy"]
    run_command(f"sudo {apt_executable} update")
    run_command(f"sudo {apt_executable} -y install " + " ".join(apt_deps) )

def disable_auto_connect_services():
    print("Disabling auto-connect services...")
    services = ["hostapd", "dnsmasq"]
    for service in services:
        run_command(f"sudo systemctl unmask {service}")
        run_command(f"sudo systemctl disable {service}")

def copy_hostapd():
    print("Copying the hostapd configuration...")
    if not os.path.lexists("/etc/hostapd/hostapd"):
        run_command("sudo cp ./systemfiles/hostapd /etc/hostapd/hostapd.conf")

def add_dnsmasq_conf():
    print("Adding dnsmasq configuration...")
    conf = (
        "#AutoHotspot Config\n"
        "#stop DNSmasq from using resolv.conf\n"
        "no-resolv\n"
        "#Interface to use\n"
        "interface=wlan0\n"
        "bind-interfaces\n"
        "dhcp-range=10.0.0.50,10.0.0.150,12h\n"
        "# Redirect all DNS queries to a specific IP address (e.g., 10.0.0.1)\n"
        "address=/#/10.0.0.1\n"
	"address=/airiana.local/10.0.0.1\n"
    )
    with open("/etc/dnsmasq.conf", "r") as dnsmasq:
        if conf not in dnsmasq.read():
            run_command(f'sudo echo "{conf}" | sudo tee -a /etc/dnsmasq.conf')

def add_dhcpcd_conf():
    print("Adding dhcpcd configuration...")
    conf = "nohook wpa_supplicant\n"
    if not os.path.isfile("/etc/dhcp.conf"):
        run_command('sudo touch /etc/dhcpcd.conf')
        run_command('sudo chmod 666 /etc/dhcpcd.conf')
    with open("/etc/dhcpcd.conf", "r+") as dhcpcd:
        dhcpcd_conf = dhcpcd.read()
        if dhcpcd_conf.find("#persistent\n") == -1:
             if "persistent\n" in dhcpcd_conf:
                 dhcpcd_conf = dhcpcd_conf.replace("persistent", "#persistent")
                 run_command(f'echo "{dhcpcd_conf}" |sudo tee /etc/dhcpcd.conf > /dev/null')
        if conf not in dhcpcd_conf:
            run_command(f'sudo echo "{conf}" >> /etc/dhcpcd.conf')

def add_sudoer_conf():
    print("Adding sudoers configuration...")
    conf = "pi ALL= NOPASSWD: /home/pi/Airiana/systemfiles/autohotspot.sh\n"
    with os.popen("sudo cat /etc/sudoers") as sudoers:
        if conf not in sudoers.read():
            run_command(f'sudo echo "{conf}" | sudo tee -a /etc/sudoers')

def set_fstab():
    global user_id, group_id
    print("Setting up RAM drive in fstab...")
    fstab_comment = "#temp filesystem only in RAM for use on Airiana tempfiles.\n"
    fstab_RAM = f"tmpfs {path}/RAM tmpfs defaults,noatime,nosuid,uid={user_id},gid={group_id},mode=0755,size=50m 0 0\n"
    fstab_var = "tmpfs /var/log tmpfs defaults,noatime,nosuid,mode=0755,size=75m 0 0"

    with open("/etc/fstab", "r+") as fstab_file:
        lines = fstab_file.readlines()
        if fstab_var not in lines or fstab_RAM not in lines:
            lines = [line for line in lines if "/RAM" not in line and "/var" not in line and "filesystem only in RAM" not in line]
            lines.extend([fstab_comment, fstab_RAM, fstab_var])
            fstab_file.seek(0)
            fstab_file.writelines(lines)
            global reboot
            reboot = True
        else:
            print("fstab already installed")

def clean_paths():
    print("Cleaning paths in configuration files...")
    files_to_clean = [
        "airiana-core.py", "public/ip-replace.sh", "public/controller.py",
        "forcast2.0.py", "humtest.py", "updater.py", "systemfiles/controller.service",
        "systemfiles/airiana.service", "systemfiles/autohotspot.service", "public/ip-util.sh"
    ]
    for file in files_to_clean:
        run_command(f"sed -i 's-/home/pi/airiana/-{path}/-g' {file}")

def redirect_console(boot_cmd):
    print("Redirecting console output...")
    run_command(f"echo {boot_cmd} > /boot/cmdline.txt")

def setup_services():
    print("Setting up services for autostart...")
    services = ["airiana.service", "controller.service"]
    for service in services:
        if not os.path.lexists(f"/etc/systemd/system/{service}"):
            run_command(f"sudo cp ./systemfiles/{service} /etc/systemd/system/")
            run_command(f"sudo systemctl enable {service}")

def setup_crontab(option):
    print("Setting up crontab entries...")
    cron = subprocess.run(["crontab", "-u", "pi", "-l"], capture_output=True, text=True).stdout
    if "no crontab for user pi" in cron:
        cron = ""
    crontab = ""
    updater_updated = False
    hotspot_updated = False

    for line in cron.splitlines():
        if "updater.py" in line:
            line = f"0 */4 * * * /usr/bin/python {path}/updater.py\n"
            updater_updated = True
        if "autohotspot.sh" in line:
            line = f"*/5 * * * * sudo /home/pi/Airiana/systemfiles/autohotspot.sh\n"
            hotspot_updated = True
        crontab += line + "\n"
    if not updater_updated\
      and option == "crontab":
        crontab += f"0 */4 * * * /usr/bin/python {path}/updater.py\n"
    if not hotspot_updated \
      and osname in ("buster", "bullseye", "bookworm")\
      and option == "hotspot":
        crontab += f"*/5 * * * * sudo /home/pi/Airiana/systemfiles/autohotspot.sh\n"
    run_command(f"echo \"{crontab.strip()}\" | crontab -u pi -")

def setup_autohotspot():
    try:
        run_command("sudo apt install -y hostapd dnsmasq")
        disable_auto_connect_services()
        copy_hostapd()
        add_dnsmasq_conf()
        add_dhcpcd_conf()
        add_sudoer_conf()
        if not os.path.lexists("/etc/systemd/system/autohotspot.service"):
            run_command("sudo cp ./systemfiles/autohotspot.service /etc/systemd/system/")
            run_command("sudo systemctl enable autohotspot.service")
    except (IndexError) as e:
        print(e)
        print("Auto hotspot config had an error")

def main():
    global path, user_id, group_id, reboot, osname
    reboot = False
    path = os.getcwd()
    print(f'Running in: {path}\n')
    osname, _ = run_command("./osname.py")

    if "clean" in sys.argv:
        print("Cleaning up installed services...")
        run_command("sudo systemctl disable controller.service")
        run_command("sudo systemctl disable airiana.service")
        run_command("sudo rm /etc/systemd/system/airiana.service /etc/systemd/system/controller.service")
        sys.exit()

    if len(sys.argv) < 2:
        print("Installing the AirianaCores")

    # setup virtual environment
    try:
        venv_path = create_virtual_env(path)
        install_deps(venv_path)
    except OSError:
        print("Virtual environment is already running, stop or manually remove if you want to reinstall.")
        print("cmd:'./stop airiana-core.py' or  'rm -r venv'")
        exit(-1)
    # clean up the exec paths to match current installation
    clean_paths()

    # setup auto start services
    setup_services()

    # add auto updater
    if (not headless and input("\nDo you want to setup, automatic updates? [y/n] ").strip().lower() == "y"):
        setup_crontab("updater")

    # setup wifi hotsput, only if bookworm
    if user_id != 0 and osname in ("bookworm") and not headless:
        if (input("\nDo you want to setup, automatic WiFi access point, if network is lost? [y/n]").strip().lower() == "y"):
            setup_autohotspot()
            setup_crontab("hotspot")

def execute_sudo_parts():
    global boot_cmd
    print("Executing sections requiring sudo...")
    set_fstab()
    setUart()
    add_dhcpcd_conf()
    with open("/boot/cmdline.txt", "r") as cmdline:
        if boot_cmd not in cmdline.read():
            print("Updating cmdline.txt")
            reboot = True
            redirect_console(boot_cmd)
        else:
            print("cmdline.txt has full command")


if __name__ == "__main__":
    reboot = False
    headless = False
    if "headless" in sys.argv:
        headless = True
    if "user" in sys.argv:
        user_id = sys.argv[sys.argv.index("user") + 1]
    if "group" in sys.argv:
        group_id = sys.argv[sys.argv.index("group") + 1]
    if "sudo-parts" in sys.argv:
        boot_cmd = "dwc_otg.lpm_enable=0 console=tty1 root=/dev/mmcblk0p2 rootfstype=ext4 elevator=deadline fsck.repair=yes rootwait"
        execute_sudo_parts()
        if reboot:
            print("Your system must be rebooted to apply all settings!")
            print("Reboot will occur in 5 seconds... ctrl-c to abort now")
            time.sleep(5)
            run_command("sudo reboot")

    else:
        main()
        print("will execute some parts as root for access...")
        os.system(f'sudo python3 install.py sudo-parts user {user_id} group {group_id}')
