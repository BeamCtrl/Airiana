os.system("wget -q -O ./RAM/VERS http://lappy.asuscomm.com:443/current_$
ver = os.popen("cat ./RAM/VERS").read()
ver = ver.split(" ")

if "debug" in sys.argv:
	print vers, "->", ver
if vers not in ver[0] and "Valid" in ver[1]:
	print "Updating Airiana system software to",ver[0]
        os.system("./update&")  

