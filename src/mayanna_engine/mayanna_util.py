import datetime
import os
import urllib
from gettext import gettext as _
import sys     # for ImplementMe
import inspect # for ImplementMe
import dbus
import gobject
import gtk
import gc
import gnome.ui
import gnomevfs
import gconf

class FileMonitor(gobject.GObject):
    '''
    A simple wrapper around Gnome VFS file monitors.  Emits created, deleted,
    and changed events.  Incoming events are queued, with the latest event
    cancelling prior undelivered events.
    '''
    
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
            self.type = gnomevfs.get_file_info(path).type
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
        del monitor_type

    def _clear_timeout(self, info_uri):
        try:
            gobject.source_remove(self.pending_timeouts[info_uri])
           # delself.pending_timeouts[info_uri]
        except KeyError:
            pass
        del info_uri

    def _queue_event(self, monitor_uri, info_uri, event):
        self._clear_timeout(info_uri)
        self.pending_timeouts[info_uri] = \
            gobject.timeout_add(250, self._timeout_cb, monitor_uri, info_uri, event)
        del monitor_uri, info_uri, event

    def queue_changed(self, info_uri):
        self._queue_event(self.path, info_uri, gnomevfs.MONITOR_EVENT_CHANGED)
        del info_uri
        
    def close(self):
        gnomevfs.monitor_cancel(self.monitor)
        self.monitor = None

    def _timeout_cb(self, monitor_uri, info_uri, event):
        if event in (gnomevfs.MONITOR_EVENT_METADATA_CHANGED, gnomevfs.MONITOR_EVENT_CHANGED):
            self.emit("changed", info_uri)
        elif event == gnomevfs.MONITOR_EVENT_CREATED:
            self.emit("created", info_uri)
        elif event == gnomevfs.MONITOR_EVENT_DELETED:
            self.emit("deleted", info_uri)
        self.emit("event", info_uri, event)

        self._clear_timeout(info_uri)
        del monitor_uri, info_uri, event
        return False

class IconFactory:
    '''
    Icon lookup swiss-army knife (from menutreemodel.py)
    '''
    def load_icon_from_path(self, icon_path, icon_size = None):
        try:
            if icon_size:
                pic = gtk.gdk.pixbuf_new_from_file_at_size(icon_path, -1, int(icon_size))
                return pic
            else:
                pic =  gtk.gdk.pixbuf_new_from_file(icon_path)
                return pic
        except:
            pass
        return None

    def load_icon_from_data_dirs(self, icon_value, icon_size = None):
        data_dirs = None
        if os.environ.has_key("XDG_DATA_DIRS"):
            data_dirs = os.environ["XDG_DATA_DIRS"]
        if not data_dirs:
            data_dirs = "/usr/local/share/:/usr/share/"

        for data_dir in data_dirs.split(":"):
            retval = self.load_icon_from_path(os.path.join(data_dir, "pixmaps", icon_value),
                                              icon_size)
            if retval:
                del icon_value,icon_size,data_dir,data_dirs
                return retval
            
            retval = self.load_icon_from_path(os.path.join(data_dir, "icons", icon_value),
                                              icon_size)
            if retval:
                del icon_value,icon_size,data_dir,data_dirs
                return retval
            
            del retval,data_dir
            
        del data_dirs
        return None

    def load_icon(self, icon_value, icon_size, force_size = True):
	
        try:
    		assert icon_value, "No icon to load!"
    
    		if isinstance(icon_value, gtk.gdk.Pixbuf):
    		    return icon_value
    
    		if os.path.isabs(icon_value):
    		    icon = self.load_icon_from_path(icon_value, icon_size)
    		    if icon:
    		        return icon
    		    icon_name = os.path.basename(icon_value)
    		else:
    		    icon_name = icon_value
    	    
    		if icon_name.endswith(".png"):
    		    icon_name = icon_name[:-len(".png")]
    		elif icon_name.endswith(".xpm"):
    		    icon_name = icon_name[:-len(".xpm")]
    		elif icon_name.endswith(".svg"):
    		    icon_name = icon_name[:-len(".svg")]
    	    
    		icon = None
    		info = icon_theme.lookup_icon(icon_name, icon_size, gtk.ICON_LOOKUP_USE_BUILTIN)
    		if info:
    		    if icon_name.startswith("gtk-"):
    		        icon = info.load_icon()
    		    elif info.get_filename():
    		        icon = self.load_icon_from_path(info.get_filename())
    		else:
    		    icon = self.load_icon_from_data_dirs(icon_value, icon_size) 
    		return icon
    	except:
    		return None

    def load_image(self, icon_value, icon_size, force_size = True):
        pixbuf = self.load_icon(icon_value, icon_size, force_size)
        img = gtk.Image()
        img.set_from_pixbuf(pixbuf)
        img.show()
        del pixbuf, icon_value, icon_size, force_size 
        return img

    def make_icon_frame(self, thumb, icon_size = None, blend = False):
        border = 1

        mythumb = gtk.gdk.Pixbuf(thumb.get_colorspace(),
                                 True,
                                 thumb.get_bits_per_sample(),
                                 thumb.get_width(),
                                 thumb.get_height())
        mythumb.fill(0x00000080) # black, 50% transparent
        if blend:
            thumb.composite(mythumb, 0, 0,
                            thumb.get_width(), thumb.get_height(),
                            0, 0,
                            1.0, 1.0,
                            gtk.gdk.INTERP_NEAREST,
                            128)
        thumb.copy_area(border, border,
                        thumb.get_width() - (border * 2), thumb.get_height() - (border * 2),
                        mythumb,
                        border, border)
        del thumb,icon_size,blend
        return mythumb


class Thumbnailer:
    def __init__(self, uri, mimetype):
        self.uri = uri or ""
        self.mimetype = mimetype or ""
        self.cached_icon = None
        self.cached_timestamp = None
        self.cached_size = None

    def get_icon(self, icon_size, timestamp = 0):
        if not self.cached_icon or \
               icon_size != self.cached_size or \
               timestamp != self.cached_timestamp:
            cached_icon = self._lookup_or_make_thumb(icon_size, timestamp)
            self.cached_icon =cached_icon
           # delcached_icon
            self.cached_size = icon_size
            self.cached_timestamp = timestamp
        return self.cached_icon

    def _lookup_or_make_thumb(self, icon_size, timestamp):
        
        icon_name, icon_type = \
                   gnome.ui.icon_lookup(icon_theme, thumb_factory, self.uri, self.mimetype, 0)
        try:
            if icon_type == gnome.ui.ICON_LOOKUP_RESULT_FLAGS_THUMBNAIL or \
                   thumb_factory.has_valid_failed_thumbnail(self.uri, timestamp):
                # Use existing thumbnail
                thumb = icon_factory.load_icon(icon_name, icon_size)
            elif self._is_local_uri(self.uri):
                # Generate a thumbnail for local files only
                #print " *** Calling generate_thumbnail for", self.uri
                thumb = thumb_factory.generate_thumbnail(self.uri, self.mimetype)
                thumb_factory.save_thumbnail(thumb, self.uri, timestamp)

            if thumb:
                thumb = icon_factory.make_icon_frame(thumb, icon_size)
                return thumb
            
        except:
            pass

        return icon_factory.load_icon(icon_name, icon_size)


    def _is_local_uri(self, uri):
        # NOTE: gnomevfs.URI.is_local seems to hang for some URIs (e.g. ssh
        #       or http).  So look in a list of local schemes which comes
        #       directly from gnome_vfs_uri_is_local_scheme.
        scheme, path = urllib.splittype(self.get_uri() or "")
        return not scheme or scheme in ("file", "help", "ghelp", "gnome-help", "trash",
                                        "man", "info", "hardware", "search", "pipe",
                                        "gnome-trash")

class LaunchManager:
    '''
    A program lauching utility which handles opening a URI or executing a
    program or .desktop launcher, handling variable expansion in the Exec
    string.

    Adds the launched URI or launcher to the ~/.recently-used log.  Sets a
    DESKTOP_STARTUP_ID environment variable containing useful information such
    as the URI which caused the program execution and a timestamp.

    See the startup notification spec for more information on
    DESKTOP_STARTUP_IDs.
    '''
    def __init__(self):
        self.recent_model = None

    def _get_recent_model(self):
        # FIXME: This avoids import cycles
        if not self.recent_model:
            import mayanna_recent
            self.recent_model = mayanna_recent.recent_model
        return self.recent_model

    def launch_uri(self, uri, mimetype = None):
        assert uri, "Must specify URI to launch"
        
        child = os.fork()
        if not child:
            # Inside forked child
            os.setsid()
            os.environ['MAYANNA_LAUNCHER'] = uri
            os.environ['DESKTOP_STARTUP_ID'] = self.make_startup_id(uri)
            os.spawnlp(os.P_NOWAIT, "gnome-open", "gnome-open", uri)
            os._exit(0)
        else:
            os.wait()

            if not mimetype:
                mimetype = "application/octet-stream"
                try:
                    # Use XDG to lookup mime type based on file name.
                    # gtk_recent_manager_add_full requires it.
                    import xdg.Mime
                    mimetype = xdg.Mime.get_type_by_name(uri)
                    if mimetype:
                        mimetype = str(mimetype)
                    return mimetype
                except (ImportError, NameError):
                    #print " !!! No mimetype found for URI: %s" % uri
                    pass
                
            #self._get_recent_model().add(uri=uri, mimetype=mimetype)
        return child

    def get_local_path(self, uri):
        scheme, path = urllib.splittype(uri)
        if scheme == None:
            return uri
        elif scheme == "file":
            path = urllib.url2pathname(path)
            if path[:3] == "///":
                path = path[2:]
            return path
        return None

    def launch_command_with_uris(self, command, uri_list, launcher_uri = None):
        if command.rfind("%U") > -1:
            uri_str = ""
            for uri in uri_list:
                uri_str = uri_str + " " + uri
            return self.launch_command(command.replace("%U", uri_str), launcher_uri)
        elif command.rfind("%F") > -1:
            file_str = ""
            for uri in uri_list:
                uri = self.get_local_path(self, uri)
                if uri:
                    file_str = file_str + " " + uri
                else:
                    #print " !!! Command does not support non-file URLs: ", command
                    pass
            return self.launch_command(command.replace("%F", file_str), launcher_uri)
        elif command.rfind("%u") > -1:
            startup_ids = []
            for uri in uri_list:
                startup_ids.append(self.launch_command(command.replace("%u", uri), launcher_uri))
            else:
                return self.launch_command(command.replace("%u", ""), launcher_uri)
            return startup_ids
        elif command.rfind("%f") > -1:
            startup_ids = []
            for uri in uri_list:
                uri = self.get_local_path(self, uri)
                if uri:
                    startup_ids.append(self.launch_command(command.replace("%f", uri),
                                                           launcher_uri))
                else:
                    #print " !!! Command does not support non-file URLs: ", command
                    pass
            else:
                return self.launch_command(command.replace("%f", ""), launcher_uri)
            return startup_ids
        else:
            return self.launch_command(command, launcher_uri)

    def make_startup_id(self, key, ev_time = None):
        if not ev_time:
            ev_time = gtk.get_current_event_time()
        if not key:
            return "MAYANNA_TIME%d" % ev_time
        else:
            return "MAYANNA:%s_TIME%d" % (key, ev_time)

    def parse_startup_id(self, id):
        if id and id.startswith("MAYANNA:"):
            try:
                uri = id[len("MAYANNA:"):id.rfind("_TIME")]
                timestamp = id[id.rfind("_TIME") + len("_TIME"):]
                return (uri, timestamp)
            except IndexError:
                pass
        return (None, None)

    def launch_command(self, command, launcher_uri = None):
        startup_id = self.make_startup_id(launcher_uri)
        child = os.fork()
        if not child:
            # Inside forked child
            os.setsid()
            os.environ['DESKTOP_STARTUP_ID'] = startup_id
            if launcher_uri:
                os.environ['MAYANNA_LAUNCHER'] = launcher_uri
            os.popen2(command)
            os._exit(0)
        else:
            os.wait()
            if launcher_uri:
                self._get_recent_model().add(uri=launcher_uri,
                                            mimetype="application/x-desktop",
                                            groups=["Launchers"])
            return (child, startup_id)

class BookmarkManager(gobject.GObject):
    '''
    Maintains a list of bookmarks in ~/.mayanna-bookmarks.
    Each line of which is of the format: URI\tMIMETYPE
    '''
    
    __gsignals__ = {
        "reload" : (gobject.SIGNAL_RUN_FIRST,
                    gobject.TYPE_NONE,
                    ())
        }

    DEFAULT_BOOKMARKS = [
        ]
    
    def __init__(self):
        gobject.GObject.__init__(self)
        self.bookmarks_path = os.path.expanduser("~/.mayanna-bookmarks")

        self.monitor = FileMonitor(self.bookmarks_path)
        self.monitor.connect("event", lambda a, b, ev: self.emit("reload"))
        self.monitor.open()
        self.bookmarks = []

        self.emit("reload")


    def do_reload(self):
       # delself.bookmarks
         
        print("reloading bookmarks")
        self.bookmarks = []
        try:
            f = file(self.bookmarks_path, "r")
            for line in f:
                line = line.strip()
                args = line.split("\t")
                try: 
                    uri, mimetype, classname = args
                except ValueError:
                    uri, mimetype = args
                    classname = "mayanna_recent.FileItem"
                self.bookmarks.append([uri, mimetype, classname])
            f.close()
        except (IOError, EOFError):
            self.bookmarks = BookmarkManager.DEFAULT_BOOKMARKS

    def _write(self):
        try:
            f = file(self.bookmarks_path, "w")
            f.writelines(["%s\t%s\t%s\n" % (u, m, c) for u, m, c in self.bookmarks])
            f.close()

            # Let the file monitor event signal the change to avoid reloading twice
            self.monitor.queue_changed(self.bookmarks_path)
        except (IOError, EOFError):
            pass # Doesn't exist, or no access

    def add_bookmark(self, uri, mimetype, classname = "mayanna_recent.FileItem"):
        assert uri, "Must specify URI to bookmark"
        assert mimetype, "Must specify MimeType for URI"

        if not [uri, mimetype, classname] in self.bookmarks:
            self.bookmarks.append([uri, mimetype, classname])
            self._write()

    def add_bookmark_item(self, item):
        classname = "%s.%s" % (item.__class__.__module__, item.__class__.__name__)
        self.add_bookmark(item.get_uri(), item.get_mimetype(), classname)

    def remove_bookmark(self, uri):
        assert uri, "Must specify URI to unbookmark"
        
        self.bookmarks = [x for x in self.bookmarks if x[0] != uri]
        self._write()

    def is_bookmark(self, check_uri):
        return len([x for x in self.bookmarks if x[0] == check_uri]) > 0

    def get_bookmarks(self, mime_type_list = None):
        '''
        Returns the current list of bookmarks as uri and mimetype pairs.  Can be
        filtered by mimetype.
        '''
        if mime_type_list:
            return [[x, y] for x, y, z in self.bookmarks if y in mime_type_list]
        return [[x, y] for x, y, z in self.bookmarks]

    def get_bookmarks_and_class(self):
        '''
        Returns the current list of bookmarks as uri and mimetype pairs.  Can be
        filtered by mimetype.
        '''
        return [[x, z] for x, y, z in self.bookmarks]

class DBusWrapper:
    '''
    Simple wrapper around DBUS object creation.  This works around older DBUS
    bindings which did not create proxy objects if the service/interface is not
    available.  If there is no proxy object, all member access will raise a
    dbus.DBusException.
    '''

    def __init__(self, service, path = None, interface = None, program_name = None, bus = None):
        assert service, "D-BUS Service name not valid"
        self.__service = service
        self.__obj = None

        # NOTE: Some services use the same name for the path
        self.__path = path or "/%s" % service.replace(".", "/")
        self.__interface = interface or service

        self.__program_name = program_name
        self.__bus = bus

    def __get_bus(self):
        if not self.__bus:
            try:
                try:
                    # pthon-dbus 0.80.x requires a mainloop to connect signals
                    from dbus.mainloop.glib import DBusGMainLoop
                    self.__bus = dbus.SessionBus(mainloop=DBusGMainLoop())
                except ImportError:
                    self.__bus = dbus.SessionBus()
            except dbus.DBusException:
                #print " !!! D-BUS Session bus is not running"
                raise 
        return self.__bus

    def __get_obj(self):
        if not self.__obj:
            try:
                svc = self.__get_bus().get_object(self.__service, self.__path)
                self.__obj = dbus.Interface(svc, self.__interface)
            except dbus.DBusException:
                #print " !!! %s D-BUS service not available." % self.__service
                raise
        return self.__obj

    def __getattr__(self, name):
        try:
            return getattr(self.__get_obj(), name)
        except AttributeError:
            raise dbus.DBusException

icon_factory = IconFactory()
icon_theme = gtk.icon_theme_get_default()
thumb_factory = gnome.ui.ThumbnailFactory("normal")
launcher = LaunchManager()
bookmarks = BookmarkManager()


