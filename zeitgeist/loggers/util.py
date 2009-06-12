# -.- encoding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Seif Lotfy <seif@lotfy.com>
# Copyright © 2009 Siegfried-Angel Gevatter Pujals <rainct@ubuntu.com>
# Copyright © 2009 Natan Yellin <aantny@gmail.com>
# Copyright © 2009 Alex Graveley <alex.graveley@beatniksoftewarel.com>
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
import os
import gobject
import gnomevfs
import gettext
import tempfile


class FileMonitor(gobject.GObject):
	"""
	A simple wrapper around GNOME VFS file monitors.  Emits created, deleted,
	and changed events.  Incoming events are queued, with the latest event
	cancelling prior undelivered events.
	"""
	
	__gsignals__ = {
		"event" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
				   (gobject.TYPE_STRING, gobject.TYPE_INT)),
		"created" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)),
		"deleted" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)),
		"changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING,))
	}

	def __init__(self, path):
		gobject.GObject.__init__(self)

		if os.path.isabs(path):
			self.path = "file://" + path
		else:
			self.path = path
		try:
			self.type = gnomevfs.get_file_info(str(path)).type
		except gnomevfs.Error:
			self.type = gnomevfs.MONITOR_FILE

		self.monitor = None
		self.pending_timeouts = {}

	def open(self):
		if not self.monitor:
			if self.type == gnomevfs.FILE_TYPE_DIRECTORY:
				monitor_type = gnomevfs.MONITOR_DIRECTORY
			else:
				monitor_type = gnomevfs.MONITOR_FILE
			self.monitor = gnomevfs.monitor_add(self.path, monitor_type, self._queue_event)

	def _clear_timeout(self, info_uri):
		try:
			gobject.source_remove(self.pending_timeouts[info_uri])
		except Exception:
			pass
		
	def _queue_event(self, monitor_uri, info_uri, event):
		print "queue event"
		self._clear_timeout(info_uri)
		self.pending_timeouts[info_uri] = \
			gobject.timeout_add(250, self._timeout_cb, monitor_uri, info_uri, event)

	def queue_changed(self, info_uri):
		print "queue changed"
		self._queue_event(self.path, info_uri, gnomevfs.MONITOR_EVENT_CHANGED)
		
	def close(self):
		gnomevfs.monitor_cancel(self.monitor)
		self.monitor = None

	def _timeout_cb(self, monitor_uri, info_uri, event):
		if event in (gnomevfs.MONITOR_EVENT_METADATA_CHANGED, gnomevfs.MONITOR_EVENT_CHANGED):
			self.emit("changed", info_uri)
			print "changed "+self.path
		elif event == gnomevfs.MONITOR_EVENT_CREATED:
			self.emit("created", info_uri)
			print "created "+self.path
		elif event == gnomevfs.MONITOR_EVENT_DELETED:
			self.emit("deleted", info_uri)
			print "deleted "+self.path
		elif event == gnomevfs.MONITOR_EVENT_STOPEXECUTING	:
			#self.emit("deleted", info_uri)
			print "closed "+self.path
		self.emit("event", info_uri, event)

		self._clear_timeout(info_uri)
		return False
