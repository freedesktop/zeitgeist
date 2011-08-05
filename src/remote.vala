/* remote.vala
 *
 * Copyright © 2011 Collabora Ltd.
 *             By Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
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

    [DBus (name = "org.gnome.zeitgeist.Log")]
    public interface RemoteLog : Object
    {

        public abstract TimeRange delete_events (
            uint32[] event_ids,
            BusName sender
        ) throws IOError;

        // This is stupid. We don't need it.
        //public void DeleteLog ();

        public abstract uint32[] find_event_ids (
            TimeRange time_range,
            [DBus (signature = "a(asaasay)")] Variant event_templates,
            uint storage_state, uint num_events, uint result_type,
            BusName sender
        ) throws IOError;

        [DBus (signature = "a(asaasay)")]
        public abstract Variant find_events (
            TimeRange time_range,
            [DBus (signature = "a(asaasay)")] Variant event_templates,
            uint storage_state, uint num_events, uint result_type,
            BusName sender
        ) throws IOError;

        public abstract string[] find_related_uris (
            TimeRange time_range,
            [DBus (signature = "a(asaasay)")] Variant event_templates,
            [DBus (signature = "a(asaasay)")] Variant result_event_templates,
            uint storage_state, uint num_events, uint result_type,
            BusName sender
        ) throws IOError;

        [DBus (signature = "a(asaasay)")]
        public abstract Variant get_events (
            uint32[] event_ids,
            BusName sender
        ) throws IOError;

        public abstract uint32[] insert_events (
            [DBus (signature = "a(asaasay)")] Variant events,
            BusName sender
        ) throws IOError;

        public abstract void install_monitor (
            ObjectPath monitor_path,
            TimeRange time_range,
            [DBus (signature = "a(asaasay)")] Variant event_templates,
            BusName owner
        ) throws IOError;

        public abstract void remove_monitor (
            ObjectPath monitor_path,
            BusName owner
        ) throws IOError;

        public abstract void quit () throws IOError;

        [DBus (name = "extensions")]
        public abstract string[] extensions { owned get; }

        [DBus (signature = "iii", name = "version")]
        public abstract Variant version { owned get; }

    }

    [DBus (name = "org.gnome.zeitgeist.Monitor")]
    public interface RemoteMonitor : Object
    {

        public async abstract void notify_insert (
            TimeRange time_range,
            [DBus (signature = "a(asaasay)")] Variant events
        ) throws IOError;

        public async abstract void notify_delete (
            TimeRange time_range,
            uint32[] event_ids
        ) throws IOError;

    }

}

// vim:expandtab:ts=4:sw=4
