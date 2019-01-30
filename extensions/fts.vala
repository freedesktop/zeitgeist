/* fts.vala
 *
 * Copyright © 2011 Seif Lotfy <seif@lotfy.com>
 * Copyright © 2011 Canonical Ltd.
 *             By Michal Hruby <michal.hruby@canonical.com>
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
    [DBus (name = "org.gnome.zeitgeist.Index")]
    public interface RemoteSearchEngine: Object
    {
        public abstract async void search (
            string query_string,
            [DBus (signature = "(xx)")] Variant time_range,
            [DBus (signature = "a(asaasay)")] Variant filter_templates,
            uint offset, uint count, uint result_type,
            Cancellable? cancellable,
            [DBus (signature = "a(asaasay)")] out Variant events,
            out uint matches) throws Error;
        public abstract async void search_with_relevancies (
            string query_string,
            [DBus (signature = "(xx)")] Variant time_range,
            [DBus (signature = "a(asaasay)")] Variant filter_templates,
            uint storage_state, uint offset, uint count, uint result_type,
            Cancellable? cancellable,
            [DBus (signature = "a(asaasay)")] out Variant events,
            out double[] relevancies,
            out uint matches) throws Error;
    }

    public class SearchEngine: Extension, RemoteSearchEngine
    {

        private const string INDEXER_NAME = "org.gnome.zeitgeist.SimpleIndexer";

        private RemoteSimpleIndexer siin;
        private bool siin_connection_failed = false;
        private uint registration_id;
        private MonitorManager? notifier;

        SearchEngine ()
        {
            Object ();
        }

        construct
        {
            if (Utils.using_in_memory_database ()) return;

            // FIXME: check dbus and see if fts is installed?

            // installing a monitor from the daemon will ensure that we don't
            // miss any notifications that would be emitted in between
            // zeitgeist start and fts daemon start
            notifier = MonitorManager.get_default ();
            notifier.install_monitor (new BusName (INDEXER_NAME),
                                      "/org/gnome/zeitgeist/monitor/special",
                                      new TimeRange.anytime (),
                                      new GenericArray<Event> ());

            try
            {
                var connection = Bus.get_sync (BusType.SESSION, null);
                registration_id = connection.register_object<RemoteSearchEngine> (
                    "/org/gnome/zeitgeist/index/activity", this);

                try
                {
                    // make sure FTS uses the same environment as us
                    var env = new HashTable<string, string> (str_hash, str_equal);
                    env["ZEITGEIST_DATA_PATH"] = Utils.get_data_path ();
                    connection.call.begin ("org.freedesktop.DBus",
                                     "/org/freedesktop/DBus",
                                     "org.freedesktop.DBus",
                                     "UpdateActivationEnvironment",
                                     new Variant.tuple ({env}),
                                     null, 0, -1, null, null);
                }
                catch (Error err)
                {
                    // isn't that terrible if this fails
                    warning ("Unable to set environment for FTS daemon!");
                }

                // FIXME: shouldn't we delay this to next idle callback?
                // Get SimpleIndexer
                connection.get_proxy.begin<RemoteSimpleIndexer> (
                    INDEXER_NAME,
                    "/org/gnome/zeitgeist/index/activity",
                    0, null, this.proxy_acquired);
            }
            catch (Error err)
            {
                warning ("%s", err.message);
            }
        }

        private void proxy_not_present()
        {
            notifier.remove_monitor (new BusName (INDEXER_NAME),"/org/gnome/zeitgeist/monitor/special");
            this.unload();
        }

        private void proxy_acquired (Object? obj, AsyncResult res)
        {
            var conn = obj as DBusConnection;
            try
            {
                siin = conn.get_proxy.end<RemoteSimpleIndexer> (res);
                if((siin as DBusProxy).g_name_owner == null)
                {
                    this.proxy_not_present();
                    siin_connection_failed = true;
                }
                else
                {
                    siin_connection_failed = false;
                }
            }
            catch (IOError err)
            {
                siin_connection_failed = true;
                warning ("%s", err.message);
            }
        }

        public async void wait_for_proxy () throws Error
        {
            int i = 0;
            while (this.siin == null && i < 6 && !siin_connection_failed)
            {
                Timeout.add_full (Priority.DEFAULT_IDLE, 250,
                                  wait_for_proxy.callback);
                i++;
                yield;
            }

            if (siin == null || !(siin is DBusProxy))
            {
                // FIXME: queue until we have the proxy
                throw new EngineError.DATABASE_ERROR (
                    "Not connected to SimpleIndexer");
            }
        }

        public override void unload ()
        {
            try
            {
                var connection = Bus.get_sync (BusType.SESSION, null);
                if (registration_id != 0)
                {
                    connection.unregister_object (registration_id);
                    registration_id = 0;
                }
            }
            catch (Error err)
            {
                warning ("%s", err.message);
            }

            debug ("%s, this.ref_count = %u", GLib.Log.METHOD, this.ref_count);
        }

        public async void search (string query_string, Variant time_range,
            Variant filter_templates, uint offset, uint count, uint result_type,
            Cancellable? cancellable, out Variant events,
            out uint matches) throws Error
        {
            if (siin == null) yield wait_for_proxy ();

            var timer = new Timer ();
            yield siin.search (query_string, time_range, filter_templates,
                               offset, count, result_type, cancellable,
                               out events, out matches);
            debug ("Got %u[/%u] results from indexer (in %f seconds)",
                (uint) events.n_children (), matches, timer.elapsed ());
        }

        public async void search_with_relevancies (
            string query_string, Variant time_range,
            Variant filter_templates, uint storage_state,
            uint offset, uint count, uint result_type,
            Cancellable? cancellable, out Variant events,
            out double[] relevancies, out uint matches) throws Error
        {
            if (siin == null) yield wait_for_proxy ();

            var timer = new Timer ();
            yield siin.search_with_relevancies (
                query_string, time_range, filter_templates,
                storage_state, offset, count, result_type, cancellable,
                out events, out relevancies, out matches);

            debug ("Got %u[/%u] results from indexer (in %f seconds)",
                (uint) events.n_children (), matches, timer.elapsed ());
        }

    }

    [ModuleInit]
#if BUILTIN_EXTENSIONS
    public static Type fts_init (TypeModule module)
    {
#else
    public static Type extension_register (TypeModule module)
    {
#endif
        return typeof (SearchEngine);
    }
}

// vim:expandtab:ts=4:sw=4
