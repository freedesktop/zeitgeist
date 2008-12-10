import datetime
import os
import re
from xml.dom.minidom import parse
from xml.parsers.expat import ExpatError

import gobject
import gtk
import gnomevfs
import W3CDate
from gettext import gettext as _

from zeitgeist_base import Data, DataProvider
from zeitgeist_util import FileMonitor, launcher

# FIXME:  This should really just use Beagle or Tracker.


class NoteData(Data):
	def __init__(self, uri,timestamp =None): 
		self.title = None
		self.content_text = None
		self.timestamp = timestamp
		self.uri = uri
		self.type = "Notes"
		self.do_reload()
		self.name = str(self.title)
		Data.__init__(self, uri=uri, name=self.name,
			timestamp=self.timestamp, icon="stock_notes",
			mimetype="x-tomboy/note", type =self.type)
		
		# Load and parse note XML
		#self.emit("reload")

	def do_open(self):
		note_uri = "note://tomboy/%s" % os.path.splitext(os.path.split(self.get_uri())[1])[0]
		launcher.launch_uri(note_uri, self.get_mimetype())

	def do_reload(self):
		try:
			note_doc = parse(self.get_uri())
		except (IOError, ExpatError), err:
			#print " !!! Error parsing note '%s': %s" % (self.get_uri(), err)
			return

		try:
			title_node = note_doc.getElementsByTagName("title")[0]
			self.title = title_node.childNodes[0].data
		except (ValueError, IndexError, AttributeError):
			pass

		try:
			# Parse the ISO timestamp format .NET's XmlConvert class uses:
			# yyyy-MM-ddTHH:mm:ss.fffffffzzzzzz, where f* is a 7-digit partial
			# second, and z* is the timezone offset from UTC in the form -08:00.
			changed_node = note_doc.getElementsByTagName("last-change-date")[0]
			changed_str = changed_node.childNodes[0].data
			changed_str = re.sub("\.[0-9]*", "", changed_str) # W3Date chokes on partial seconds
			self.timestamp = int(W3CDate.W3CDate(changed_str).getSeconds())
		except (ValueError, IndexError, AttributeError):
			pass

		try:
			content_node = note_doc.getElementsByTagName("note-content")[0]
			self.content_text = self._get_text_from_node(content_node).lower()
		except (ValueError, IndexError, AttributeError):
			pass

		note_doc.unlink()

	def _get_text_from_node(self, node):
		if node.nodeType == node.TEXT_NODE:
			return node.data
		else:
			return "".join([self._get_text_from_node(x) for x in node.childNodes])


	def get_name(self):
		return self.title or os.path.basename(self.get_uri()) or self.get_uri()


class TomboySource(DataProvider):
	def __init__(self, note_path=None):
		DataProvider.__init__(self,
							name=_("Notes"),
							icon="stock_notes",
							uri="source:///Documents/Tomboy")
		self.name=_("Notes")
		self.new_note_item = Data(name=_("Create New Note"),
								  comment=_("Make a new Tomboy note"),
								  icon=gtk.STOCK_NEW)
		self.new_note_item.do_open = lambda: self._make_new_note()
		if not note_path:
			if os.environ.has_key("TOMBOY_PATH"):
				note_path = os.environ["TOMBOY_PATH"]
			else:
				note_path = "~/.tomboy"
			note_path = os.path.expanduser(note_path)
		self.note_path = note_path

		self.notes = {}

		self.note_path_monitor = FileMonitor(self.note_path)
		self.note_path_monitor.connect("event", self._file_event)
		self.note_path_monitor.open()

		# Load notes in an idle handler
		#gobject.idle_add(self._idle_load_notes().next, priority=gobject.PRIORITY_LOW)

	def _file_event(self, monitor, info_uri, ev):
		filename = os.path.basename(info_uri)

		if ev == gnomevfs.MONITOR_EVENT_CREATED:
			notepath = os.path.join(self.note_path, filename)
			self.notes[filename] = NoteData(notepath)
			self.emit("reload")
		elif self.notes.has_key(filename):
			if ev == gnomevfs.MONITOR_EVENT_DELETED:
			   # delself.notes[filename]
				self.emit("reload")
			else:
				self.notes[filename].emit("reload")

	def _make_new_note(self):
		launcher.launch_command("tomboy --new-note")

	def get_items_uncached(self):
		try: 
			for filename in os.listdir(self.note_path):
				if filename.endswith(".note"):
					notepath = os.path.join(self.note_path, filename)
					yield NoteData(notepath)
		except (OSError, IOError), err:
		   pass  #print " !!! Error loading Tomboy notes:", err
