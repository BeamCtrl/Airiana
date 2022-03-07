#!/usr/bin/python3
import os
import sys

path = os.path.abspath(__file__).replace(__file__, "")
os.chdir(path)
deb_versions = ("wheezy", "jessie", "stretch", "buster")

for system in enumerate(deb_versions):
    os_name = os.popen("./osname.py").readline()[:-1]
    if os_name in system:
        print("current", system[1])
        print("future", deb_versions[system[0]+1])
        print("Updating to", deb_versions[system[0]+1])
        print("./systemfiles/upgrade.sh " + system[1] + " " + deb_versions[system[0] + 1])
        os.system("./systemfiles/upgrade.sh " + system[1] + " " + deb_versions[system[0]+1] + " && sudo reboot")


os.system("git fetch && git checkout -m origin/master ./public/current_version")
ver = os.popen("cat ./public/current_version").read()
ver = ver.split(" ")
tmp = os.popen("head -30 airiana-core.py").readlines()
for each in tmp:
    if "vers" in each:
        temp = each.split("=")
        vers = temp[-1][2:-2]

if "debug" in sys.argv:
    print(vers, "->", ver, "will update", vers not in ver[0])
if vers not in ver[0] and "Valid" in ver[1]:
    print("Updating Airiana system software to", ver[0])
    if "debug" not in sys.argv or len(sys.argv) > 1:
        os.system("./update&")
