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
 * Query the Zeitgeist Full Text Search Extension
 *
 * include: zeitgeist.h
 */
public class Index : QueuedProxyWrapper
{
    private RemoteSimpleIndexer proxy;

    /**
     * Create a new index that interfaces with the default event index of the
     * Zeitgeist daemon.
     *
     * Create a new {@link Index} instance. The index will start to connect
     * to Zeitgeist asynchronously. You can however start calling methods on
     * the returned instance immediately, any method calls issued before the
     * connection has been established will simply be queued and executed once
     * the connection is up.
     *
     * Returns: A reference to a newly allocated index. Free with g_object_unref().
     */
    public Index ()
    {
        Bus.get_proxy.begin<RemoteSimpleIndexer> (BusType.SESSION,
            Utils.ENGINE_DBUS_NAME, "/org/gnome/zeitgeist/index/activity", 0,
            null, (obj, res) =>
            {
                try
                {
                    proxy = Bus.get_proxy.end (res);
                    proxy_acquired (proxy);
                }
                catch (IOError err)
                {
                    critical ("Unable to connect to Zeitgeist FTS: %s",
                        err.message);
                    proxy_unavailable (err);
                }
            });
    }

    protected override void on_connection_established ()
    {
    }

    protected override void on_connection_lost () {
    }

    /**
     * Perform a full text search possibly restricted to a {@link TimeRange}
     * and/or set of event templates.
     *
     * The default boolean operator is %AND. Thus the query
     * //foo bar// will be interpreted as //foo AND bar//. To exclude a term
     * from the result set prepend it with a minus sign - eg. //foo -bar//.
     * Phrase queries can be done by double quoting the string
     * //"foo is a bar"//. You can truncate terms by appending a *.
     *
     * There are a few keys you can prefix to a term or phrase to search within
     * a specific set of metadata. They are used like //key:value//. The keys
     * //name// and //title// search strictly within the text field of the
     * event subjects. The key //app// searches within the application name or
     * description that is found in the actor attribute of the events. Lastly,
     * you can use the //site// key to search within the domain name of subject
     * URIs.
     *
     * You can also control the results with the boolean operators //AND// and
     * //OR// and you may use brackets, ( and ), to control the operator
     * precedence.
     *
     * FIXME: how do we put documentation into _finish?
     * The total hit count of the query will be available via the returned
     * result set by calling zeitgeist_result_set_estimated_matches(). This will
     * often be bigger than the actual number of events held in the result set,
     * which is limited by the @num_events parameter passed to
     * zeitgeist_index_search().
     *
     * @param query The search string to send to Zeitgeist
     * @param time_range Restrict matched events to ones within this time
     *     range. If you are not interested in restricting the timerange pass
     *     zeitgeist_time_range_new_anytime() as Zeitgeist will detect
     *     this and optimize the query accordingly
     * @param event_templates Restrict matches events to ones matching these
     *     templates
     * @param offset Offset into the result set to read events from
     * @param num_events Maximal number of events to retrieve
     * @param result_type The {@link ResultType} determining the sort order.
     *     You may pass {@link ResultType.RELEVANCY} to this
     *     method to have the results ordered by relevancy calculated
     *     in relation to @query
     * @param cancellable A {@link GLib.Cancellable} used to cancel the
     *     call or %NULL
     */
    public async ResultSet search (
        string query,
        TimeRange time_range,
        GenericArray<Event> event_templates,
        uint32 offset,
        uint32 num_events,
        ResultType result_type,
        Cancellable? cancellable=null) throws Error
    {
        yield wait_for_proxy ();

        Variant result;
        uint matches;

        yield proxy.search (query, time_range.to_variant (),
            Events.to_variant (event_templates), offset, num_events,
            result_type, out result, out matches, cancellable);

        return new SimpleResultSet.with_num_matches (
            Events.from_variant (result), matches);
    }

    /**
     * Perform a full text search possibly restricted to a {@link TimeRange}
     * and/or set of event templates. As opposed to zeitgeist_index_search(),
     * this call will also return numeric relevancies of the events
     * in the {@link ResultSet}.
     *
     * See zeitgeist_index_search() for more details on how to create the
     * query.
     *
     * @param query The search string to send to Zeitgeist
     * @param time_range Restrict matched events to ones within this time
     *     range. If you are not interested in restricting the timerange pass
     *     zeitgeist_time_range_new_anytime() as Zeitgeist will detect
     *     this and optimize the query accordingly
     * @param event_templates Restrict matched events to ones matching these
     *     templates
     * @param storage_state Filter the events by availability of the storage
     *     medium.
     * @param offset Offset into the result set to read events from
     * @param num_events Maximal number of events to retrieve
     * @param result_type The {@link ResultType} determining the sort order
     *     You may pass {@link ResultType.RELEVANCY} to this method to
     *     have the results ordered by relevancy calculated in relation
     *     to "query"
     * @param cancellable a {@link GLib.Cancellable} to cancel the operation or %NULL
     */
    public async ResultSet search_with_relevancies (
        string query,
        TimeRange time_range,
        GenericArray<Event> event_templates,
        StorageState storage_state,
        uint32 offset,
        uint32 num_events,
        ResultType result_type,
        Cancellable? cancellable=null,
        out double[] relevancies) throws Error
    {
        yield wait_for_proxy ();

        Variant result;
        Variant relevancies_variant;
        uint matches;

        yield proxy.search_with_relevancies (query, time_range.to_variant (),
            Events.to_variant (event_templates), storage_state, offset,
            num_events, result_type, out relevancies_variant, out result,
            out matches, cancellable);

        relevancies = new double[relevancies_variant.n_children ()];
        VariantIter iter = relevancies_variant.iterator ();
        for (int i = 0; i < iter.n_children (); ++i)
        {
            double relevancy;
            iter.next ("d", out relevancy);
            relevancies[i] = relevancy;
        }

        return new SimpleResultSet.with_num_matches (
            Events.from_variant (result), matches);
    }

}

}

// vim:expandtab:ts=4:sw=4
