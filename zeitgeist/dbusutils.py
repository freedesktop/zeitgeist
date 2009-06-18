# -.- encoding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Siegfried-Angel Gevatter Pujals <rainct@ubuntu.com>
# Copyright © 2009 Mikkel Kamstrup Erlandsen <mikkel.kamstrup@gmail.com>
# Copyright © 2009 Markus Korn <thekorn@gmx.de>
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

_bus = None
_engine_proxy = None
_engine_iface = None

def get_session_bus():
	global _bus
	
	if _bus :
		return bus
	
	try:
		_bus = dbus.SessionBus()
		return _bus
	except dbus.exceptions.DBusException:
		print _("Error: Could not connect to D-Bus.")
		sys.exit(1)

def get_engine_proxy():
	global _engine_proxy
	
	if _engine_proxy :
		return _engine_proxy
	
	try:
		_engine_proxy = get_session_bus().get_object("org.gnome.Zeitgeist",
													 "/org/gnome/Zeitgeist")
		return _engine_proxy
	except dbus.exceptions.DBusException:
		print _("Error: Zeitgeist service not running.")
		sys.exit(1)

def get_engine_interface():
	global _engine_iface
	
	if _engine_iface:
		return _engine_iface
	
	_engine_iface = dbus.Interface(get_engine_proxy(), "org.gnome.Zeitgeist")
	return _engine_iface

def dbus_connect(signal, callback, arg0=None):
	if not arg0:
		get_engine_proxy().connect_to_signal(signal, callback,
			dbus_interface="org.gnome.Zeitgeist")
	else:
		# TODO: This is ugly and limited to 1 argument. Find a better
		# way to do it.
		get_engine_proxy().connect_to_signal(signal, callback,
			dbus_interface="org.gnome.Zeitgeist", arg0=arg0)

# (isssssssbssss)
ITEM_STRUCTURE = (
	("timestamp", int),
	("uri", unicode),
	("text", unicode),
	("source", unicode),
	("content", unicode),
	("mimetype", unicode),
	("tags", unicode),
	("comment", unicode),
	("bookmark", bool),
	("use", unicode),
	("icon", unicode),
	("app", unicode),
	("origin", unicode),
)

ITEM_STRUCTURE_KEYS = set(i[0] for i in ITEM_STRUCTURE)

DEFAULTS = {"i": 0, "s": "", "b": False}
TYPES = {int: "i", unicode: "s", bool: "b"}
TYPES_DICT = dict(ITEM_STRUCTURE) 

sig_plain_data = "(%s)" %"".join(TYPES[i[1]] for i in ITEM_STRUCTURE)

def plainify_dict(item_list):
	return tuple(item_list.get(name, DEFAULTS[type]) for name, type in ITEM_STRUCTURE)

def dictify_data(item_list):
    return dict((key[0], item_list[i]) for i, key in enumerate(ITEM_STRUCTURE))
