int main ()
{
    uint32[] ids = { 31575, 31569 };

    var loop = new MainLoop();

    Zeitgeist.Log zg = new Zeitgeist.Log ();
    zg.get_events (ids, null, (obj, res) => {
        Zeitgeist.ResultSet events = zg.get_events.end (res);
        while (events.has_next ())
        {
            Zeitgeist.Event event = events.next ();
            stdout.printf ("Subject: %s\n", event.subjects[0].uri);
        }
        loop.quit();
    });

    loop.run ();

    return 0;
}
