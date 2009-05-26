#! /usr/bin/env python
# -.- coding: utf-8 -.-

import sys
import dbus
import dbus.mainloop.glib
import gobject
import urllib

def updated_signal_handler():
	print "Received reload signal."

if '--listen' in sys.argv:
	dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
bus = dbus.SessionBus()

remote_object = bus.get_object("org.gnome.Zeitgeist", "/org/gnome/zeitgeist")
if '--listen' in sys.argv:
	remote_object.connect_to_signal("signal_updated", updated_signal_handler, dbus_interface="org.gnome.Zeitgeist")
iface = dbus.Interface(remote_object, "org.gnome.Zeitgeist")

print '\nDifferent types in the database:'
for name, icon in iface.get_types():
	print '- %s (%s)' % (name, icon)
print

print 'Your bookmarks are:'
bookmarks = iface.get_bookmarks()
first_item = None
for bookmark in bookmarks:
	print '-', bookmark[2], '«' +  urllib.unquote(str(bookmark[1])) + '»'
	if not first_item: first_item = bookmark

print '\nYour most used tags are:'
print '-', ', '.join(iface.get_most_used_tags(0, 0, 0))

print '\nYour recently used tags are:'
print '-', ', '.join(iface.get_recent_used_tags(0, 0, 0))

mimetype = 'text/plain'
print '\nItems with mimetype «%s»:' % mimetype
for item in iface.get_items_with_mimetype(mimetype, 0, 0, "")[:5]:
	print '-', item[2]

if first_item:
	print u'\nTags for item «%s»:' % first_item[2]
	print '-', ', '.join(first_item[4].split(','))
	
	print u'\nItems related to «%s»:' % first_item[2]
	related_items = iface.get_related_items(first_item[1])
	for related_item in related_items[:5]:
		print '-', related_item[2]
	del related_items
	
	print u'\nItems sharing some tag with «%s»:' % first_item[2]
	related_items = iface.get_items_related_by_tags(first_item[1])
	for related_item in related_items[:5]:
		print '-', related_item[2] + ':', ', '.join(related_item[6].split(','))
	del related_items
	
	last_tag = first_item[4].split(',')[-1]
	if last_tag:
		print u'\nItems with tag «%s»:' % last_tag
		tag_items = iface.get_items(0, 0, last_tag)
		for tag_item in tag_items[:5]:
			print '-', tag_item[2] + ':', ', '.join(tag_item[6].split(','))

if '--listen' in sys.argv:
	loop = gobject.MainLoop()
	loop.run()
