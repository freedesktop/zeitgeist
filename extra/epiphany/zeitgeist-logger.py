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
import dbus
import time

def page_changed(embed, load_status, window):
	print embed
	print "'%s', '%s', '%s', '%s', '%s', '%s', '%s'" % (load_status.blurb, load_status.default_value, load_status.flags, load_status.name, load_status.nick, load_status.owner_type, load_status.value_type)
	print window
	print '----'
	#if embed._zeitgeist_stamp != load_status:
	#	# Send this info via D-Bus
	#	title = embed.get_title()
	#	timestamp = time.time()
	#	icon = "gnome-globe"
	#	print title

def attach_tab(window, tab):
	try:
		signal = tab.connect("notify::load-status", page_changed, window)
	except Exception:
		signal = tab.connect("ge-content-change", page_changed, window)
	
	tab._page_changed = signal

def detach_tab(window, tab):
	if not hasattr(tab, "_page_changed"):
		return
	tab.disconnect(tab._page_changed)
	delattr(tab, "_page_changed")
