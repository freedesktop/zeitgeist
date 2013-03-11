from gi.repository import Zeitgeist, GLib
log = Zeitgeist.Log.get_default()
mainloop = GLib.MainLoop()

def callback (log, result, data):
    events = log.get_events_finish(result)
    event_list = []
    for i in xrange(events.size()):
        event = events.next_value()
        if event:
           event_list.append(event.get_property("id"))
    print event_list
    mainloop.quit()

log.get_events([x for x in xrange(200, 222)], None, callback, None)
mainloop.run()
