using Zeitgeist;

int main ()
{
    var mainloop = new MainLoop(MainContext.default ());
    var events = new GenericArray<Event> ();
    var ev = new Event ();
    var su = new Subject ();
    ev.add_subject (su);
    events.add (ev);
    ev.interpretation = "foo://Interp";
    ev.manifestation = "foo://Manif";
    ev.actor = "app://firefox.desktop";

    su.uri = "file:///tmp/bar.txt";
    su.interpretation = "foo://TextDoc";
    su.manifestation = "foo://File";
    su.mimetype = "text/plain";
    su.origin = "file:///tmp";
    su.text = "bar.txt";
    su.storage = "bfb486f6-f5f8-4296-8871-0cc749cf8ef7";

    Zeitgeist.Log.get_default ().insert_events.begin (
        events, null, (log, res) => {
            Array<uint32> event_ids;
            Zeitgeist.Log zg = (Zeitgeist.Log) log;
            try {
                event_ids = zg.insert_events.end (res);
            }
            catch (Error error) {
                critical ("Failed to insert events: %s", error.message);
                return;
            }
            mainloop.quit ();
        });
    mainloop.run ();
    return 0;
}
