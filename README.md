# Mooshimeter-Pythonista-IOS
A Python 3.5 application using Bluetooth Low Energy BLE interfacing to the Mooshimeter multimeter on IOS using Pythonista

The application is able to 
 - let user apply settings to the multimeter
 - show meter results on screen
 - read command tree from instrument and show it on the console
and
 - read Voltage, Current, Resistance, Temperature and other measured values 
   from the multimeter and show them (on the console crudely for the moment)
 - show live channel measurements in pyui screen (pythonista graphical user interface for IOS)

Todo
 - graphical user interface (pages : Settings, Results, Graph)
 - picklist for meter options
 - Retrieve log files from the instrument (how?)

There are still some issues (who can help?)
 - there is a BADREAD diagnostics message shown
 - some unknown data items in time_utc node
 - crc32 does not calculate correctly reading cmd_tree

Refered products:

http://omz-software.com/pythonista/

https://moosh.im/mooshimeter/
