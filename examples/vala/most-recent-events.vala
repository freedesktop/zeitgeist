using Zeitgeist;

int main ()
{
    var loop = new MainLoop();
    var log  = new Zeitgeist.Log ();

    var time_range = new TimeRange.anytime ();
    var templates  = new GenericArray<Event> ();
    int num_events = 20;

    log.find_events.begin (time_range, templates, StorageState.ANY, num_events,
        ResultType.MOST_RECENT_SUBJECTS, null, (obj, res) =>
        {
            ResultSet events = log.find_events.end (res);
            stdout.printf ("%u most recent subjects:", events.size ());
            foreach (Event event in events)
            {
                stdout.printf (" - %s\n", event.subjects[0].uri);
            }
            loop.quit();
        }
    );

    loop.run ();

    return 0;
}
