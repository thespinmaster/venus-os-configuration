#!/bin/bash
#
# Start script for dbus-nu-shunt
#   First parameter: tty device to use
#
# Keep this script running with daemon tools. If it exits because the
# connection crashes, or whatever, daemon tools will start a new one.
#
# Arguments
# -d -debug  : debug logging
# -s -serial : serial port such as ttyACM0

. /opt/victronenergy/serial-starter/run-service.sh

app=/opt/victronenergy/dbus-ne-shunt/main.py
args="/dev/$tty"

start -d -s $args
