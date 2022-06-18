# Airiana
SystemAir control,

Get your Systemair unit under control.
Airiana talks to it via modbus and hooks you up with some extra featrues, most important it's fire and forget. 
she keeps her self in check.


#### featured special effects:

  **Shower detections

  **Pre-emptive cooling with forcasts from met.no

  **Dynamic pressure control to save some €

  **Neat RH adaptations for units with RH sensor

  **Filter % remaining counter 

  **24hr plotter all put on web-page for your convenience

  **Internal AI to map temperature response for acurate home environment control.
  

  does alot more calculation and spits out more data than you'll ever need.
 
 
 
##### HW recomendation: Rpi + RS485 TxRx module, VR400/VR700/VTR300/VSR300 or savecair unit from systemair.



#### Installation:
   ** INSTALLATION IS CURRENTLY BROKEN IN RASPBERRY OS DUE TO DEPRECATION OF python2. **
   ** optional install in branch python3-migration, ""May contain bugs, is a work in progress"" ** 
   
  -Install an Rs485 hat on your pi.

  -Connect A and B to your ventilation units Modbus connector.

  -Set comms on Ventilation unit to 19200baud no pairity 1 stopbit. 

  -Clone this repo.
  -'git checkout python3-migration'

  -Run  "python3 ./install.py"

  -When the forcasting reciever is first run it will create a latlong.json file based on IP geolocation. If you want a more precise location forcast update the latlong.json file with your position.   


#### To enable HomeAssitant integration:

  -edit the ha-token file, add your server port and bearer token.

  -edit /etc/systemd/system/airiana.service, add "homeAss" to commandline option
  
  or
  
  use MQTT to push data to HomeAssistant via the json data file air.out.
  This will require you to install a MQTT-publisher and a broker to handle the data distribution.

#### To run it against an Systemair Internet Access Module, 

  -edit /etc/systemd/system/airiana.service, add "TCP" to commandline option.

  -edit the ipconfig file.
  

# Feature details.

#### Shower Detections:

The Airiana system will continuously monitor the exhaust temperatures and if RH sensor is installed, humities. If it detects a sharp rise in temperature or humidity it will run the fans att maximum speed until the temperature/humidity values have returned to normal. It has a timeout of 45 minutes at witch point it will return to normal automation.


#### Pressure reduction:

The Ariana system will using the installed RH sensor or calculated RH values set a 10% flow differential to create a negative pressure difference indoors. This is done when the algorithm finds a risk of condensation if there is air transport from the indoor climate to the outside. It will if no RH sensor is availible use a margin of +10%RH from which it sets a pressure difference. If there is a RH sensor installed the difference is margin will be +5%RH.


#### Temperature control:

The airiana system will employ a strategy of retaining heat by temperature demand control. It will as a base target try to maintain 22C as indoor target temperature. If the outside temperature is below 13C target temperature increases to 23C.
Low fanspeed will be set at and around the target temperature.
Mid fanpeed will be set at target +0.6C
High fanspeed will be set at target +1.2


#### Humidity control: 

The airiana system will monitor the humidity level in the exhaust air if there is a relative humidity sensor installed on your unit. 
During the course of a 24hr period it will calculate the expected outside vapor content of the air. This value will be used in relation to the measured indoor humidity to increase the fanspeed if there is a difference of more than +500Pa H2O partial pressure. it will also reduce the fanspeed if the partial pressure difference is less than +300Pa H2O


#### Sensor AI:

The system will when activated map the sensor offset of the extracted air at different speeds and temperature ranges. This is accomplished by the system sensing that is is in a steady state of low speed and then changing to high speed and mapping the sensor respons. It will learn how the system reacts in different senarios and compensate accordingly for more exact system regulation.


#### Preemptive cooling:

The system will if the location file is properly updated monitor the current atmospheric conditions thru the MET.no weather service. If it detects that the comming days will have temperatures netting above 17deg average it will go into cooling mode. In this mode only shower detection is active. It will run the fans at maximum speed with a target temperature of 20.7C to cool the building going into a hot day. When during the day the outside temperature surpasses the inside temperature it will lower fanspeed to low to conserve the indoor cold air. It will return to high speed when the outside conditions allows.


#### Exchanger control:

It will change the settings to controll the exchanger with regards to the forcasted weather and or temperature conditions. If it is a cold day with sub 5C, or  inlet temperature < 10C, or extract temperature < target -1C it will be forced to on.
If the forcast says the high temperature for tomorrow will be below 10C it will be set to on.
The exchanger will be forced off if inlet temp > 10C and extract temp is above target temp.
It will be forced off if the suppy temperature is above target.

#### Auto update:

Airana will every 4hrs check if there is a new stable release availible in this git repo. If there is, it will be automatically fetched and the system will restart.

#### Interface:

System control and monitoring is done via a web-page at http://airana.local. from this interface you can toggle the winter/summer mode, set fanspeed low/mid/high, force the high mode on a timer for 2hrs if there is need for forced ventilation. System control is separated from the display so if you like you kan expose the web interface to the Internet without having outsiders change your settings. The sytem will not allow access from an external network unless explicitly directed to do so.

Tips and Tricks: if you want to run fans at low on a timer set forced ventilation and then manually set low speed. the timer inhibits the automation for 2 hrs

#### HomeAssistant:
If configured the ha-token file can contain the ip, port and token of your runnning homeAssistant server. Airiana will then send temperature/humidity and extract fan rpm as http sensors and they śhould pop up in you HomeAssistant.

Example config file for use with json data over MQTT, availible in file airiana_config.yml

### Json data:
There is a json file availible for thrid-party integrations which contain a limited set of data för use as anyone sees fit to do. I use it as a data source for publishing on MQTT for homeassistant to read.
This file is availible at "./RAM/air.out"



### Tools:
 
Restart: "./restart" restarts the airiana core service.

Watch: "./watch" outputs the running parameters to terminal.

Grapher: "./grapher.py #number of days#" will generate a new graph with an arbitrary number of days to be plotted.
use "hasRH" as an added argument if you also want the humidity graph added to the *.png

A runnning log file is availble in ./RAM/err.

Communication error rate if any is availble in ./RAM/error_rate.
