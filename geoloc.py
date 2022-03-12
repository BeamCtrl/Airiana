#!/usr/bin/python3

import os, sys

ip = sys.argv[-1]

# Test for valid ip and if not supplied use external.
if ip.count(".") != 3:
    ip = eval(os.popen("curl \'https://api.ipify.org?format=json\'").read())
    ip = ip["ip"]

# try to read a location
location = os.popen("curl http://www.geoplugin.net/json.gp?ip=" + ip)
try:
    loc = eval(location.read())
    print(loc["geoplugin_city"], ",", loc["geoplugin_countryName"])
    if "debug" in sys.argv:
        print(loc)
    # test for location file and create if not availible
    if not os.path.lexists("./latlong.json"):
        pos = "{\"lat\":" + loc["geoplugin_latitude"] + ",\"long\":" + loc["geoplugin_longitude"] + "}"
        # print pos
        with open("latlong.json", "w") as f:
            f.write(pos)
except NameError:
    # Try another api if the first test fails
    try:
        location = os.popen(" curl http://ip-api.com/json/" + ip).read()
        loc = eval(location)
        print(loc["city"], ",", loc["country"])
        if "debug" in sys.argv:
            print(loc)
        # test for location file and create if not availible
        if not os.path.lexists("./latlong.json"):
            pos = "{\"lat\":\"" + str(loc["lat"]) + "\",\"long\":\"" + str(loc["lon"]) + "\"}"
            # print pos
            with open("latlong.json", "w") as f:
                f.write(pos)
    except IOError:
        print("unknown")
        if "debug" in sys.argv:
            print(loc)
