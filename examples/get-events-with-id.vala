int main ()
{
    var ids = new Array<uint32>();
    ids.append_val(210);
    ids.append_val(222);

    var loop = new MainLoop();

    Zeitgeist.Log zg = new Zeitgeist.Log ();
    zg.get_events (ids, null, (obj, res) => {
        Zeitgeist.ResultSet events = zg.get_events.end (res);
        foreach (Zeitgeist.Event event in events)
        {
            stdout.printf ("Subject: %s\n", event.subjects[0].uri);
        }
        loop.quit();
    });

    loop.run ();

    return 0;
}
