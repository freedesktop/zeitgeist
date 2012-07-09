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

// FIXME: private or something
public abstract class QueuedProxyWrapper : Object
{
    public bool proxy_created { get; private set; default = false; }
    public bool is_connected { get; private set; default = false; }

    protected SList<QueuedMethod> method_dispatch_queue;

    protected class QueuedMethod
    {

        public SourceFunc queued_method { public /*owned*/ get; private /*owned*/ set; }

        public QueuedMethod (SourceFunc callback)
        {
            queued_method = callback;
        }

    }

    protected void proxy_acquired(Object proxy)
    {
        is_connected = true;
        proxy_created = true;
        proxy.notify["g-name-owner"].connect (name_owner_changed);
        on_connection_established ();
        process_queued_methods ();
    }

    protected void proxy_unavailable()
    {
        // Zeitgeist couldn't be auto-started. We'll run the callbacks
        // anyway giving them an error.
        method_dispatch_queue_reverse ();
        foreach (QueuedMethod m in method_dispatch_queue)
        {
        }
        // FIXME: process_queued_methods() with manual error callbacks
    }

    protected void process_queued_methods ()
    {
        method_dispatch_queue.reverse ();
        foreach (QueuedMethod m in method_dispatch_queue)
            m.queued_method ();
        method_dispatch_queue = null;
    }

    protected void name_owner_changed (ParamSpec pspec)
    {
        string? name_owner = null; // FIXME: .get_name_owner ();
        this.is_connected = name_owner != null;

        if (this.is_connected)
            on_connection_established ();
        else
            on_connection_lost ();
    }

    protected abstract void on_connection_established ();
    protected abstract void on_connection_lost ();

    protected async void wait_for_proxy (SourceFunc callback)
    {
        if (likely (proxy_created))
            return;
        if (method_dispatch_queue == null)
            method_dispatch_queue = new SList<QueuedMethod> ();
        method_dispatch_queue.prepend (new QueuedMethod (callback));
        yield;
    }

}

}

// vim:expandtab:ts=4:sw=4
