# Airiana
SystemAir control,

Get your Systemair unit under control
Airiana talks to it via modbus and hooks you up with some extra featrues, most important it's fire and forget. 
she keeps her self in check.

featured special effects:
  Shower detections
  Pre-emptive cooling with forcasts from YR.no
  Dynamic pressure control to save some €
  Neat RH adaptations for units with RH sensor
  Filter % remaining counter 
  24hr plotter all put on web-page for your convenience
  Internal AI to map temperature response for acurate home environment control.
  does alot more calculation and spits out more data than you'll ever need.
  
HW: Rpi + RS485 TxRx module, VR400/VR700/VTR300/VSR300 or savecair unit from systemair.


Installation:
Install an Rs485 hat on your pi.
Connect A and B to your ventilation units Modbus connector.
Set comms to 19200baud no pairity. 
Clone this repo.
Run  "sudo ./install.py"
Update the location file with your current position for YR.no  
