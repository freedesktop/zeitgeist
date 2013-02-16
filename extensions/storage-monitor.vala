/* ds-registry.vala
 *
 * Copyright © 2011 Collabora Ltd.
 *             By Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
 * Copyright © 2011 Stefano Candori <stefano.candori@gmail.com>
 * Copyright © 2012 Canonical Ltd.
 *             By Siegfried-A. Gevatter <siegfried.gevatter@collabora.co.uk>
 *
 * Based upon a Python implementation:
 *  Copyright © 2009 Mikkel Kamstrup Erlandsen <mikkel.kamstrup@gmail.com>
 *  Copyright © 2011 Canonical Ltd.
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
    [DBus (name = "org.gnome.zeitgeist.StorageMonitor")]
    public interface RemoteStorageMonitor: Object
    {
        [DBus (signature = "a(sa{sv})")]
        public abstract Variant get_storages () throws Error;

        public signal void storage_available (string storage_id,
            [DBus (signature = "a{sv}")] Variant storage_description);
        public signal void storage_unavailable (string storage_id);
    }

    public interface NetworkMonitor: Object
    {
        // This method emits the on_network_up/on_network_up signals
        // basing on the initial state of the network.
        public abstract void setup ();

        public signal void on_network_up ();
        public signal void on_network_down ();
    }

    namespace StorageMedia
    {
        private Variant to_variant (string medium_name, bool available,
            string icon, string display_name)
        {
            var vb = new VariantBuilder (new VariantType ("(sa{sv})"));

            vb.add ("s", medium_name);
            vb.open (new VariantType ("a{sv}"));
            {
                vb.open (new VariantType ("{sv}"));
                vb.add ("s", "available");
                vb.add ("v", new Variant ("b", available));
                vb.close ();
                vb.open (new VariantType ("{sv}"));
                vb.add ("s", "icon");
                vb.add ("v", new Variant ("s", icon));
                vb.close ();
                vb.open (new VariantType ("{sv}"));
                vb.add ("s", "display-name");
                vb.add ("v", new Variant ("s", display_name));
                vb.close ();
            }
            vb.close ();

            return vb.end ();
        }
    }

    /*
     * The Storage Monitor monitors the availability of network interfaces
     * and storage devices (USB drives, data/audio/video CD/DVDs, etc) and
     * updates the Zeitgeist database with this information so clients can
     * efficiently query based on the storage identifier and availability
     * of the storage medium the event subjects reside on.
     *
     * Subject can have the following types of storage identifiers:
     *  - for local resources, the fixed identifier `local`;
     *  - for network URIs, the fixed identifier `net`;
     *  - for resources on storage devices, the UUID of the partition
     *    they reside in;
     *  - otherwise, the fixed identifier `unknown`.
     *
     * Subjects with storage `local` or `unknown` are always considered as
     * available; for network resources, the monitor will use either ConnMan
     * or NetworkManager (whichever is available).
     *
     * For subjects being inserted without a storage id set, this extension
     * will attempt to determine it and update the subject on the fly.
     */
    class StorageMonitor: Extension, RemoteStorageMonitor
    {
        private const string[] network_uri_schemes = {
            "dav", "davs", "ftp", "http", "https", "mailto",
            "sftp", "smb", "ssh" };

        private Zeitgeist.SQLite.Database database;
        private unowned Sqlite.Database db;
        private uint registration_id;

        private Sqlite.Statement get_storages_stmt;
        private Sqlite.Statement store_storage_medium_stmt;
        private Sqlite.Statement update_storage_medium_stmt;
        private Sqlite.Statement insert_unavailable_medium_stmt;
        private Sqlite.Statement update_medium_state_stmt;

        private NetworkMonitor network;
        private uint watch_connman;
        private uint watch_nm;

        StorageMonitor ()
        {
            Object ();
        }

        construct
        {
            try
            {
                prepare_queries ();
            }
            catch (EngineError e)
            {
                warning ("Storage Monitor couldn't communicate with DB - bye");
                return;
            }

            // This will be called after bus is acquired, so it shouldn't block
            try
            {
                var connection = Bus.get_sync (BusType.SESSION, null);
                registration_id = connection.register_object<RemoteStorageMonitor> (
                    "/org/gnome/zeitgeist/storagemonitor", this);
            }
            catch (Error err)
            {
                warning ("%s", err.message);
            }

            /*
             * This is disabled because it causes races on some hardware
             * (zg will be using 100% cpu, maybe eat up lots of memory etc.)
             */
            /*
            VolumeMonitor monitor = VolumeMonitor.get ();
            monitor.volume_added.connect (on_volume_added);
            monitor.volume_removed.connect (on_volume_removed);
            foreach (Volume volume in monitor.get_volumes ())
            {
                add_storage_medium (get_volume_id (volume),
                    volume.get_icon ().to_string (), volume.get_name ());
            }
            */

            // Dynamically decide whether to use Connman or NetworkManager
            watch_connman = Bus.watch_name (BusType.SYSTEM,
                                      "net.connman",
                                      BusNameWatcherFlags.NONE,
                                      name_appeared_handler,
                                      null);
            watch_nm = Bus.watch_name (BusType.SYSTEM,
                                      "org.freedesktop.NetworkManager",
                                      BusNameWatcherFlags.NONE,
                                      name_appeared_handler,
                                      null);

        }

        private void name_appeared_handler (DBusConnection connection, string name, string name_owner)
        {
            if (this.network != null)
                return;

            if (name == "net.connman")
                this.network = new ConnmanNetworkMonitor ();
            else if (name == "org.freedesktop.NetworkManager")
                this.network = new NMNetworkMonitor ();

            this.network.on_network_up.connect (() =>
                this.add_storage_medium ("net", "stock_internet", "Internet"));
            this.network.on_network_down.connect (() =>
                this.remove_storage_medium ("net"));

            this.network.setup ();

            Bus.unwatch_name (watch_connman);
            Bus.unwatch_name (watch_nm);
        }

        public override void unload ()
        {
            // FIXME: move all this D-Bus stuff to some shared
            // {request,release}_iface functions
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

        private void prepare_queries () throws EngineError
        {
            database = engine.database;
            db = database.database;

            int rc;
            string sql;

            // Prepare query to retrieve all storage medium information
            sql = """
                SELECT value, state, icon, display_name
                FROM storage
                """;
            rc = db.prepare_v2 (sql, -1, out get_storages_stmt);
            database.assert_query_success (rc, "Storage retrieval query error");

            sql = """
                INSERT INTO storage (
                    value, state, icon, display_name
                ) VALUES (
                    ?, ?, ?, ?
                )""";
            rc = db.prepare_v2 (sql, -1, out store_storage_medium_stmt);
            database.assert_query_success (rc, "Storage insertion query error");

            sql = """
                UPDATE storage SET 
                state=?, icon=?, display_name=? 
                WHERE value=?
                """;
            rc = db.prepare_v2 (sql, -1, out update_storage_medium_stmt);
            database.assert_query_success (rc, "Storage update query error");

            sql = """
                INSERT INTO storage (
                    state, value
                ) VALUES (
                    ?, ?
                )""";
            rc = db.prepare_v2 (sql, -1, out insert_unavailable_medium_stmt);
            database.assert_query_success (rc,
                "insert_unavailable_medium_stmt error");

            sql = """
                UPDATE storage
                SET state=?
                WHERE value=?
                """;
            rc = db.prepare_v2 (sql, -1, out update_medium_state_stmt);
            database.assert_query_success (rc,
                "update_medium_state_stmt error");
        }

        public override void pre_insert_events (GenericArray<Event?> events,
            BusName? sender)
        {
            for (int i = 0; i < events.length; ++i)
            {
                if (events[i] == null) continue;
                for (int j = 0; j < events[i].subjects.length; ++j)
                {
                    Subject subject = events[i].subjects[j];
                    if (Utils.is_empty_string (subject.storage))
                        subject.storage = find_storage_for_uri (subject.uri);
                }
            }
        }

        /*
         * Find the name of the storage medium the given URI resides on.
         */
        private string find_storage_for_uri (string uri)
        {
            File file = File.new_for_uri (uri);
            string uri_scheme = file.get_uri_scheme ();
            /*
            // FIXME: uncomment this once gvfs is our friend again
            if (uri_scheme == "file")
            {
                try
                {
                    Mount mount = file.find_enclosing_mount ();
                    return get_volume_id (mount.get_volume ());
                }
                catch (Error err)
                {
                    return "local";
                }
            }
            else*/
            if (uri_scheme in network_uri_schemes)
            {
                return "net";
            }

            return "unknown";
        }

        /*
        // It is not being used since gvfs is not being friendly
        private void on_volume_added (Volume volume)
        {
            debug ("volume added");
            Icon icon = volume.get_icon ();
            string icon_name = "";
            // FIXME: why volume.get_icon ().to_string () above but not here?
            if (icon is ThemedIcon && ((ThemedIcon) icon).get_names ().length > 0)
                icon_name = ((ThemedIcon) icon).get_names ()[0];
            add_storage_medium (get_volume_id (volume), icon_name,
                volume.get_name ());
        }

        private void on_volume_removed (Volume volume)
        {
            debug ("Volume removed");
            remove_storage_medium (get_volume_id (volume));
        }
        */

        /*
         * Return a string identifier for a GIO Volume. This id is constructed
         * as a `best effort` since we can not always uniquely identify
         * volumes, especially audio- and data CDs are problematic.
         */

        /*private string get_volume_id (Volume volume)
        {
            string volume_id;

            volume_id = volume.get_uuid ();
            if (volume_id != null)
                return volume_id;

            volume_id = volume.get_identifier ("uuid");
            if (volume_id != null)
                return volume_id;

            volume_id = volume.get_identifier ("label");
            if (volume_id != null)
                return volume_id;

            return "unknown";
        }*/

        public void add_storage_medium (string medium_name, string icon,
            string display_name)
        {
            debug ("VOLUME ADDED: %s".printf(medium_name));
            store_storage_medium_stmt.reset ();
            store_storage_medium_stmt.bind_text (1, medium_name);
            store_storage_medium_stmt.bind_int (2, 1);
            store_storage_medium_stmt.bind_text (3, icon);
            store_storage_medium_stmt.bind_text (4, display_name);
            if (store_storage_medium_stmt.step () != Sqlite.DONE)
            {
                update_storage_medium_stmt.reset ();
                update_storage_medium_stmt.bind_int (1, 1);
                update_storage_medium_stmt.bind_text (2, icon);
                update_storage_medium_stmt.bind_text (3, display_name);
                update_storage_medium_stmt.bind_text (4, medium_name);
                int rc = update_storage_medium_stmt.step ();
                try
                {
                    database.assert_query_success (rc, "add_storage_medium", Sqlite.DONE);
                }
                catch (EngineError e)
                {
                    warning ("Could not add storage medium: %s", e.message);
                }
            }
            storage_available (medium_name, StorageMedia.to_variant (
                medium_name, true, icon, display_name));
        }

        public void remove_storage_medium (string medium_name)
        {
            debug ("VOLUME REMOVED: %s".printf(medium_name));
            insert_unavailable_medium_stmt.reset ();
            insert_unavailable_medium_stmt.bind_int (1, 0);
            insert_unavailable_medium_stmt.bind_text (2, medium_name);
            if (insert_unavailable_medium_stmt.step () != Sqlite.DONE)
            {
                update_medium_state_stmt.reset ();
                update_medium_state_stmt.bind_int (1, 0);
                update_medium_state_stmt.bind_text (2, medium_name);
                int rc = update_medium_state_stmt.step ();
                try
                {
                    database.assert_query_success (rc, "remove_storage_medium",
                        Sqlite.DONE);
                }
                catch (EngineError e)
                {
                    warning ("Could not remove storage medium: %s", e.message);
                }
            }
            storage_unavailable (medium_name);
        }

        public Variant get_storages () throws EngineError
        {
            var vb = new VariantBuilder (new VariantType ("a(sa{sv})"));

            int rc;
            get_storages_stmt.reset ();
            while ((rc = get_storages_stmt.step ()) == Sqlite.ROW)
            {
                // name, available?, icon, display name
                Variant medium = StorageMedia.to_variant (
                    get_storages_stmt.column_text (0),
                    get_storages_stmt.column_int (1) == 1,
                    get_storages_stmt.column_text (2) ?? "",
                    get_storages_stmt.column_text (3) ?? "");
                vb.add_value (medium);
            }
            database.assert_query_success (rc, "get_storages", Sqlite.DONE);

            return vb.end ();
        }

    }

    /*
     * Monitor the availability of working network connections using
     *  Network Manager (requires 0.8 or later).
     * See http://projects.gnome.org/NetworkManager/developers/spec-08.html
     */
    private class NMNetworkMonitor : Object, NetworkMonitor
    {
        private const string NM_BUS_NAME = "org.freedesktop.NetworkManager";
        private const string NM_IFACE = "org.freedesktop.NetworkManager";
        private const string NM_OBJECT_PATH = "/org/freedesktop/NetworkManager";

        // NM 0.9 broke API so we have to check for two possible values for the state
        private const int NM_STATE_CONNECTED_PRE_09 = 3;
        private const int NM_STATE_CONNECTED_POST_09 = 70;

        private NetworkManagerDBus proxy;

        public NMNetworkMonitor ()
        {
            Object ();
        }

        public void setup ()
        {
            debug ("Creating NetworkManager network monitor");
            try
            {
                proxy = Bus.get_proxy_sync<NetworkManagerDBus> (BusType.SYSTEM,
                                            NM_BUS_NAME,
                                            NM_OBJECT_PATH);
                proxy.state_changed.connect (this.on_state_changed);

                uint32 state = proxy.state ();
                this.on_state_changed (state);
            }
            catch (IOError e )
            {
                warning ("%s", e.message);
            }
        }

        private void on_state_changed(uint32 state)
        {
            debug ("NetworkManager network state: %u", state);
            if (state == NMNetworkMonitor.NM_STATE_CONNECTED_PRE_09 ||
                state == NMNetworkMonitor.NM_STATE_CONNECTED_POST_09)
                on_network_up ();
            else
                on_network_down ();
        }
    }

    private class ConnmanNetworkMonitor : Object, NetworkMonitor
    {
        private const string CM_BUS_NAME = "net.connman";
        private const string CM_IFACE = "net.connman.Manager";
        private const string CM_OBJECT_PATH = "/";

        private ConnmanManagerDBus proxy;

        public ConnmanNetworkMonitor ()
        {
            Object ();
        }

        public void setup ()
        {
            debug ("Creating ConnmanNetworkManager network monitor");

            try
            {
                proxy = Bus.get_proxy_sync<ConnmanManagerDBus> (
                    BusType.SYSTEM, CM_BUS_NAME, CM_OBJECT_PATH);

                // There is a bug in some Connman versions causing it
                // to not emit the net.connman.Manager.StateChanged
                // signal. We take our chances this instance is working
                // properly :-)
                proxy.state_changed.connect (this.on_state_changed);

                string state = proxy.get_state ();
                this.on_state_changed (state);
            }
            catch (IOError e )
            {
                warning ("%s", e.message);
            }
        }

        private void on_state_changed(string state)
        {
            debug ("ConnmanNetworkMonitor network state: %s", state);
            if (state == "online")
                on_network_up ();
            else
                on_network_down ();
        }
    }

    [ModuleInit]
#if BUILTIN_EXTENSIONS
    public static Type storage_monitor_init (TypeModule module)
    {
#else
    public static Type extension_register (TypeModule module)
    {
#endif
        return typeof (StorageMonitor);
    }
}

// vim:expandtab:ts=4:sw=4
