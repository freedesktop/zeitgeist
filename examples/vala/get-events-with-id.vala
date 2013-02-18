int main ()
{
    var ids = new Array<uint32>();
    uint32 id1 = 2100000;
    uint32 id2 = 222;
    ids.append_val(id1);
    ids.append_val(id2);

    var loop = new MainLoop();

    Zeitgeist.Log zg = new Zeitgeist.Log ();
    zg.get_events.begin (ids, null, (obj, res) => {
        var events = zg.get_events.end (res);
        for (int i = 0; i < events.size(); ++i)
        {
            Zeitgeist.Event event = events.next_value();
            if (event != null)
                stdout.printf ("First subject: %s\n", event.subjects[0].uri);
            else
                stdout.printf ("Event %d doesn't exist.\n", (int) ids.index (i));
        }
        loop.quit();
    });

    loop.run ();

    return 0;
}
