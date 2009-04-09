#! /usr/bin/env python
# -.- coding: utf-8 -.-

import dbus
import dbus.mainloop.glib
import gobject
import urllib

def reload_signal_handler():
	print "Received reload signal."

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
bus = dbus.SessionBus()

remote_object = bus.get_object("org.gnome.zeitgeist", "/RemoteInterface")
remote_object.connect_to_signal("signal_reload", reload_signal_handler, dbus_interface="org.gnome.zeitgeist")
iface = dbus.Interface(remote_object, "org.gnome.zeitgeist")

print 'Your bookmarks are:'
bookmarks = iface.get_bookmarks()
last_item = None
for bookmark in bookmarks:
	print '-', bookmark[0], '"' +  urllib.unquote(str(bookmark[1])) + '"'
	last_item = bookmark

print '\nYour most used tags are:'
print ', '.join(iface.get_most_used_tags(0, 0, 0))

print '\nYour recently used tags are:'
print ', '.join(iface.get_recent_used_tags(0, 0, 0))

if last_item:
	print '\nItems related to "%s":' % last_item[0]
	related_items = iface.get_related_items(last_item[1])
	for related_item in related_items:
		print '-', related_item[0], '"' +  urllib.unquote(str(related_item[1])) + '"'

loop = gobject.MainLoop()
loop.run()
