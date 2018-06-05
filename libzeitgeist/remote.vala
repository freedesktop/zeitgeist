/* remote.vala
 *
 * Copyright © 2011-2012 Collabora Ltd.
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
    /**
     * Version struct consisting of the following fields:
     * - major
     * - minor
     * - minus
     */
    public struct VersionStruct
    {
        /**
         * Major version number.
         */
        int major;
        /**
         * Minor version number.
         */
        int minor;
        /**
         * Micro version number.
         */
        int micro;
    }

    [DBus (name = "org.gnome.zeitgeist.Log")]
    protected interface RemoteLog : Object
    {

        [DBus (signature = "(xx)")]
        public async abstract Variant delete_events (
            uint32[] event_ids,
            Cancellable? cancellable=null,
            BusName? sender=null
        ) throws Error;

        public async abstract uint32[] find_event_ids (
            [DBus (signature = "(xx)")] Variant time_range,
            [DBus (signature = "a(asaasay)")] Variant event_templates,
            uint storage_state, uint num_events, uint result_type,
            Cancellable? cancellable=null, BusName? sender=null
        ) throws Error;

        [DBus (signature = "a(asaasay)")]
        public async abstract Variant find_events (
            [DBus (signature = "(xx)")] Variant time_range,
            [DBus (signature = "a(asaasay)")] Variant event_templates,
            uint storage_state, uint num_events, uint result_type,
            Cancellable? cancellable=null, BusName? sender=null
        ) throws Error;

        public async abstract string[] find_related_uris (
            [DBus (signature = "(xx)")] Variant time_range,
            [DBus (signature = "a(asaasay)")] Variant event_templates,
            [DBus (signature = "a(asaasay)")] Variant result_event_templates,
            uint storage_state, uint num_events, uint result_type,
            Cancellable? cancellable=null, BusName? sender=null
        ) throws Error;

        [DBus (signature = "a(asaasay)")]
        public async abstract Variant get_events (
            uint32[] event_ids,
            Cancellable? cancellable=null,
            BusName? sender=null
        ) throws Error;

        public async abstract uint32[] insert_events (
            [DBus (signature = "a(asaasay)")] Variant events,
            Cancellable? cancellable=null,
            BusName? sender=null
        ) throws Error;

        public async abstract void install_monitor (
            ObjectPath monitor_path,
            [DBus (signature = "(xx)")] Variant time_range,
            [DBus (signature = "a(asaasay)")] Variant event_templates,
            BusName? owner=null
        ) throws Error;

        public async abstract void remove_monitor (
            ObjectPath monitor_path,
            BusName? owner=null
        ) throws Error;

        public async abstract void quit (
            Cancellable? cancellable=null
        ) throws Error;

        [DBus (name = "extensions")]
        public abstract string[] extensions { owned get; }

        [DBus (name = "version")]
        public abstract VersionStruct version { owned get; }

        [DBus (name = "datapath")]
        public abstract string datapath { owned get; }

    }

    [DBus (name = "org.gnome.zeitgeist.Monitor")]
    protected interface RemoteMonitor : Object
    {

        public async abstract void notify_insert (
            [DBus (signature = "(xx)")] Variant time_range,
            [DBus (signature = "a(asaasay)")] Variant events
        ) throws Error;

        public async abstract void notify_delete (
            [DBus (signature = "(xx)")] Variant time_range,
            uint32[] event_ids
        ) throws Error;

    }

    [DBus (name = "org.gnome.zeitgeist.Index")]
    protected interface RemoteSimpleIndexer : Object
    {
        public abstract async void search (
            string query_string,
            [DBus (signature = "(xx)")] Variant time_range,
            [DBus (signature = "a(asaasay)")] Variant filter_templates,
            uint offset, uint count, uint result_type,
            Cancellable? cancellable,
            [DBus (signature = "a(asaasay)")] out Variant events,
            out uint matches) throws Error;
        public abstract async void search_with_relevancies (
            string query_string,
            [DBus (signature = "(xx)")] Variant time_range,
            [DBus (signature = "a(asaasay)")] Variant filter_templates,
            uint storage_state, uint offset, uint count, uint result_type,
            Cancellable? cancellable,
            [DBus (signature = "a(asaasay)")] out Variant events,
            out double[] relevancies, out uint matches) throws Error;
    }

    /* FIXME: Remove this! Only here because of a bug
              in Vala (Vala Bug #661361) */
    [DBus (name = "org.freedesktop.NetworkManager")]
    protected interface NetworkManagerDBus : Object
    {
        [DBus (name = "state")]
        public abstract uint32 state () throws Error;
        public signal void state_changed (uint32 state);
    }

    /* FIXME: Remove this! Only here because of a bug
              in Vala (Vala Bug #661361) */
    [DBus (name = "net.connman.Manager")]
    protected interface ConnmanManagerDBus : Object
    {
        public abstract string get_state () throws Error;
        public signal void state_changed (string state);
    }

}

// vim:expandtab:ts=4:sw=4
