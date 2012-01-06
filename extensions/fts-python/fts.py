#!/usr/bin/env python
# -.- coding: utf-8 -.-

# Zeitgeist
#
# Copyright © 2009 Mikkel Kamstrup Erlandsen <mikkel.kamstrup@gmail.com>
# Copyright © 2010 Canonical Ltd
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
#

#
# TODO
#
# - Delete events hook
# - ? Filter on StorageState
# - Throttle IO and CPU where possible

import os, sys
import time
import pickle
import dbus
import sqlite3
import dbus.service
from xdg import BaseDirectory
from xdg.DesktopEntry import DesktopEntry, xdg_data_dirs
import logging
import subprocess
from xml.dom import minidom
import xapian
import os
from Queue import Queue, Empty
import threading
from urllib import quote as url_escape, unquote as url_unescape
import gobject, gio
from cStringIO import StringIO

from collections import defaultdict
from array import array
from zeitgeist.datamodel import Event as OrigEvent, StorageState, TimeRange, \
    ResultType, get_timestamp_for_now, Interpretation, Symbol, NEGATION_OPERATOR, WILDCARD, NULL_EVENT
from datamodel import Event, Subject
from constants import constants
from zeitgeist.client import ZeitgeistClient, ZeitgeistDBusInterface
from sql import get_default_cursor, unset_cursor, TableLookup, WhereClause
from lrucache import LRUCache

ZG_CLIENT = ZeitgeistClient()

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("zeitgeist.fts")

INDEX_FILE = os.path.join(constants.DATA_PATH, "bb.fts.index")
INDEX_VERSION = "1"
INDEX_LOCK = threading.Lock()
FTS_DBUS_BUS_NAME = "org.gnome.zeitgeist.SimpleIndexer"
FTS_DBUS_OBJECT_PATH = "/org/gnome/zeitgeist/index/activity"
FTS_DBUS_INTERFACE = "org.gnome.zeitgeist.Index"

FILTER_PREFIX_EVENT_INTERPRETATION = "ZGEI"
FILTER_PREFIX_EVENT_MANIFESTATION = "ZGEM"
FILTER_PREFIX_ACTOR = "ZGA"
FILTER_PREFIX_SUBJECT_URI = "ZGSU"
FILTER_PREFIX_SUBJECT_INTERPRETATION = "ZGSI"
FILTER_PREFIX_SUBJECT_MANIFESTATION = "ZGSM"
FILTER_PREFIX_SUBJECT_ORIGIN = "ZGSO"
FILTER_PREFIX_SUBJECT_MIMETYPE = "ZGST"
FILTER_PREFIX_SUBJECT_STORAGE = "ZGSS"
FILTER_PREFIX_XDG_CATEGORY = "AC"

VALUE_EVENT_ID = 0
VALUE_TIMESTAMP = 1

MAX_CACHE_BATCH_SIZE = constants.CACHE_SIZE/2

# When sorting by of the COALESCING_RESULT_TYPES result types,
# we need to fetch some extra events from the Xapian index because
# the final result set will be coalesced on some property of the event
COALESCING_RESULT_TYPES = [ \
    ResultType.MostRecentSubjects,
    ResultType.LeastRecentSubjects,
    ResultType.MostPopularSubjects,
    ResultType.LeastPopularSubjects,
    ResultType.MostRecentActor,
    ResultType.LeastRecentActor,
    ResultType.MostPopularActor,
    ResultType.LeastPopularActor,
]

MAX_TERM_LENGTH = 245


class NegationNotSupported(ValueError):
    pass

class WildcardNotSupported(ValueError):
    pass

def parse_negation(kind, field, value, parse_negation=True):
    """checks if value starts with the negation operator,
    if value starts with the negation operator but the field does
    not support negation a ValueError is raised.
    This function returns a (value_without_negation, negation)-tuple
    """
    negation = False
    if parse_negation and value.startswith(NEGATION_OPERATOR):
        negation = True
        value = value[len(NEGATION_OPERATOR):]
    if negation and field not in kind.SUPPORTS_NEGATION:
        raise NegationNotSupported("This field does not support negation")
    return value, negation
    
def parse_wildcard(kind, field, value):
    """checks if value ends with the a wildcard,
    if value ends with a wildcard but the field does not support wildcards
    a ValueError is raised.
    This function returns a (value_without_wildcard, wildcard)-tuple
    """
    wildcard = False
    if value.endswith(WILDCARD):
        wildcard = True
        value = value[:-len(WILDCARD)]
    if wildcard and field not in kind.SUPPORTS_WILDCARDS:
        raise WildcardNotSupported("This field does not support wildcards")
    return value, wildcard
    
def parse_operators(kind, field, value):
    """runs both (parse_negation and parse_wildcard) parser functions
    on query values, and handles the special case of Subject.Text correctly.
    returns a (value_without_negation_and_wildcard, negation, wildcard)-tuple
    """
    try:
        value, negation = parse_negation(kind, field, value)
    except ValueError:
        if kind is Subject and field == Subject.Text:
            # we do not support negation of the text field,
            # the text field starts with the NEGATION_OPERATOR
            # so we handle this string as the content instead
            # of an operator
            negation = False
        else:
            raise
    value, wildcard = parse_wildcard(kind, field, value)
    return value, negation, wildcard


def synchronized(lock):
    """ Synchronization decorator. """
    def wrap(f):
        def newFunction(*args, **kw):
            lock.acquire()
            try:
                return f(*args, **kw)
            finally:
                lock.release()
        return newFunction
    return wrap

class Deletion:
    """
    A marker class that marks an event id for deletion
    """
    def __init__ (self, event_id):
        self.event_id = event_id

class Reindex:
    """
    Marker class that tells the worker thread to rebuild the entire index.
    On construction time all events are pulled out of the zg_engine
    argument and stored for later processing in the worker thread.
    This avoid concurrent access to the ZG sqlite db from the worker thread.
    """
    def __init__ (self, zg_engine):
        all_events = zg_engine._find_events(1, TimeRange.always(),
            [], StorageState.Any,
            sys.maxint,
            ResultType.MostRecentEvents)
        self.all_events = all_events

class SearchEngineExtension (dbus.service.Object):
    """
    Full text indexing and searching extension for Zeitgeist
    """
    PUBLIC_METHODS = []
    
    def __init__ (self):
        bus_name = dbus.service.BusName(FTS_DBUS_BUS_NAME, bus=dbus.SessionBus())
        dbus.service.Object.__init__(self, bus_name, FTS_DBUS_OBJECT_PATH)
        self._indexer = Indexer()
        
        ZG_CLIENT.install_monitor((0, 2**63 - 1), [],
            self.pre_insert_event, self.post_delete_events)
    
    def pre_insert_event(self, timerange, events):
        for event in events:
            self._indexer.index_event (event)

    def post_delete_events (self, ids):
        for _id in ids:
            self._indexer.delete_event (_id)
                
    @dbus.service.method(FTS_DBUS_INTERFACE,
                         in_signature="s(xx)a("+constants.SIG_EVENT+")uuu",
                         out_signature="a("+constants.SIG_EVENT+")u")
    def Search(self, query_string, time_range, filter_templates, offset, count, result_type):
        """
        DBus method to perform a full text search against the contents of the
        Zeitgeist log. Returns an array of events.
        """
        time_range = TimeRange(time_range[0], time_range[1])
        filter_templates = map(Event, filter_templates)
        events, hit_count = self._indexer.search(query_string, time_range,
                                                 filter_templates,
                                                 offset, count, result_type)
        return self._make_events_sendable (events), hit_count
        
    @dbus.service.method(FTS_DBUS_INTERFACE,
                       in_signature="",
                       out_signature="")
    def ForceReindex(self):
        """
        DBus method to force a reindex of the entire Zeitgeist log.
        This method is only intended for debugging purposes and is not
        considered blessed public API.
        """
        log.debug ("Received ForceReindex request over DBus.")
        self._indexer._queue.put (Reindex (self._indexer))
    
    def _make_events_sendable(self, events):
        return [NULL_EVENT if event is None else Event._make_dbus_sendable(event) for event in events]

def mangle_uri (uri):
    """
    Converts a URI into an index- and query friendly string. The problem
    is that Xapian doesn't handle CAPITAL letters or most non-alphanumeric
    symbols in a boolean term when it does prefix matching. The mangled
    URIs returned from this function are suitable for boolean prefix searches.
    
    IMPORTANT: This is a 1-way function! You can not convert back.
    """
    result = ""
    for c in uri.lower():
        if c in (": /"):
            result += "_"
        else:
            result += c
    return result

def cap_string (s, nbytes=MAX_TERM_LENGTH):
    """
    If s has more than nbytes bytes (not characters) then cap it off
    after nbytes bytes in a way still producing a valid utf-8 string.
    
    Assumes that s is a utf-8 string.
    
    This function useful for working with Xapian terms because Xapian has
    a max term length of 245 (which is not very well documented, but see
    http://xapian.org/docs/omega/termprefixes.html).
    """
    # Check if we can fast-path this string
    if (len(s.encode("utf-8")) <= nbytes):
        return s
    
    # We use a StringIO here to avoid mem thrashing via naiive
    # string concatenation. See fx. http://www.skymind.com/~ocrow/python_string/
    buf = StringIO()
    for char in s :
        if buf.tell() >= nbytes - 1 :
            return buf.getvalue()
        buf.write(char.encode("utf-8"))
    
    return unicode(buf.getvalue().decode("utf-8"))


def expand_type (type_prefix, uri):
    """
    Return a string with a Xapian query matching all child types of 'uri'
    inside the Xapian prefix 'type_prefix'.
    """
    is_negation = uri.startswith(NEGATION_OPERATOR)
    uri = uri[1:] if is_negation else uri
    children = Symbol.find_child_uris_extended(uri)
    children = [ "%s:%s" % (type_prefix, child) for child in children ]

    result = " OR ".join(children)
    return result if not is_negation else "NOT (%s)" % result

class Indexer:
    """
    Abstraction of the FT indexer and search engine
    """
    
    QUERY_PARSER_FLAGS = xapian.QueryParser.FLAG_PHRASE |   \
                         xapian.QueryParser.FLAG_BOOLEAN |  \
                         xapian.QueryParser.FLAG_PURE_NOT |  \
                         xapian.QueryParser.FLAG_LOVEHATE | \
                         xapian.QueryParser.FLAG_WILDCARD
    
    def __init__ (self):
        
        self._cursor = cursor = get_default_cursor()
        os.environ["XAPIAN_CJK_NGRAM"] = "1"
        self._interpretation = TableLookup(cursor, "interpretation")
        self._manifestation = TableLookup(cursor, "manifestation")
        self._mimetype = TableLookup(cursor, "mimetype")
        self._actor = TableLookup(cursor, "actor")
        self._event_cache = LRUCache(constants.CACHE_SIZE)
        
        log.debug("Opening full text index: %s" % INDEX_FILE)
        try:
            self._index = xapian.WritableDatabase(INDEX_FILE, xapian.DB_CREATE_OR_OPEN)
        except xapian.DatabaseError, e:
            log.warn("Full text index corrupted: '%s'. Rebuilding index." % e)
            self._index = xapian.WritableDatabase(INDEX_FILE, xapian.DB_CREATE_OR_OVERWRITE)
        self._tokenizer = indexer = xapian.TermGenerator()
        self._query_parser = xapian.QueryParser()
        self._query_parser.set_database (self._index)
        self._query_parser.add_prefix("name", "N")
        self._query_parser.add_prefix("title", "N")
        self._query_parser.add_prefix("site", "S")
        self._query_parser.add_prefix("app", "A")
        self._query_parser.add_boolean_prefix("zgei", FILTER_PREFIX_EVENT_INTERPRETATION)
        self._query_parser.add_boolean_prefix("zgem", FILTER_PREFIX_EVENT_MANIFESTATION)
        self._query_parser.add_boolean_prefix("zga", FILTER_PREFIX_ACTOR)
        self._query_parser.add_prefix("zgsu", FILTER_PREFIX_SUBJECT_URI)
        self._query_parser.add_boolean_prefix("zgsi", FILTER_PREFIX_SUBJECT_INTERPRETATION)
        self._query_parser.add_boolean_prefix("zgsm", FILTER_PREFIX_SUBJECT_MANIFESTATION)
        self._query_parser.add_prefix("zgso", FILTER_PREFIX_SUBJECT_ORIGIN)
        self._query_parser.add_boolean_prefix("zgst", FILTER_PREFIX_SUBJECT_MIMETYPE)
        self._query_parser.add_boolean_prefix("zgss", FILTER_PREFIX_SUBJECT_STORAGE)
        self._query_parser.add_prefix("category", FILTER_PREFIX_XDG_CATEGORY)
        self._query_parser.add_valuerangeprocessor(
              xapian.NumberValueRangeProcessor(VALUE_EVENT_ID, "id", True))
        self._query_parser.add_valuerangeprocessor(
              xapian.NumberValueRangeProcessor(VALUE_TIMESTAMP, "ms", False))
        self._query_parser.set_default_op(xapian.Query.OP_AND)
        self._enquire = xapian.Enquire(self._index)
        
        self._desktops = {}
        
        gobject.threads_init()
        self._may_run = True
        self._queue = Queue(0)
        self._worker = threading.Thread(target=self._worker_thread,
                                        name="IndexWorker")
        self._worker.daemon = True
        
        # We need to defer the index checking until after ZG has completed
        # full setup. Hence the idle handler.
        # We also don't start the worker until after we've checked the index
        gobject.idle_add (self._check_index_and_start_worker)

    @synchronized (INDEX_LOCK)
    def _check_index_and_start_worker (self):
        """
        Check whether we need a rebuild of the index.
        Returns True if the index is good. False if a reindexing has
        been commenced.
        
        This method should be called from the main thread and only once.
        It starts the worker thread as a side effect.

        We are clearing the queue, because there may be a race when an
        event insertion / deletion is already queued and our index
        is corrupted. Creating a new queue instance should be safe,
        because we're running in main thread as are the index_event
        and delete_event methods, and the worker thread wasn't yet
        started.
        """
        if self._index.get_metadata("fts_index_version") != INDEX_VERSION:
            log.info("Index must be upgraded. Doing full rebuild")
            self._queue = Queue(0)
            self._queue.put(Reindex(self))
        elif self._index.get_doccount() == 0:
            # If the index is empty we trigger a rebuild
            # We must delay reindexing until after the engine is done setting up
            log.info("Empty index detected. Doing full rebuild")
            self._queue = Queue(0)
            self._queue.put(Reindex(self))
        
        # Now that we've checked the index from the main thread we can start the worker
        self._worker.start()
    
    def index_event (self, event):
        """
        This method schedules and event for indexing. It returns immediate and
        defers the actual work to a bottom half thread. This means that it
        will not block the main loop of the Zeitgeist daemon while indexing
        (which may be a heavy operation)
        """
        self._queue.put (event)
        return event
    
    def delete_event (self, event_id):
        """
        Remove an event from the index given its event id
        """
        self._queue.put (Deletion(event_id))
        return        
    
    @synchronized (INDEX_LOCK)
    def search (self, query_string, time_range=None, filters=None, offset=0, maxhits=10, result_type=100):
        """
        Do a full text search over the indexed corpus. The `result_type`
        parameter may be a zeitgeist.datamodel.ResultType or 100. In case it is
        100 the textual relevancy of the search engine will be used to sort the
        results. Result type 100 is the fastest (and default) mode.
        
        The filters argument should be a list of event templates.
        """
        # Expand event template filters if necessary
        if filters:
            query_string = "(%s) AND (%s)" % (query_string, self._compile_event_filter_query (filters))
        
        # Expand time range value query
        if time_range and not time_range.is_always():
            query_string = "(%s) AND (%s)" % (query_string, self._compile_time_range_filter_query (time_range))
        
        # If the result type coalesces the events we need to fetch some extra
        # events from the index to have a chance of actually holding 'maxhits'
        # unique events
        if result_type in COALESCING_RESULT_TYPES:
            raw_maxhits = maxhits * 3
        else:
            raw_maxhits = maxhits
        
        # When not sorting by relevance, we fetch the results from Xapian sorted,
        # by timestamp. That minimizes the skew we get from otherwise doing a
        # relevancy ranked xapaian query and then resorting with Zeitgeist. The
        # "skew" is that low-relevancy results may still have the highest timestamp
        if result_type == 100:
          self._enquire.set_sort_by_relevance()
        else:
          self._enquire.set_sort_by_value(VALUE_TIMESTAMP, True)
        
        # Allow wildcards
        query_start = time.time()
        query = self._query_parser.parse_query (query_string,
                                                self.QUERY_PARSER_FLAGS)
        self._enquire.set_query (query)
        hits = self._enquire.get_mset (offset, raw_maxhits)
        hit_count = hits.get_matches_estimated()
        log.debug("Search '%s' gave %s hits in %sms" %
                  (query_string, hits.get_matches_estimated(), (time.time() - query_start)*1000))
        
        if result_type == 100:
            event_ids = []
            for m in hits:
                event_id = int(xapian.sortable_unserialise(
                                          m.document.get_value(VALUE_EVENT_ID)))                
                event_ids.append (event_id)
            if event_ids:
                return self.get_events(event_ids), hit_count
            else:
                return [], 0
        else:
            templates = []
            for m in hits:
                event_id = int(xapian.sortable_unserialise(
                                          m.document.get_value(VALUE_EVENT_ID)))
                ev = Event()
                ev[0][Event.Id] = str(event_id)
                templates.append(ev)
            if templates:
                x = self._find_events(1, TimeRange.always(),
                                                 templates,
                                                 StorageState.Any,
                                                 maxhits,
                                                 result_type), hit_count
                return x
            else:
                return [], 0
    
    def _worker_thread (self):
        is_dirty = False
        while self._may_run:
            # FIXME: Throttle IO and CPU
            try:
                # If we are dirty wait a while before we flush,
                # or if we are clean wait indefinitely to avoid
                # needless wakeups
                if is_dirty:
                    event = self._queue.get(True, 0.5)
                else:
                    event = self._queue.get(True)
                
                if isinstance (event, Deletion):
                    self._delete_event_real (event.event_id)
                elif isinstance (event, Reindex):
                    self._reindex (event.all_events)
                else:
                    self._index_event_real (event)
                
                is_dirty = True
            except Empty:
                if is_dirty:
                    # Write changes to disk
                    log.debug("Committing FTS index")
                    self._index.flush()
                    is_dirty = False
                else:
                    log.debug("No changes to index. Sleeping")
    
    @synchronized (INDEX_LOCK)
    def _reindex (self, event_list):
        """
        Index everything in the ZG log. The argument must be a list
        of events. Typically extracted by a Reindex instance.
        Only call from worker thread as it writes to the db and Xapian
        is *not* thread safe (only single-writer-multiple-reader).
        """
        self._index.close ()
        self._index = xapian.WritableDatabase(INDEX_FILE, xapian.DB_CREATE_OR_OVERWRITE)
        self._query_parser.set_database (self._index)
        self._enquire = xapian.Enquire(self._index)
        # Register that this index was built with CJK enabled
        self._index.set_metadata("fts_index_version", INDEX_VERSION)
        log.info("Preparing to rebuild index with %s events" % len(event_list))
        for e in event_list : self._queue.put(e)
    
    @synchronized (INDEX_LOCK)
    def _delete_event_real (self, event_id):
        """
        Look up the doc id given an event id and remove the xapian.Document
        for that doc id.
        Note: This is slow, but there's not much we can do about it
        """
        try:
            _id = xapian.sortable_serialise(float(event_id))
            query = xapian.Query(xapian.Query.OP_VALUE_RANGE, 
                                 VALUE_EVENT_ID, _id, _id)
            
            self._enquire.set_query (query)
            hits = self._enquire.get_mset (0, 10)
            
            total = hits.get_matches_estimated()
            if total > 1:
                log.warning ("More than one event found with id '%s'" % event_id)
            elif total <= 0:
                log.debug ("No event for id '%s'" % event_id)
                return
        
            for m in hits:
                log.debug("Deleting event '%s' with docid '%s'" %
                          (event_id, m.docid))
                self._index.delete_document(m.docid)
        except Exception, e:
            log.error("Failed to delete event '%s': %s" % (event_id, e))
        
    def _split_uri (self, uri):
        """
        Returns a triple of (scheme, host, and path) extracted from `uri`
        """        
        i = uri.find(":")
        if i == -1 :
            scheme =  ""
            host = ""
            path = uri
        else:
            scheme = uri[:i]
            host = ""
            path = ""
          
        if uri[i+1] == "/" and uri[i+2] == "/":
            j = uri.find("/", i+3)
            if j == -1 :
                host = uri[i+3:]
            else:
                host = uri[i+3:j]
                path = uri[j:]
        else:
            host = uri[i+1:]
        
        # Strip out URI query part
        i = path.find("?")
        if i != -1:
            path = path[:i]
        
        return scheme, host, path
    
    def _get_desktop_entry (self, app_id):
        """
        Return a xdg.DesktopEntry.DesktopEntry `app_id` or None in case
        no file is found for the given desktop id
        """
        if app_id in self._desktops:
            return self._desktops[app_id]
        
        for datadir in xdg_data_dirs:
            path = os.path.join(datadir, "applications", app_id)
            if os.path.exists(path):
                try:
                    desktop = DesktopEntry(path)
                    self._desktops[app_id] = desktop
                    return desktop
                except Exception, e:
                    log.warning("Unable to load %s: %s" % (path, e))
                    return None
        
        return None
    
    def _index_actor (self, actor):
        """
        Takes an actor as a path to a .desktop file or app:// uri
        and index the contents of the corresponding .desktop file
        into the document currently set for self._tokenizer.
        """
        if not actor : return
        
        # Get the path of the .desktop file and convert it to
        # an app id (eg. 'gedit.desktop')
        scheme, host, path = self._split_uri(url_unescape (actor))
        if not path:
            path = host
        
        if not path :
            log.debug("Unable to determine application id for %s" % actor)
            return
        
        if path.startswith("/") :
            path = os.path.basename(path)
        
        desktop = self._get_desktop_entry(path)
        if desktop:
            if not desktop.getNoDisplay():
                self._tokenizer.index_text(desktop.getName(), 5)
                self._tokenizer.index_text(desktop.getName(), 5, "A")
                self._tokenizer.index_text(desktop.getGenericName(), 5)
                self._tokenizer.index_text(desktop.getGenericName(), 5, "A")
                self._tokenizer.index_text(desktop.getComment(), 2)
                self._tokenizer.index_text(desktop.getComment(), 2, "A")
            
                doc = self._tokenizer.get_document()
                for cat in desktop.getCategories():
                    doc.add_boolean_term(FILTER_PREFIX_XDG_CATEGORY+cat.lower())
        else:
            log.debug("Unable to look up app info for %s" % actor)
        
    
    def _index_uri (self, uri):
        """
        Index `uri` into the document currectly set on self._tokenizer
        """
        # File URIs and paths are indexed in one way, and all other,
        # usually web URIs, are indexed in another way because there may
        # be domain name etc. in there we want to rank differently
        scheme, host, path = self._split_uri (url_unescape (uri))
        if scheme == "file" or not scheme:
            path, name = os.path.split(path)
            self._tokenizer.index_text(name, 5)
            self._tokenizer.index_text(name, 5, "N")
            
            # Index parent names with descending weight
            weight = 5
            while path and name:
                weight = weight / 1.5
                path, name = os.path.split(path)
                self._tokenizer.index_text(name, int(weight))
            
        elif scheme == "mailto":
            tokens = host.split("@")
            name = tokens[0]
            self._tokenizer.index_text(name, 6)
            if len(tokens) > 1:
                self._tokenizer.index_text(" ".join[1:], 1)
        else:
            # We're cautious about indexing the path components of
            # non-file URIs as some websites practice *extremely* long
            # and useless URLs
            path, name = os.path.split(path)
            if len(name) > 30 : name = name[:30]
            if len(path) > 30 : path = path[30]
            if name:
                self._tokenizer.index_text(name, 5)
                self._tokenizer.index_text(name, 5, "N")
            if path:
                self._tokenizer.index_text(path, 1)
                self._tokenizer.index_text(path, 1, "N")
            if host:
                self._tokenizer.index_text(host, 2)
                self._tokenizer.index_text(host, 2, "N")
                self._tokenizer.index_text(host, 2, "S")
    
    def _index_text (self, text):
        """
        Index `text` as raw text data for the document currently
        set on self._tokenizer. The text is assumed to be a primary
        description of the subject, such as the basename of a file.
        
        Primary use is for subject.text
        """
        self._tokenizer.index_text(text, 5)
    
    def _index_contents (self, uri):
        # xmlindexer doesn't extract words for URIs only for file paths
        
        # FIXME: IONICE and NICE on xmlindexer
        
        path = uri.replace("file://", "")
        xmlindexer = subprocess.Popen(['xmlindexer', path],
                                      stdout=subprocess.PIPE)
        xml = xmlindexer.communicate()[0].strip()
        xmlindexer.wait()        
        
        dom = minidom.parseString(xml)
        text_nodes = dom.getElementsByTagName("text")
        lines = []
        if text_nodes:
            for line in text_nodes[0].childNodes:
                lines.append(line.data)
        
        if lines:
                self._tokenizer.index_text (" ".join(lines))
        
    
    def _add_doc_filters (self, event, doc):
        """Adds the filtering rules to the doc. Filtering rules will
           not affect the relevancy ranking of the event/doc"""
        if event.interpretation:
            doc.add_boolean_term (cap_string(FILTER_PREFIX_EVENT_INTERPRETATION+event.interpretation))
        if event.manifestation:
            doc.add_boolean_term (cap_string(FILTER_PREFIX_EVENT_MANIFESTATION+event.manifestation))
        if event.actor:
            doc.add_boolean_term (cap_string(FILTER_PREFIX_ACTOR+mangle_uri(event.actor)))
        
        for su in event.subjects:
            if su.uri:
                doc.add_boolean_term (cap_string(FILTER_PREFIX_SUBJECT_URI+mangle_uri(su.uri)))
            if su.interpretation:
                doc.add_boolean_term (cap_string(FILTER_PREFIX_SUBJECT_INTERPRETATION+su.interpretation))
            if su.manifestation:
                doc.add_boolean_term (cap_string(FILTER_PREFIX_SUBJECT_MANIFESTATION+su.manifestation))
            if su.origin:
                doc.add_boolean_term (cap_string(FILTER_PREFIX_SUBJECT_ORIGIN+mangle_uri(su.origin)))
            if su.mimetype:
                doc.add_boolean_term (cap_string(FILTER_PREFIX_SUBJECT_MIMETYPE+su.mimetype))
            if su.storage:
                doc.add_boolean_term (cap_string(FILTER_PREFIX_SUBJECT_STORAGE+su.storage))
    
    @synchronized (INDEX_LOCK)
    def _index_event_real (self, event):
        if not isinstance (event, OrigEvent):
            log.error("Not an Event, found: %s" % type(event))
        if not event.id:
            log.warning("Not indexing event. Event has no id")
            return
        
        try:
            doc = xapian.Document()
            doc.add_value (VALUE_EVENT_ID,
                           xapian.sortable_serialise(float(event.id)))
            doc.add_value (VALUE_TIMESTAMP,
                           xapian.sortable_serialise(float(event.timestamp)))
            self._tokenizer.set_document (doc)
        
            self._index_actor (event.actor)
        
            for subject in event.subjects:
                if not subject.uri : continue
                
                # By spec URIs can have arbitrary length. In reality that's just silly.
                # The general online "rule" is to keep URLs less than 2k so we just
                # choose to enforce that
                if len(subject.uri) > 2000:
                    log.info ("URI too long (%s). Discarding: %s..."% (len(subject.uri), subject.uri[:30]))
                    return
                log.debug("Indexing '%s'" % subject.uri)
                
                self._index_uri (subject.uri)
                self._index_text (subject.text)
                
                # If the subject URI is an actor, we index the .desktop also
                if subject.uri.startswith ("application://"):
                    self._index_actor (subject.uri)
                
                # File contents indexing disabled for now...
                #self._index_contents (subject.uri)
                
                # FIXME: Possibly index payloads when we have apriori knowledge
            
            self._add_doc_filters (event, doc)    
            self._index.add_document (doc)
        
        except Exception, e:
            log.error("Error indexing event: %s" % e)

    def _compile_event_filter_query (self, events):
        """Takes a list of event templates and compiles a filter query
           based on their, interpretations, manifestations, and actor,
           for event and subjects.
           
           All fields within the same event will be ANDed and each template
           will be ORed with the others. Like elsewhere in Zeitgeist the
           type tree of the interpretations and manifestations will be expanded
           to match all child symbols as well
        """
        query = []
        for event in events:
            if not isinstance(event, Event):
                raise TypeError("Expected Event. Found %s" % type(event))
            
            tmpl = []
            if event.interpretation :
                tmpl.append(expand_type("zgei", event.interpretation))
            if event.manifestation :
                tmpl.append(expand_type("zgem", event.manifestation))
            if event.actor : tmpl.append("zga:%s" % mangle_uri(event.actor))
            for su in event.subjects:
                if su.uri :
                    tmpl.append("zgsu:%s" % mangle_uri(su.uri))
                if su.interpretation :
                    tmpl.append(expand_type("zgsi", su.interpretation))
                if su.manifestation :
                    tmpl.append(expand_type("zgsm", su.manifestation))
                if su.origin :
                    tmpl.append("zgso:%s" % mangle_uri(su.origin))
                if su.mimetype :
                    tmpl.append("zgst:%s" % su.mimetype)
                if su.storage :
                    tmpl.append("zgss:%s" % su.storage)
            
            tmpl = "(" + ") AND (".join(tmpl) + ")"
            query.append(tmpl)
        
        return " OR ".join(query)
    
    def _compile_time_range_filter_query (self, time_range):
        """Takes a TimeRange and compiles a range query for it"""
        
        if not isinstance(time_range, TimeRange):
            raise TypeError("Expected TimeRange, but found %s" % type(time_range))
        
        return "%s..%sms" % (time_range.begin, time_range.end)
    
    def _get_event_from_row(self, row):
        event = Event()
        event[0][Event.Id] = row["id"] # Id property is read-only in the public API
        event.timestamp = row["timestamp"]
        for field in ("interpretation", "manifestation", "actor"):
            # Try to get event attributes from row using the attributed field id
            # If attribute does not exist we break the attribute fetching and return
            # None instead of of crashing
            try:
                setattr(event, field, getattr(self, "_" + field).value(row[field]))
            except KeyError, e:
                log.error("Event %i broken: Table %s has no id %i" \
                        %(row["id"], field, row[field]))
                return None
        event.origin = row["event_origin_uri"] or ""
        event.payload = row["payload"] or "" # default payload: empty string
        return event
    
    def _get_subject_from_row(self, row):
        subject = Subject()
        for field in ("uri", "text", "storage"):
            setattr(subject, field, row["subj_" + field])
        subject.origin = row["subj_origin_uri"]
        if row["subj_current_uri"]:
            subject.current_uri = row["subj_current_uri"]
        for field in ("interpretation", "manifestation", "mimetype"):
            # Try to get subject attributes from row using the attributed field id
            # If attribute does not exist we break the attribute fetching and return
            # None instead of crashing
            try:
                setattr(subject, field,
                    getattr(self, "_" + field).value(row["subj_" + field]))
            except KeyError, e:
                log.error("Event %i broken: Table %s has no id %i" \
                        %(row["id"], field, row["subj_" + field]))
                return None
        return subject
    
    def get_events(self, ids, sender=None):
        """
        Look up a list of events.
        """
        
        t = time.time()
        
        if not ids:
            return []
        
        # Split ids into cached and uncached
        uncached_ids = array("i")
        cached_ids = array("i")
        
        # If ids batch greater than MAX_CACHE_BATCH_SIZE ids ignore cache
        use_cache = True
        if len(ids) > MAX_CACHE_BATCH_SIZE:
            use_cache = False
        if not use_cache:
            uncached_ids = ids
        else:
            for id in ids:
                if id in self._event_cache:
                    cached_ids.append(id)
                else:
                    uncached_ids.append(id)
        
        id_hash = defaultdict(lambda: array("i"))
        for n, id in enumerate(ids):
            # the same id can be at multible places (LP: #673916)
            # cache all of them
            id_hash[id].append(n)
        
        # If we are not able to get an event by the given id
        # append None instead of raising an Error. The client
        # might simply have requested an event that has been
        # deleted
        events = {}
        sorted_events = [None]*len(ids)
        
        for id in cached_ids:
            event = self._event_cache[id]
            if event:
                if event is not None:
                    for n in id_hash[event.id]:
                        # insert the event into all necessary spots (LP: #673916)
                        sorted_events[n] = event
        
        # Get uncached events
        rows = self._cursor.execute("""
            SELECT * FROM event_view
            WHERE id IN (%s)
            """ % ",".join("%d" % _id for _id in uncached_ids))
        
        time_get_uncached = time.time() - t
        t = time.time()
        
        t_get_event = 0
        t_get_subject = 0
        t_apply_get_hooks = 0
        
        row_counter = 0
        for row in rows:
            row_counter += 1
            # Assumption: all rows of a same event for its different
            # subjects are in consecutive order.
            t_get_event -= time.time()
            event = self._get_event_from_row(row)
            t_get_event += time.time()
            
            if event:
                # Check for existing event.id in event to attach 
                # other subjects to it
                if event.id not in events:
                    events[event.id] = event
                else:
                    event = events[event.id]
                    
                t_get_subject -= time.time()
                subject = self._get_subject_from_row(row)
                t_get_subject += time.time()
                # Check if subject has a proper value. If none than something went
                # wrong while trying to fetch the subject from the row. So instead
                # of failing and raising an error. We silently skip the event.
                if subject:
                    event.append_subject(subject)
                    if use_cache and not event.payload:
                        self._event_cache[event.id] = event
                    if event is not None:
                        for n in id_hash[event.id]:
                            # insert the event into all necessary spots (LP: #673916)
                            sorted_events[n] = event
                    # Avoid caching events with payloads to have keep the cache MB size 
                    # at a decent level
                    

        log.debug("Got %d raw events in %fs" % (row_counter, time_get_uncached))
        log.debug("Got %d events in %fs" % (len(sorted_events), time.time()-t))
        log.debug("    Where time spent in _get_event_from_row in %fs" % (t_get_event))
        log.debug("    Where time spent in _get_subject_from_row in %fs" % (t_get_subject))
        log.debug("    Where time spent in apply_get_hooks in %fs" % (t_apply_get_hooks))
        return sorted_events
    
    def _find_events(self, return_mode, time_range, event_templates,
        storage_state, max_events, order, sender=None):
        """
        Accepts 'event_templates' as either a real list of Events or as
        a list of tuples (event_data, subject_data) as we do in the
        DBus API.
        
        Return modes:
         - 0: IDs.
         - 1: Events.
        """
        t = time.time()
        
        where = self._build_sql_event_filter(time_range, event_templates,
            storage_state)
        
        if not where.may_have_results():
            return []
        
        if return_mode == 0:
            sql = "SELECT DISTINCT id FROM event_view"
        elif return_mode == 1:
            sql = "SELECT id FROM event_view"
        else:
            raise NotImplementedError, "Unsupported return_mode."
        
        wheresql = " WHERE %s" % where.sql if where else ""
        
        def group_and_sort(field, wheresql, time_asc=False, count_asc=None,
            aggregation_type='max'):
            
            args = {
                'field': field,
                'aggregation_type': aggregation_type,
                'where_sql': wheresql,
                'time_sorting': 'ASC' if time_asc else 'DESC',
                'aggregation_sql': '',
                'order_sql': '',
            }
            
            if count_asc is not None:
                args['aggregation_sql'] = ', COUNT(%s) AS num_events' % \
                    field
                args['order_sql'] = 'num_events %s,' % \
                    ('ASC' if count_asc else 'DESC')
            
            return """
                NATURAL JOIN (
                    SELECT %(field)s,
                        %(aggregation_type)s(timestamp) AS timestamp
                        %(aggregation_sql)s
                    FROM event_view %(where_sql)s
                    GROUP BY %(field)s)
                GROUP BY %(field)s
                ORDER BY %(order_sql)s timestamp %(time_sorting)s
                """ % args
        
        if order == ResultType.MostRecentEvents:
            sql += wheresql + " ORDER BY timestamp DESC"
        elif order == ResultType.LeastRecentEvents:
            sql += wheresql + " ORDER BY timestamp ASC"
        elif order == ResultType.MostRecentEventOrigin:
            sql += group_and_sort("origin", wheresql, time_asc=False)
        elif order == ResultType.LeastRecentEventOrigin:
            sql += group_and_sort("origin", wheresql, time_asc=True)
        elif order == ResultType.MostPopularEventOrigin:
            sql += group_and_sort("origin", wheresql, time_asc=False,
                count_asc=False)
        elif order == ResultType.LeastPopularEventOrigin:
            sql += group_and_sort("origin", wheresql, time_asc=True,
                count_asc=True)
        elif order == ResultType.MostRecentSubjects:
            # Remember, event.subj_id identifies the subject URI
            sql += group_and_sort("subj_id", wheresql, time_asc=False)
        elif order == ResultType.LeastRecentSubjects:
            sql += group_and_sort("subj_id", wheresql, time_asc=True)
        elif order == ResultType.MostPopularSubjects:
            sql += group_and_sort("subj_id", wheresql, time_asc=False,
                count_asc=False)
        elif order == ResultType.LeastPopularSubjects:
            sql += group_and_sort("subj_id", wheresql, time_asc=True,
                count_asc=True)
        elif order == ResultType.MostRecentCurrentUri:
            sql += group_and_sort("subj_id_current", wheresql, time_asc=False)
        elif order == ResultType.LeastRecentCurrentUri:
            sql += group_and_sort("subj_id_current", wheresql, time_asc=True)
        elif order == ResultType.MostPopularCurrentUri:
            sql += group_and_sort("subj_id_current", wheresql, time_asc=False,
                count_asc=False)
        elif order == ResultType.LeastPopularCurrentUri:
            sql += group_and_sort("subj_id_current", wheresql, time_asc=True,
                count_asc=True)
        elif order == ResultType.MostRecentActor:
            sql += group_and_sort("actor", wheresql, time_asc=False)
        elif order == ResultType.LeastRecentActor:
            sql += group_and_sort("actor", wheresql, time_asc=True)
        elif order == ResultType.MostPopularActor:
            sql += group_and_sort("actor", wheresql, time_asc=False,
                count_asc=False)
        elif order == ResultType.LeastPopularActor:
            sql += group_and_sort("actor", wheresql, time_asc=True,
                count_asc=True)
        elif order == ResultType.OldestActor:
            sql += group_and_sort("actor", wheresql, time_asc=True,
                aggregation_type="min")
        elif order == ResultType.MostRecentOrigin:
            sql += group_and_sort("subj_origin", wheresql, time_asc=False)
        elif order == ResultType.LeastRecentOrigin:
            sql += group_and_sort("subj_origin", wheresql, time_asc=True)
        elif order == ResultType.MostPopularOrigin:
            sql += group_and_sort("subj_origin", wheresql, time_asc=False,
                count_asc=False)
        elif order == ResultType.LeastPopularOrigin:
            sql += group_and_sort("subj_origin", wheresql, time_asc=True,
                count_asc=True)
        elif order == ResultType.MostRecentSubjectInterpretation:
            sql += group_and_sort("subj_interpretation", wheresql,
                time_asc=False)
        elif order == ResultType.LeastRecentSubjectInterpretation:
            sql += group_and_sort("subj_interpretation", wheresql,
                time_asc=True)
        elif order == ResultType.MostPopularSubjectInterpretation:
            sql += group_and_sort("subj_interpretation", wheresql,
                time_asc=False, count_asc=False)
        elif order == ResultType.LeastPopularSubjectInterpretation:
            sql += group_and_sort("subj_interpretation", wheresql,
                time_asc=True, count_asc=True)
        elif order == ResultType.MostRecentMimeType:
            sql += group_and_sort("subj_mimetype", wheresql, time_asc=False)
        elif order == ResultType.LeastRecentMimeType:
            sql += group_and_sort("subj_mimetype", wheresql, time_asc=True)
        elif order == ResultType.MostPopularMimeType:
            sql += group_and_sort("subj_mimetype", wheresql, time_asc=False,
                count_asc=False)
        elif order == ResultType.LeastPopularMimeType:
            sql += group_and_sort("subj_mimetype", wheresql, time_asc=True,
                count_asc=True)
        
        if max_events > 0:
            sql += " LIMIT %d" % max_events
        result = array("i", self._cursor.execute(sql, where.arguments).fetch(0))
        
        if return_mode == 0:
            log.debug("Found %d event IDs in %fs" % (len(result), time.time()- t))
        elif return_mode == 1:
            log.debug("Found %d events in %fs" % (len(result), time.time()- t))
            result = self.get_events(ids=result, sender=sender)    
        else:
            raise Exception("%d" % return_mode)
        
        return result
        
    @staticmethod
    def _build_templates(templates):
        for event_template in templates:
            event_data = event_template[0]
            for subject in (event_template[1] or (Subject(),)):
                yield Event((event_data, [], None)), Subject(subject)
    
    def _build_sql_from_event_templates(self, templates):
    
        where_or = WhereClause(WhereClause.OR)
        
        for template in templates:
            event_template = Event((template[0], [], None))
            if template[1]:
                subject_templates = [Subject(data) for data in template[1]]
            else:
                subject_templates = None
            
            subwhere = WhereClause(WhereClause.AND)
            
            if event_template.id:
                subwhere.add("id = ?", event_template.id)
            
            try:
                value, negation, wildcard = parse_operators(Event, Event.Interpretation, event_template.interpretation)
                # Expand event interpretation children
                event_interp_where = WhereClause(WhereClause.OR, negation)
                for child_interp in (Symbol.find_child_uris_extended(value)):
                    if child_interp:
                        event_interp_where.add_text_condition("interpretation",
                                               child_interp, like=wildcard, cache=self._interpretation)
                if event_interp_where:
                    subwhere.extend(event_interp_where)
                
                value, negation, wildcard = parse_operators(Event, Event.Manifestation, event_template.manifestation)
                # Expand event manifestation children
                event_manif_where = WhereClause(WhereClause.OR, negation)
                for child_manif in (Symbol.find_child_uris_extended(value)):
                    if child_manif:
                        event_manif_where.add_text_condition("manifestation",
                                              child_manif, like=wildcard, cache=self._manifestation)
                if event_manif_where:
                    subwhere.extend(event_manif_where)
                
                value, negation, wildcard = parse_operators(Event, Event.Actor, event_template.actor)
                if value:
                    subwhere.add_text_condition("actor", value, wildcard, negation, cache=self._actor)
                
                value, negation, wildcard = parse_operators(Event, Event.Origin, event_template.origin)
                if value:
                    subwhere.add_text_condition("origin", value, wildcard, negation)
                
                if subject_templates is not None:
                    for subject_template in subject_templates:
                        value, negation, wildcard = parse_operators(Subject, Subject.Interpretation, subject_template.interpretation)
                        # Expand subject interpretation children
                        su_interp_where = WhereClause(WhereClause.OR, negation)
                        for child_interp in (Symbol.find_child_uris_extended(value)):
                            if child_interp:
                                su_interp_where.add_text_condition("subj_interpretation",
                                                    child_interp, like=wildcard, cache=self._interpretation)
                        if su_interp_where:
                            subwhere.extend(su_interp_where)
                        
                        value, negation, wildcard = parse_operators(Subject, Subject.Manifestation, subject_template.manifestation)
                        # Expand subject manifestation children
                        su_manif_where = WhereClause(WhereClause.OR, negation)
                        for child_manif in (Symbol.find_child_uris_extended(value)):
                            if child_manif:
                                su_manif_where.add_text_condition("subj_manifestation",
                                                   child_manif, like=wildcard, cache=self._manifestation)
                        if su_manif_where:
                            subwhere.extend(su_manif_where)
                        
                        # FIXME: Expand mime children as well.
                        # Right now we only do exact matching for mimetypes
                        # thekorn: this will be fixed when wildcards are supported
                        value, negation, wildcard = parse_operators(Subject, Subject.Mimetype, subject_template.mimetype)
                        if value:
                            subwhere.add_text_condition("subj_mimetype",
                                         value, wildcard, negation, cache=self._mimetype)
                
                        for key in ("uri", "origin", "text"):
                            value = getattr(subject_template, key)
                            if value:
                                value, negation, wildcard = parse_operators(Subject, getattr(Subject, key.title()), value)
                                subwhere.add_text_condition("subj_%s" % key, value, wildcard, negation)
                        
                        if subject_template.current_uri:
                            value, negation, wildcard = parse_operators(Subject,
                                Subject.CurrentUri, subject_template.current_uri)
                            subwhere.add_text_condition("subj_current_uri", value, wildcard, negation)
                        
                        if subject_template.storage:
                            subwhere.add_text_condition("subj_storage", subject_template.storage)
                        
            except KeyError, e:
                # Value not in DB
                log.debug("Unknown entity in query: %s" % e)
                where_or.register_no_result()
                continue
            where_or.extend(subwhere) 
        return where_or
    
    def _build_sql_event_filter(self, time_range, templates, storage_state):
        
        where = WhereClause(WhereClause.AND)
        
        # thekorn: we are using the unary operator here to tell sql to not use
        # the index on the timestamp column at the first place. This `fix` for
        # (LP: #672965) is based on some benchmarks, which suggest a performance
        # win, but we might not oversee all implications.
        # (see http://www.sqlite.org/optoverview.html section 6.0)
        min_time, max_time = time_range
        if min_time != 0:
            where.add("+timestamp >= ?", min_time)
        if max_time != sys.maxint:
            where.add("+timestamp <= ?", max_time)
        
        if storage_state in (StorageState.Available, StorageState.NotAvailable):
            where.add("(subj_storage_state = ? OR subj_storage_state IS NULL)",
                storage_state)
        elif storage_state != StorageState.Any:
            raise ValueError, "Unknown storage state '%d'" % storage_state
        
        where.extend(self._build_sql_from_event_templates(templates))
        
        return where

if __name__ == "__main__":
    mainloop = gobject.MainLoop(is_running=True)
    search_engine = SearchEngineExtension()
    ZG_CLIENT._iface.connect_exit(lambda: mainloop.quit ())
    mainloop.run()

