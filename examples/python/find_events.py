from gi.repository import Zeitgeist, Gtk
log = Zeitgeist.Log.get_default()

def callback (log, result, data):
    events = log.get_events_finish(result)
    print len(events)
    #for event in events:
    #    if event:
    #        print "==="
    Gtk.main_quit()

log.get_events([x for x in xrange(200, 222)], None, callback, None)
Gtk.main()
