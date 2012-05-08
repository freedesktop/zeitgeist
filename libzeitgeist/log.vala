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

/**
 * SECTION:zeitgeist-log
 * @short_description: Primary access point for talking to the Zeitgeist daemon
 * @include: zeitgeist.h
 *
 * #ZeitgeistLog encapsulates the low level access to the Zeitgeist daemon.
 * You can use it to manage the log by inserting and deleting entries as well
 * as do queries on the logged data.
 *
 * It's important to realize that the #ZeitgeistLog class does not expose
 * any API that does synchronous communications with the message bus -
 * everything is asynchronous. To ease development some of the methods have
 * variants that are "fire and forget" ignoring the normal return value, so
 * that callbacks does not have to be set up.
 */
public class Log : Object
{
    private static Log default_instance;

    private RemoteLog proxy;
    private Variant? engine_version;
    private SList<QueuedMethod> method_dispatch_queue;

    public bool is_connected { get; private set; default = false; }

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
        warning ("hi! requesting proxy...");
        Bus.get_proxy<RemoteLog> (BusType.SESSION, Utils.ENGINE_DBUS_NAME,
            Utils.ENGINE_DBUS_PATH, 0, null, (obj, res) =>
            {
                warning ("ok! proxy acquired!");
                try
                {
                    proxy = Bus.get_proxy.end (res);

                    engine_version = proxy.version;
                    warn_if_fail (engine_version.get_type_string () == "(iii)");

                    process_queued_methods ();

                    proxy.notify["g-name-owner"].connect (name_owner_changed);

                    is_connected = true;
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
        this.is_connected = name_owner != null;

        if (is_connected)
        {
            // Reinstate all active monitors

            // Update our cached version property
            engine_version = proxy.version;
            warn_if_fail (engine_version.get_type_string () == "(iii)");
        }
    }

    private async void wait_for_proxy (SourceFunc callback) {
        if (likely (proxy != null))
            return;
        if (method_dispatch_queue == null)
            method_dispatch_queue = new SList<QueuedMethod> ();
        method_dispatch_queue.prepend (new QueuedMethod (callback));
        yield;
    }

    /*
    public async void insert_events (Cancellable? cancellable=null, ...)
        throws Error
    {
        var lalala = va_list ();
        // FIXME: variadic async functions are broken! This generates:
        // static gboolean zeitgeist_log_insert_events_co (ZeitgeistLogInsertEventsData* _data_) {
        //     ...
        //     va_start (_data_->lalala, cancellable);
        //     ...
        // }
        yield insert_events_valist (cancellable, lalala);
    }

    public async void insert_events_valist (Cancellable? cancellable=null,
        va_list events) throws Error
    {
        Event event = events.arg ();
    }
    */

    /*
    public async void insert_events_no_reply (...) throws Error
    {
    }
    */

    public async void insert_events_from_ptrarray (GenericArray<Event> events,
        Cancellable? cancellable=null) throws Error
    {
        yield wait_for_proxy (insert_events_from_ptrarray.callback);
        yield proxy.insert_events (Events.to_variant (events), cancellable);
    }

    public async void find_events (
        TimeRange time_range,
        GenericArray<Event> event_templates,
        StorageState storage_state,
        uint32 num_events,
        ResultType result_type,
        Cancellable? cancellable=null) throws Error
    {
    }

    public async void find_event_ids (
        TimeRange time_range,
        GenericArray<Event> event_templates,
        StorageState storage_state,
        uint32 num_events,
        ResultType result_type,
        Cancellable? cancellable=null) throws Error
    {
    }

    public async GenericArray<Event> get_events (uint32[] event_ids,
            Cancellable? cancellable=null) throws Error
    {
        yield wait_for_proxy (get_events.callback);
        var result = yield proxy.get_events (event_ids, cancellable);
        return Events.from_variant (result);
    }

    public async void find_related_uris (
        TimeRange time_range,
        GenericArray<Event> event_templates,
        GenericArray<Event> result_event_templates,
        StorageState storage_state,
        uint32 num_events,
        ResultType result_type,
        Cancellable? cancellable=null) throws Error
    {
    }

    public async void delete_events (uint32[] event_ids,
            Cancellable? cancellable=null) throws Error
    {
        yield wait_for_proxy (delete_events.callback);
        yield proxy.delete_events (event_ids, cancellable);
    }

    public async void quit (Cancellable? cancellable=null) throws Error
    {
        yield wait_for_proxy (quit.callback);
        yield proxy.quit (cancellable);
    }

    public async void install_monitor (Monitor monitor) throws Error
    {
    }

    public async void remove_monitor (Monitor monitor) throws Error
    {
    }

   /**
    * zeitgeist_log_get_version:
    * @self: A #ZeitgeistLog instance
    * @major: (out): Location for the major version
    * @minor: (out): Location for the minor version
    * @micro: (out): Location for the micro version
    *
    * Gets version of currently running Zeitgeist daemon.
    *
    * This method will return the version of Zeitgeist daemon this instance is
    * connected to. If you call this method right after zeitgeist_log_new(),
    * only zeros will be returned, a valid version number will only be returned
    * once this instance successfully connected to the Zeitgeist daemon - ie.
    * the value of the "is-connected" property must be TRUE (you can connect
    * to the "notify::is-connected" signal otherwise).
    */
    public void get_version (out int major, out int minor, out int micro) {
        major = minor = micro = 0;
        if (engine_version != null)
            engine_version.get ("(iii)", &major, &minor, &micro);
    }

}

}
