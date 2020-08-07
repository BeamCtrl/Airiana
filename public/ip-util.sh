#!/bin/bash
HOST_IP_ADDRESS=$(hostname -I | cut -f1 -d' ')
YRLOCATION_xml=$(cat ../location)
YRLOCATION=${YRLOCATION_xml//forecast.xml}
cd /home/pi/airiana/public/
sed -r "s/(\b[0-9]{1,3}\.){3}[0-9]{1,3}\b"/$HOST_IP_ADDRESS/ util.html.template > util.html.new
#sed -r "s/\"YRlocation\"\b"/$YRLOCATION/ ajax.template > ajax.html.new
rm -f util.html
mv util.html.new util.html
rm -f util.html
mv util.html.new util.html
