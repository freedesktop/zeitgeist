import os
import sys	   # for ImplementMe
import gobject
import gtk
import gnomevfs
import gconf
from gettext import gettext as _
import tempfile, shutil
import subprocess
import webbrowser

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
			print "got it"
		except gnomevfs.Error:
			self.type = gnomevfs.MONITOR_FILE
			print "did not get it"

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
		print"open"

	def _clear_timeout(self, info_uri):
		try:
			gobject.source_remove(self.pending_timeouts[info_uri])
		   # delself.pending_timeouts[info_uri]
		except KeyError:
			pass
		del info_uri

	def _queue_event(self, monitor_uri, info_uri, event):
		print "queue event"
		self._clear_timeout(info_uri)
		self.pending_timeouts[info_uri] = \
			gobject.timeout_add(250, self._timeout_cb, monitor_uri, info_uri, event)
		del monitor_uri, info_uri, event

	def queue_changed(self, info_uri):
		print "queue changed"
		self._queue_event(self.path, info_uri, gnomevfs.MONITOR_EVENT_CHANGED)
		del info_uri
		
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
		del monitor_uri, info_uri, event
		return False

class DiffFactory:
	def __init__(self):
		pass
	
	def create_diff(self,uri1,content):
		fd, path = tempfile.mkstemp()
		os.write(fd, content)
		diff =	os.popen("diff -u "+path+" "+uri1.replace("file://","",1)).read()
		os.close(fd)
		os.remove(path)
		return diff
		
	def restore_file(self,item):
		fd1, orginalfile = tempfile.mkstemp()
		fd2, patch = tempfile.mkstemp()
		
		os.write(fd1, item.original_source)
		os.write(fd2, item.diff)
		
		os.close(fd1)
		os.close(fd2)
		
		os.system("patch %s < %s" % (orginalfile, patch))
		return orginalfile
	


class GConfBridge(gobject.GObject):
    DEFAULTS = {
        'compress_empty_days'   : True, 
        'show_note_button'      : True,
        'show_file_button'      : True
    }

    ZEITGEIST_PREFIX = "/apps/zeitgeist/"

    __gsignals__ = {
        'changed' : (gobject.SIGNAL_RUN_LAST | gobject.SIGNAL_DETAILED, gobject.TYPE_NONE, ()),
    }

    def __init__(self, prefix = None):
        gobject.GObject.__init__(self)

        if not prefix:
            prefix = self.ZEITGEIST_PREFIX
        if prefix[-1] != "/":
            prefix = prefix + "/"
        self.prefix = prefix
        
        self.gconf_client = gconf.client_get_default()
        self.gconf_client.add_dir(prefix[:-1], gconf.CLIENT_PRELOAD_RECURSIVE)

        self.notify_keys = { }

    def connect(self, detailed_signal, handler, *args):
        # Ensure we are watching the GConf key
        if detailed_signal.startswith("changed::"):
            key = detailed_signal[len("changed::"):]
            if not key.startswith(self.prefix):
                key = self.prefix + key
            if key not in self.notify_keys:
                self.notify_keys[key] = self.gconf_client.notify_add(key, self._key_changed)

        return gobject.GObject.connect(self, detailed_signal, handler, *args)

    def get(self, key, default=None):
        if not default:
            if key in self.DEFAULTS:
                default = self.DEFAULTS[key]
                vtype = type(default)
            else:
                assert "Unknown GConf key '%s', and no default value" % key

        vtype = type(default)
        if vtype not in (bool, str, int):
            assert "Invalid GConf key type '%s'" % vtype

        if not key.startswith(self.prefix):
            key = self.prefix + key

        value = self.gconf_client.get(key)
        if not value:
            self.set(key, default)
            return default

        if vtype is bool:
            return value.get_bool()
        elif vtype is str:
            return value.get_string()
        elif vtype is int:
            return value.get_int()
        else:
            return value

    def set(self, key, value):
        vtype = type(value)
        if vtype not in (bool, str, int):
            assert "Invalid GConf key type '%s'" % vtype

        if not key.startswith(self.prefix):
            key = self.prefix + key

        if vtype is bool:
            self.gconf_client.set_bool(key, value)
        elif vtype is str:
            self.gconf_client.set_string(key, value)
        elif vtype is int:
            self.gconf_client.set_int(key, value)

    def _key_changed(self, client, cnxn_id, entry, data=None):
        if entry.key.startswith(self.prefix):
            key = entry.key[len(self.prefix):]
        else:
            key = entry.key
        detailed_signal = "changed::%s" % key
        self.emit(detailed_signal)


class ZeitgeistTrayIcon(gtk.StatusIcon):
	
	def __init__(self):
		gtk.StatusIcon.__init__(self)
		self.set_from_file("data/gnome-zeitgeist.png")
		self.set_visible(True)
		
		self.about_visible=False
		
		menu = gtk.Menu()
		
		self.journal_proc = None
		self.project_viewer_proc = None
		
		menuItem = gtk.ImageMenuItem(gtk.STOCK_HOME)
		menuItem.set_name("Open Journal")
		menu.append(menuItem)
		menuItem.connect('activate', self.open_journal)
		
		menuItem = gtk.ImageMenuItem(gtk.STOCK_DIRECTORY)
		menuItem.set_name("Open Project Viewer")
		menu.append(menuItem)
		menuItem.connect('activate', self.open_project_viewer)
		
		menuItem = gtk.ImageMenuItem(gtk.STOCK_PREFERENCES)
		#menu.append(menuItem)
		menuItem.connect('activate', self.open_about)
		
		
		menuItem = gtk.ImageMenuItem(gtk.STOCK_ABOUT)
		menu.append(menuItem)
		menuItem.connect('activate', self.open_about)
		
		menuItem = gtk.ImageMenuItem(gtk.STOCK_QUIT)
		menu.append(menuItem)
		menuItem.connect('activate', self.quit)
		 
		self.about = AboutWindow()
		
		self.about.connect("destroy",self.close_about)
		self.about.connect("response",self.close_about)
		 
		self.set_tooltip("Zeitgeist")
		self.connect('popup-menu', self.popup_menu_cb, menu)

	def open_journal(self,widget):
		if self.journal_proc == None or not self.journal_proc.poll() == None:
			self.journal_proc = subprocess.Popen("sh zeitgeist-journal.sh",shell=True)
			
	def open_project_viewer(self,widget):
		if self.project_viewer_proc == None or not self.project_viewer_proc.poll() == None:
			self.project_viewer_proc = subprocess.Popen("sh zeitgeist-projectviewer.sh",shell=True)
			
	def open_about(self,widget):
		self.about = AboutWindow()
		self.about.show()
		self.about_visible = True
	
	def close_about(self,x=None,y=None):
		self.about_visible = False
			
 	def popup_menu_cb(self,widget, button, time, data = None):
 		if button == 3:
 			if data:
 				data.show_all()
                data.popup(None, None, None, 3, time)
            
 	def quit(self,widget):
 		sys.exit(-1)

class AboutWindow(gtk.AboutDialog):
	def __init__(self):
		gtk.AboutDialog.__init__(self)
		self.set_name("GNOME Zeitgeist")
		self.set_version("0.0.3")
		self.set_copyright("Copyright 2009 (c) GNOME Zeitgeist Developers")
		self.set_website("http://zeitgeist.geekyogre.com")
		gtk.about_dialog_set_url_hook(self.open_url,None)
		gtk.about_dialog_set_email_hook(self.open_mail, None)


		self.set_program_name("GNOME Zeitgeist")
		image = gtk.image_new_from_file("data/gnome-zeitgeist.png")
		
		f = open("AUTHORS","r")
		authors =["Alexander Gabriel <Alexander.Gabriel@tu-harburg.de>",
						"Federico Mena-Quintero <federico@gnome.org>",
						"Jason Smith <jassmith@gmail.com>",
						"Natan Yellin <aantny@gmail.com>",
						"Seif Lotfy <seilo@geekyogre.com>",
						"Siegfried-Angel Gevatter <rainct@ubuntu.com>",
						"Thorsten Prante <thorsten@prante.eu>"]
			
		self.set_authors(authors)
		self.set_comments("Gnome Zeitgeist is a tool for easily browsing and finding files on your computer.")
		self.set_logo(gtk.gdk.pixbuf_new_from_file("data/gnome-zeitgeist.png"))
		
		
		artists =["Jason Smith <jassmith@gmail.com>",
						"Kalle Persson <kalle@nemus.se>"]
		self.set_artists(artists)
		self.set_icon_from_file("data/gnome-zeitgeist.png")
	
		self.connect("response", self.close)
		self.hide()
		
	def close(self, w, res=None):
		if res == gtk.RESPONSE_CANCEL:
			self.hide()
		
	def open_url(self, dialog, link, ignored):
		webbrowser.open_new(link)

	def open_mail(self, dialog, link, ignored):
		webbrowser.open_new("mailto:" + link)

difffactory=DiffFactory()
gconf_bridge = GConfBridge()
