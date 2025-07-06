.PHONY : ./source/virtual-gps ./source/dbus-relay-board ./dbus-ne-shunt  ./feed/package all


none:
	@echo "building none... specify the ipk folder to build"

all: virtual-gps dbus-relay-board package
	@echo "building all targets"

virtual-gps:
	@echo "building virtual-gps"
	cd ./feed && opkg-build ../source/virtual-gps ./

dbus-ne-shunt:
	@echo "building dbus-ne-shunt"
	cd ./feed && opkg-build ../source/dbus-ne-shunt ./

dbus-relay-board:
	@echo "building dbus-relay-board"
	cd ./feed && opkg-build ../source/dbus-relay-board ./

package:
	@echo "building package index"
	opkg-make-index ./ -p ./feed/Packages

