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

remote_object = bus.get_object("org.gnome.zeitgeist", "/org/gnome/zeitgeist")
if '--listen' in sys.argv:
	remote_object.connect_to_signal("EventsChanged", updated_signal_handler, dbus_interface="org.gnome.zeitgeist")
iface = dbus.Interface(remote_object, "org.gnome.zeitgeist")

print '\nDifferent types in the database:'
for name in iface.GetTypes():
	print '- %s' % name
print

print 'Your bookmarks are:'
bookmarks = iface.GetBookmarks()
first_item = None
for bookmark in bookmarks:
	print '-', bookmark[2], '«' +  urllib.unquote(str(bookmark[1])) + '»'
	if not first_item: first_item = bookmark

print '\nYour most used tags are:'
print '-', ', '.join(iface.GetMostUsedTags(0, 0, 0))

print '\nYour recently used tags are:'
print '-', ', '.join(iface.GetRecentUsedTags(0, 0, 0))

mimetype = 'text/plain'
print '\nItems with mimetype «%s»:' % mimetype
for item in iface.GetItemsWithMimetype(mimetype, 0, 0, '')[:5]:
	print '-', item[2]

if first_item:
	print u'\nTags for item «%s»:' % first_item[2]
	print '-', ', '.join(first_item[4].split(','))
	
	print u'\nItems related to «%s»:' % first_item[2]
	related_items = iface.GetRelatedItems(first_item[1])
	for related_item in related_items[:5]:
		print '-', related_item[2]
	del related_items
	
	#print u'\nItems sharing some tag with «%s»:' % first_item[2]
	#related_items = iface.GetItemsRelatedByTags(first_item[1])
	#for related_item in related_items[:5]:
	#	print '-', related_item[2] + ':', ', '.join(related_item[6].split(','))
	#del related_items
	
	last_tag = first_item[4].split(',')[-1]
	if last_tag:
		print u'\nItems with tag «%s»:' % last_tag
		tag_items = iface.GetItems(0, 0, 0, last_tag, '')
		for tag_item in tag_items[:5]:
			print '-', tag_item[2] + ':', ', '.join(tag_item[6].split(','))

if '--listen' in sys.argv:
	loop = gobject.MainLoop()
	loop.run()

# For copy-pasting into an interactive Python shell:
## import dbus; bus = dbus.SessionBus(); remote_object = bus.get_object("org.gnome.zeitgeist", "/org/gnome/zeitgeist"); iface = dbus.Interface(remote_object, "org.gnome.zeitgeist");
