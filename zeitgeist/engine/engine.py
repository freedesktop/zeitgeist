# -.- encoding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Seif Lotfy <seif@lotfy.com>
# Copyright © 2009 Siegfried-Angel Gevatter Pujals <rainct@ubuntu.com>
# Copyright © 2009 Natan Yellin <aantny@gmail.com>
# Copyright © 2009 Mikkel Kamstrup Erlandsen <mikkel.kamstrup@gmail.com>
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

import time
import sys
import os
import gettext
import gobject
import logging
from xdg import BaseDirectory
from xdg.DesktopEntry import DesktopEntry

from zeitgeist import config
from zeitgeist.engine.base import *
from zeitgeist.dbusutils import ITEM_STRUCTURE_KEYS, TYPES_DICT

class ZeitgeistEngine(gobject.GObject):

	def __init__(self, storm_store):
		
		gobject.GObject.__init__(self)
		
		assert storm_store is not None
		self.store = storm_store
		self._apps = set()
		self._last_time_from_app = {}
		
		'''
		path = BaseDirectory.save_data_path("zeitgeist")
		database = os.path.join(path, "zeitgeist.sqlite")
		self.connection = self._get_database(database)
		self.cursor = self.connection.cursor()
		'''
	
	def _result2data(self, event=None, item=None):
		
		if not item:
			item = event.subject
		
		# Check if the item is bookmarked
		# FIXME: this seems redundant if i am fetching bookmarked items
		bookmark = bool(self.store.find(Item,
			Item.content_id == Content.BOOKMARK.id,
			Annotation.subject_id == item.id,
			Annotation.item_id == Item.id).one())
		
		result = self._get_tags_for_item(item)
		tags = ",".join(set(result)) if result else ""
		
		return (
			event.start if event else 0, # timestamp
			item.uri.value, # uri
			item.text or os.path.basename(item.uri.value), # name
			item.source.value or "", # source
			item.content.value or "", # content
			item.mimetype or "", # mimetype
			tags, # tags
			"", # comment
			bookmark, # bookmark
			# FIXME: I guess event.item.content below should never be None
			event.item.content.value if (event and event.item.content) else "", # usage is determined by the event Content type
			item.icon or "", # icon
			"", # app	  # FIXME!
			item.origin or "" # origin
			)
	
	def _ensure_item(self, item, uri_only=False):
		"""
		Takes either a Data object or an URI for an item in the
		database. If it's a Data object it is returned unchanged,
		but if it's an URI it's looked up in the database and the
		its returned converted into a complete Data object.
		
		If uri_only is True, only the URI of the item is returned
		(and no database query needs to take place).
		"""
		
		# Is it a string (can be str, dbus.String, etc.)?
		if hasattr(item, "capitalize"):
			if uri_only:
				return item
			else:
				item = self.get_item(item)
		elif uri_only:
			return item["uri"]
		
		return item
	
	def get_last_timestamp(self, uri=None):
		"""
		Gets the timestamp of the most recent item in the database. If
		`uri' is not empty, it will give the last timestamp for the
		indicated URI.
		
		Returns 0 if there are no items in the database.
		"""
		
		return 0
	
	def _get_ids(self, uri, content, source):	
		if uri:
			uri_id = URI.lookup_or_create(uri).id
		else:
			uri_id = None
			
		if source:
			source_id = Source.lookup_or_create(source).id
		else:
			source_id = None
			
		if content:
			content_id = Content.lookup_or_create(content).id
		else:
			content_id = None
		
		return uri_id, content_id, source_id
	
	def _get_item(self, id, content_id, source_id, text, origin=None, mimetype=None, icon=None):
		self._insert_item(id, content_id, source_id, text, origin, mimetype, icon)
		return self.store.find(Item, Item.id == id)
	
	def _insert_item(self, id, content_id, source_id, text, origin=None, mimetype=None, icon=None):
		try:
			self.store.execute("""
				INSERT INTO Item
				(id, content_id, source_id, text, origin, mimetype, icon)
				VALUES (?,?,?,?,?,?,?)""",
				(id, content_id, source_id, text, origin, mimetype, icon),
				noresult=True)
		except Exception:
			self.store.execute("""
				UPDATE Item SET
				content_id=?, source_id=?, text=?, origin=?,
				mimetype=?, icon=? WHERE id=?""",
				(content_id, source_id, text, origin, mimetype, icon, id),
				noresult=True)
	
	def insert_item(self, ritem, commit=True, force=False):
		"""
		Inserts an item into the database. Returns True on success,
		False otherwise (for example, if the item already is in the
		database).
		"""
		# we require all  all keys here
		missing = ITEM_STRUCTURE_KEYS - set(ritem.keys())
		if missing:
			raise KeyError(("these keys are missing in order to add "
							"this item properly: %s" %", ".join(missing)))
		if not ritem["uri"].strip():
			logging.warning("Discarding item without a URI: %s" % ritem)
			return False
		if not ritem["content"].strip():
			logging.warning("Discarding item without a Content type: %s" % ritem)
			return False
		if not ritem["source"].strip():
			logging.warning("Discarding item without a Source type: %s" % ritem)
			return False
		if not ritem["mimetype"].strip():
			logging.warning("Discarding item without a mimetype: %s" % ritem)
			return False
		ritem = dict((key, TYPES_DICT[key](value)) for key, value in ritem.iteritems())
		
		try:
			'''
			Init URI, Content and Source
			'''
			uri_id, content_id, source_id = self._get_ids(
				ritem["uri"], ritem["content"], ritem["source"])
			
			'''
			Create Item for Data
			'''
			item = self._get_item(uri_id, content_id, source_id,
				ritem["text"], ritem["origin"], ritem["mimetype"], ritem["icon"])
			
			'''
			 Extract tags
			'''
			for tag in ritem["tags"].split(","):
				tag = tag.strip()
				if not tag:
					# ignore empty tags
					continue
				anno_uri = "zeitgeist://tag/%s" % tag
				anno_id, x, y = self._get_ids(anno_uri,None,None)
				anno_item = self._get_item(anno_id, Content.TAG.id, Source.USER_ACTIVITY.id, tag)
				try:
					self.store.execute(
						"INSERT INTO annotation (item_id, subject_id) VALUES (?,?)",
						(anno_id, uri_id), noresult=True)
				except Exception, ex:
					pass
			
			'''
			Bookmark
			'''
			if ritem["bookmark"]:
				anno_uri = "zeitgeist://bookmark/%s" % ritem["uri"]
				anno_id, x, y = self._get_ids(anno_uri,None,None)
				anno_item = self._get_item(anno_id, Content.BOOKMARK.id, Source.USER_ACTIVITY.id, u"Bookmark")
				try:
					self.store.execute(
						"INSERT INTO annotation (item_id, subject_id) VALUES (?,?)",
						(anno_id, uri_id), noresult=True)
				except Exception, ex:
					pass
			
			if force:
				return True
			
			'''
			Init App
			'''
			# Store the application
			app_info = DesktopEntry(ritem["app"])			
			app_uri_id, app_content_id, app_source_id = \
							self._get_ids(ritem["app"],
										  unicode(app_info.getType()),
										  unicode(app_info.getExec()).split()[0])
			app_item = self._get_item(app_uri_id,
									  app_content_id,
									  app_source_id,
									  unicode(app_info.getName()),
									  icon=unicode(app_info.getIcon()))
			try:
				self.store.execute("INSERT INTO app (item_id, info) VALUES (?,?)",
					(app_uri_id, unicode(ritem["app"])), noresult=True)
			except Exception, ex:
				pass
			
			'''
			Set event 
			'''
			e_uri = "zeitgeist://event/%s/%%s/%s#%d" % (ritem["use"],ritem["timestamp"], uri_id)		
			e_id , e_content_id, e_subject_id = self._get_ids(e_uri,ritem["use"],None )
			e_item = self._get_item(e_id, e_content_id, Source.USER_ACTIVITY.id, u"Activity")
			
			try:
				self.store.execute(
					"INSERT INTO event (item_id, subject_id, start, app_id) VALUES (?,?,?,?)",
					(e_id, uri_id, ritem["timestamp"], app_uri_id), noresult=True)
			except Exception, ex:
				pass
			return True
		
		except Exception, ex:
			pass
	
	def insert_items(self, items):
		"""
		Inserts items into the database and returns the amount of
		items it inserted.
		"""
		
		amount_items = 0
		
		# Check if event is before the last logs
		t1 = time.time()
		for item in items:
			if self.insert_item(item, commit=False):
				amount_items += 1
		self.store.commit()
		t2 = time.time()
		logging.debug("Inserted %s items in %.5f s" % (amount_items,t2-t1))
		
		return amount_items
	
	def get_item(self, uri):
		"""Returns basic information about the indicated URI."""
		item = self.store.find(Item, Item.id == URI.id,
			URI.value == unicode(uri)).one()
		if item:
			return self._result2data(item=item)
	
	def find_events(self, min=0, max=sys.maxint, limit=0,
	sorting_asc=True, unique=False, filters=()):
		"""
		Returns all items from the database between the indicated
		timestamps `min' and `max'. Optionally the argument `tags'
		may be used to filter on tags or `mimetypes' to filter on
		mimetypes.
		
		Parameter filters is an array of structs containing: (text
		to search in the name, text to search in the URI, tags,
		mimetypes, source, content). The filter between characteristics
		inside the same struct is of type AND (all need to match), but
		between diferent structs it is OR-like (only the conditions
		described in one of the structs need to match for the item to
		be returned).
		"""
		
		# Emulate optional arguments for the D-Bus interface
		if not max: max = sys.maxint
		
		# filters: ((text_name, text_uri, (tags), (mimetypes), source, content, bookmarked),)
		expressions = []
		for filter in filters:
			if not isinstance(filter, (list, tuple)) and len(filter) == 7:
				raise TypeError("Expected a struct, got %s." % type(filter).__name__)
			filterset = []
			if filter[0]:
				filterset += [ Item.text.like(filter[0], escape="\\") ]
			if filter[1]:
				filterset += [ URI.value.like(filter[1], escape="\\") ]
			if filter[2]:
				pass # tags...
			if filter[3]:
				condition = ' OR '.join(
					['mimetype LIKE ? ESCAPE "\\"'] * len(filter[3]))
				mimetypes = [m[0] for m in self.store.execute("""
						SELECT DISTINCT(mimetype) FROM item
						WHERE %s""" % condition, filter[3]).get_all()]
				filterset += [ Item.mimetype.is_in(mimetypes) ]
			if filter[4]:
				pass # source ...
			if filter[5]:
				pass # content
			if filter[6] > 0:
				bookmarks = Select(Annotation.subject_id, And(
					Item.content_id == Content.BOOKMARK.id,
					Annotation.item_id == Item.id))
				if filter[6] == 1:
					# Only get bookmarked items
					filterset += [Event.subject_id.is_in(bookmarks)]
				elif filter[6] == 2:
					# Only get items that aren't bookmarked
					filterset += [Not(Event.subject_id.is_in(bookmarks))]
				else:
					raise ValueError(
						"Unsupported bookmark filter: %d. Expected 0, 1 or 2." \
						 % filter[6])
			if filterset:
				expressions += [ And(*filterset) ]
		
		t1 = time.time()
		events = self.store.find(Event, Event.start >= min, Event.start <= max,
			URI.id == Event.subject_id, Item.id == Event.subject_id,
			Or(*expressions) if expressions else True)[:limit or None]
		events.order_by(Event.start if sorting_asc else Desc(Event.start))
		
		if unique:
			events.max(Event.start)
			events.group_by(Event.subject_id)
		
		return [self._result2data(event) for event in events]
	
	def _update_item(self, item):
		"""
		Updates an item already in the database.
		
		If the item has tags, then the tags will also be updated.
		"""
		
		#FIXME Delete all tags of the ITEM
		self.delete_item(item)
		self.store.commit()
		self.store.flush()
		self.insert_item(item, True, True)
		self.store.commit()
		self.store.flush()
	
	def update_items(self, items):
		map(self._update_item, items)
	
	def _get_tags_for_item(self, item):
		package = []
		id = item.id
		tags = self.store.find(Annotation.item_id, Annotation.subject_id == id)
		for tag in tags:
			tag = self.store.find(Item.text, Item.id == tag).one()
			package.append(tag)
		return package
	
	def _delete_item(self, item):
		
		uri_id = self.store.execute("SELECT id FROM URI WHERE value=?",(item["uri"],)).get_one()
		uri_id = uri_id[0]
		annotation_ids = self.store.execute("SELECT item_id FROM Annotation WHERE subject_id=?",(uri_id,)).get_all()
		if len(annotation_ids) > 0:
			for anno in annotation_ids[0]:
				self.store.execute("DELETE FROM Annotation WHERE subject_id=?",
					(uri_id,), noresult=True)
				self.store.execute("DELETE FROM Item WHERE id=?",
					(anno,), noresult=True)		
		self.store.execute("DELETE FROM Item WHERE id=?",
			(uri_id,), noresult=True)
	
	def delete_items(self, items):
		map(self._delete_item, items)
	
	def get_types(self):
		"""
		Returns a list of all different types in the database.
		"""
		contents = self.store.find(Content)
		return [content.value for content in contents]
	
	def get_tags(self, name_filter="", limit=0, min_timestamp=0, max_timestamp=0):
		"""
		Returns a list containing tuples with the name and the number of
		occurencies of the tags matching `name_filter', or all existing
		tags in case it's empty, sorted from most used to least used. `limit'
		can base used to limit the amount of results.
		
		Use `min_timestamp' and `max_timestamp' to limit the time frames you
		want to consider.
		"""
		
		return self.store.execute("""
			SELECT item.text, (SELECT COUNT(rowid) FROM annotation
				WHERE annotation.item_id = item.id) AS amount
			FROM item
			WHERE item.id IN (SELECT annotation.item_id FROM annotation
				INNER JOIN event ON (event.subject_id = annotation.subject_id)
				WHERE event.start >= ? AND event.start <= ?)
				AND item.content_id = ? AND item.text LIKE ? ESCAPE "\\"
			ORDER BY amount DESC LIMIT ?
			""", (min_timestamp, max_timestamp or sys.maxint, Content.TAG.id,
			name_filter or "%", limit or sys.maxint)).get_all()
	
	def get_last_insertion_date(self, application):
		"""
		Returns the timestamp of the last item which was inserted
		related to the given application. If there is no such record,
		0 is returned.
		"""
		
		app = App.lookup(application)
		
		return self.store.find(Event.start, Event.app == app.item.id
			).order_by(Event.start).last() if app else 0
	
	def get_related_items(self, uri):
		return []

_engine = None
def get_default_engine():
	global _engine
	if not _engine:
		_engine = ZeitgeistEngine(get_default_store())
	return _engine
