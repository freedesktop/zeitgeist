/* zeitgeist-daemon.vala
 *
 * Copyright © 2011 Seif Lotfy <seif@lotfy.com>
 * Copyright © 2011 Michal Hruby <michal.mhr@gmail.com>
 * Copyright © 2011 Collabora Ltd.
 *             By Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
 *             By Seif Lotfy <seif@lotfy.com>
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

namespace Zeitgeist
{

    public class Daemon : Object, RemoteLog
    {

        private static Daemon? instance;
        private static MainLoop mainloop;

        private Engine engine;
        private MonitorManager notifications;
        private ExtensionCollection extension_collection;

        private uint log_register_id;
        private unowned DBusConnection connection;

        public string[] extensions
        {
            owned get
            {
                string[] ext = extension_collection.get_extension_names ();
                return ext;
            }
        }

        public Variant version
        {
            owned get
            {
                var vb = new VariantBuilder (new VariantType ("(iii)"));
                vb.add ("i", 0);
                vb.add ("i", 8);
                vb.add ("i", 99);
                return vb.end ();
            }
        }

        public Daemon ()
        {
            stdout.printf("Hi!\n");

            try
            {
                engine = new Engine();
            }
            catch (EngineError e)
            {
                // FIXME
                safe_exit ();
            }

            notifications = new MonitorManager ();
            extension_collection = new ExtensionCollection ();

            // FIXME: tmp:
            /*
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

            var events = new GenericArray<Event>();
            events.add(new Event.from_variant(vb.end()));
            stdout.printf ("INSERTED: %u\n", engine.insert_events(events)[0]);
            */
        }

        ~Daemon ()
        {
            stdout.printf ("BYE\n");
            engine.close ();
        }

        // FIXME
        public Variant get_events (uint32[] event_ids, BusName sender)
        {
            GenericArray<Event> events = engine.get_events (event_ids);
            return Events.to_variant (events);
        }

        // FIXME
        public string[] find_related_uris (Variant time_range,
                Variant event_templates,
                Variant result_event_templates,
                uint storage_state, uint num_events, uint result_type,
                BusName sender)
        {
            return engine.find_related_uris(new TimeRange.from_variant (time_range),
                Events.from_variant(event_templates),
                Events.from_variant(result_event_templates),
                storage_state, num_events, result_type);
        }

        // FIXME
        public uint32[] find_event_ids (Variant time_range,
                Variant event_templates,
                uint storage_state, uint num_events, uint result_type,
                BusName sender)
        {
            return engine.find_event_ids (
                new TimeRange.from_variant (time_range),
                Events.from_variant(event_templates),
                storage_state, num_events, result_type, sender);
        }

        // FIXME
        public Variant find_events (Variant time_range,
                Variant event_templates,
                uint storage_state, uint num_events, uint result_type,
                BusName sender)
        {
            return Events.to_variant (engine.find_events (
                new TimeRange.from_variant (time_range),
                Events.from_variant (event_templates),
                storage_state, num_events, result_type, sender));
        }

        // FIXME
        public uint32[] insert_events (
                Variant vevents,
                BusName sender)
        {
            var events = Events.from_variant (vevents);

            // FIXME: trigger notifications

            uint32[] event_ids = engine.insert_events (events, sender);
            // FIXME: time_range
            notifications.notify_insert (new TimeRange (-1, -1), events);

            return event_ids;
        }

        // FIXME
        public Variant delete_events (uint32[] event_ids, BusName sender)
        {
            TimeRange? time_range = engine.delete_events (event_ids, sender);
            if (time_range != null)
            {
                // FIXME: trigger notifications
            }
            else
            {
                // All the given event_ids are invalid or the events
                // have already been deleted before!
                time_range = new TimeRange (-1, -1);
            }

            return time_range.to_variant ();
        }

        public void quit ()
        {
            do_quit ();
        }

        private void do_quit ()
        {
            mainloop.quit ();
        }

        public void install_monitor (ObjectPath monitor_path,
                Variant time_range,
                Variant event_templates,
                BusName owner)
        {
            notifications.install_monitor (owner, monitor_path,
                new TimeRange.from_variant (time_range),
                Events.from_variant (event_templates));
        }

        public void remove_monitor (ObjectPath monitor_path, BusName owner)
        {
            notifications.remove_monitor (owner, monitor_path);
        }

        public void register_dbus_object (DBusConnection conn) throws Error
        {
            connection = conn;
            log_register_id = conn.register_object<RemoteLog> (
                    "/org/gnome/zeitgeist/log/activity", this);
        }

        public void unregister_dbus_object ()
        {
            if (log_register_id != 0)
            {
                connection.unregister_object (log_register_id);
                log_register_id = 0;
            }
        }

        static void on_bus_aquired (DBusConnection conn)
        {
            instance = new Daemon ();
            try
            {
                instance.register_dbus_object (conn);
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

            instance.unregister_dbus_object ();
            instance = null;
        }

        static void safe_exit ()
        {
            instance.do_quit ();
        }

        static int main (string[] args)
        {
            Posix.signal (Posix.SIGHUP, safe_exit);
            Posix.signal (Posix.SIGTERM, safe_exit);

            run ();
            return 0;
        }

    }

}
// vim:expandtab:ts=4:sw=4
