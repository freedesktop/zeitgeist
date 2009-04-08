#! /usr/bin/env python
# -.- coding: utf-8 -.-

import dbus
import urllib

bus = dbus.SessionBus()
remote_object = bus.get_object("org.gnome.zeitgeist", "/DBusInterface")
iface = dbus.Interface(remote_object, "org.gnome.zeitgeist")

bookmarks = iface.get_bookmarks()
print 'Your bookmarks are:'
for bookmark in bookmarks:
	print '-', bookmark[0], '"' +  urllib.unquote(str(bookmark[1])) + '"'
