from gi.repository import Zeitgeist, Gtk
log = Zeitgeist.Log.get_default()

def callback (x):
    print x

log.get_events([x for x in xrange(100)], None, callback, None)
Gtk.main()
