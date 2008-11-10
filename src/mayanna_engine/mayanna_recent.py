import re
import sys
import gc
import urlparse
import datetime
import os
import urllib
import time
from gettext import gettext as _
import gobject
import gtk
import gnome.ui
import gnomevfs
import gnomevfs.async
from mayanna_base import Item, ItemSource

class RecentlyUsedManagerGtk(ItemSource):
    def __init__(self):
        ItemSource.__init__(self)
        self.recent_manager = gtk.recent_manager_get_default()
        self.recent_manager.set_limit(-1)
        self.recent_manager.connect("changed", lambda m: self.emit("reload"))
    def get_items_uncached(self):
        # 
       # delself.temp_list
        self.recent_list = self.recent_manager.get_items()
        for info in self.recent_list:
            if info.exists():
                if not info.get_private_hint():
                  yield Item(name=info.get_display_name(),
                           uri=info.get_uri(),
                           mimetype=info.get_mime_type(),
                           timestamp=info.get_modified(),
                           tags=info.get_groups())
        
class RecentlyUsed(ItemSource):
    '''
    Recently-used documents, log stored in ~/.recently-used.
    '''
    def __init__(self, name, icon = "stock_calendar"):
        ItemSource.__init__(self, name=name, icon=icon)
        recent_model.connect("reload", lambda m: self.emit("reload"))
        self.temp_list = []
        self.counter = 0
    
    def get_items_uncached(self):
       # 
        self.counter  =self.counter  + 1
        #print ( " getting recently used " + str(self.counter))
       # delself.temp_list
        self.temp_list = []
        for item in recent_model.get_items():
            # Check whether to include this item
            if self.include_item(item):
                yield item
    
    def include_item(self, item):
        return True

class RecentlyUsedOfMimeType(RecentlyUsed):
    '''
    Recently-used items filtered by a set of mimetypes.
    '''
    def __init__(self, name, icon, mimetype_list):
        RecentlyUsed.__init__(self, name, icon)
        self.mimetype_list = mimetype_list

    def include_item(self, item):
        item_mime = item.get_mimetype()
        for mimetype in self.mimetype_list:
            if hasattr(mimetype, "match") and mimetype.match(item_mime) \
                   or item_mime == mimetype:
                return True
        return False

class RecentAggregate(ItemSource):
    '''
    This ItemSource subclass aggregates all the items from a list of
    ItemSources, by including the first Item encountered of a URI and
    filtering duplicates.
    '''
    def __init__(self, sources, name = _("Recently Used"), icon = "stock_calendar"):
        ItemSource.__init__(self, name=name, icon=icon)

        # Sources provide the real items we will display
        self.sources = sources
        for source in self.sources:
            self._listen_to_source(source)
        self.temp_list = None
    def _listen_to_source(self, source):
        source.connect("reload", lambda x: self.emit("reload"))

    def get_items_uncached(self):
        # 
       # delself.temp_list
        item_uris = {}
        # Find items matching recent uris
        self.temp_list=[]
        for source in self.sources:
            for item in source.get_items_uncached():
                uri = item.get_uri()
                if  uri and uri not in item_uris:
                    item_uris[uri] = item
                    self.temp_list.append( item)
                    yield item
#
# Globals
#
class RecentlyUsedDocumentsSource(RecentlyUsedOfMimeType):
    ### FIXME: This is lame, we should generate this list somehow.
    DOCUMENT_MIMETYPES = [
        # Covers:
        #   vnd.corel-draw
        #   vnd.ms-powerpoint
        #   vnd.ms-excel
        #   vnd.oasis.opendocument.*
        #   vnd.stardivision.*
        #   vnd.sun.xml.*
        re.compile("application/vnd.*"),
        # Covers: x-applix-word, x-applix-spreadsheet, x-applix-presents
        re.compile("application/x-applix-*"),
        # Covers: x-kword, x-kspread, x-kpresenter, x-killustrator
        re.compile("application/x-k(word|spread|presenter|illustrator)"),
        "application/ms-powerpoint",
        "application/msword",
        "application/pdf",
        "application/postscript",
        "application/ps",
        "application/rtf",
        "application/x-abiword",
        "application/x-gnucash",
        "application/x-gnumeric",
        ]
    
    def __init__(self):
        RecentlyUsedOfMimeType.__init__(self,
                                        name=_("Documents"),
                                        icon="stock_new-presentation",
                                        mimetype_list=self.DOCUMENT_MIMETYPES)
        self.name = _("Documents")
    def get_items_uncached(self):
        temp_list=[]
        for item in RecentlyUsedOfMimeType.get_items_uncached(self):
            yield Item(uri=item.get_uri(), timestamp=item.timestamp)
           
        
class RecentlyUsedOthersSource(RecentlyUsedOfMimeType):
    ### FIXME: This is lame, we should generate this list somehow.
    DOCUMENT_MIMETYPES = [
        # Covers:
        #   vnd.corel-draw
        #   vnd.ms-powerpoint
        #   vnd.ms-excel
        #   vnd.oasis.opendocument.*
        #   vnd.stardivision.*
        #   vnd.sun.xml.*
        re.compile("text/*"),
        "application/x-asp",
        "application/x-bittorrent",
        "application/x-blender",
        "application/x-cgi",
        "application/x-dia-diagram",
        "application/x-dvi",
        "application/x-glade",
        "application/x-iso-image",
        "application/x-jbuilder-project",
        "application/x-magicpoint",
        "application/x-mrproject",
        "application/x-php",
        ]
    
    def __init__(self):
        RecentlyUsedOfMimeType.__init__(self,
                                        name=_("Other"),
                                        icon="applications-other",
                                        mimetype_list=self.DOCUMENT_MIMETYPES)
        self.name = _("Other")
    def get_items_uncached(self):
        temp_list=[]
        items = RecentlyUsedOfMimeType.get_items_uncached(self)
        for item in items:
             temp_item = Item(uri=item.get_uri(), timestamp=item.timestamp)
             temp_list.append( temp_item)
            # delitem,temp_item
         
        return temp_list
        
class RecentlyUsedImagesSource(RecentlyUsedOfMimeType):
    ### FIXME: This is lame, we should generate this list somehow.
    DOCUMENT_MIMETYPES = [
        # Covers:
        #   vnd.corel-draw
        re.compile("application/vnd.corel-draw"),
        # Covers: x-kword, x-kspread, x-kpresenter, x-killustrator
        re.compile("application/x-k(illustrator)"),
        re.compile("image/*"),
        ]
    
    def __init__(self):
        RecentlyUsedOfMimeType.__init__(self,
                                        name=_("Images"),
                                        icon="gnome-mime-image",
                                        mimetype_list=self.DOCUMENT_MIMETYPES)
        self.name = _("Images")
    
    
    def get_items_uncached(self):
        temp_list=[]
        items = RecentlyUsedOfMimeType.get_items_uncached(self)
        for item in items:
             temp_item = Item(uri=item.get_uri(), timestamp=item.timestamp)
             temp_list.append( temp_item)
            # delitem,temp_item
         
        return temp_list
        
class RecentlyUsedMusicSource(RecentlyUsedOfMimeType):
    ### FIXME: This is lame, we should generate this list somehow.
    MEDIA_MIMETYPES = [
        re.compile("audio/*"),
        "application/ogg"
        ]

    def __init__(self):
        RecentlyUsedOfMimeType.__init__(self,
                                        name=_("Music"),
                                        icon="gnome-mime-audio",
                                        mimetype_list=self.MEDIA_MIMETYPES)
        self.name = _("Music")
    def get_items_uncached(self):
        temp_list = []
        for item in RecentlyUsedOfMimeType.get_items_uncached(self):
             temp_item = Item(uri=item.get_uri(), timestamp=item.timestamp)
             temp_list.append( temp_item)
            # delitem,temp_item
         
        return temp_list
               
class RecentlyUsedVideoSource(RecentlyUsedOfMimeType):
    ### FIXME: This is lame, we should generate this list somehow.
    MEDIA_MIMETYPES = [
        re.compile("video/*"),
        "application/ogg"
        ]

    def __init__(self):
        RecentlyUsedOfMimeType.__init__(self,
                                        name=_("Movies"),
                                        icon="gnome-mime-video",
                                        mimetype_list=self.MEDIA_MIMETYPES)
        self.name = _("Movies")
    def get_items_uncached(self):
        #print("videos uncached")
        temp_list = []
        for item in RecentlyUsedOfMimeType.get_items_uncached(self):
             temp_item = Item(uri=item.get_uri(), timestamp=item.timestamp)
             temp_list.append( temp_item)
            # delitem,temp_item
         
        return temp_list


recent_model = RecentlyUsedManagerGtk()

