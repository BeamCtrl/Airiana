#!/usr/bin/python3
import os

tmp = os.popen("cat /etc/os-release")
for line in tmp.readlines():
    if "VERSION_CODENAME" in line:
        osname = line.split("=")[-1][:-1]
print (osname)
