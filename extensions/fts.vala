/* ds-registry.vala
 *
 * Copyright © 2011 Seif Lotfy <seif@lotfy.com>
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
        public abstract Variant search (
            string query_string,
            [DBus (signature = "(xx)")] Variant time_range,
            [DBus (signature = "a(asaasay)")] Variant filter_templates,
            uint offset, uint count, uint result_type) throws Error;
    }

    [DBus (name = "org.gnome.zeitgeist.SimpleIndexer")]
    public interface Siin : Object 
    {
        [DBus (signature = "a(asaasay)u")]
        public abstract Variant search (
            string query_string,
            [DBus (signature = "(xx)")] Variant time_range,
            [DBus (signature = "a(asaasay)")] Variant filter_templates,
            uint offset, uint count, uint result_type) throws Error;
    }

    class SearchEngine: Extension, RemoteSearchEngine
    {
        
        private Siin siin;
        private uint registration_id;
        
        SearchEngine ()
        {
            Object ();
        }
        
        construct
        {
            try
            {
                siin = Bus.get_proxy_sync (BusType.SESSION, "org.gnome.zeitgeist.Index",
                                                    "/org/gnome/zeitgeist/index/activity");
                warning ("=============================================");
                var connection = Bus.get_sync (BusType.SESSION, null);
                registration_id = connection.register_object<RemoteSearchEngine> (
                    "/org/gnome/zeitgeist/index/activity", this);
            }
            catch (Error err)
            {
                warning ("%s", err.message);
            }
        }
        
        public Variant search (string query_string, Variant time_range, 
            Variant filter_templates, uint offset, uint count, uint result_type)
        {
            return siin.search (query_string, time_range, filter_templates,
                offset, count, result_type);
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
