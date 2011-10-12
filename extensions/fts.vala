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
        [DBus (signature = "a(asaasay)u")]
        public abstract async Variant search (
            string query_string,
            [DBus (signature = "(xx)")] Variant time_range,
            [DBus (signature = "a(asaasay)")] Variant filter_templates,
            uint offset, uint count, uint result_type,
            [DBus (signature = "a(asaasay)")] out Variant events) throws Error;
    }

    /* Because of a Vala bug we have to define the proxy interface outside of
     * [ModuleInit] source */
    /*
    [DBus (name = "org.gnome.zeitgeist.SimpleIndexer")]
    public interface RemoteSimpleIndexer : Object
    {
        [DBus (signature = "a(asaasay)u")]
        public abstract async Variant search (
            string query_string,
            [DBus (signature = "(xx)")] Variant time_range,
            [DBus (signature = "a(asaasay)")] Variant filter_templates,
            uint offset, uint count, uint result_type) throws Error;
    }
    */

    class SearchEngine: Extension, RemoteSearchEngine
    {

        private RemoteSimpleIndexer siin;
        private uint registration_id;

        SearchEngine ()
        {
            Object ();
        }

        construct
        {
            try
            {
                var connection = Bus.get_sync (BusType.SESSION, null);
                registration_id = connection.register_object<RemoteSearchEngine> (
                    "/org/gnome/zeitgeist/index/activity", this);

                // FIXME: shouldn't we delay this to next idle callback?
                // Get SimpleIndexer
                Bus.watch_name_on_connection (connection,
                    "org.gnome.zeitgeist.SimpleIndexer",
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

        /* This whole method is one huge workaround for an issue with Vala
         * enclosing all out/return parameters in a TUPLE variant */
        public async Variant search (string query_string, Variant time_range,
            Variant filter_templates, uint offset, uint count, uint result_type,
            out Variant events) throws Error
        {
            debug ("Performing search for %s", query_string);
            if (siin == null || !(siin is DBusProxy))
            {
                // FIXME: queue until we have the proxy
                throw new EngineError.DATABASE_ERROR (
                    "Not connected to SimpleIndexer");
            }
            var timer = new Timer ();
            DBusProxy proxy = (DBusProxy) siin;
            var b = new VariantBuilder (new VariantType ("(s(xx)a(asaasay)uuu)"));
            b.add ("s", query_string);
            b.add_value (time_range);
            b.add_value (filter_templates);
            b.add ("u", offset);
            b.add ("u", count);
            b.add ("u", result_type);
            var result = yield proxy.call ("Search", b.end (), 0, -1, null);
            events = result.get_child_value (0);
            /* FIXME: this somehow doesn't work :(
             *   but it's fixable in a similar way as this method's signature
             *   is done */
            /*
            var result = yield siin.search (query_string, time_range,
                filter_templates, offset, count, result_type);
            */
            debug ("Got %u results from indexer (in %f seconds)",
                (uint) events.n_children (), timer.elapsed ());
            return result.get_child_value (1);
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
