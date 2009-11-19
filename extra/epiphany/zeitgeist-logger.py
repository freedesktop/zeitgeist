# -.- coding: utf-8 -.-

# Unofficial Epiphany Extension
# Pushes visited websites to Zeitgeist
#
# Copyright © 2009 Seif Lotfy <seif@lotfy.com>
# Copyright © 2009 Siegfried-Angel Gevatter Pujals <rainct@ubuntu.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import epiphany
import sys
import time
import urllib

from zeitgeist import dbusutils

try:
	iface = dbusutils.ZeitgeistDBusInterface()
except RuntimeError:
	print >>sys.stderr, "GNOME Zeitgeist Logger: " \
		"The Zeitgeist service isn't running."
else:
	def page_changed(embed, load_status, window):
		if not embed.get_property('load-status'):
			item = {
				"timestamp": int(time.time()),
				"uri": unicode(urllib.unquote(embed.get_location(True))),
				"text": unicode(embed.get_title()),
				"source": u"Web History",
				"content": u"Web",
				"mimetype": u"text/html", # TODO: Can we get a mime-type here?
				"tags": u"",
				"comment": u"",
				"bookmark": False,
				"use": u"visited",
				"app": u"/usr/share/applications/epiphany.desktop",
				"origin": u"", # FIXME: In case the user reaches this page by
					# by clicking on a link, put there the page with the link.
				}
			
			# Insert it into Zeitgeist
			iface.InsertEvents([item])
	
	def attach_tab(window, tab):
		tab.connect_after("notify::load-status", page_changed, window)
	
	def detach_tab(window, tab):
		if hasattr(tab, "_page_changed"):
			tab.disconnect(tab._page_changed)
			delattr(tab, "_page_changed")
