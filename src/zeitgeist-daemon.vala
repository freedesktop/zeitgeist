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
        private static bool show_version_info = false;
        private static bool show_options = false;
        private static bool no_datahub = false;
        private static bool replace_mode = false;
        private static bool quit_daemon = false;
        private static string log_level = "";

        const OptionEntry[] options =
        {
            {
                "version", 'v', 0, OptionArg.NONE, out show_version_info,
                "Print program's version number and exit", null
            },
            {
                "no-datahub", 0, 0, OptionArg.NONE, out no_datahub,
                "Do not start zeitgeist-datahub automatically", null
            },
            {
                "no-passive-loggers", 0, OptionFlags.HIDDEN, OptionArg.NONE,
                out no_datahub, null, null
            },
            {
                "replace", 'r', 0, OptionArg.NONE, out replace_mode,
                "If another Zeitgeist instance is already running, replace it",
                null
            },
            {
                "quit", 0, 0, OptionArg.NONE, out quit_daemon,
                "Quit running Zeitgeist daemon instance", null
            },
            {
                "log-level", 0, 0, OptionArg.STRING, out log_level,
                "How much information should be printed; possible values: " +
                "DEBUG, INFO, WARNING, ERROR, CRITICAL", "LEVEL"
            },
            {
                "shell-completion", 0, OptionFlags.HIDDEN, OptionArg.NONE,
                out show_options, null, null
            },
            {
                null
            }
        };

        private static Daemon? instance;
        private static MainLoop mainloop;

        private Engine engine;
        private MonitorManager notifications;

        private uint log_register_id;
        private unowned DBusConnection connection;

        public string[] extensions
        {
            owned get
            {
                string[] ext = engine.get_extension_names ();
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
        }

        ~Daemon ()
        {
            stdout.printf ("BYE\n");
            engine.close ();
        }

        public Variant get_events (uint32[] event_ids, BusName sender)
            throws Error
        {
            GenericArray<Event> events = engine.get_events (event_ids);
            return Events.to_variant (events);
        }

        public string[] find_related_uris (Variant time_range,
                Variant event_templates,
                Variant result_event_templates,
                uint storage_state, uint num_events, uint result_type,
                BusName sender) throws Error
        {
            return engine.find_related_uris(new TimeRange.from_variant (time_range),
                Events.from_variant(event_templates),
                Events.from_variant(result_event_templates),
                storage_state, num_events, result_type);
        }

        public uint32[] find_event_ids (Variant time_range,
                Variant event_templates,
                uint storage_state, uint num_events, uint result_type,
                BusName sender) throws Error
        {
            return engine.find_event_ids (
                new TimeRange.from_variant (time_range),
                Events.from_variant(event_templates),
                storage_state, num_events, result_type, sender);
        }

        public Variant find_events (Variant time_range,
                Variant event_templates,
                uint storage_state, uint num_events, uint result_type,
                BusName sender) throws Error
        {
            var timer = new Timer ();
            var events = engine.find_events (
                new TimeRange.from_variant (time_range),
                Events.from_variant (event_templates),
                storage_state, num_events, result_type, sender);
            debug ("%s executed in %f seconds", Log.METHOD, timer.elapsed ());
            return Events.to_variant (events);
        }

        public uint32[] insert_events (
                Variant vevents,
                BusName sender) throws Error
        {
            var events = Events.from_variant (vevents);

            uint32[] event_ids = engine.insert_events (events, sender);
            var min_timestamp = events[0].timestamp;
            var max_timestamp = min_timestamp;
            for(int i=0; i<events.length; i++)
            {
                min_timestamp = int64.min(min_timestamp, events[i].timestamp);
                max_timestamp = int64.max(max_timestamp, events[i].timestamp);
            }
            notifications.notify_insert (new TimeRange (min_timestamp, max_timestamp), events);

            return event_ids;
        }

        // FIXME
        public Variant delete_events (uint32[] event_ids, BusName sender)
            throws Error
        {
            //FIXME: Why is this not called?
            TimeRange? time_range = engine.delete_events (event_ids, sender);
            if (time_range != null)
            {
                notifications.notify_delete(time_range, event_ids);
            }
            else
            {
                // All the given event_ids are invalod or the events
                // have already been deleted before!
                time_range = new TimeRange (-1, -1);
            }
            return time_range.to_variant ();
        }

        public void quit () throws Error
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
                BusName owner) throws Error
        {
            notifications.install_monitor (owner, monitor_path,
                new TimeRange.from_variant (time_range),
                Events.from_variant (event_templates));
        }

        public void remove_monitor (ObjectPath monitor_path, BusName owner)
            throws Error
        {
            notifications.remove_monitor (owner, monitor_path);
        }

        public void register_dbus_object (DBusConnection conn) throws IOError
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

            var opt_context = new OptionContext (" - Zeitgeist daemon");
            opt_context.add_main_entries (options, null);

            try
            {
                opt_context.parse (ref args);

                if (show_version_info)
                {
                    stdout.printf ("0.8.99\n"); // FIXME!
                    return 0;
                }
                if (show_options)
                {
                    foreach (unowned OptionEntry? entry in options)
                    {
                        if (entry.long_name != null)
                            stdout.printf ("--%s ", entry.long_name);
                        if (entry.short_name != 0)
                            stdout.printf ("-%c ", entry.short_name);
                    }
                    stdout.printf ("--help\n");

                    return 0;
                }
                run ();
            }
            catch (Error err)
            {
                warning ("%s", err.message);
            }

            return 0;
        }

    }

}
// vim:expandtab:ts=4:sw=4
