# Mooshimeter-Pythonista-IOS
A Python 3.5 application using Bluetooth Low Energy BLE interfacing to the Mooshimeter multimeter on IOS using Pythonista

The application is able to 
 - let user edit and apply settings to the multimeter
   Including: channel functions and ranges
 - show meter results on ui screen
   Including Voltage, Current, Resistance, Temperature and other measured values
 - read command tree from instrument and show it on the console or in a log file

Usage
 - fetch this github repository files in Pythonista 3
 - have Bluetooth enabled on IOS
 - have Mooshimeter ready
 - run file uiMeter.py

Todo
 - graphical user interface with graphs 
 - Retrieve log files from the instrument (how?)

There are still some issues (but not too serious)
 - there is a BADREAD diagnostics message shown
 - some unknown data items in time_utc node
 - crc32 does not calculate correctly reading cmd_tree

Refered products:

http://omz-software.com/pythonista/

https://moosh.im/mooshimeter/
