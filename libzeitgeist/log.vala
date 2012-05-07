/*
 * Copyright © 2012 Canonical Ltd.
 *             By Siegfried-A. Gevatter <siegfried.gevatter@collabora.co.uk>
 *
 * Based upon a C implementation (© 2010-2012 Canonical Ltd) by:
 *  Mikkel Kamstrup Erlandsen <mikkel.kamstrup@canonical.com>
 *  Michal Hruby <michal.hruby@canonical.com>
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

public class Log : Object
{
    private static Log default_instance;

    private RemoteLog proxy;
    private Variant engine_version;
    private SList<QueuedMethod> method_dispatch_queue;

    private class QueuedMethod
    {

        public SourceFunc queued_method { public /*owned*/ get; private /*owned*/ set; }

        public QueuedMethod (SourceFunc callback)
        {
            queued_method = callback;
        }
    }

    public Log ()
    {
        Bus.get_proxy<RemoteLog> (BusType.SESSION, Utils.ENGINE_DBUS_NAME,
            Utils.ENGINE_DBUS_PATH, 0, null, (obj, res) =>
            {
                try
                {
                    proxy = Bus.get_proxy.end (res);

                    process_queued_methods ();

                    proxy.notify["g-name-owner"].connect (name_owner_changed);
                }
                catch (IOError err)
                {
                    warning ("%s", err.message);
                }
            });
    }

    public static Log get_default ()
    {
        if (default_instance == null)
            default_instance = new Log ();
        return default_instance;
    }

    private void process_queued_methods ()
    {
        warning ("Processing queued methods...");
        method_dispatch_queue.reverse ();
        foreach (QueuedMethod m in method_dispatch_queue)
            m.queued_method ();
        method_dispatch_queue = null;
    }

    private void name_owner_changed (ParamSpec pspec)
    {
        string? name_owner = null; // .get_name_owner ();

        if (name_owner != null)
        {
            // Reinstate all active monitors

            // Update our cached version property
        }
    }

    private async void wait_for_proxy (SourceFunc callback) {
        if (likely (proxy != null))
            return;
        if (method_dispatch_queue == null)
            method_dispatch_queue = new SList<QueuedMethod> ();
        method_dispatch_queue.append (new QueuedMethod (callback));
        yield;
    }

    public async GenericArray<Event> get_events (uint32[] event_ids,
            Cancellable? cancellable=null) throws Error
    {
        yield wait_for_proxy (get_events.callback);
        var result = yield proxy.get_events (event_ids, cancellable);
        return Events.from_variant (result);
    }

}

}
