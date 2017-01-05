# Mooshimeter-Pythonista-IOS
A Python 3.5 application using Bluetooth Low Energy BLE interfacing to the Mooshimeter multimeter on IOS using Pythonista

The application is able to 
 - read command tree from instrument and show it on the console
 - set the multimeter ranges and input channels (only fixed settings for the moment) and
 - read Voltage, Current, Resistance, Temperature and other measured values 
   from the multimeter and show them (on the console crudely for the moment)

Todo
 - graphical user interface 
 - picklist for meter options

There are still some issues (who can help?)
 - there is a BADREAD diagnostics message shown
 - logging logs too much info to console
 - some unknown data items in time_utc node

Refered products:

http://omz-software.com/pythonista/

https://moosh.im/mooshimeter/
