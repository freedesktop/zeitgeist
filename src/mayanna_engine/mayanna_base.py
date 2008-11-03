import datetime
import string
import time

from gettext import ngettext, gettext as _
from xml.sax import saxutils
import gobject
import gtk
import gc

from mayanna_util import Thumbnailer, bookmarks, icon_factory, launcher

class Item(gobject.GObject):
    __gsignals__ = {
        "reload" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        "open" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        }

    def __init__(self,
                 uri = None,
                 name = None,
                 comment = None,
                 timestamp = 0,
                 mimetype = None,
                 icon = None,
                 special = False,
                 tags = None):
        gobject.GObject.__init__(self)
        self.uri = uri
        self.name = name
        self.comment = comment
        self.timestamp = timestamp
        
        self.time =  datetime.datetime.fromtimestamp(self.timestamp).strftime(_(" %l:%M:%S %p"))
        self.day =  datetime.datetime.fromtimestamp(self.timestamp).strftime(_(" %d"))
        self.weekday =  datetime.datetime.fromtimestamp(self.timestamp).strftime(_(" %a"))
        self.month =  datetime.datetime.fromtimestamp(self.timestamp).strftime(_(" %b"))
        self.cmonth = datetime.datetime.fromtimestamp(self.timestamp).strftime(_(" %m"))
        self.year =  datetime.datetime.fromtimestamp(self.timestamp).strftime(_(" %Y"))
        self.date =  datetime.datetime.fromtimestamp(self.timestamp).strftime(_(" %x"))
        self.datestring =  self.weekday+" "+self.day+" "+self.month+" "+self.year
        
        self.ctimestamp = int(string.replace(self.year+self.cmonth+self.day," ",""))
        
        self.mimetype = mimetype
        self.icon = icon
        self.special = special
        self.tags = tags or []
        self.thumbnailer = None
        self.type = None
        self.needs_view=False

    def get_demands_attention(self):
        return False

    def get_icon(self, icon_size):
        if self.icon:
            return icon_factory.load_icon(self.icon, icon_size)

        if not self.thumbnailer:
            self.thumbnailer = Thumbnailer(self.get_uri(), self.get_mimetype())
        return self.thumbnailer.get_icon(icon_size, self.get_timestamp())

    def get_timestamp(self):
        return self.timestamp

    def get_mimetype(self):
        return self.mimetype

    def get_uri(self):
        return self.uri

    def get_name(self):
        return self.name or self.get_uri()

    def get_comment(self):
        return self.comment

    def get_name_markup(self):
        name = saxutils.escape(self.get_name() or "")
        if self.get_is_pinned():
            name += " <span foreground='red'>&#x2665;</span>"
        return name

    def get_comment_markup(self):
        return "<span foreground='black'>%s</span>" % \
               saxutils.escape(self.get_comment() or "")

    def do_open(self):
        uri_to_open = self.get_uri()
        if uri_to_open:
            self.timestamp = time.time()
            launcher.launch_uri(uri_to_open, self.get_mimetype())
        else:
            pass
            #print " !!! Item has no URI to open: %s" % self

    def open(self):
        self.emit("open")


    def get_is_user_visible(self):
        return True

    def get_is_opened(self):
        return False


    def get_can_pin(self):
        return self.get_uri() != None

    def get_is_pinned(self):
        return bookmarks.is_bookmark(self.get_uri())

    def pin(self):
        bookmarks.add_bookmark_item(self)
        self.emit("reload")

    def unpin(self):
        bookmarks.remove_bookmark(self.get_uri())
        self.emit("reload")

    def matches_text(self, text):
        name = self.get_name()
        comment = self.get_comment()
        return (name and name.lower().find(text) > -1) or \
               (comment and comment.lower().find(text) > -1)

    def populate_popup(self, menu):
        open = gtk.ImageMenuItem (gtk.STOCK_OPEN)
        open.connect("activate", lambda w: self.open())
        open.show()
        menu.append(open)

        fav = gtk.CheckMenuItem (_("Add to Favorites"))
        fav.set_sensitive(self.get_can_pin())
        fav.set_active(self.get_is_pinned())
        fav.connect("toggled", self._add_to_favorites_toggled)
        fav.show()
        menu.append(fav)
        del fav,open
        gc.collect()

    def _add_to_favorites_toggled(self, fav):
        if fav.get_active():
            self.pin()
        else:
            self.unpin()


    def get_tooltip(self):
        return self.get_name()

    def pretty_print_time_since(self, timestamp, include_today = True):
        '''
        Format a timestamp in a readable way (for English).
        '''
        now = datetime.datetime.now()
        then = datetime.datetime.fromtimestamp(timestamp)
        if then.year == now.year:
            then_ord = then.toordinal()
            now_ord = now.toordinal()
            time_str = then.strftime(_("%l:%M %p"))
            if then_ord == now_ord:
                if include_today:
                    return _("Today, %s") % time_str
                else:
                    return time_str
            elif then_ord == now_ord - 1:
                return _("Yesterday, %s") % time_str
            elif then_ord > now_ord - 4:
                return ngettext("%d day ago, %s",
                                "%d days ago, %s",
                                now_ord - then_ord) % (now_ord - then_ord, time_str)
            elif then_ord > now_ord - 6:
                return ngettext("%d day ago",
                                "%d days ago",
                                now_ord - then_ord) % (now_ord - then_ord)
            else:
                return then.strftime(_("%B %e"))
        else:
            return then.strftime(_("%B %e, %G"))

    def handle_drag_data_received(self, selection, target_type):
        pass

    def is_special(self):
        '''
        Special items are always displayed when browsing an ItemSource,
        regardless of the active date filter.  Usually special items denote
        meta-tasks such as configuring or creating other items.
        '''
        return self.special


class ItemSource(Item):
    # Clear cached items after 4 minutes of inactivity
    CACHE_CLEAR_TIMEOUT_MS = 1000 * 60 * 4
    
    def __init__(self,
                 name = None,
                 icon = None,
                 comment = None,
                 uri = None,
                 filter_by_date = True):
        Item.__init__(self,
                      name=name,
                      icon=icon,
                      comment=comment,
                      uri=uri,
                      mimetype="mayanna/item-source")
		#self.sourceType = None
        self.filter_by_date = filter_by_date
        self.items = None
        self.clear_cache_timeout_id = None
        # Clear cached items on reload
        self.connect("reload", lambda x: self.set_items(None))
        self.hasPref = None
        self.counter = 0
        self.needs_view=True
        
    def get_items(self):
        '''
        Return cached items if available, otherwise get_items_uncached() is
        called to create a new cache, yielding each result along the way.  A
        timeout is set to invalidate the cached items to free memory.
        '''
        
        
        if self.clear_cache_timeout_id:
            gobject.source_remove(self.clear_cache_timeout_id)
        self.clear_cache_timeout_id = gobject.timeout_add(ItemSource.CACHE_CLEAR_TIMEOUT_MS, lambda: self.set_items(None))
        
        if self.items:
           return self.items
        else:
            del self.items
            gc.collect()
            self.items =self.get_items_uncached()
            return self.items


    def get_items_uncached(self):
        '''Subclasses should override this to return/yield Items. The results
        will be cached.'''
        return []

    def set_items(self, items):
        '''Set the cached items.  Pass None for items to reset the cache.'''
        self.items = items
       # delitems
        
    def get_enabled(self):
        return True

    def get_filter_by_date(self):
        '''False if consumers should avoid using timestamps to filter items, True otherwise.'''
        return self.filter_by_date


mayanna_topics = []

def mayanna_get_topic_for_uri(uri):
    for topic in mayanna_topics:
        if topic.get_uri() == uri:
            return topic
    return None

 

