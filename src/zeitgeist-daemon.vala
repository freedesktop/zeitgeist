/* zeitgeist-daemon.vala
 *
 * Copyright © 2011 Seif Lotfy <seif@lotfy.com>
 * Copyright © 2011 Michal Hruby <michal.mhr@gmail.com>
 * Copyright © 2011 Collabora Ltd.
 *             By Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
 *             By Seif Lotfy <seif@lotfy.com>
 * Copyright © 2012 Canonical Ltd.
 *             By Siegfried-A. Gevatter <siegfried.gevatter@collabora.co.uk>
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

    [DBus (name = "org.freedesktop.DBus")]
    public interface RemoteDBus : Object
    {
        public abstract bool name_has_owner (string name) throws GLib.Error;
    }

    public class Daemon : Object, RemoteLog
    {
        private static bool show_version_info = false;
        private static bool show_options = false;
        private static bool no_datahub = false;
        private static bool perform_vacuum = false;
        private static bool replace_mode = false;
        private static bool quit_daemon = false;
        private static string log_level = "";
        private static string? log_file = null;

        // load the builtin extensions first
        RegisterExtensionFunc[] builtins = {};

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
                "vacuum", 0, 0, OptionArg.NONE, out perform_vacuum,
                "Perform VACUUM on database and exit", null
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
                "quit", 'q', 0, OptionArg.NONE, out quit_daemon,
                "Quit running Zeitgeist daemon instance", null
            },
            {
                "log-level", 0, 0, OptionArg.STRING, out log_level,
                "How much information should be printed; possible values: " +
                "DEBUG, INFO, WARNING, ERROR, CRITICAL", "LEVEL"
            },
            {
                "log-file", 0, 0, OptionArg.STRING, out log_file,
                "File to which the log output will be appended", null
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
        private static bool name_acquired = false;

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

        public VersionStruct version
        {
            owned get
            {
                var s = VersionStruct ();
                string[] ver = Config.VERSION.split (".");
                if (ver.length >= 1)
                {
                    s.major = int.parse (ver[0]);
                    s.minor = (ver.length >= 2) ? int.parse (ver[1]) : 0;
                    s.micro = (ver.length >= 3) ? int.parse (ver[2]) : 0;
                } else {
                    warning ("Unable to parse version info `%s`!", Config.VERSION);
                    s.major = 1;
                    s.minor = 0;
                    s.micro = 0;
                }

                return s;
            }
        }

        public string datapath
        {
            owned get
            {
                return Utils.get_database_file_path ();
            }
        }

        public Daemon () throws EngineError
        {
#if BUILTIN_EXTENSIONS
            builtins = {
                data_source_registry_extension_init,
                blacklist_init,
                histogram_init,
                storage_monitor_init,
                fts_init,
                benchmark_init
            };
#endif
            engine = new Engine.with_builtins (builtins);
            notifications = MonitorManager.get_default ();
        }

        public async Variant get_events (uint32[] event_ids, Cancellable? cancellable,
            BusName? sender=null) throws Error
        {
            var timer = new Timer ();
            GenericArray<Event> events = engine.get_events (event_ids);
            debug ("%s executed in %f seconds: got %i events",
                GLib.Log.METHOD, timer.elapsed (), events.length);
            return Events.to_variant_with_limit (events);
        }

        public async string[] find_related_uris (Variant time_range,
                Variant event_templates,
                Variant result_event_templates,
                uint storage_state, uint num_events, uint result_type,
                Cancellable? cancellable, BusName? sender=null) throws Error
        {
            return engine.find_related_uris (
                new TimeRange.from_variant (time_range),
                Events.from_variant (event_templates),
                Events.from_variant (result_event_templates),
                storage_state, num_events, result_type);
        }

        public async uint32[] find_event_ids (Variant time_range,
                Variant event_templates,
                uint storage_state, uint num_events, uint result_type,
                Cancellable? cancellable=null,
                BusName? sender=null) throws Error
        {
            var timer = new Timer ();
            var ids = engine.find_event_ids (
                new TimeRange.from_variant (time_range),
                Events.from_variant(event_templates),
                storage_state, num_events, result_type, sender);
            debug ("%s executed in %f seconds: found %i event ids",
                GLib.Log.METHOD, timer.elapsed (), ids.length);
            return ids;
        }

        public async Variant find_events (Variant time_range,
                Variant event_templates,
                uint storage_state, uint num_events, uint result_type,
                Cancellable? cancellable=null,
                BusName? sender=null) throws Error
        {
            var timer = new Timer ();
            var events = engine.find_events (
                new TimeRange.from_variant (time_range),
                Events.from_variant (event_templates),
                storage_state, num_events, result_type, sender);
            debug ("%s executed in %f seconds: found %i events",
                GLib.Log.METHOD, timer.elapsed (), events.length);
            return Events.to_variant_with_limit (events);
        }

        public async uint32[] insert_events (
                Variant vevents,
                Cancellable? cancellable=null,
                BusName? sender=null) throws Error
        {
            var events = Events.from_variant (vevents);
            uint32[] event_ids = engine.insert_events (events, sender);
            var min_timestamp = int64.MAX;
            var max_timestamp = int64.MIN;
            for (int i = 0; i < events.length; i++)
            {
                if (events[i] == null) continue;
                min_timestamp = int64.min (min_timestamp, events[i].timestamp);
                max_timestamp = int64.max (max_timestamp, events[i].timestamp);
            }

            if (min_timestamp < int64.MAX)
            {
                notifications.notify_insert (
                    new TimeRange (min_timestamp, max_timestamp), events);
            }
            /* else { there's not even one valid event } */

            return event_ids;
        }

        public async Variant delete_events (uint32[] event_ids,
            Cancellable? cancellable=null, BusName? sender=null) throws Error
        {
            TimeRange? time_range = engine.delete_events (event_ids, sender);
            if (time_range != null)
            {
                notifications.notify_delete (time_range, event_ids);
            }
            else
            {
                // All the given event_ids are invalod or the events
                // have already been deleted before!
                time_range = new TimeRange (-1, -1);
            }
            return time_range.to_variant ();
        }

        public async void quit (Cancellable? cancellable=null) throws Error
        {
            do_quit ();
        }

        private void do_quit ()
        {
            engine.close ();
            mainloop.quit ();
        }

        public async void install_monitor (ObjectPath monitor_path,
                Variant time_range,
                Variant event_templates,
                BusName? owner=null) throws Error
        {
            assert (owner != null);
            notifications.install_monitor (owner, monitor_path,
                new TimeRange.from_variant (time_range),
                Events.from_variant (event_templates));
        }

        public async void remove_monitor (ObjectPath monitor_path, BusName? owner=null)
            throws Error
        {
            assert (owner != null);
            notifications.remove_monitor (owner, monitor_path);
        }

        public void register_dbus_object (DBusConnection conn) throws IOError
        {
            connection = conn;
            log_register_id = conn.register_object<RemoteLog> (
                Utils.ENGINE_DBUS_PATH, this);
        }

        public void unregister_dbus_object ()
        {
            if (log_register_id != 0)
            {
                connection.unregister_object (log_register_id);
                log_register_id = 0;
            }
        }

        private static bool quit_running_instance (DBusConnection conn)
        {
            try
            {
                var running_instance = conn.get_proxy_sync<RemoteLog> (
                    Utils.ENGINE_DBUS_NAME, Utils.ENGINE_DBUS_PATH);

                running_instance.quit.begin ();
                return true;
            }
            catch (Error err)
            {
                warning ("%s", err.message);
            }

            return false;
        }

        private static void name_acquired_callback (DBusConnection conn)
        {
            name_acquired = true;

            // only run datahub when we acquire bus name
            if (!no_datahub)
            {
                try
                {
                    Process.spawn_command_line_async ("zeitgeist-datahub");
                }
                catch (SpawnError err)
                {
                    warning ("%s", err.message);
                }
            }
        }

        private static void name_lost_callback (DBusConnection? conn)
        {
            if (conn == null)
            {
                // something happened to our bus connection
                mainloop.quit ();
            }
            else if (instance != null && !name_acquired)
            {
                // we acquired bus connection, but couldn't own the name
                if (!replace_mode)
                {
                }

                debug ("Waiting 10 seconds to acquire name...");
                // we already called Quit, let's wait a while
                // for the running instance to quit, bail out
                // if it doesn't
                Timeout.add (10000, () =>
                {
                    if (!name_acquired)
                    {
                        warning ("Timeout reached, unable to acquire name!");
                        mainloop.quit ();
                    }
                    return false;
                });
            }
            else if (instance != null && name_acquired)
            {
                // we owned the name and we lost it... what to do?
                mainloop.quit ();
            }
        }

        static void run ()
            throws Error
        {
            DBusConnection connection;
            bool name_owned;
            try
            {
                connection = Bus.get_sync (BusType.SESSION);
                var proxy = connection.get_proxy_sync<RemoteDBus> (
                    "org.freedesktop.DBus", "/org/freedesktop/DBus",
                    DBusProxyFlags.DO_NOT_LOAD_PROPERTIES);
                name_owned = proxy.name_has_owner (Utils.ENGINE_DBUS_NAME);
            }
            catch (IOError err)
            {
                throw err;
            }
            if (name_owned)
            {
                if (replace_mode || quit_daemon)
                {
                    quit_running_instance (connection);
                }
                else
                {
                    warning ("An existing instance was found. Please use " +
                        "--replace to stop it and start a new instance.");
                    throw new EngineError.EXISTING_INSTANCE (
                        "Zeitgeist is running already.");
                }
            }

            /* don't do anything else if we were called with --quit param */
            if (quit_daemon) return;

            /* setup Engine instance and register objects on dbus */
            try
            {
                instance = new Daemon ();
                instance.register_dbus_object (connection);
            }
            catch (Error err)
            {
                if (err is EngineError.DATABASE_CANTOPEN)
                {
                    warning ("Could not access the database file.\n" +
                        "Please check the permissions of file %s.",
                        Utils.get_database_file_path ());
                }
                else if (err is EngineError.DATABASE_BUSY)
                {
                    warning ("It looks like another Zeitgeist instance " +
                        "is already running (the database is locked). " +
                        "If you want to start a new instance, use --replace.");
                }
                throw err;
            }

            uint owner_id = Bus.own_name_on_connection (connection,
                Utils.ENGINE_DBUS_NAME,
                BusNameOwnerFlags.NONE,
                name_acquired_callback,
                name_lost_callback);

            mainloop = new MainLoop ();
            mainloop.run ();

            if (instance != null)
            {
                Bus.unown_name (owner_id);
                instance.unregister_dbus_object ();
                instance = null;

                // make sure we send quit reply
                try
                {
                    connection.flush_sync ();
                }
                catch (Error e)
                {
                    warning ("%s", e.message);
                }
            }
        }

        static void safe_exit ()
        {
            instance.do_quit ();
        }

        static int vacuum ()
        {
            Sqlite.Database database;

            if (Utils.using_in_memory_database ())
                warning ("Using in-memory database, no VACUUM needed");

            unowned string db_path = Utils.get_database_file_path ();
            debug ("Opening database file at %s", db_path);

            int rc = Sqlite.Database.open_v2 (db_path, out database, Sqlite.OPEN_READWRITE);
            if (rc != Sqlite.OK)
            {
                warning ("Failed to open database \"%s\" (%s)", db_path, database.errmsg ());
                return rc;
            }

            stdout.printf ("Performing VACUUM operation... ");
            stdout.flush ();
            rc = database.exec ("VACUUM");
            if (rc != Sqlite.OK)
            {
                stdout.printf ("FAIL\n");
                warning (database.errmsg ());
                return rc;
            }

            stdout.printf ("OK\n");

            return 0;
        }

        static int main (string[] args)
        {
            Posix.signal (Posix.SIGHUP, safe_exit);
            Posix.signal (Posix.SIGINT, safe_exit);
            Posix.signal (Posix.SIGTERM, safe_exit);

            Intl.setlocale (LocaleCategory.ALL, "");

            var opt_context = new OptionContext (" - Zeitgeist daemon");
            opt_context.add_main_entries (options, null);

            try
            {
                opt_context.parse (ref args);

                if (show_version_info)
                {
                    stdout.printf (Config.VERSION + "\n");
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
                if (perform_vacuum)
                {
                    return vacuum ();
                }

                Logging.setup_logging (log_level, log_file);

                run ();
            }
            catch (Error err)
            {
                if (err is EngineError.EXISTING_INSTANCE)
                    return 10;
                if (err is EngineError.DATABASE_CANTOPEN)
                    return 21;
                if (err is EngineError.DATABASE_BUSY)
                    return 22;

                warning ("%s", err.message);
                return 1;
            }

            return 0;
        }

    }

#if BUILTIN_EXTENSIONS
    private extern static Type data_source_registry_extension_init (TypeModule mod);
    private extern static Type blacklist_init (TypeModule mod);
    private extern static Type histogram_init (TypeModule mod);
    private extern static Type storage_monitor_init (TypeModule mod);
    private extern static Type fts_init (TypeModule mod);
    private extern static Type benchmark_init (TypeModule mod);
#endif
}

// vim:expandtab:ts=4:sw=4
