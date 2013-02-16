/* benchmark.vala
 *
 * Copyright © 2011 Collabora Ltd.
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
    [DBus (name = "org.gnome.zeitgeist.Benchmark")]
    public interface RemoteBenchmarker: Object
    {
        public abstract async HashTable<string, Variant> find_events (
            [DBus (signature = "(xx)")] Variant time_range,
            [DBus (signature = "a(asaasay)")] Variant event_templates,
            uint storage_state, uint num_events, uint result_type)
            throws Error;
    }

    public class Benchmarker: Extension, RemoteBenchmarker
    {

        private uint registration_id;

        Benchmarker ()
        {
            Object ();
        }

        construct
        {
            try
            {
                var connection = Bus.get_sync (BusType.SESSION, null);
                registration_id = connection.register_object<RemoteBenchmarker> (
                    "/org/gnome/zeitgeist/benchmark", this);
            }
            catch (Error err)
            {
                warning ("%s", err.message);
            }
        }

        public async HashTable<string, Variant> find_events (Variant time_range,
            Variant filter_templates, uint storage_state, uint num_events,
            uint result_type)
            throws Error
        {
            var data = new HashTable<string, Variant> (str_hash, str_equal);

            var find_event_ids_timer = new Timer ();
            var ids = engine.find_event_ids (
                new TimeRange.from_variant (time_range),
                Events.from_variant (filter_templates),
                storage_state, num_events, result_type);
            var find_event_ids_elapsed = find_event_ids_timer.elapsed();

            var get_events_timer = new Timer ();
            var events = engine.get_events (ids);
            var get_events_elapsed = get_events_timer.elapsed();

            var marsh_events_timer = new Timer ();
            var marsh_events = Events.to_variant(events);
            var marsh_events_elapsed = marsh_events_timer.elapsed();

            var find_events_elapsed = get_events_elapsed + find_event_ids_elapsed + marsh_events_elapsed;

            data.insert("find_event_ids",
                new Variant.double(find_event_ids_elapsed));
            data.insert("get_events",
                new Variant.double(get_events_elapsed));
            data.insert("find_events",
                new Variant.double(find_events_elapsed));
            data.insert("marsh_events",
                new Variant.double(marsh_events_elapsed));
            data.insert("events", marsh_events);

            return data;
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

    }

    [ModuleInit]
#if BUILTIN_EXTENSIONS
    public static Type benchmark_init (TypeModule module)
    {
#else
    public static Type extension_register (TypeModule module)
    {
#endif
        return typeof (Benchmarker);
    }
}

// vim:expandtab:ts=4:sw=4
