import datetime
import os
import pwd

from gettext import gettext as _
import gobject
import gtk
import gnomevfs
import gc
try:
    import gnomecups
except ImportError:
    gnomecups = None

#import gdmclient

from mayanna_engine.mayanna_base import Item, ItemSource
from mayanna_engine.mayanna_util import *
#from mayanna_applications import MenuTree, RecentSettingsLaunchers, LauncherItem

# FIXME: Move these to another file?
class FavoritesSource(ItemSource):
    '''
    Item source that lists all favorite items.
    '''
    def __init__(self):
        ItemSource.__init__(self,
                            name=_("All Favorites"),
                            icon="gnome-favorites",
                            uri="source://AllFavorites",
                            filter_by_date=False)
        bookmarks.connect("reload", self.pitstop_reload)

    def pitstop_reload(self,x=None):
        print("FavoritesSource::pitstop_reload")
        self.emit("reload")

    def get_items_uncached(self):
        for uri, itemclass in bookmarks.get_bookmarks_and_class():
            try:
                mod, cls = itemclass.rsplit(".", 1)
                dynmod = __import__(mod, None, None, cls)
                dyncls = getattr(dynmod, cls)
                dynobj = dyncls(uri=uri)
                name = uri.rsplit("/",1)
                dynobj.name = name[1]
                dynobj.time = ""
                yield dynobj
            except (ValueError, TypeError, ImportError, AttributeError), err:
                # ValueError - thrown by Item constructor, or strange itemclass
                # TypeError - thrown by Item not accepting uri arg
                # ImportError - error importing mod
                # AttributeError - mod doesn't contain cls
                print "Error creating %s for URI \"%s\": %s" % (itemclass, uri, err)
