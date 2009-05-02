# -*- coding: utf-8 -*-
#
# Unofficial Epiphany Extension
# Push websites to GNOME Zeitgeist
#
# Copyright (C) 2008 Seif Lotfy <seiflotfy@gnome.org> 2008 Siegfried Gevatter <rainct@ubuntu.com>
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

i = 0

def page_changed(embed, uri, window):
	global i
	i = i+1
	if i%2 == 0:

	'''
	Send this info via D-Bus
	'''	
		title = embed.get_title()
		timestamp = time.time()
		icon = "gnome-globe"

def attach_tab(window, tab):
	if hasattr(tab, "get_embed"):
		embed = tab.get_embed()
	else:
		embed = tab
	try:
		signal = embed.connect("notify::load-status", page_changed, window)
	except:
		signal = embed.connect("ge-content-change", page_changed, window)

	tab._page_changed = signal

def detach_tab(window, tab):
	if not hasattr(tab, "_page_changed"):
		return
	if hasattr(tab, "get_embed"):
		embed = tab.get_embed()
	else:
		embed = tab
	embed.disconnect(tab._page_changed)
	delattr(tab, "_page_changed")


