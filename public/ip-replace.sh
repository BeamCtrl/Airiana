#!/bin/bash
HOST_IP_ADDRESS=$(hostname -I | cut -f1 -d' ')
cd public
sed -r "s/(\b[0-9]{1,3}\.){3}[0-9]{1,3}\b"/$HOST_IP_ADDRESS/ buttons.html.template > buttons.html.new
rm -f buttons.html
mv buttons.html.new buttons.html

