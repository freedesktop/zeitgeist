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
            [DBus (signature = "a(asaasay)")] out Variant events,
            out uint matches) throws Error;
    }

    /* Because of a Vala bug we have to define the proxy interface outside of
     * [ModuleInit] source */
    /*
    [DBus (name = "org.gnome.zeitgeist.SimpleIndexer")]
    public interface RemoteSimpleIndexer : Object
    {
        public abstract async void search (
            string query_string,
            [DBus (signature = "(xx)")] Variant time_range,
            [DBus (signature = "a(asaasay)")] Variant filter_templates,
            uint offset, uint count, uint result_type,
            [DBus (signature = "a(asaasay)")] out Variant events,
            out uint matches) throws Error;
    }
    */

    class SearchEngine: Extension, RemoteSearchEngine
    {

        private const string INDEXER_NAME = "org.gnome.zeitgeist.SimpleIndexer";

        private RemoteSimpleIndexer siin;
        private uint registration_id;
        private MonitorManager? notifier;

        SearchEngine ()
        {
            Object ();
        }

        construct
        {
            if (Utils.using_in_memory_database ()) return;

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

                // FIXME: shouldn't we delay this to next idle callback?
                // Get SimpleIndexer
                Bus.watch_name_on_connection (connection,
                    INDEXER_NAME,
                    BusNameWatcherFlags.AUTO_START,
                    (conn) =>
                    {
                        if (siin != null) return;
                        conn.get_proxy.begin<RemoteSimpleIndexer> (
                            "org.gnome.zeitgeist.SimpleIndexer",
                            "/org/gnome/zeitgeist/index/activity",
                            0, null, this.proxy_acquired);
                    },
                    () => {});
            }
            catch (Error err)
            {
                warning ("%s", err.message);
            }
        }

        private void proxy_acquired (Object? obj, AsyncResult res)
        {
            var conn = obj as DBusConnection;
            try
            {
                siin = conn.get_proxy.end<RemoteSimpleIndexer> (res);
            }
            catch (IOError err)
            {
                warning ("%s", err.message);
            }
        }

        public async void search (string query_string, Variant time_range,
            Variant filter_templates, uint offset, uint count, uint result_type,
            out Variant events, out uint matches) throws Error
        {
            if (siin == null || !(siin is DBusProxy))
            {
                // FIXME: queue until we have the proxy
                throw new EngineError.DATABASE_ERROR (
                    "Not connected to SimpleIndexer");
            }
            var timer = new Timer ();
            yield siin.search (query_string, time_range, filter_templates,
                               offset, count, result_type,
                               out events, out matches);
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
