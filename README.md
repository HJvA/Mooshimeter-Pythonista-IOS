# Mooshimeter-Pythonista-IOS
A Python application using Bluetooth BLE interfacing with the Mooshimeter multimeter on IOS using Pythonista

The application is able to 
 - set the multimeter ranges and input channels (only fixed settings for the moment) and
 - read Voltage, Current, Resistance, Temperature and other values from the multimeter and show them (on the console crudely for the moment)

There are still some issues (who can help?)
 - values are beeing read on polling basis thus giving the same values repeatedly
 - when a new sample is available the instrument dumps some data to the BLE channel that is not yet understood
 - there is a BADREAD diagnostics message shown

Refered products:

http://omz-software.com/pythonista/

https://moosh.im/mooshimeter/
