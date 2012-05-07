int main ()
{
    uint32[] ids = { 31575, 31569 };

    var loop = new MainLoop();

    Zeitgeist.Log zg = new Zeitgeist.Log ();
    zg.get_events (ids, null, (obj, res) => {
        var events = zg.get_events.end (res);
        for (int i = 0; i < events.length; ++i)
        {
            Zeitgeist.Event event = events[i];
            stdout.printf ("Subject: %s\n", event.subjects[0].uri);
        }
        loop.quit();
    });

    loop.run ();

    return 0;
}
