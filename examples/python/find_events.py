from gi.repository import Zeitgeist, GLib
log = Zeitgeist.Log.get_default()
mainloop = GLib.MainLoop()

def on_events_received(log, result, data):
    events = log.find_events_finish(result)
    for i in xrange(events.size()):
        event = events.next_value()
        if event:
            print "Event id:", event.get_property("id")
            for i in xrange(event.num_subjects()):
                subj = event.get_subject(i)
                print "  -", subj.get_property("uri")
    mainloop.quit()

subject = Zeitgeist.Subject.full("", Zeitgeist.AUDIO, "", "", "", "", "")
event = Zeitgeist.Event()
event.add_subject(subject)
time_range = Zeitgeist.TimeRange.anytime ();

log.find_events(time_range, 
                        [event],
                        Zeitgeist.StorageState.ANY,
                        20,
                        Zeitgeist.ResultType.MOST_RECENT_SUBJECTS,
                        None,
                        on_events_received,
                        None)

mainloop.run()
