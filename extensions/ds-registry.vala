/* ds-registry.vala
 *
 * Copyright © 2011 Michal Hruby <michal.mhr@gmail.com>
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

namespace Zeitgeist
{
    [DBus (name = "org.gnome.zeitgeist.DataSourceRegistry")]
    public interface RemoteRegistry: Object
    {
        [DBus (signature = "a(sssa(asaasay)bxb)")]
        public abstract Variant get_data_sources () throws Error;
        public abstract bool register_data_source (string unique_id,
            string name, string description,
            [DBus (signature = "a(asaasay)")] Variant event_templates, BusName? sender)
            throws Error;
        public abstract void set_data_source_enabled (string unique_id,
            bool enabled) throws Error;
        [DBus (signature = "(sssa(asaasay)bxb)")]
        public abstract Variant get_data_source_from_id (string id) throws Error;

        public signal void data_source_disconnected (
            [DBus (signature = "(sssa(asaasay)bxb)")] Variant data_source);
        public signal void data_source_enabled (string unique_id,
            bool enabled);
        public signal void data_source_registered (
            [DBus (signature = "(sssa(asaasay)bxb)")] Variant data_source);
    }

    class DataSource: Object
    {
        public GenericArray<Event>? event_templates { get; set; }
        public string unique_id { get; set; }
        public string name { get; set; }
        public string description { get; set; }

        public bool enabled { get; set; }
        public bool running { get; set; }
        public int64 timestamp { get; set; }

        public DataSource ()
        {
            Object ();
        }

        public DataSource.full (string unique_id, string name,
            string description, GenericArray<Event> templates)
        {
            Object (unique_id: unique_id, name: name, description: description,
                event_templates: templates);
        }

        public DataSource.from_variant (Variant variant)
        {
            // we expect (sssa(asaasay)bxb)
            warn_if_fail (variant.get_type_string () == "(sssa(asaasay)bxb)"
                || variant.get_type_string () == "sssa(asaasay)");
            var iter = variant.iterator ();

            assert (iter.n_children () >= 4);

            unique_id = iter.next_value ().get_string ();
            name = iter.next_value ().get_string ();
            description = iter.next_value ().get_string ();
            event_templates = Events.from_variant (iter.next_value ());

            if (iter.n_children () > 4)
            {
                running = iter.next_value ().get_boolean ();
                timestamp = iter.next_value ().get_int64 ();
                enabled = iter.next_value ().get_boolean ();
            }
        }

        public Variant to_variant ()
        {
            var vb = new VariantBuilder (new VariantType (
                "(sssa(asaasay)bxb)"));

            vb.add ("s", unique_id);
            vb.add ("s", name);
            vb.add ("s", description);
            if (event_templates != null && event_templates.length > 0)
            {
                vb.add_value (Events.to_variant (event_templates));
            }
            else
            {
                vb.open (new VariantType ("a(asaasay)"));
                vb.close ();
            }

            vb.add ("b", running);
            vb.add ("x", timestamp);
            vb.add ("b", enabled);

            return vb.end ();
        }
    }

    class DataSourceRegistry: Extension, RemoteRegistry
    {
        private HashTable<string, DataSource> sources;
        private HashTable<string, GenericArray<BusName?>> running;
        private uint registration_id;
        private bool dirty;

        DataSourceRegistry ()
        {
            Object ();
        }

        construct
        {
            sources = new HashTable<string, DataSource> (str_hash, str_equal);
            running = new HashTable<string, GenericArray<BusName?>>(str_hash, str_equal);
            // FIXME: load data sources

            // this will be called after bus is acquired, so it shouldn't block
            try
            {
                var connection = Bus.get_sync (BusType.SESSION, null);
                registration_id = connection.register_object<RemoteRegistry> (
                    "/org/gnome/zeitgeist/data_source_registry", this);
                
                connection.signal_subscribe ("org.freedesktop.DBus",
                    "org.freedesktop.DBus", "NameOwnerChanged",
                    "/org/freedesktop/DBus", null, 0,
                    (conn, sender, path, ifc_name, sig_name, parameters) =>
                    {
                        // name, old_owner, new_owner
                        var name = parameters.get_child_value (0).dup_string ();
                        var old_owner = parameters.get_child_value (1).dup_string ();
                        var new_owner = parameters.get_child_value (2).dup_string ();
                        if (new_owner != "") return;

                        // are there DataSources with this BusName?
                        var disconnected_ds = new GenericArray<DataSource> ();
                        var iter = HashTableIter<string, GenericArray<BusName?>> (running);
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

                        if (disconnected_ds.length == 0) return;

                        for (int i = 0; i < disconnected_ds.length; i++)
                        {
                            var ds = disconnected_ds[i];
                            uid = ds.unique_id;
                            ds.timestamp = Timestamp.now ();
                            var strid = "%s [%s]".printf (ds.name, uid);
                            debug ("Client disconnected: %s", strid);

                            if (running.lookup (uid).length == 0)
                            {
                                debug ("No remaining client running: %s", strid);
                                running.remove (uid);
                                ds.running = false;

                                data_source_disconnected (ds.to_variant ());
                            }
                        }
                    });
            }
            catch (Error err)
            {
                warning ("%s", err.message);
            }

            // FIXME: nothing changed, why is this here?
            dirty = true;
            // FIXME: set up gobject timer like ->
            // gobject.timeout_add(DISK_WRITE_TIMEOUT, self._write_to_disk)
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

            debug ("%s, this.ref_count = %u", Log.METHOD, this.ref_count);
        }

        public Variant get_data_sources ()
        {
            var array = new VariantBuilder (new VariantType (
                "a(sssa(asaasay)bxb)"));
            List<unowned DataSource> data_sources = sources.get_values ();
            data_sources.sort ((a, b) =>
            {
                return strcmp (a.unique_id, b.unique_id);
            });

            foreach (unowned DataSource ds in data_sources)
            {
                array.add_value (ds.to_variant ());
            }

            return array.end ();
        }

        private bool is_sender_known(BusName? sender,
            GenericArray<BusName?> sender_array)
        {
            for (int i=0; i<sender_array.length; i++)
            {
                if (sender == sender_array[i])
                    return true;
            }
            return false;
        }

        public bool register_data_source (string unique_id, string name,
            string description, Variant event_templates, BusName? sender)
        {
            debug ("%s: %s, %s, %s", Log.METHOD, unique_id, name, description);

            var sender_array = running.lookup (unique_id);
            if (sender_array == null)
            {
                running.insert (unique_id, new GenericArray<BusName?>());
                running.lookup (unique_id).add (sender);
            }
            else if (is_sender_known (sender, sender_array))
            {
                running.lookup (unique_id).add (sender);
            }

            unowned DataSource? ds = sources.lookup (unique_id);
            if (ds != null)
            {
                var templates = Events.from_variant (event_templates);
                ds.name = name;
                ds.description = description;
                ds.event_templates = templates;
                ds.timestamp = Timestamp.now ();
                ds.running = true;
                // FIXME: Write to disk here
                
                data_source_registered (ds.to_variant ());

                return ds.enabled;
            }
            else
            {
                var templates = Events.from_variant (event_templates);
                DataSource new_ds = new DataSource.full (unique_id, name,
                    description, templates);
                new_ds.enabled = true;
                new_ds.running = true;
                new_ds.timestamp = Timestamp.now ();
                sources.insert (unique_id, new_ds);
                // FIXME: Write to disk here
                
                data_source_registered (new_ds.to_variant ());
                
                return new_ds.enabled;
            }

        }

        public void set_data_source_enabled (string unique_id, bool enabled)
        {
            debug ("%s: %s, %d", Log.METHOD, unique_id, (int) enabled);
            unowned DataSource? ds = sources.lookup (unique_id);
            if (ds != null)
            {
                bool changed = ds.enabled != enabled;
                ds.enabled = enabled;

                if (changed) data_source_enabled (unique_id, enabled);
            }
            else
            {
                warning ("DataSource \"%s\" wasn't registered!", unique_id);
            }
        }

        public Variant get_data_source_from_id (string unique_id) throws Error
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
            foreach (string unique_id in running.get_keys())
            {
                GenericArray<BusName?> bus_names = running.lookup(unique_id);
                if (is_sender_known(sender, bus_names))
                {
                    var data_source = sources.lookup(unique_id);
                    data_source.timestamp =  Timestamp.now ();
                    dirty = false;
                    if (!data_source.enabled)
                    {
                        for (int i=0; i < events.length; i++)
                        {
                            events[i] = null;
                        }
                    }
                }
            }
        }

        private bool write_to_disk ()
        {
            //FIXME: Write to disk needs to be implemented
            return true;
        }
    }

    [ModuleInit]
#if BUILTIN_EXTENSIONS
    public static Type data_source_registry_init (TypeModule module)
    {
#else
    public static Type extension_register (TypeModule module)
    {
#endif
        return typeof (DataSourceRegistry);
    }
}

// vim:expandtab:ts=4:sw=4
