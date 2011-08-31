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
    interface RemoteBlacklist: Object
    {
        public abstract void add_template (string blacklist_id,
            [DBus (signature = "(asaasay)")] Variant event_template)
            throws Error;
        [DBus (signature = "a{s(asaasay)}")]
        public abstract Variant get_templates () throws Error;
        public abstract void remove_template (string blacklist_id)
            throws Error;

        public signal void template_added (string blacklist_id,
            [DBus (signature = "s(asaasay)")] Variant event_template);
        public signal void template_removed (string blacklist_id,
            [DBus (signature = "s(asassay)")] Variant event_template);
    }

    class Blacklist: Extension, RemoteBlacklist
    {
        private HashTable<string, Event> blacklist;
        private uint registration_id;

        Blacklist ()
        {
            Object ();
        }

        construct
        {
            blacklist = new HashTable<string, Event> (str_hash, str_equal);

            // FIXME: load blacklist from file

            // This will be called after bus is acquired, so it shouldn't block
            var connection = Bus.get_sync (BusType.SESSION, null);
            registration_id = connection.register_object<RemoteBlacklist> (
                "/org/gnome/zeitgeist/blacklist", this);
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

        private void flush ()
        {
            // FIXME: write to file.
        }

        public GenericArray<Event?> pre_insert_events (
            GenericArray<Event?> events, BusName sender)
        {
            // FIXME: do template matching...
            // for event in events:
            //     for tmpl in blacklist:
            //         if event.matches_template(tmpl): event = null
            return events;
        }

        public void add_template (string blacklist_id, Variant event_template)
        {
            Event template = new Event.from_variant (event_template);
            blacklist.insert (blacklist_id, template);
            flush ();
        }

        public void remove_template (string blacklist_id)
        {
            Event template = blacklist.lookup (blacklist_id);
            blacklist.remove (blacklist_id);
            flush ();
        }

        public Variant get_templates ()
        {
            return null; //blacklist;
        }

    }

    [ModuleInit]
#if BUILTIN_EXTENSIONS
    Type blacklist_init (TypeModule module)
    {
#else
    Type extension_register (TypeModule module)
    {
#endif
        return typeof (Blacklist);
    }
}

// vim:expandtab:ts=4:sw=4
