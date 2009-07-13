#! /usr/bin/env python
# -.- coding: utf-8 -.-

# Zeitgeist - Example / Test script
#
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

import sys
import os
import gobject
import urllib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from zeitgeist import dbusutils

iface = dbusutils.DBusInterface()

def updated_signal_handler(value):
	print "Received signal: ", value

if '--listen' in sys.argv:
	iface.connect("EventsChanged", updated_signal_handler)

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
	gobject.MainLoop().run()
