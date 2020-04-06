/* ds-registry.vala
 *
 * Copyright © 2011 Michal Hruby <michal.mhr@gmail.com>
 * Copyright © 2011 Collabora Ltd.
 *             By Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
 *
 * Based upon a Python implementation (2009-2010) by:
 *  Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
 *  Mikkel Kamstrup Erlandsen <mikkel.kamstrup@gmail.com>
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

using Zeitgeist;

namespace Zeitgeist
{

    namespace DataSources
    {
        private static HashTable<string, DataSource> registry_from_variant (
            Variant sources_variant, bool reset_running=false) throws DataModelError
        {
            var registry = new HashTable<string, DataSource> (
                str_hash, str_equal);

            warn_if_fail (
                sources_variant.get_type_string() == DataSources.SIG_DATASOURCES);
            foreach (Variant ds_variant in sources_variant)
            {
                DataSource ds = new DataSource.from_variant (ds_variant,
                    reset_running);
                registry.insert (ds.unique_id, ds);
            }

            return registry;
        }
    }

    public class DataSourceRegistryExtension: Extension, RemoteRegistry
    {
        private const string MULTIPLE_MARKER = "<multiple>";
        private HashTable<string, DataSource> sources;
        private HashTable<string, GenericArray<BusName>> running_ds;
        private HashTable<string, string> bus_name_2_ds;
        private uint registration_id;
        private bool dirty;

        private const uint DISK_WRITE_TIMEOUT = 5 * 60; // 5 minutes

        DataSourceRegistryExtension ()
        {
            Object ();
        }

        construct
        {
            bus_name_2_ds = new HashTable<string, string> (str_hash, str_equal);
            running_ds = new HashTable<string, GenericArray<BusName?>>(
                str_hash, str_equal);

            Variant? registry = retrieve_config ("registry",
                DataSources.SIG_DATASOURCES);
            if (registry != null)
            {
                try
                {
                    sources = DataSources.registry_from_variant (registry, true);
                }
                catch (DataModelError e)
                {
                    warning ("Error while loading datasource registry: %s", e.message);
                    sources = new HashTable<string, DataSource> (
                        str_hash, str_equal);
                }
            }
            else
            {
                sources = new HashTable<string, DataSource> (
                    str_hash, str_equal);
            }

            // this will be called after bus is acquired, so it shouldn't block
            try
            {
                var connection = Bus.get_sync (BusType.SESSION, null);
                registration_id = connection.register_object<RemoteRegistry> (
                    "/org/gnome/zeitgeist/data_source_registry", this);

                connection.signal_subscribe ("org.freedesktop.DBus",
                    "org.freedesktop.DBus", "NameOwnerChanged",
                    "/org/freedesktop/DBus", null, 0,
                    name_owner_changed);
            }
            catch (Error err)
            {
                warning ("%s", err.message);
            }

            // Changes are saved to the DB every few seconds and at unload.
            Timeout.add_seconds (DISK_WRITE_TIMEOUT, flush, Priority.LOW);
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

            flush ();
            debug ("%s, this.ref_count = %u", GLib.Log.METHOD, this.ref_count);
        }

        public async Variant get_data_sources (Cancellable? cancellable=null)
        {
            return DataSources.to_variant (sources);
        }

        private bool is_sender_known (BusName sender,
            GenericArray<BusName> sender_array)
        {
            for (int i = 0; i < sender_array.length; i++)
            {
                if (sender == sender_array[i])
                    return true;
            }
            return false;
        }

        public async bool register_data_source (string unique_id,
            string name, string description, Variant event_templates,
            Cancellable? cancellable=null, BusName? sender)
            throws DataModelError
        {
            debug ("%s: %s, %s, %s", GLib.Log.METHOD, unique_id,
                name, description);
            if (sender == null)
            {
                warning ("%s: sender == null, ignoring request", GLib.Log.METHOD);
                return false;
            }


            var sender_array = running_ds.lookup (unique_id);
            if (sender_array == null)
            {
                sender_array = new GenericArray<BusName?>();
                sender_array.add (sender);
                running_ds.insert (unique_id, sender_array);
            }
            else if (!is_sender_known (sender, sender_array))
            {
                sender_array.add (sender);
            }

            unowned string ds_id = bus_name_2_ds.lookup (sender);
            if (ds_id == null)
            {
                bus_name_2_ds.insert (sender, unique_id);
            }
            else if (ds_id != unique_id && ds_id != MULTIPLE_MARKER)
            {
                bus_name_2_ds.insert (sender, MULTIPLE_MARKER);
            }

            GenericArray<Event> templates; // Vala: block scopes in async buggy
            unowned DataSource? ds = sources.lookup (unique_id);
            if (ds != null)
            {
                templates = Events.from_variant (event_templates);
                ds.name = name;
                ds.description = description;
                ds.event_templates = templates;
                ds.timestamp = Timestamp.from_now ();
                ds.running = true;
                dirty = true;

                data_source_registered (ds.to_variant ());

                return ds.enabled;
            }
            else
            {
                templates = Events.from_variant (event_templates);
                DataSource new_ds = new DataSource.full (unique_id, name,
                    description, templates);
                new_ds.enabled = true;
                new_ds.running = true;
                new_ds.timestamp = Timestamp.from_now ();
                sources.insert (unique_id, new_ds);
                dirty = true;

                data_source_registered (new_ds.to_variant ());

                return new_ds.enabled;
            }

        }

        public async void set_data_source_enabled (string unique_id, bool enabled,
            Cancellable? cancellable=null)
        {
            debug ("%s: %s, %d", GLib.Log.METHOD, unique_id, (int) enabled);
            unowned DataSource? ds = sources.lookup (unique_id);
            if (ds != null)
            {
                if (ds.enabled != enabled)
                {
                    ds.enabled = enabled;
                    dirty = true;
                    data_source_enabled (unique_id, enabled);
                }
            }
            else
            {
                warning ("DataSource \"%s\" isn't registered!", unique_id);
            }
        }

        public async Variant get_data_source_from_id (string unique_id,
            Cancellable? cancellable=null) throws Error
        {
            unowned DataSource? ds = sources.lookup (unique_id);
            if (ds != null)
            {
                return ds.to_variant ();
            }

            throw new EngineError.INVALID_KEY (
                "Datasource with unique ID: %s not found".printf (unique_id));
        }

        public override void pre_insert_events (GenericArray<Event?> events,
            BusName? sender)
        {
            foreach (unowned string unique_id in running_ds.get_keys())
            {
                GenericArray<BusName?> bus_names = running_ds.lookup (unique_id);
                if (is_sender_known (sender, bus_names))
                {
                    var data_source = sources.lookup (unique_id);

                    data_source.timestamp = Timestamp.from_now ();
                    dirty = true;

                    // if one sender registers multiple unique data sources,
                    // we have to rely that it's the correct thing, otherwise
                    // we can just ignore the events
                    unowned string ds_id = bus_name_2_ds.lookup (sender);
                    if (!data_source.enabled && ds_id != MULTIPLE_MARKER)
                    {
                        for (int i = 0; i < events.length; i++)
                            events[i] = null;
                    }
                }
            }
        }

        /*
         * Cleanup disconnected clients and mark data-sources as not running
         * when no client remains.
         **/
        private void name_owner_changed (DBusConnection conn, string? sender,
            string path, string interface_name, string signal_name,
            Variant parameters)
        {
            var name = parameters.get_child_value (0).dup_string ();
            //var old_owner = parameters.get_child_value (1).dup_string ();
            var new_owner = parameters.get_child_value (2).dup_string ();
            if (new_owner != "") return;

            // Are there data-sources with this bus name?
            var disconnected_ds = new GenericArray<DataSource> ();
            {
                var iter = HashTableIter<string, GenericArray<BusName?>> (
                    running_ds);
                unowned string uid;
                unowned GenericArray<BusName> name_arr;
                while (iter.next (out uid, out name_arr))
                {
                    for (int i = 0; i < name_arr.length; i++)
                    {
                        if (name_arr[i] == name)
                        {
                            disconnected_ds.add (sources.lookup (uid));
                            name_arr.remove_index_fast (i--);
                        }
                    }
                }
            }

            if (disconnected_ds.length == 0) return;

            for (int i = 0; i < disconnected_ds.length; i++)
            {
                var ds = disconnected_ds[i];
                unowned string uid = ds.unique_id;
                debug ("Client disconnected: %s [%s]", ds.name, uid);

                // FIXME: Update here or change semantics to "last insert"?
                ds.timestamp = Timestamp.from_now ();
                dirty = true;

                if (running_ds.lookup (uid).length == 0)
                {
                    debug ("No remaining client running: %s [%s]",
                        ds.name, uid);
                    running_ds.remove (uid);
                    ds.running = false;

                    data_source_disconnected (ds.to_variant ());
                }
            }
        }

        private bool flush ()
        {
            if (dirty)
            {
                Variant v = DataSources.to_variant (sources);
                store_config ("registry", v);
                dirty = false;
            }
            return true;
        }
    }

    [ModuleInit]
#if BUILTIN_EXTENSIONS
    public static Type data_source_registry_extension_init (TypeModule module)
    {
#else
    public static Type extension_register (TypeModule module)
    {
#endif
        return typeof (DataSourceRegistryExtension);
    }
}

// vim:expandtab:ts=4:sw=4
