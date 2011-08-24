/* ds-registry.vala
 *
 * Copyright © 2011 Michal Hruby <michal.mhr@gmail.com>
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
    interface RemoteRegistry: Object
    {
        [DBus (signature = "a(sssa(asaasay)bxb)")]
        public abstract Variant get_data_sources () throws Error;
        public abstract bool register_data_source (string unique_id,
            string name, string description,
            [DBus (signature = "a(asaasay)")] Variant event_templates)
            throws Error;
        public abstract void set_data_source_enabled (string unique_id,
            bool enabled) throws Error;

        public signal void data_source_disconnected (
            [DBus (signature = "(sssa(asaasay)bxb)")] Variant data_source);
        public signal void data_source_enabled (string unique_id,
            bool enabled);
        public signal void data_source_registered (
            [DBus (signature = "(sssa(asaasay)bxb)")] Variant data_source);
    }

    class DataSource: Object
    {
        private GenericArray<Event> event_templates;
        private string unique_id;
        private string name;
        private string description;

        bool enabled;
        bool running;
        int64 timestamp;

        public DataSource.from_variant (Variant variant)
        {
            // we expect (sssa(asaasay)bxb)
            var iter = variant.iterator ();

            assert (iter.n_children () >= 4);

            unique_id = iter.next_value ().get_string ();
            name = iter.next_value ().get_string ();
            description = iter.next_value ().get_string ();
            event_templates = Events.from_variant (iter.next_value ());

            if (iter.n_children () > 4)
            {
                enabled = iter.next_value ().get_boolean ();
                timestamp = iter.next_value ().get_int64 ();
                running = iter.next_value ().get_boolean ();
            }
        }

        public Variant to_variant ()
        {
            var vb = new VariantBuilder (new VariantType (
                "(sssa(asaasay)bxb)"));

            vb.add ("s", unique_id);
            vb.add ("s", name);
            vb.add ("s", description);
            vb.open (new VariantType ("a(asaasay)"));
            vb.add_value (Events.to_variant (event_templates));
            vb.close ();

            vb.add ("b", enabled);
            vb.add ("x", timestamp);
            vb.add ("b", running);

            return vb.end ();
        }
    }

    class DataSourceRegistry: Extension, RemoteRegistry
    {
        private GenericArray<DataSource> sources;
        private uint registration_id;

        DataSourceRegistry ()
        {
            Object ();
        }

        construct
        {
            sources = new GenericArray<DataSource> ();
            
            // this will be called after bus is acquired, so it shouldn't block
            var connection = Bus.get_sync (BusType.SESSION, null);
            registration_id = connection.register_object<RemoteRegistry> (
                "/org/gnome/zeitgeist/data_source_registry", this);
        }

        public override void unload ()
        {
            var connection = Bus.get_sync (BusType.SESSION, null);
            if (registration_id != 0)
            {
                connection.unregister_object (registration_id);
                registration_id = 0;
            }

            debug ("%s, this.ref_count = %u", Log.METHOD, this.ref_count);
        }

        public Variant get_data_sources ()
        {
            var array = new VariantBuilder (new VariantType (
                "a(sssa(asaasay)bxb)"));
            for (int i = 0; i < sources.length; i++)
            {
                array.add_value (sources[i].to_variant ());
            }
            
            return array.end ();
        }

        public bool register_data_source (string unique_id, string name,
            string description, Variant event_templates)
        {
            debug ("%s: %s, %s, %s", Log.METHOD, unique_id, name, description);
            return false;
        }

        public void set_data_source_enabled (string unique_id, bool enabled)
        {
            debug ("%s: %s, %d", Log.METHOD, unique_id, (int) enabled);
        }
    }

    [ModuleInit]
    Type extension_register (TypeModule module)
    {
        return typeof (DataSourceRegistry);
    }
}

// vim:expandtab:ts=4:sw=4
