/* notify.vala
 *
 * Copyright © 2011 Collabora Ltd.
 *             By Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
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

        private HashTable<string, Monitor> monitors;
        private string[] peers;

        construct
        {
            monitors = new HashTable<string, Monitor> (str_hash, str_equal);

            // FIXME: it'd be nice if this supported arg2
            try
            {
                var conn = Bus.get_sync (BusType.SESSION);
                conn.signal_subscribe ("org.freedesktop.DBus",
                    "org.freedesktop.DBus", "NameOwnerChanged",
                    "/org/freedesktop/DBus", null, 0,
                    (connection, sender, path, @interface, @signal, parameters) =>
                    {
                        var arg0 = parameters.get_child_value (0).dup_string ();
                        var arg1 = parameters.get_child_value (1).dup_string ();
                        var arg2 = parameters.get_child_value (2).dup_string ();

                        debug ("%s %s %s", arg0, arg1, arg2);

                        if (arg2 != "") return;

                        if (arg1 in peers)
                        {
                            // FIXME: remove the monitor ourselves
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

            public Monitor (BusName peer, string object_path,
                TimeRange tr, GenericArray<Event> templates)
            {
                Bus.get_proxy<RemoteMonitor> (BusType.SESSION, peer,
                    object_path, 0, null, (obj, res) =>
                    {
                        try
                        {
                            proxy_object = Bus.get_proxy.end (res);
                        }
                        catch (IOError err)
                        {
                            warning ("%s", err.message);
                        }
                    });
                time_range = tr;
                event_templates = templates;
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
                if (!(peer in peers)) peers += peer;

                debug ("Installed new monitor for %s", peer);
            }
            else
            {
                warning ("There's already a monitor installed for %s", hash);
            }
        }

        public void remove_monitor (BusName peer, string object_path)
        {
            var hash = "%s#%s".printf (peer, object_path);
            if (monitors.lookup (hash) != null)
            {
                monitors.remove (hash);
                // FIXME: remove from peers (needs check to be sure though)
                debug ("Removed monitor for %s", hash);
            }
            else
            {
                warning ("There's no monitor installed for %s", hash);
            }
        }

    }

}

// vim:expandtab:ts=4:sw=4
