/* ds-registry.vala
 *
 * Copyright © 2011 Collabora Ltd.
 *             By Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
 * Copyright © 2011 Michal Hruby <michal.mhr@gmail.com>
 *
 * Based upon a Python implementation (2009-2011) by:
 *  Mikkel Kamstrup Erlandsen <mikkel.kamstrup@gmail.com>
 *  Manish Sinha <manishsinha@ubuntu.com>
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
    [DBus (name = "org.gnome.zeitgeist.Blacklist")]
    public interface RemoteBlacklist: Object
    {
        public abstract void add_template (string template_id,
            [DBus (signature = "(asaasay)")] Variant event_template)
            throws Error;
        [DBus (signature = "a{s(asaasay)}")]
        public abstract Variant get_templates () throws Error;
        public abstract void remove_template (string template_id)
            throws Error;

        public signal void template_added (string template_id,
            [DBus (signature = "(asaasay)")] Variant event_template);
        public signal void template_removed (string template_id,
            [DBus (signature = "(asassay)")] Variant event_template);
    }

    namespace BlacklistTemplates
    {
        private const string SIG_BLACKLIST = "a{s("+Utils.SIG_EVENT+")}";

        private static HashTable<string, Event> from_variant (
            Variant templates_variant) throws DataModelError
        {
            var blacklist = new HashTable<string, Event> (str_hash, str_equal);

            warn_if_fail (
                templates_variant.get_type_string () == SIG_BLACKLIST);
            foreach (Variant template_variant in templates_variant)
            {
                VariantIter iter = template_variant.iterator ();
                string template_id = iter.next_value ().get_string ();
                // FIXME: throw exception upon error instead of aborting
                Event template = new Event.from_variant (iter.next_value ());
                blacklist.insert (template_id, template);
            }

            return blacklist;
        }

        public static Variant to_variant (HashTable<string, Event> blacklist)
        {
            var vb = new VariantBuilder (new VariantType (SIG_BLACKLIST));
            {
                var iter = HashTableIter<string, Event> (blacklist);
                string template_id;
                Event event_template;
                while (iter.next (out template_id, out event_template))
                {
                    vb.open (new VariantType ("{s("+Utils.SIG_EVENT+")}"));
                    vb.add ("s", template_id);
                    vb.add_value (event_template.to_variant ());
                    vb.close ();
                }
            }
            return vb.end ();
        }
    }

    public class Blacklist: Extension, RemoteBlacklist
    {
        private HashTable<string, Event> blacklist;
        private uint registration_id;

        Blacklist ()
        {
            Object ();
        }

        construct
        {
            // Restore previous blacklist from database, or create an empty one
            Variant? templates = retrieve_config ("blacklist",
                BlacklistTemplates.SIG_BLACKLIST);
            if (templates != null)
            {
                try
                {
                    blacklist = BlacklistTemplates.from_variant (templates);
                }
                catch (DataModelError e)
                {
                    warning ("Could not load blacklist from variant: %s", e.message);
                    blacklist = new HashTable<string, Event> (str_hash, str_equal);
                }
            }
            else
            {
                blacklist = new HashTable<string, Event> (str_hash, str_equal);
            }

            // This will be called after bus is acquired, so it shouldn't block
            try
            {
                var connection = Bus.get_sync (BusType.SESSION, null);
                registration_id = connection.register_object<RemoteBlacklist> (
                    "/org/gnome/zeitgeist/blacklist", this);
            }
            catch (Error err)
            {
                warning ("%s", err.message);
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

        private void flush ()
        {
            Variant v = BlacklistTemplates.to_variant (blacklist);
            store_config ("blacklist", v);
        }

        public override void pre_insert_events (GenericArray<Event?> events,
            BusName? sender)
        {
            for (int i = 0; i < events.length; i++)
            {
                if (events[i] == null) continue;
                foreach (var tmpl in blacklist.get_values ())
                {
                    if (events[i].matches_template (tmpl))
                    {
                        events[i] = null;
                        break;
                    }
                }
            }
        }

        public void add_template (string template_id, Variant event_template)
            throws DataModelError
        {
            Event template = new Event.from_variant (event_template);
            blacklist.insert (template_id, template);
            debug ("Added blacklist template: [#%u]", template_id.hash ());
            template_added (template_id, event_template);
            flush ();
        }

        public void remove_template (string template_id)
        {
            Event event_template = blacklist.lookup (template_id);
            if (blacklist.remove (template_id))
            {
                debug ("Removed blacklist template: [#%u]", template_id.hash ());
                template_removed (template_id, event_template.to_variant ());
                flush ();
            }
            else
            {
                debug ("Blacklist template [#%u] not found.", template_id.hash ());
            }
        }

        public Variant get_templates ()
        {
            return BlacklistTemplates.to_variant (blacklist);
        }

    }

    [ModuleInit]
#if BUILTIN_EXTENSIONS
    public static Type blacklist_init (TypeModule module)
    {
#else
    public static Type extension_register (TypeModule module)
    {
#endif
        return typeof (Blacklist);
    }
}

// vim:expandtab:ts=4:sw=4
