from gi.repository import Zeitgeist, GObject
log = Zeitgeist.Log.get_default()
mainloop = GObject.MainLoop()

def callback (log, result, data):
    events = log.get_events_finish(result)
    print events.size()
    for i in xrange(events.size()):
        event = events.next_value()
        if event:
            print event.get_property("id")
    mainloop.quit()

log.get_events([x for x in xrange(200, 222)], None, callback, None)
mainloop.run()
