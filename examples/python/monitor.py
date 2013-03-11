from gi.repository import Zeitgeist, GLib
log = Zeitgeist.Log.get_default()
mainloop = GLib.MainLoop()

def on_events_inserted(log, time_range, events):
    print time_range, events

subject = Zeitgeist.Subject.full("", Zeitgeist.AUDIO, "", "", "", "", "")
event = Zeitgeist.Event()
event.add_subject(subject)
time_range = Zeitgeist.TimeRange.from_now()
monitor = Zeitgeist.Monitor.new(time_range, [event])
monitor.connect("events-inserted", on_events_inserted)
log.install_monitor(monitor)

mainloop.run()
