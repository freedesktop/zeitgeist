/*
 * Copyright © 2012 Canonical Ltd.
 *             By Siegfried-A. Gevatter <siegfried.gevatter@collabora.co.uk>
 * Copyright © 2013 Seif Lotfy <seif@lotfy.com>
 * Copyright © 2013 Rico Tzschichholz <ricotz@ubuntu.com>
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

/**
 * Zeitgeist is an activity-logging framework to enable the desktop of
 * the future.
 *
 * Its main component is the Zeitgeist engine, a D-Bus service that logs
 * any events other applications send to it. An event may be anything like:
 *
 *  - The user opened/created/modified/closed a file, or visited a website.
 *  - The user received an e-mail, a phone call or an IM notification.
 *  - Someone modified a remote (eg. Google Drive) document owned by the user.
 *
 * This information is then made available to other Zeitgeist-enabled
 * applications over a powerful querying and monitoring API, and can be used
 * and analyzed to create intelligent or adaptive interfaces.
 *
 * Zeitgeist also comes with a blacklist extension to make sure the user
 * always stays in control of what information is logged.
 */

namespace Zeitgeist
{

/**
 * Primary access point for talking to the Zeitgeist daemon
 *
 * {@link Log} encapsulates the low level access to the Zeitgeist daemon.
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
    class DbWorker
    {
        private unowned ThreadFunc<void*> func;

        public DbWorker (ThreadFunc<void*> func)
        {
            this.func = func;
        }

        public void run ()
        {
            this.func ();
        }
    }

    private static Log default_instance;

    private RemoteLog proxy;
    private Variant? engine_version;
    private HashTable<Monitor, uint> monitors;
    private DbReader dbreader;
    private ThreadPool<DbWorker> threads;
    private bool allow_direct_read;

    public Log ()
    {
        monitors = new HashTable<Monitor, uint> (direct_hash, direct_equal);
        MainLoop mainloop = new MainLoop (MainContext.get_thread_default ());
        allow_direct_read = Utils.log_may_read_directly ();

        Bus.get_proxy.begin<RemoteLog> (BusType.SESSION, Utils.ENGINE_DBUS_NAME,
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
                finally
                {
                    mainloop.quit();
                }
            });

        mainloop.run();
    }

    /**
     * Get a unique instance of #ZeitgeistLog, that you can share in your
     * application without caring about memory management.
     *
     * See zeitgeist_log_new() for more information.
     *
     * @return ZeitgeistLog.
     */
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
            reinstall_monitor.begin (monitor);
        }

        // Update our cached version property
        engine_version = proxy.version;
        warn_if_fail (engine_version.get_type_string () == "(iii)");

        try {
            threads = new ThreadPool<DbWorker>.with_owned_data ((worker) => {
                worker.run ();
            }, (int) get_num_processors (), true);
        } catch (ThreadError err) {
            warning ("%s", err.message);
            threads = null;
        }

        if (allow_direct_read && threads != null &&
            proxy.datapath != ":memory:" &&
            FileUtils.test (proxy.datapath, GLib.FileTest.EXISTS)) {
            Utils.set_database_file_path (proxy.datapath);
            try {
                dbreader = new DbReader ();
            } catch (EngineError err){
                warning ("%s", err.message);
                dbreader = null;
            }
        }
        else
        {
            dbreader = null;
        }
    }

    protected override void on_connection_lost ()
    {
        // Reset the monitor's registration id (0 = not registered)
        foreach (unowned Monitor monitor in monitors.get_keys ())
        {
            monitors.replace (monitor, 0);
        }

        dbreader = null;
    }

    /**
    * Asynchronously send a set of events to the Zeitgeist daemon, requesting they
    * be inserted into the log.
    *
    * @param event A {@link Event}
    * @param cancellable a {@link GLib.Cancellable} to cancel the operation or %NULL
    */
    public async Array<uint32> insert_event (Event event,
        Cancellable? cancellable=null) throws Error
    {
        var events = new GenericArray<Event> ();
        events.add (event);
        return yield insert_events (events, cancellable);
    }


    /**
    * Asynchronously send a set of events to the Zeitgeist daemon, requesting they
    * be inserted into the log.
    *
    * @param events An {@link GLib.GenericArray} of {@link Event}
    * @param cancellable a {@link GLib.Cancellable} to cancel the operation or %NULL
    */
    public async Array<uint32> insert_events (GenericArray<Event> events,
        Cancellable? cancellable=null) throws Error
    {
        var events_cp = new GenericArray<Event> ();
        for (int i = 0; i < events.length; i++)
            events_cp.add (events.get (i));
        yield wait_for_proxy ();
        uint32[] ids = yield proxy.insert_events (Events.to_variant (events_cp), cancellable);
        var result = new Array<uint32> ();
        // Ideally we'd just place "(owned) ids" into the GArray, but .data isn't
        // in the Vala bindings...
        for (int i = 0; i < ids.length; ++i)
            result.append_val (ids[i]);
        return result;
    }

    /**
    * Asynchronously send a set of events to the Zeitgeist daemon, requesting they
    * be inserted into the log.
    * This method is &quot;fire and forget&quot; and the caller will never know
    * whether the events was successfully inserted or not.
    *
    * This method is exactly equivalent to calling zeitgeist_log_insert_event()
    * with NULL set as @cancellable, @callback, and @user_data.
    *
    * @param event A {@link Event}
    */
    public void insert_event_no_reply (Event event)
        throws Error
    {
        insert_event.begin (event);
    }

    /**
    * Asynchronously send a set of events to the Zeitgeist daemon, requesting they
    * be inserted into the log.
    * This method is &quot;fire and forget&quot; and the caller will never know
    * whether the events was successfully inserted or not.
    *
    * This method is exactly equivalent to calling zeitgeist_log_insert_event()
    * with NULL set as @cancellable, @callback, and @user_data.
    *
    * @param events An {@link GLib.GenericArray} of {@link Event}
    */
    public void insert_events_no_reply (GenericArray<Event> events)
        throws Error
    {
        insert_events.begin (events);
    }

    /**
    * Send a query matching a collection of {@link Event} templates to the {@link Log}.
    * The query will match if an event matches any of the templates. If an event
    * template has more than one {@link Subject} the query will match if any one
    * of the {@link Subject}s templates match.
    *
    * The query will be done via an asynchronous DBus call and this method will
    * return immediately. The return value will be passed to callback as a list
    * of {@link Event}s. This list must be the sole argument for the callback.
    *
    * If you need to do a query yielding a large (or unpredictable) result set
    * and you only want to show some of the results at the same time (eg., by
    * paging them), consider using {@link find_event_ids}.
    *
    * In order to use this method there needs to be a mainloop runnning.
    * Both Qt and GLib mainloops are supported.
    *
    * @param time_range {@link TimeRange} A time range in which the events should be considered in
    * @param storage_state {@link StorageState} storage state
    * @param event_templates An {@link GLib.GenericArray} of {@link Event}
    * @param num_events int represteing the number of events that should be returned
    * @param result_type {@link ResultType} how the events should be grouped and sorted
    * @param cancellable a {@link GLib.Cancellable} to cancel the operation or %NULL
    */
    public async ResultSet find_events (
        TimeRange time_range,
        GenericArray<Event> event_templates,
        StorageState storage_state,
        uint32 num_events,
        ResultType result_type,
        Cancellable? cancellable=null) throws Error
    {
        var event_templates_cp = new GenericArray<Event> ();
        for (int i = 0; i < event_templates.length; i++)
            event_templates_cp.add (event_templates.get (i));
    
        if (dbreader != null) {
            SimpleResultSet result_set = null;
            EngineError error = null;
            ThreadFunc<void*> run = () => {
                try {
                    var result = dbreader.find_events (time_range, event_templates_cp,
                        storage_state, num_events, result_type);
                    result_set = new SimpleResultSet (result);
                } catch (EngineError err) {
                    error = err;
                } finally {
                    Idle.add (find_events.callback);
                }
                return null;
            };

            threads.add (new DbWorker (run));
            yield;

            if (error != null)
                throw error;
            return result_set;
        }

        yield wait_for_proxy ();
        var result = yield proxy.find_events (time_range.to_variant (),
            Events.to_variant (event_templates_cp), storage_state,
            num_events, result_type, cancellable);
        return new SimpleResultSet (Events.from_variant (result));
    }

    /**
    * Send a query matching a collection of {@link Event} templates to the {@link Log}.
    * The query will match if an event matches any of the templates. If an event
    * template has more than one {@link Subject} the query will match if any one
    * of the {@link Subject}s templates match.
    *
    * The query will be done via an asynchronous DBus call and this method will
    * return immediately. The return value will be passed to callback as a list
    * of intergers represrting {@link Event} id's.
    * This list must be the sole argument for the callback.
    *
    * In order to use this method there needs to be a mainloop runnning.
    * Both Qt and GLib mainloops are supported.
    *
    * @param time_range {@link TimeRange} A time range in which the events should be considered in
    * @param storage_state {@link StorageState} storage state
    * @param event_templates An {@link GLib.GenericArray} of {@link Event}
    * @param num_events int represteing the number of events that should be returned
    * @param result_type {@link ResultType} how the events should be grouped and sorted
    * @param cancellable a {@link GLib.Cancellable} to cancel the operation or %NULL
    */
    public async uint32[] find_event_ids (
        TimeRange time_range,
        GenericArray<Event> event_templates,
        StorageState storage_state,
        uint32 num_events,
        ResultType result_type,
        Cancellable? cancellable=null) throws Error
    {
        var event_templates_cp = new GenericArray<Event> ();
        for (int i = 0; i < event_templates.length; i++)
            event_templates_cp.add(event_templates.get (i));

        if (dbreader != null) {
            uint32[] ids = null;
            EngineError error = null;
            ThreadFunc<void*> run = () => {
                try {
                    ids = dbreader.find_event_ids (time_range, event_templates_cp,
                        storage_state, num_events, result_type);
                } catch (EngineError err) {
                    error = err;
                } finally {
                    Idle.add (find_event_ids.callback);
                }
                return null;
            };

            threads.add (new DbWorker (run));
            yield;

            if (error != null)
                throw error;
            return ids;
        }

        yield wait_for_proxy ();
        return yield proxy.find_event_ids (time_range.to_variant (),
            Events.to_variant (event_templates_cp), storage_state,
            num_events, result_type, cancellable);
    }

    /**
    * Look up a collection of {@link Event} in the {@link Log} given a collection
    * of event ids. This is useful for looking up the event data for events found
    * with the find_event_ids_* family of functions.
    *
    * Each {@link Event} which is not found in the {@link Log} is represented by
    * NULL in the resulting collection. The query will be done via an asynchronous
    * DBus call and this method will return immediately. The returned events will
    * be passed to callback as a list of {@link Event}s, which must be the only
    * argument of the function.
    *
    * In order to use this method there needs to be a mainloop runnning.
    *
    * @param event_ids a {@link GLib.Array} of {@link Event} ids
    * @param cancellable a {@link GLib.Cancellable} to cancel the operation or %NULL
    */
    public async ResultSet get_events (
        Array<uint32> event_ids,
        Cancellable? cancellable=null) throws Error
    {
        uint32[] simple_event_ids = new uint32[event_ids.length];
        for (int i = 0; i < event_ids.length; i++)
            simple_event_ids[i] = event_ids.index (i);

        if (dbreader != null)
        {
            SimpleResultSet result_set = null;
            EngineError error = null;
            ThreadFunc<void*> run = () => {
                try {
                    var result = dbreader.get_events (simple_event_ids);
                    result_set = new SimpleResultSet (result);
                } catch (EngineError err) {
                    error = err;
                } finally {
                    Idle.add (get_events.callback);
                }
                return null;
            };

            threads.add (new DbWorker (run));
            yield;

            if (error != null)
                throw error;
            return result_set;
        }

        yield wait_for_proxy ();
        var result = yield proxy.get_events (simple_event_ids, cancellable);
        return new SimpleResultSet (Events.from_variant (result));
    }

    /**
    * Get a list of URIs of subjects which frequently occur together with events
    * matching event_templates. Possibly restricting to time_range or to URIs
    * that occur as subject of events matching result_event_templates.
    *
    * @param time_range {@link TimeRange} A time range in which the events should be considered in
    * @param storage_state {@link StorageState} storage state
    * @param event_templates An {@link GLib.GenericArray} of {@link Event} describing the events to relate to
    * @param result_event_templates An {@link GLib.GenericArray} of {@link Event} desrcibing the result to be returned
    * @param num_events int represteing the number of events that should be returned
    * @param result_type {@link ResultType} how the events should be grouped and sorted
    * @param cancellable a {@link GLib.Cancellable} to cancel the operation or %NULL
    */
    public async string[] find_related_uris (
        TimeRange time_range,
        GenericArray<Event> event_templates,
        GenericArray<Event> result_event_templates,
        StorageState storage_state,
        uint32 num_events,
        RelevantResultType result_type,
        Cancellable? cancellable=null) throws Error
    {
        var events_cp = new GenericArray<Event> ();
        for (int i = 0; i < event_templates.length; i++)
            events_cp.add (event_templates.get (i));

        var results_cp = new GenericArray<Event> ();
        for (int i = 0; i < result_event_templates.length; i++)
            results_cp.add (result_event_templates.get (i));

        if (dbreader != null) {
            string[] uris = null;
            EngineError error = null;
            ThreadFunc<void*> run = () => {
                try {
                    uris = dbreader.find_related_uris (time_range, events_cp,
                    results_cp, storage_state, num_events, result_type);
                } catch (EngineError err) {
                    error = err;
                } finally {
                    Idle.add (find_related_uris.callback);
                }
                return null;
            };

            threads.add (new DbWorker (run));
            yield;
            
            if (error != null)
                throw error;
            return uris;
        }

        yield wait_for_proxy ();
        return yield proxy.find_related_uris (time_range.to_variant (),
            Events.to_variant (events_cp),
            Events.to_variant (results_cp),
            storage_state, num_events, result_type, cancellable);
    }


    /**
    * Delete a collection of events from the zeitgeist log given their event ids.
    *
    * The deletion will be done asynchronously, and this method returns immediately.
    *
    * @param event_ids Array<uint32>
    * @param cancellable a {@link GLib.Cancellable} to cancel the operation or %NULL
    */
    public async TimeRange delete_events (Array<uint32> event_ids,
            Cancellable? cancellable=null) throws Error
    {
        uint32[] _ids = new uint32 [event_ids.length];
        for (int i=0; i<event_ids.length; i++)
            _ids[i] = event_ids.index (i);
        yield wait_for_proxy ();
        Variant time_range = yield proxy.delete_events (_ids, cancellable);
        return new TimeRange.from_variant (time_range);
    }

    /**
    * @param cancellable a {@link GLib.Cancellable} to cancel the operation or %NULL
    */
    public async void quit (Cancellable? cancellable=null) throws Error
    {
        yield wait_for_proxy ();
        yield proxy.quit (cancellable);
    }

    /**
    * Install a monitor in the Zeitgeist engine that calls back when events matching
    * event_templates are logged. The matching is done exactly as in the find_* family
    * of methods and in Event.matches_template. Furthermore matched events must also
    * have timestamps lying in time_range.
    *
    * To remove a monitor call remove_monitor() on the returned Monitor instance.
    *
    * @param monitor A {@link Monitor} to report back inserts and deletes
    */
    public void install_monitor (Monitor monitor) throws Error
    {
        // FIXME
        //monitor.destroy.connect (() => {});

        // Save the monitor's registration id (0 = not registered)
        monitors.insert(monitor, 0);

        if (is_connected)
            reinstall_monitor.begin (monitor);
    }

    private async void reinstall_monitor (Monitor monitor)
        requires (is_connected)
    {
        if (monitors.lookup (monitor) == 0)
        {
            DBusConnection conn = ((DBusProxy) proxy).get_connection ();

            try
            {
                uint registration_id = conn.register_object<RemoteMonitor> (
                    monitor.get_path (), monitor);
                monitors.replace (monitor, registration_id);
            }
            catch (GLib.IOError err)
            {
                warning ("Error installing monitor: %s", err.message);
                return;
            }
        }

        proxy.install_monitor.begin (
            monitor.get_path (),
            monitor.time_range.to_variant (),
            Events.to_variant (monitor.get_templates ()));
    }

    /**
    * Remove a monitor from Zeitgeist engine that calls back when events matching event_templates are logged.
    *
    * @param monitor A {@link Monitor} to report back inserts and deletes
    */
    public void remove_monitor (owned Monitor monitor) throws Error
    {
        proxy.remove_monitor.begin (monitor.get_path (), null, (obj, res) =>
        {
            try
            {
                ((RemoteLog) obj).remove_monitor.end (res);
            }
            catch (Error err)
            {
                warning ("Failed to remove monitor from Zeitgeist. Retracting" +
                    "%s from the bus nonetheless: %s", monitor.get_path (),
                    err.message);
            }
        });

        uint registration_id = monitors.lookup (monitor);
        if (registration_id != 0)
        {
            var connection = ((DBusProxy) proxy).get_connection ();
            connection.unregister_object (registration_id);
        }

        monitors.remove (monitor);
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
    * @param major Location for the major version
    * @param minor Location for the minor version
    * @param micro Location for the micro version
    */
    public void get_version (out int major, out int minor, out int micro) {
        major = minor = micro = 0;
        if (engine_version != null)
            engine_version.get ("(iii)", &major, &minor, &micro);
    }

   /**
    * Gets extensions of the running Zeitgeist daemon.
    *
    * @return array of extenstions names strings
    */
    public string[] get_extensions () {
        return proxy.extensions;
    }

   /**
    * Gets datapath of the running Zeitgeist daemon.
    *
    * @return string datapath
    */
    public string datapath () {
        return proxy.datapath;
    }
}

}

