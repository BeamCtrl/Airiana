#!/usr/bin/python2.7
import os, sys
#os.chdir("/home/pi/airiana/")
deb_versions = ("wheezy", "jessie", "stretch", "buster", "bullseye",
                "bookworm", "trixie", "focal")

os_name = os.popen("./osname.py").readline()[:-1]
for system in enumerate(deb_versions):
    if os_name in system and deb_versions.index(os_name) < len(deb_versions)-1:
        print("current", system[1])
        print("future", deb_versions[system[0]+1])
        print("updating to future")
        os.system("./systemfiles/upgrade.sh " + system[1] + " " + deb_versions[system[0]+1])
    elif os_name == deb_versions[-1]:
        print("os codename checked [" + os_name + "], we're good.")
        break

os.system("git fetch && git checkout -m origin/master ./public/current_version" )
ver = os.popen("cat ./public/current_version").read()
ver = ver.split(" ")
tmp = os.popen("head -30 airiana-core.py").readlines()
for each in tmp:
	if "vers" in each:
		temp = each.split("=")
		vers = temp[-1][2:-2]

if "debug" in sys.argv:
	print vers, "->", ver, "will update", vers not in ver[0]
if vers not in ver[0] and "Valid" in ver[1]:
	print "Updating Airiana system software to",ver[0]
        if "debug" not in sys.argv:
		os.system("./update&")  

