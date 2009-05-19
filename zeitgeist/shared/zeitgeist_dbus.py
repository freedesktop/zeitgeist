# -.- encoding: utf-8 -.-

import sys
import dbus
import dbus.mainloop.glib
import gettext

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

try:
	bus = dbus.SessionBus()
except dbus.exceptions.DBusException:
	print _("Error: Could not connect to D-Bus.")
	sys.exit(1)
try:
	remote_object = bus.get_object("org.gnome.Zeitgeist", "/org/gnome/zeitgeist")
except dbus.exceptions.DBusException:
	print _("Error: Zeitgeist service not running.")
	sys.exit(1)

iface = dbus.Interface(remote_object, "org.gnome.Zeitgeist")

def dbus_connect(signal, callback, arg0=None):
	if not arg0:
		remote_object.connect_to_signal(signal, callback,
			dbus_interface="org.gnome.Zeitgeist")
	else:
		# TODO: This is ugly and limited to 1 argument. Find a better
		# way to do it.
		remote_object.connect_to_signal(signal, callback,
			dbus_interface="org.gnome.Zeitgeist", arg0=arg0)
