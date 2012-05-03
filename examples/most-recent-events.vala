int main ()
{
    try
    {
        uint32[] ids = { 31575, 31569 };

        //Zeitgeist.RemoteLog zg = Bus.get_proxy_sync<Zeitgeist.RemoteLog> (
        //    BusType.SESSION, "org.gnome.zeitgeist.Engine",
        //    "/org/gnome/zeitgeist/log/activity");

        Zeitgeist.Log zg = new Zeitgeist.Log ();
        zg.get_events (ids, null, (obj, res) => { debug("hi!"); });
        /*
        var events = zg.get_events (ids);
        foreach (Variant event in events)
        {
            stdout.printf ("got one event!\n");
        }
        */
    }
    catch (Error e)
    {
        stderr.printf ("%s\n", e.message);
        return 1;
    }

    var loop = new MainLoop();
    loop.run ();

    return 0;
}
