from gi.repository import Zeitgeist, GObject
import time

log = Zeitgeist.Log.get_default()
mainloop = GObject.MainLoop()

def on_events_inserted(log, time_range, events):
    print "==="

ev = Zeitgeist.Event();
ev.set_property("interpretation", "foo://Interp");
ev.set_property("timestamp", time.time()*1000);
ev.debug_print()
log.insert_event(ev, None, on_events_inserted, None)

mainloop.run()
