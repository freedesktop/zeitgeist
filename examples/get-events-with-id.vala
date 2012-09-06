int main ()
{
    var ids = new Array<uint32>();
    uint32 id1 = 210;
    uint32 id2 = 222;
    ids.append_val(id1);
    ids.append_val(id2);

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
