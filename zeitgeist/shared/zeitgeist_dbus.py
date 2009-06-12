# -.- encoding: utf-8 -.-
# -.- encoding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Siegfried-Angel Gevatter Pujals <rainct@ubuntu.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

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
