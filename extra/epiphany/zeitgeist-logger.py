# -*- coding: utf-8 -*-
#
# Unofficial Epiphany Extension
# Push websites to GNOME Zeitgeist
#
# Copyright (C) 2009 Seif Lotfy <seiflotfy@gnome.org>
# Copyright (C) 2008-2009 Siegfried Gevatter <rainct@ubuntu.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import epiphany
import sys
import dbus
import time
import urllib

# Connect to D-Bus
bus = dbus.SessionBus()
try:
	remote_object = bus.get_object("org.gnome.Zeitgeist", "/org/gnome/zeitgeist")
except dbus.exceptions.DBusException:
	print >>sys.stderr, "GNOME Zeitgeist Logger: Error: Could not connect to D-Bus."
else:
	iface = dbus.Interface(remote_object, "org.gnome.Zeitgeist")

	def page_changed(embed, load_status, window):
		if not embed.get_property('load-status'):
			# Send this info via D-Bus
			icon = "gnome-globe"
			iface.insert_item((
				int(time.time()), # timestamp
				urllib.unquote(embed.get_location(True)), # uri
				embed.get_title(), # name
				u"Epiphany History", # type
				u"", # mimetype
				u"", # tags
				u"", # comment
				0, # count
				u"visited", # use
				False, # bookmark
				u"gnome-globe", # icon
				))

	def attach_tab(window, tab):
		try:
			signal = tab.connect_after("notify::load-status", page_changed, window)
		except Exception:
			signal = tab.connect_after("ge-content-change", page_changed, window)
		
		tab._page_changed = signal

	def detach_tab(window, tab):
		if hasattr(tab, "_page_changed"):
			tab.disconnect(tab._page_changed)
			delattr(tab, "_page_changed")
