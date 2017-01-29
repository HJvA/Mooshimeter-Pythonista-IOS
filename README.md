# Mooshimeter-Pythonista-IOS
A Python 3.5 application using Bluetooth Low Energy BLE interfacing to the Mooshimeter multimeter on IOS using Pythonista

The application is able to 
 - let user edit and apply settings to the multimeter
   Including: channel functions and ranges
 - show meter results on ui screen
   Including Voltage, Current, Resistance, Temperature and other measured values
 - read command tree from instrument and show it on the console
 - provide debug communication data in a log file

Usage
 - fetch this github repository files in Pythonista 3
 - have Bluetooth enabled on IOS
 - have Mooshimeter ready 
 - run file uiMeter.py
 - to see diagnostic messages see the log file and the console

Todo
 - graphical user interface 
 - Retrieve log files from the instrument
 - show depth buffer in a graph

There are still some issues (some not too serious)
 - there is a BADREAD diagnostics message shown
 - some unknown data items in time_utc node when trigger continuous
 - depth buffer is dumped to time_utc node when analysis=2 but format not yet understood
 - BUF_LSB2NATIVE is 0.0 when analysis has not been set to 2 before
 - BUF_BPS has value 8 but should have value 24
 - CHn:BUF node does not return enough samples according to depth setting
 - internal temperature is not very accurate (can it be calibrated?)

Refered products:

http://omz-software.com/pythonista/

https://moosh.im/mooshimeter/
