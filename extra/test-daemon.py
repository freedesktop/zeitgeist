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

iface = dbusutils.ZeitgeistDBusInterface()

def updated_signal_handler(value):
	print "Received signal: ", value

if '--listen' in sys.argv:
	iface.connect("EventsChanged", updated_signal_handler)

print '\nSome of the different types in the database:'
for name in iface.GetTypes()[:5]:
	print '- %s' % name
print

print 'Your most recently used bookmarks are:'
bookmarks = iface.FindEvents(0, 0, 5, False, "item", [{"bookmarked": True}])
sample_item = None
for bookmark in bookmarks:
	print '-', bookmark["text"], '«' +  urllib.unquote(str(bookmark["uri"])) + '»'
	if not sample_item or (not sample_item["tags"] and bookmark["tags"]):
		sample_item = bookmark

print '\nYour most used tags are:'
print '-', ', '.join([tag[0] for tag in iface.GetTags(0, 0, 5, u"")])

mimetype = 'text/plain'
print '\nMost recent items with mimetype «%s»:' % mimetype
for item in iface.FindEvents(0, 0, 5, False, "item", [{"mimetypes": [mimetype]}]):
	print '-', item["text"]

if sample_item:
	print u'\nTags for item «%s»:' % sample_item["text"]
	print '-', ', '.join(sample_item["tags"].split(','))
	
	if sample_item["tags"]:
		print u'\nMost recent items sharing some tag with «%s»:' % sample_item["text"]
		related_items = iface.FindEvents(0, 0, 5, False, "item",
			[{"tags": [tag.strip()]} for tag in sample_item["tags"].split(",")])
		for related_item in related_items:
			print '- %s: %s' % (related_item["text"], related_item["tags"])
		del related_items
		
		last_tag = sample_item["tags"].split(",")[-1].strip()
		print u'\nMost recent items with tag «%s»:' % last_tag
		tag_items = iface.FindEvents(0, 0, 5, False, "item",
			[{"tags": [last_tag]}])
		for tag_item in tag_items:
			print '- %s: %s' % (tag_item["text"], tag_item["tags"])

if '--listen' in sys.argv:
	gobject.MainLoop().run()
