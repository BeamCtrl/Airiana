#!/usr/bin/python3
import sys
import os
import time
import json
import datetime
import traceback
import math

import pathlib

path = pathlib.Path(__file__).parent.resolve()
os.chdir(path)


def get_sun(lat, long):
    import ephem

    o = ephem.Observer()
    o.lat = str(lat)
    o.long = str(long)
    s = ephem.Sun()
    s.compute()
    try:
        return ephem.localtime(o.next_rising(s)), ephem.localtime(o.next_setting(s))
    except (ephem.NeverUpError, ephem.AlwaysUpError):
        up = datetime.time(minute=0, hour=6)
        down = datetime.time(minute=0, hour=19)
        return up, down


def print_weather(tm, weather, rain):
    print(
        tm,
        str(weather["air_temperature"]) + "C",
        str(weather["wind_speed"]) + "m/s",
        "at",
        str(weather["wind_from_direction"]) + "deg.",
        str(rain) + "mm",
        str(weather["relative_humidity"]) + "%",
        "Press.:" + str(weather["air_pressure_at_sea_level"]) + "hPa",
    )


# weather types
MAX_CLOUD_LVL = 8

weather_types = {
    1: "Clear skies",
    2: "Fair weather",
    3: "Partly cloudy",
    4: "Cloudy",
    40: "Light showers",
    41: "Heavy showers",
    5: "Rain",
    24: "Light rain and thunder",
    6: "Rain and thunder",
    25: "Heavy rain and thunder",
    42: "light sleet showers",
    7: "Sleet showers",
    43: "Heavy sleet showers",
    26: "Light sleet showers and thunder",
    20: "sleet showers and thunder",
    27: "Heavy sleet showers and thunder",
    44: "Light snowfall",
    8: "Snow",
    45: "Heavy snow showers",
    28: "Light snow and thunder",
    29: "Heavy snow and thunder",
    21: "Snow showers and thunder",
    46: "Light rain",
    9: "Rain",
    10: "Heavy rain",
    30: "Light rain and thunder",
    22: "Rain and thunder",
    11: "Heavy rain and thunder",
    47: "Light sleet",
    12: "Sleet",
    48: "Heavy Sleet",
    31: "Light sleet and thunder",
    23: "Sleet and thunder",
    32: "Heavy sleet and thunder",
    49: "Light snow",
    13: "Snow",
    50: "Heavy snow",
    33: "Light snow and thunder",
    14: "Snow and thunder",
    34: "Heavy snow and thunder",
    15: "Fog",
    0: "No weather data",
}
weather_types = {value: key for (key, value) in list(weather_types.items())}
## tomorrow date
tomorrow_list = []
tomorrow = datetime.date.today() + datetime.timedelta(days=1)
tomorrow = tomorrow.timetuple()
###
## get longlat from file
try:
    f = open("latlong.json")
    latlong = json.load(f)
except:
    print(traceback.print_exc())
    os.system("./geoloc.py")
    print("-1 -1")
    exit(-1)
# print sunrise and sunset for current location
if "sun" in sys.argv:
    rise, setting = get_sun(latlong["lat"], latlong["long"])
    print(
        str(rise.hour).zfill(2)
        + ":"
        + str(rise.minute).zfill(2)
        + ":"
        + str(rise.second).zfill(2)
        + "\n"
        + str(setting.hour).zfill(2)
        + ":"
        + str(setting.minute).zfill(2)
        + ":"
        + str(setting.second).zfill(2)
    )
    exit(0)

# save forecast to file in RAM
if not os.path.lexists("RAM/forecast.json"):
    os.system("touch RAM/forecast.json")
if (
    os.stat("RAM/forecast.json").st_ctime - time.time() < -3600
    or os.stat("RAM/forecast.json").st_size == 0
    or "-f" in sys.argv
):
    # print "updateing forecast", os.stat("RAM/forecast.json").st_ctime - time.time()
    loc = (
        '"https://api.met.no/weatherapi/locationforecast/2.0/complete?lat='
        + str(latlong["lat"])
        + "&lon="
        + str(latlong["long"])
        + '"'
    )
    os.system(
        'wget -q -T 5 -U "Airiana-forecast-agent github.com/beamctrl/Airiana/" -O ./RAM/forecast.json '
        + loc
    )
# get long lat alt from forecast
with open("RAM/forecast.json") as source:
    try:
        data = json.load(source)
    except:
        print("-1,-1")
        exit()
[int, lat, alt] = data["geometry"]["coordinates"]
# print position altitude
if "altitude" in sys.argv:
    print(alt)
# print current weather
if "now" in sys.argv:
    for each in data["properties"]["timeseries"]:
        curr = time.strptime(each["time"], "%Y-%m-%dT%H:%M:%SZ")
        if (
            curr.tm_mday == time.localtime().tm_mday
            and time.localtime().tm_hour == curr.tm_hour
        ):
            print_weather(
                each["time"],
                each["data"]["instant"]["details"],
                each["data"]["next_1_hours"]["details"]["precipitation_amount"],
            )
if "wind/fog" in sys.argv:
    for each in data["properties"]["timeseries"]:
        curr = time.strptime(each["time"], "%Y-%m-%dT%H:%M:%SZ")
        if (
            curr.tm_mday == time.localtime().tm_mday
            and time.localtime().tm_hour == curr.tm_hour
        ):
            print(
                each["time"],
                each["data"]["instant"]["details"]["wind_speed"],
                each["data"]["instant"]["details"]["fog_area_fraction"],
            )

# print current sealvl pressure
if "pressure" in sys.argv:
    for each in data["properties"]["timeseries"]:
        curr = time.strptime(each["time"], "%Y-%m-%dT%H:%M:%SZ")
        if (
            curr.tm_mday == time.localtime().tm_mday
            and time.localtime().tm_hour == curr.tm_hour
        ):
            print(
                (
                    data["properties"]["timeseries"][0]["data"]["instant"]["details"][
                        "air_pressure_at_sea_level"
                    ]
                )
            )
        # print tomorrows mid day weather
if "tomorrow" in sys.argv:
    for each in data["properties"]["timeseries"]:
        curr = time.strptime(each["time"], "%Y-%m-%dT%H:%M:%SZ")
        if curr.tm_mday == tomorrow.tm_mday and curr.tm_hour == 13:
            wind = float(each["data"]["instant"]["details"]["wind_speed"])
            wt = float(each["data"]["instant"]["details"]["cloud_area_fraction"]) / 100
            temp = float(each["data"]["instant"]["details"]["air_temperature"])
            humid = float(each["data"]["instant"]["details"]["relative_humidity"])
    print(temp, math.ceil(wt * MAX_CLOUD_LVL), wind)
    print(humid)

# print lowest temp tomorrow
if "tomorrows-low" in sys.argv:
    low = -60
    wind = 0
    for each in data["properties"]["timeseries"]:
        curr = time.strptime(each["time"], "%Y-%m-%dT%H:%M:%SZ")
        if curr.tm_mday == tomorrow.tm_mday:
            tomorrow_list.append(each)
            temp = float(each["data"]["instant"]["details"]["air_temperature"])
            if low > temp or low == -60:
                low = temp
                wind = float(each["data"]["instant"]["details"]["wind_speed"])
                rh = float(each["data"]["instant"]["details"]["relative_humidity"])
                wt = (
                    float(each["data"]["instant"]["details"]["cloud_area_fraction"])
                    / 100
                )
    print(low, math.ceil(wt * MAX_CLOUD_LVL), wind, rh)

if "integral" in sys.argv:
    try:
        center = float(sys.argv[-1])
    except:
        print("usage forcast2.0.py integral [center temperature]")
        exit()
    sum = 0
    limit = time.mktime(time.localtime()) + 3600 * 24 * 2  # add two days
    for each in data["properties"]["timeseries"]:
        curr = time.mktime(time.strptime(each["time"], "%Y-%m-%dT%H:%M:%SZ"))
        if curr > time.time() and curr < limit:
            sum += float(each["data"]["instant"]["details"]["air_temperature"]) - center
    print(sum / len(data))

if len(sys.argv) < 2 or "all" in sys.argv:
    try:
        for each in data["properties"]["timeseries"]:
            try:
                print_weather(
                    each["time"],
                    each["data"]["instant"]["details"],
                    each["data"]["next_1_hours"]["details"]["precipitation_amount"],
                )
            except KeyError:
                print_weather(each["time"], each["data"]["instant"]["details"], 0)
    except:
        pass
