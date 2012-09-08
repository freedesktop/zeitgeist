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
 *
 * Primary access point for talking to the Zeitgeist daemon
 *
 * include: zeitgeist.h
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
public class Log : QueuedProxyWrapper
{
    private static Log default_instance;

    private RemoteLog proxy;
    private Variant? engine_version;
    private HashTable<Monitor, uint> monitors;

    public Log ()
    {
        monitors = new HashTable<Monitor, int>(direct_hash, direct_equal);
        Bus.get_proxy<RemoteLog> (BusType.SESSION, Utils.ENGINE_DBUS_NAME,
            Utils.ENGINE_DBUS_PATH, 0, null, (obj, res) =>
            {
                try
                {
                    proxy = Bus.get_proxy.end (res);
                    proxy_acquired (proxy);
                }
                catch (IOError err)
                {
                    critical ("Unable to connect to Zeitgeist: %s",
                        err.message);
                    proxy_unavailable (err);
                }
            });
    }

    public static Log get_default ()
    {
        if (default_instance == null)
            default_instance = new Log ();
        return default_instance;
    }

    protected override void on_connection_established ()
    {
        // Reinstate all active monitors
        foreach (unowned Monitor monitor in monitors.get_keys ())
        {
            reinstall_monitor (monitor);
        }

        // Update our cached version property
        engine_version = proxy.version;
        warn_if_fail (engine_version.get_type_string () == "(iii)");
    }

    protected override void on_connection_lost () {
    }

    /*
    public async void insert_events_valist (Cancellable? cancellable=null,
        va_list events) throws Error
    {
        Event event = events.arg ();
    }
    */

    public async void insert_events_no_reply (GenericArray<Event> events)
        throws Error
    {
        yield wait_for_proxy ();
        yield proxy.insert_events (Events.to_variant (events), null);
    }

    // FIXME: make variadic
    public async Array<uint32> insert_events (GenericArray<Event> events,
        Cancellable? cancellable=null) throws Error
    {
        yield wait_for_proxy ();
        uint32[] ids = yield proxy.insert_events (Events.to_variant (events), cancellable);
        Array<uint32> _ids = new Array<uint32> ();
        for (int i=0; i<ids.length; i++)
            _ids.append_val (ids[i]);
        return _ids;
    }

    public async Array<uint32> insert_events_from_ptrarray (GenericArray<Event> events,
        Cancellable? cancellable=null) throws Error
    {
        return yield insert_events (events, cancellable);
    }

    public async ResultSet find_events (
        TimeRange time_range,
        GenericArray<Event> event_templates,
        StorageState storage_state,
        uint32 num_events,
        ResultType result_type,
        Cancellable? cancellable=null) throws Error
    {
        yield wait_for_proxy ();
        var result = yield proxy.find_events (time_range.to_variant (),
            Events.to_variant (event_templates), storage_state,
            num_events, result_type, cancellable);
        return new SimpleResultSet (Events.from_variant (result));
    }

    public async uint32[] find_event_ids (
        TimeRange time_range,
        GenericArray<Event> event_templates,
        StorageState storage_state,
        uint32 num_events,
        ResultType result_type,
        Cancellable? cancellable=null) throws Error
    {
        yield wait_for_proxy ();
        return yield proxy.find_event_ids (time_range.to_variant (),
            Events.to_variant (event_templates), storage_state,
            num_events, result_type, cancellable);
    }

    public async GenericArray<Event> get_events (
        Array<uint32> event_ids,
        Cancellable? cancellable=null) throws Error
    {
        yield wait_for_proxy ();
        uint32[] simple_event_ids = new uint32[event_ids.length];
        for (int i = 0; i < event_ids.length; i++)
            simple_event_ids[i] = event_ids.index (i);
        var result = yield proxy.get_events (simple_event_ids, cancellable);
        return Events.from_variant (result);
    }

    public async string[] find_related_uris (
        TimeRange time_range,
        GenericArray<Event> event_templates,
        GenericArray<Event> result_event_templates,
        StorageState storage_state,
        uint32 num_events,
        ResultType result_type,
        Cancellable? cancellable=null) throws Error
    {
        yield wait_for_proxy ();
        return yield proxy.find_related_uris (time_range.to_variant (),
            Events.to_variant (event_templates),
            Events.to_variant (result_event_templates),
            storage_state, num_events, result_type, cancellable);
    }

    public async TimeRange delete_events (Array<uint32> event_ids,
            Cancellable? cancellable=null) throws Error
    {
        yield wait_for_proxy ();
        uint32[] _ids = new uint32 [event_ids.length];
        for (int i=0; i<event_ids.length; i++)
            _ids[i] = event_ids.index(i);
        Variant time_range = yield proxy.delete_events (_ids, cancellable);
        return new TimeRange.from_variant(time_range);
    }

    public async void quit (Cancellable? cancellable=null) throws Error
    {
        yield wait_for_proxy ();
        yield proxy.quit (cancellable);
    }

    public async void install_monitor (Monitor monitor) throws Error
    {
        // FIXME
        //monitor.destroy.connect (() => {});

        // Save the monitor's registration id (0 = not registered)
        monitors.insert(monitor, 0);

        if (is_connected)
            reinstall_monitor (monitor);
    }

    private async void reinstall_monitor (Monitor monitor)
        requires (is_connected)
    {
        if (monitors.lookup (monitor) == 0)
        {
            DBusConnection conn = ((DBusProxy) proxy).get_connection ();

            // FIXME: check exception
            uint registration_id = conn.register_object<RemoteMonitor> (
                monitor.get_path (), monitor);
            monitors.insert (monitor, registration_id);
        }

        proxy.install_monitor (
            monitor.get_path (),
            monitor.time_range.to_variant (),
            Events.to_variant (monitor.get_templates ()));
    }

    public async void remove_monitor (Monitor monitor) throws Error
    {
        yield wait_for_proxy ();

        try
        {
            yield proxy.remove_monitor (monitor.get_path ());
        }
        catch (IOError err)
        {
            warning ("Failed to remove monitor from Zeitgeist. Retracting" +
                "%s from the bus nonetheless: %s", monitor.get_path (),
                err.message);
            return;
        }

        uint registration_id = monitors.lookup (monitor);
        if (registration_id != 0)
        {
            var connection = ((DBusProxy) proxy).get_connection ();
            connection.unregister_object (registration_id);
        }
    }

   /**
    * Gets version of currently running Zeitgeist daemon.
    *
    * This method will return the version of Zeitgeist daemon this instance is
    * connected to. If you call this method right after zeitgeist_log_new(),
    * only zeros will be returned, a valid version number will only be returned
    * once this instance successfully connected to the Zeitgeist daemon - ie.
    * the value of the "is-connected" property must be TRUE (you can connect
    * to the "notify::is-connected" signal otherwise).
    *
    * @param self A #ZeitgeistLog instance
    * @param major Location for the major version
    * @param minor Location for the minor version
    * @param micro: Location for the micro version
    */
    public void get_version (out int major, out int minor, out int micro) {
        major = minor = micro = 0;
        if (engine_version != null)
            engine_version.get ("(iii)", &major, &minor, &micro);
    }

}

}

// vim:expandtab:ts=4:sw=4
