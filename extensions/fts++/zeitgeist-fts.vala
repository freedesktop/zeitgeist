/* zeitgeist-fts.vala
 *
 * Copyright © 2012 Canonical Ltd.
 * Copyright © 2012 Michal Hruby <michal.mhr@gmail.com>
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 */

namespace Zeitgeist
{

    [DBus (name = "org.freedesktop.DBus")]
    public interface RemoteDBus : Object
    {
        public abstract bool name_has_owner (string name) throws IOError;
    }

    public class FtsDaemon : Object, RemoteSimpleIndexer, RemoteMonitor
    {
        //const string DBUS_NAME = "org.gnome.zeitgeist.Fts";
        const string DBUS_NAME = "org.gnome.zeitgeist.SimpleIndexer";
        const string ZEITGEIST_DBUS_NAME = "org.gnome.zeitgeist.Engine";
        private static bool show_version_info = false;
        private static string log_level = "";

        const OptionEntry[] options =
        {
            {
                "version", 'v', 0, OptionArg.NONE, out show_version_info,
                "Print program's version number and exit", null
            },
            {
                "log-level", 0, 0, OptionArg.STRING, out log_level,
                "How much information should be printed; possible values: " +
                "DEBUG, INFO, WARNING, ERROR, CRITICAL", "LEVEL"
            },
            {
                null
            }
        };

        private static FtsDaemon? instance;
        private static MainLoop mainloop;
        private static bool name_acquired = false;
        private static bool zeitgeist_up = false;

        private DbReader engine;
        private Indexer indexer;

        private uint indexer_register_id;
        private uint monitor_register_id;
        private unowned DBusConnection connection;

        public FtsDaemon () throws EngineError
        {
            engine = new DbReader ();
            engine.database.set_cache_size (16);
            indexer = new Indexer (engine);
        }

        private void close ()
        {
            engine.close ();
            indexer = null; // close the index
        }

        public void register_dbus_object (DBusConnection conn) throws IOError
        {
            connection = conn;
            indexer_register_id = conn.register_object<RemoteSimpleIndexer> (
                    "/org/gnome/zeitgeist/index/activity", this);
            monitor_register_id = conn.register_object<RemoteMonitor> (
                    "/org/gnome/zeitgeist/monitor/special", this);
        }

        public void unregister_dbus_object ()
        {
            if (indexer_register_id != 0)
            {
                connection.unregister_object (indexer_register_id);
                indexer_register_id = 0;
            }

            if (monitor_register_id != 0)
            {
                connection.unregister_object (monitor_register_id);
                monitor_register_id = 0;
            }
        }

        public async void notify_insert (Variant time_range, Variant events)
            throws Error
        {
            debug ("got insertion notification");
            var events_arr = Events.from_variant (events);
            indexer.index_events (events_arr);
        }

        public async void notify_delete (Variant time_range, uint32[] event_ids)
            throws IOError
        {
            debug ("got deletion notification");
            indexer.delete_events (event_ids);
        }

        public async void search (string query_string, Variant time_range,
                                  Variant filter_templates,
                                  uint offset, uint count, uint result_type,
                                  Cancellable? cancellable,
                                  out Variant events, out uint matches)
            throws Error
        {
            var tr = new TimeRange.from_variant (time_range);
            var templates = Events.from_variant (filter_templates);
            var results = instance.indexer.search (query_string,
                                                   tr,
                                                   templates,
                                                   offset,
                                                   count,
                                                   (ResultType) result_type,
                                                   out matches);

            events = Events.to_variant (results);
        }

        public async void search_with_relevancies (
                                  string query_string, Variant time_range,
                                  Variant filter_templates,
                                  uint storage_state, uint offset,
                                  uint count, uint result_type,
                                  Cancellable? cancellable,
                                  out Variant events, out double[] relevancies,
                                  out uint matches)
            throws Error
        {
            var tr = new TimeRange.from_variant (time_range);
            var templates = Events.from_variant (filter_templates);
            var results = instance.indexer.search_with_relevancies (
                    query_string, tr, templates, (StorageState) storage_state,
                    offset, count, (ResultType) result_type,
                    out relevancies, out matches);

            events = Events.to_variant (results);
        }

        private static void name_acquired_callback (DBusConnection conn)
        {
            name_acquired = true;
        }

        private static void name_lost_callback (DBusConnection? conn)
        {
            if (conn == null)
            {
                // something happened to our bus connection
                mainloop.quit ();
            }
            else if (instance != null && name_acquired)
            {
                // we owned the name and we lost it... what to do?
                mainloop.quit ();
            }
        }

        private static void zeitgeist_vanished ()
        {
            if (zeitgeist_up)
            {
                // client APIs query us via zeitgeist, so quit if ZG goes away
                mainloop.quit ();
            }
            zeitgeist_up = false;
        }

        static void run ()
            throws Error
        {
            DBusConnection connection = Bus.get_sync (BusType.SESSION);
            var proxy = connection.get_proxy_sync<RemoteDBus> (
                "org.freedesktop.DBus", "/org/freedesktop/DBus",
                DBusProxyFlags.DO_NOT_LOAD_PROPERTIES);
            if (proxy.name_has_owner (DBUS_NAME))
            {
                throw new EngineError.EXISTING_INSTANCE (
                    "The FTS daemon is running already.");
            }

            /* setup Engine instance and register objects on dbus */
            try
            {
                instance = new FtsDaemon ();
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
                        "is already running (the database is locked).");
                }
                throw err;
            }

            uint owner_id = Bus.own_name_on_connection (connection,
                DBUS_NAME,
                BusNameOwnerFlags.NONE,
                name_acquired_callback,
                name_lost_callback);

            Bus.watch_name (BusType.SESSION, ZEITGEIST_DBUS_NAME, 0,
                () => { zeitgeist_up = true; },
                zeitgeist_vanished);

            mainloop = new MainLoop ();
            mainloop.run ();

            if (instance != null)
            {
                // Close any database connections
                instance.close ();

                // Release the bus name
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
            mainloop.quit ();
        }

        static int main (string[] args)
        {
            // FIXME: the cat process xapian spawns won't like this and we
            // can freeze if it dies
            Posix.signal (Posix.SIGHUP, safe_exit);
            Posix.signal (Posix.SIGINT, safe_exit);
            Posix.signal (Posix.SIGTERM, safe_exit);

            var opt_context = new OptionContext (" - Zeitgeist FTS daemon");
            opt_context.add_main_entries (options, null);

            try
            {
                opt_context.parse (ref args);

                if (show_version_info)
                {
                    stdout.printf (Config.VERSION + "\n");
                    return 0;
                }

                LogLevelFlags discarded = LogLevelFlags.LEVEL_DEBUG;
                if (log_level != null)
                {
                    var ld = LogLevelFlags.LEVEL_DEBUG;
                    var li = LogLevelFlags.LEVEL_INFO;
                    var lm = LogLevelFlags.LEVEL_MESSAGE;
                    var lw = LogLevelFlags.LEVEL_WARNING;
                    var lc = LogLevelFlags.LEVEL_CRITICAL;
                    switch (log_level.up ())
                    {
                        case "DEBUG":
                            discarded = 0;
                            break;
                        case "INFO":
                            discarded = ld;
                            break;
                        case "WARNING":
                            discarded = ld | li | lm;
                            break;
                        case "CRITICAL":
                            discarded = ld | li | lm | lw;
                            break;
                        case "ERROR":
                            discarded = ld | li | lm | lw | lc;
                            break;
                    }
                }
                if (discarded != 0)
                {
                    GLib.Log.set_handler ("", discarded, () => {});
                }
                else
                {
                    Environment.set_variable ("G_MESSAGES_DEBUG", "all", true);
                }

                run ();
            }
            catch (Error err)
            {
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

}

// vim:expandtab:ts=4:sw=4
