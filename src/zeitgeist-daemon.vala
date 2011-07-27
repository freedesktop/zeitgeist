/* zeitgeist-daemon.vala
 *
 * Copyright © 2011 Seif Lotfy <seif@lotfy.com>
 * Copyright © 2011 Collabora Ltd.
 *             By Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Lesser General Public License as published by
 * the Free Software Foundation, either version 2.1 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 */

public class ZeitgeistDaemon : Object, Zeitgeist.RemoteLogInterface
{

    private static MainLoop mainloop;
    private Engine engine;
    private MonitorManager notifications;

    public string[] extensions
    {
        owned get
        {
            string[] ext = { "extension1", "extension2" };
            return ext;
        }
    }

    public Variant version
    {
        owned get
        {
            var vb = new VariantBuilder (new VariantType ("(iii)"));
            vb.add ("i", 0);
            vb.add ("i", 1);
            vb.add ("i", 2);
            return vb.end ();
        }
    }

    public ZeitgeistDaemon ()
    {
        stdout.printf("Hi!\n");
        
        try
        {
        engine = new Engine();
        }
        catch (EngineError e)
        {
            //quit();
        }
        
        notifications = new MonitorManager();

        var vb = new VariantBuilder(new VariantType("(asaasay)"));
        vb.open(new VariantType("as"));
            vb.add("s", "0"); // id
            vb.add("s", "123"); // timestamp
            vb.add("s", "stfu:OpenEvent"); // interpretation
            vb.add("s", "stfu:UserActivity"); // manifestation
            vb.add("s", "firefox"); // actor
            vb.add("s", "nowhere"); // origin
        vb.close();
        vb.open(new VariantType("aas"));
            vb.open(new VariantType("as"));
                vb.add("s", "file:///tmp/foo.txt"); // uri
                vb.add("s", "stfu:Document"); // interpretation
                vb.add("s", "stfu:File"); // manifestation
                vb.add("s", "file:///tmp"); // origin
                vb.add("s", "text/plain"); // mimetype
                vb.add("s", "this item has no text... rly!"); // text
                vb.add("s", "368c991f-8b59-4018-8130-3ce0ec944157"); // storage
                vb.add("s", "file:///tmp/foo.txt"); // current_uri
            vb.close();
        vb.close();
        vb.open(new VariantType("ay"));
        vb.close();

        new Event.from_variant(vb.end());
    }

    // FIXME
    public Variant get_events (uint32[] event_ids, BusName sender)
    {
        stdout.printf ("yeah!\n");
        //return new Variant("us", 5, "OK");
        return 1;
    }

    // FIXME
    public string[] find_related_uris (TimeRange time_range,
            Variant event_templates,
            Variant result_event_templates,
            uint storage_state, uint num_events, uint result_type,
            BusName sender)
    {
        return new string[] { "hi", "bar" };
    }

    // FIXME
    public uint[] find_event_ids (TimeRange time_range,
            Variant event_templates,
            uint storage_state, uint num_events, uint result_type,
            BusName sender)
    {
        return new uint[] { 1, 2, 3 };
    }

    // FIXME
    public Variant find_events (TimeRange time_range,
            Variant event_templates,
            uint storage_state, uint num_events, uint result_type,
            BusName sender)
    {
        return 1;
    }

    // FIXME
    public uint[] insert_events (
            Variant events,
            BusName sender)
    {
        return new uint[] { 1, 2, 3 };
    }

    // FIXME
    public TimeRange delete_events (uint[] event_ids, BusName sender)
    {
        return TimeRange() { start = 30, end = 40 };
    }

    public void quit ()
    {
        stdout.printf("BYE\n");
        engine.close();
        mainloop.quit();
    }

    public void install_monitor (ObjectPath monitor_path,
            TimeRange time_range,
            Variant event_templates,
            BusName owner)
    {
        stdout.printf("i'll let you know!\n");
    }

    public void remove_monitor (ObjectPath monitor_path, BusName owner)
    {
        stdout.printf("bye my friend\n");
    }

    static void on_bus_aquired (DBusConnection conn)
    {
        try
        {
            conn.register_object (
                "/org/gnome/zeitgeist/log/activity",
                (Zeitgeist.RemoteLogInterface) new ZeitgeistDaemon ());
        }
        catch (IOError e)
        {
            stderr.printf ("Could not register service\n");
        }
    }

    static void run ()
    {
        // TODO: look at zeitgeist/singleton.py
        Bus.own_name (BusType.SESSION, "org.gnome.zeitgeist.Engine",
            BusNameOwnerFlags.NONE,
            on_bus_aquired,
            () => {},
            () => stderr.printf ("Could not aquire name\n"));
        mainloop = new MainLoop ();
        mainloop.run ();
    }

    static int main (string[] args)
    {
        Zeitgeist.Constants.initialize ();
        run ();
        return 0;
    }

}
