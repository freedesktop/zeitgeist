/* notify.vala
 *
 * Copyright © 2011 Collabora Ltd.
 *             By Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
 *             By Seif Lotfy <seif@lotfy.com>
 * Copyright © 2011 Michal Hruby <michal.mhr@gmail.com>
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 */

namespace Zeitgeist
{

    public class MonitorManager : Object
    {

        private static unowned MonitorManager? instance;

        private HashTable<string, Monitor> monitors;
        private HashTable<string, GenericArray<string>> connections;

        // ref-counted singleton - it can get destroyed easily, but has
        // singleton semantics as long as some top-level instance keeps
        // a reference to it
        public static MonitorManager get_default ()
        {
            return instance ?? new MonitorManager ();
        }

        private MonitorManager ()
        {
        }

        ~MonitorManager ()
        {
            instance = null;
        }

        construct
        {
            instance = this;

            monitors = new HashTable<string, Monitor> (str_hash, str_equal);
            connections = new HashTable<string, GenericArray<string>>
                (str_hash, str_equal);

            // FIXME: it'd be nice if this supported arg2
            try
            {
                var connection = Bus.get_sync (BusType.SESSION);
                connection.signal_subscribe ("org.freedesktop.DBus",
                    "org.freedesktop.DBus", "NameOwnerChanged",
                    "/org/freedesktop/DBus", null, 0,
                    (conn, sender, path, ifc_name, sig_name, parameters) =>
                    {
                        // name, old_owner, new_owner
                        var arg0 = parameters.get_child_value (0).dup_string ();
                        var arg1 = parameters.get_child_value (1).dup_string ();
                        var arg2 = parameters.get_child_value (2).dup_string ();

                        if (arg2 != "") return;

                        foreach (var owner in connections.get_keys())
                        {
                            // Don't disconnect monitors using service names
                            if (arg0 == owner && DBus.is_unique_name (arg0))
                            {
                                var paths = connections.lookup (arg0);
                                debug("Client disconnected %s", owner);
                                for (int i = 0; i < paths.length; i++)
                                    remove_monitor ((BusName)arg0, paths[i]);
                                connections.remove(arg0);
                            }
                        }
                    });
            }
            catch (IOError err)
            {
                warning ("Cannot subscribe to NameOwnerChanged signal! %s",
                    err.message);
            }
        }

        private class Monitor
        {

            private GenericArray<Event> event_templates;
            private TimeRange time_range;
            private RemoteMonitor? proxy_object = null;

            private enum NotificationType
            {
                INSERTION,
                DELETION
            }
            [Compact]
            private class QueuedNotification {
                // (Compact classes don't support private fields)
                public NotificationType type;
                public Variant time_range;
                public Variant events; // for insertions
                public uint32[] event_ids; // for deletions

                public QueuedNotification.insertion (Variant time_range, Variant events)
                {
                    type = NotificationType.INSERTION;
                    this.time_range = time_range;
                    this.events = events;
                }

                public QueuedNotification.deletion (Variant time_range, uint32[] event_ids)
                {
                    type = NotificationType.DELETION;
                    this.time_range = time_range;
                    this.event_ids = event_ids;
                }

                public void send (RemoteMonitor proxy_object)
                {
                    if (type == NotificationType.INSERTION)
                        proxy_object.notify_insert.begin (time_range, events);
                    else
                        proxy_object.notify_delete.begin (time_range, event_ids);
                }
            }
            private SList<QueuedNotification> queued_notifications;

            public Monitor (BusName peer, string object_path,
                TimeRange tr, GenericArray<Event> templates)
            {
                queued_notifications = new SList<QueuedNotification> ();
                Bus.get_proxy.begin<RemoteMonitor> (BusType.SESSION, peer,
                    object_path,
                    DBusProxyFlags.DO_NOT_LOAD_PROPERTIES
                    | DBusProxyFlags.DO_NOT_CONNECT_SIGNALS
                    | DBusProxyFlags.DO_NOT_AUTO_START,
                    null, (obj, res) =>
                    {
                        try
                        {
                            proxy_object = Bus.get_proxy.end (res);
                            // Process queued notifications...
                            flush_notifications ();

                            proxy_object.notify["g-name-owner"].connect (name_owner_changed);
                        }
                        catch (IOError err)
                        {
                            warning ("%s", err.message);
                        }
                    });
                time_range = tr;
                event_templates = templates;
            }

            private void name_owner_changed ()
                requires (proxy_object != null)
            {
                // FIXME: can we use this to actually remove the monitor?
                //  (instead of using NameOwnerChanged signal)
                DBusProxy p = proxy_object as DBusProxy;
                if (p.g_name_owner != null) flush_notifications ();
            }

            private void flush_notifications ()
            {
                queued_notifications.reverse ();
                foreach (unowned QueuedNotification notification
                    in queued_notifications)
                {
                    notification.send (proxy_object);
                }
                queued_notifications = null;
            }

            private bool matches (Event event)
            {
                if (event_templates.length == 0)
                    return true;
                for (var i = 0; i < event_templates.length; i++)
                {
                    if (event.matches_template (event_templates[i]))
                    {
                        return true;
                    }
                }
                return false;
            }

            public void notify_insert (TimeRange time_range, GenericArray<Event> events)
            {
                var intersect_tr = time_range.intersect (this.time_range);
                if (intersect_tr != null)
                {
                    var matching_events = new GenericArray<Event> ();
                    for (int i = 0; i < events.length; i++)
                    {
                        if (events[i] != null && matches (events[i])
                            && events[i].timestamp >= intersect_tr.start
                            && events[i].timestamp <= intersect_tr.end)
                        {
                            matching_events.add (events[i]);
                        }
                    }
                    if (matching_events.length > 0)
                    {
                        Variant time_v = intersect_tr.to_variant ();
                        // FIXME: do we want to "cache" this for sharing
                        // between monitors?
                        Variant events_v = Events.to_variant (matching_events);

                        string? name_owner = null;
                        if (proxy_object != null)
                        {
                            DBusProxy p = proxy_object as DBusProxy;
                            if (p != null) name_owner = p.g_name_owner;
                        }

                        if (proxy_object != null && name_owner != null)
                        {
                            DBusProxy p = (DBusProxy) proxy_object;
                            debug ("Notifying %s about %d insertions",
                                p.get_name (), matching_events.length);

                            proxy_object.notify_insert.begin (time_v, events_v);
                        }
                        else
                        {
                            debug ("Queueing notification about %d insertions",
                                matching_events.length);
                            queued_notifications.prepend (
                                new QueuedNotification.insertion (time_v, events_v));
                        }
                    }
                }
            }

            public void notify_delete (TimeRange time_range, uint32[] event_ids)
            {
                var intersect_tr = time_range.intersect (this.time_range);
                if (intersect_tr != null)
                {
                    Variant time_v = intersect_tr.to_variant ();

                    string? name_owner = null;
                    if (proxy_object != null)
                    {
                        DBusProxy p = proxy_object as DBusProxy;
                        if (p != null) name_owner = p.g_name_owner;
                    }

                    if (proxy_object != null && name_owner != null)
                    {
                        proxy_object.notify_delete.begin (time_v, event_ids);
                    }
                    else
                    {
                        queued_notifications.prepend (
                            new QueuedNotification.deletion (time_v, event_ids));
                    }
                }
            }
        }

        public void install_monitor (BusName peer, string object_path,
            TimeRange time_range, GenericArray<Event> templates)
        {
            var hash = "%s#%s".printf (peer, object_path);
            if (monitors.lookup (hash) == null)
            {
                var monitor = new Monitor (peer, object_path, time_range,
                    templates);
                monitors.insert (hash, monitor);
                if (connections.lookup (peer) == null)
                    connections.insert (peer, new GenericArray<string> ());
                connections.lookup (peer).add (object_path);

                debug ("Installed new monitor for %s", peer);
            }
            else
            {
                warning ("There's already a monitor installed for %s", hash);
            }
        }

        public void remove_monitor (BusName peer, string object_path)
        {
            debug ("Removing monitor %s%s", peer, object_path);
            var hash = "%s#%s".printf (peer, object_path);

            if (monitors.lookup (hash) != null)
                monitors.remove (hash);
            else
                warning ("There's no monitor installed for %s", hash);

            if (connections.lookup (peer) != null)
            {
                var paths = connections.lookup (peer);
                for (int i = 0; i < paths.length; i++)
                {
                    if (paths[i] == object_path)
                    {
                        paths.remove_index_fast (i);
                        break;
                    }
                }
            }

        }

        public void notify_insert (TimeRange time_range,
            GenericArray<Event> events)
        {
            foreach (unowned Monitor mon in monitors.get_values ())
                mon.notify_insert (time_range, events);
        }

        public void notify_delete (TimeRange time_range, uint32[] event_ids)
        {
            foreach (unowned Monitor mon in monitors.get_values ())
                mon.notify_delete (time_range, event_ids);
        }
    }

}

// vim:expandtab:ts=4:sw=4
