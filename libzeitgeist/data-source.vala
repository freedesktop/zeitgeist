/* 
 * Copyright © 2011 Michal Hruby <michal.mhr@gmail.com>
 * Copyright © 2011-2012 Collabora Ltd.
 *             By Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
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

/**
 * Abstracts data sources used by the DataSourceRegistry extension
 *
 * ZeitgeistDataSource represents a data source used to insert events into
 * Zeitgeist. The data sources are identified using the unique_id property,
 * and when querying the data source registry you get other interesting
 * information like timestamp of the last action of the data source, flag
 * whether it is currently running etc.
 */

namespace Zeitgeist
{

    public class DataSource: Object
    {
        public string unique_id { get; set; }
        public string name { get; set; }
        public string description { get; set; }

        public GenericArray<Event>? event_templates { get; set; }

        public bool enabled { get; set; }
        public bool running { get; set; }
        public int64 timestamp { get; set; }
        /**
         * ZeitgeistDataSource
         *
         * Abstracts data sources used by the ZeitgeistDataSourceRegistry extension
         * 
         * ZeitgeistDataSource represents a data source used to insert events into
         * Zeitgeist. The data sources are identified using the unique_id property,
         * and when querying the data source registry you get other interesting
         * information like timestamp of the last action of the data source, flag
         * whether it is currently running etc.
         *
         */
        public DataSource ()
        {
            Object ();
            this.enabled = true;
        }

        public DataSource.full (string unique_id, string name,
            string description, GenericArray<Event>? templates)
        {
            Object (unique_id: unique_id, name: name, description: description,
                event_templates: templates);
            this.enabled = true;
        }

        public DataSource.from_variant (Variant variant,
            bool reset_running=false) throws DataModelError
        {
            warn_if_fail (
                variant.get_type_string () == "(sssa("+Utils.SIG_EVENT+")bxb)"
                || variant.get_type_string () == "sssa("+Utils.SIG_EVENT+")");
            var iter = variant.iterator ();

            assert (iter.n_children () >= 4);
            unique_id = iter.next_value ().get_string ();
            name = iter.next_value ().get_string ();
            description = iter.next_value ().get_string ();
            event_templates = Events.from_variant (iter.next_value ());

            if (iter.n_children () > 4)
            {
                running = iter.next_value ().get_boolean ();
                if (reset_running)
                    running = false;
                timestamp = iter.next_value ().get_int64 ();
                enabled = iter.next_value ().get_boolean ();
            }
        }

        public Variant to_variant ()
        {
            var vb = new VariantBuilder (new VariantType (
                "(sssa("+Utils.SIG_EVENT+")bxb)"));

            vb.add ("s", unique_id);
            vb.add ("s", name);
            vb.add ("s", description);
            if (event_templates != null && event_templates.length > 0)
            {
                vb.add_value (Events.to_variant (event_templates));
            }
            else
            {
                vb.open (new VariantType ("a("+Utils.SIG_EVENT+")"));
                vb.close ();
            }

            vb.add ("b", running);
            vb.add ("x", timestamp);
            vb.add ("b", enabled);

            return vb.end ();
        }
    }

    namespace DataSources
    {
        public const string SIG_DATASOURCES =
            "a(sssa("+Utils.SIG_EVENT+")bxb)";

        public static GenericArray<DataSource> from_variant (
            Variant sources_variant) throws DataModelError
        {
            var sources = new GenericArray<DataSource> ();

            warn_if_fail (
                sources_variant.get_type_string() == SIG_DATASOURCES);
            foreach (Variant ds_variant in sources_variant)
            {
                sources.add (new DataSource.from_variant (ds_variant));
            }

            return sources;
        }

        public static Variant to_variant (
            HashTable<string, DataSource> sources)
        {
            var vb = new VariantBuilder (new VariantType (SIG_DATASOURCES));

            List<unowned DataSource> data_sources = sources.get_values ();
            data_sources.sort ((a, b) =>
            {
                return strcmp (a.unique_id, b.unique_id);
            });

            foreach (unowned DataSource ds in data_sources)
            {
                vb.add_value (ds.to_variant ());
            }

            return vb.end ();
        }
    }

}

// vim:expandtab:ts=4:sw=4
