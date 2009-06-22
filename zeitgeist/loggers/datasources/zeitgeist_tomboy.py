# -.- encoding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Seif Lotfy <seif@lotfy.com>
# Copyright © 2009 Siegfried-Angel Gevatter Pujals <rainct@ubuntu.com>
# Copyright © 2009 Natan Yellin <aantny@gmail.com>
# Copyright © 2009 Alex Graveley <alex.graveley@beatniksoftewarel.com>
# Copyright © 2009 Markus Korn <thekorn@gmx.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import gobject
import gio
import os.path
import logging
import time
from xml.dom.minidom import parseString
from xml.parsers.expat import ExpatError

from zeitgeist.loggers.zeitgeist_base import DataProvider
from zeitgeist.loggers.iso_strptime import iso_strptime

# FIXME: This should really just use Beagle or Tracker.

def flatten_text(node):
	if node.nodeType == node.TEXT_NODE:
		return node.data
	else:
		return "".join([flatten_text(x) for x in node.childNodes])
	

class TomboyNote(object):
	
	@classmethod
	def parse_content(cls, content, uri=None):
		try:
			content, length, tag = content
		except ValueError:
			pass
		assert isinstance(content, (unicode, str))
		result = {"uri": uri}
		try:
			note = parseString(content)
		except (IOError, ExpatError), err:
			logging.error("could not parse note '%s'" %uri)
			return None
		else:
			nodes = note.getElementsByTagName("title")
			if nodes:
				result["title"] = nodes[0].childNodes[0].data
			nodes = note.getElementsByTagName("note-content")
			if nodes:
				result["content"] = flatten_text(nodes[0])
			nodes = note.getElementsByTagName("last-change-date")
			if nodes:
				result["date_changed"] = nodes[0].childNodes[0].data
			nodes = note.getElementsByTagName("create-date")
			if nodes:
				result["date_created"] = nodes[0].childNodes[0].data
		try:
			note_obj = cls(**result)
		except:
			logging.exception("error initializing '%s'" %uri)
			note_obj = None
		note.unlink()
		return note_obj
	
	def __init__(self, uri, date_created, title=None, content=None,
			date_changed=None):
		self.uri = uri
		self.date_created = iso_strptime(date_created)
		self.date_created = int(time.mktime(self.date_created.timetuple()))
		self.title = title
		self.content = content
		if date_changed:
			self.date_changed = iso_strptime(date_changed)
			self.date_changed = int(time.mktime(self.date_changed.timetuple()))

class TomboyNotes(gobject.GObject):
	
	PATH = os.path.expanduser("~/.tomboy")
	
	def __init__(self):
		gobject.GObject.__init__(self)
		logging.debug("watching '%s' for tomboy notes" %self.PATH)
		path_object = gio.File(self.PATH)
		self.notes_monitor = path_object.monitor_directory()
		self.notes_monitor.connect("changed", self.notes_changed)
		
	def load_all(self):
		for filename in os.listdir(self.PATH):
			filename = os.path.join(self.PATH, filename)
			if os.path.splitext(filename)[-1] == ".note":
				with open(filename) as fileobj:
					note = TomboyNote.parse_content(fileobj.read(),
							u"file://%s" %filename)
				if note is not None:
					yield note
		
	def notes_changed(self, monitor, fileobj, _, event):
		filename = fileobj.get_path()
		if os.path.splitext(filename)[-1] == ".note":
			if event in (gio.FILE_MONITOR_EVENT_CHANGED,
					gio.FILE_MONITOR_EVENT_CREATED):
				logging.debug("changed note '%s'" %filename)
				note = TomboyNote.parse_content(fileobj.load_contents(),
					fileobj.get_uri())
				if note is not None:
					self.emit("note-changed", note)
			elif event == gio.FILE_MONITOR_EVENT_DELETED:
				logging.debug("deleted note '%s'" %filename)
				# send one last item for this note to the engine :)
				# this idea is not easy, as tomboy does not change a file,
				# but delete a .note and recreates this file on changes
				
gobject.signal_new("note-changed", TomboyNotes,
					gobject.SIGNAL_RUN_LAST,
					gobject.TYPE_NONE,
					(gobject.TYPE_PYOBJECT,))


class TomboySource(DataProvider):
	
	def __init__(self, note_path=None):
		DataProvider.__init__(self, name="tomboy notes")
		self.notes = TomboyNotes()
		self.__notes_queue = list(self.notes.load_all())
		self.notes.connect("note-changed", self.item_changed)
		self.config.connect("configured", self.reload_proxy_config)
		
	def item_changed(self, monitor, note):
		self.__notes_queue.append(note)
		self.emit("reload")
		
	def reload_proxy_config(self, configuration):
		self.emit("reload")

	def get_items_uncached(self):
		for note in self.__notes_queue:
			times = [(note.date_created, u"CreateEvent"),]
			if note.date_changed is not None:
				times.append((note.date_changed, u"ModifyEvent"))
			for timestamp, use in times:
				item = {
					"timestamp": timestamp,
					"uri": note.uri,
					"text": note.title, # or note.content
					"source": "Tomboy Notes",
					"content": u"Note",
					"use": u"http://gnome.org/zeitgeist/schema/1.0/core#%s" %use,
					"mimetype": u"text/plain",
					"tags": u"",
					"icon": u"",
					"app": u"/usr/share/applications/tomboy.desktop",
					"origin": u"", 	# we are not sure about the origin of this item,
									# let's make it NULL, it has to be a string
				}
				yield item
			

__datasource__ = TomboySource()
