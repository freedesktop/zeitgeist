#! /usr/bin/env python
# -.- coding: utf-8 -.-

import dbus
import urllib

bus = dbus.SessionBus()
remote_object = bus.get_object("org.gnome.zeitgeist", "/RemoteInterface")
iface = dbus.Interface(remote_object, "org.gnome.zeitgeist")

print 'Your bookmarks are:'
bookmarks = iface.get_bookmarks()
for bookmark in bookmarks:
	print '-', bookmark[0], '"' +  urllib.unquote(str(bookmark[1])) + '"'

print '\nYour most used tags are:'
print ', '.join(iface.get_most_used_tags(0, 0, 0))

print '\nYour recently used tags are:'
print ', '.join(iface.get_most_used_tags(0, 0, 0))
