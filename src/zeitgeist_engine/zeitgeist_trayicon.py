import sys
import gtk
import subprocess
import webbrowser

from zeitgeist_shared.basics import BASEDIR


class ZeitgeistTrayIcon(gtk.StatusIcon):
	
	def __init__(self, mainloop):
		
		gtk.StatusIcon.__init__(self)
		
		self.set_from_file("%s/data/gnome-zeitgeist.png" % BASEDIR)
		self.set_visible(True)
		
		self._mainloop = mainloop
		self.journal_proc = None
		self.project_viewer_proc = None
		self.timeline_proc = None
		self._about = None
		
		menu = gtk.Menu()
		self.connect("activate",self.open_journal)
		
		menuItem = gtk.ImageMenuItem(gtk.STOCK_HOME)
		menuItem.get_children()[0].set_label("Open Journal")
		menu.append(menuItem)
		menuItem.connect('activate', self.open_journal)
		
		menuItem = gtk.ImageMenuItem(gtk.STOCK_DIRECTORY)
		menuItem.get_children()[0].set_label("Open Project Viewer")
		menu.append(menuItem)
		menuItem.connect('activate', self.open_project_viewer)
		
		menuItem = gtk.ImageMenuItem(gtk.STOCK_DIRECTORY)
		menuItem.get_children()[0].set_label("Open Timeline")
		menu.append(menuItem)
		menuItem.connect('activate', self.open_timeline)
		
		menuItem = gtk.ImageMenuItem(gtk.STOCK_PREFERENCES)
		#menu.append(menuItem)
		menuItem.connect('activate', self.open_about)
		
		menuItem = gtk.ImageMenuItem(gtk.STOCK_ABOUT)
		menu.append(menuItem)
		menuItem.connect('activate', self.open_about)
		
		menuItem = gtk.ImageMenuItem(gtk.STOCK_QUIT)
		menu.append(menuItem)
		menuItem.connect('activate', self.quit)
		 
		self.set_tooltip("GNOME Zeitgeist")
		self.connect('popup-menu', self.popup_menu_cb, menu)

	def open_journal(self, widget):
		if self.journal_proc == None or not self.journal_proc.poll() == None:
			self.journal_proc = subprocess.Popen("python %s/src/zeitgeist_gui/zeitgeist-journal.py" % BASEDIR, shell=True)
	
	def open_project_viewer(self, widget):
		if self.project_viewer_proc == None or not self.project_viewer_proc.poll() == None:
			self.project_viewer_proc = subprocess.Popen("python %s/src/zeitgeist_gui/zeitgeist-projectviewer.py" % BASEDIR, shell=True)
	
	def open_timeline(self, widget):
		if self.timeline_proc == None or not self.timeline_proc.poll() == None:
			self.timeline_proc = subprocess.Popen("python %s/src/zeitgeist_gui/zeitgeist-timeline.py" % BASEDIR, shell=True)
			
	def open_about(self, widget):
		if not self._about:
			self._about = AboutWindow()
			self._about.connect("destroy", self._about_destroyed)
		self._about.show()
	
	def _about_destroyed(self, *discard):
		self._about = None
	
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
		self.set_copyright("Copyright 2009 (c) The Zeitgeist Team")
		self.set_website("http://zeitgeist.geekyogre.com")
		gtk.about_dialog_set_url_hook(self.open_url,None)
		gtk.about_dialog_set_email_hook(self.open_mail, None)
		
		self.set_program_name("GNOME Zeitgeist")
		image = gtk.image_new_from_file("%s/data/gnome-zeitgeist.png" % BASEDIR)
		
		authors = ["Alexander Gabriel <Alexander.Gabriel@tu-harburg.de>",
						"Federico Mena-Quintero <federico@gnome.org>",
						"Jason Smith <jassmith@gmail.com>",
						"Natan Yellin <aantny@gmail.com>",
						"Seif Lotfy <seilo@geekyogre.com>",
						"Siegfried-Angel Gevatter <rainct@ubuntu.com>",
						"Thorsten Prante <thorsten@prante.eu>"]
		
		self.set_authors(authors)
		self.set_comments("GNOME Zeitgeist is a tool for easily browsing and finding files on your computer.")
		self.set_logo(gtk.gdk.pixbuf_new_from_file("%s/data/gnome-zeitgeist.png" % BASEDIR))
		
		artists =["Jason Smith <jassmith@gmail.com>",
						"Kalle Persson <kalle@nemus.se>"]
		self.set_artists(artists)
		self.set_icon_from_file("%s/data/gnome-zeitgeist.png" % BASEDIR)
	
		self.connect("response", self.close)
		self.hide()
	
	def close(self, w, res=None):
		if res == gtk.RESPONSE_CANCEL:
			self.hide()
	
	def open_url(self, dialog, link, ignored):
		webbrowser.open_new(link)

	def open_mail(self, dialog, link, ignored):
		webbrowser.open_new("mailto:%s" % link)
