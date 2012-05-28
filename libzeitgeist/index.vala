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
 * SECTION:zeitgeist-index
 * @short_description: Query the Zeitgeist Full Text Search Extension
 * @include: zeitgeist.h
 */
public class Index : QueuedProxyWrapper
{
    private RemoteSimpleIndexer proxy;

    /**
     * zeitgeist_index_new:
     * Create a new index that interfaces with the default event index of the
     * Zeitgeist daemon.
     *
     * Create a new #ZeitgeistIndex instance. The index will start to connect
     * to Zeitgeist asynchronously. You can however start calling methods on
     * the returned instance immediately, any method calls issued before the
     * connection has been established will simply be queued and executed once
     * the connection is up.
     *
     * Returns: A reference to a newly allocated index. Free with g_object_unref().
     */
    public Index ()
    {
        Bus.get_proxy<RemoteSimpleIndexer> (BusType.SESSION,
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
                    proxy_unavailable();
                }
            });
    }

    protected override void on_connection_established ()
    {
    }

    protected override void on_connection_lost () {
    }

    /**
     * zeitgeist_index_search:
     * @self: The #ZeitgeistIndex you want to query
     * @query: The search string to send to Zeitgeist
     * @time_range: Restrict matched events to ones within this time range. If
     *              you are not interested in restricting the timerange pass
     *              zeitgeist_time_range_new_anytime() as Zeitgeist will detect
     *              this and optimize the query accordingly
     * @event_templates: Restrict matches events to ones matching these
     *                   templates
     * @offset: Offset into the result set to read events from
     * @num_events: Maximal number of events to retrieve
     * @result_type: The #ZeitgeistResultType determining the sort order.
     *               You may pass #ZEITGEIST_RESULT_TYPE_RELEVANCY to this
     *               method to have the results ordered by relevancy calculated
     *               in relation to @query
     * @cancellable: A #GCancellable used to cancel the call or %NULL
     * @callback: A #GAsyncReadyCallback to invoke when the search results are
                  ready
     * @user_data: User data to pass back with @callback
     *
     * Perform a full text search possibly restricted to a #ZeitgeistTimeRange
     * and/or set of event templates.
     *
     * The default boolean operator is %AND. Thus the query
     * <emphasis>foo bar</emphasis> will be interpreted as
     * <emphasis>foo AND bar</emphasis>. To exclude a term from the result
     * set prepend it with a minus sign - eg <emphasis>foo -bar</emphasis>.
     * Phrase queries can be done by double quoting the string
     * <emphasis>"foo is a bar"</emphasis>. You can truncate terms by appending
     * a *.
     *
     * There are a few keys you can prefix to a term or phrase to search within
     * a specific set of metadata. They are used like
     * <emphasis>key:value</emphasis>. The keys <emphasis>name</emphasis> and
     * <emphasis>title</emphasis> search strictly within the text field of the
     * event subjects. The key <emphasis>app</emphasis> searches within the
     * application name or description that is found in the actor attribute of
     * the events. Lastly you can use the <emphasis>site</emphasis> key to search
     * within the domain name of the subject URIs.
     *
     * You can also control the results with the boolean operators
     * <emphasis>AND</emphasis> and <emphasis>OR</emphasis> and you may
     * use brackets, ( and ), to control the operator precedence.
     *
     * // FIXME: how do we put documentation into _finish?
     * The total hit count of the query will be available via the returned
     * result set by calling zeitgeist_result_set_estimated_matches(). This will
     * often be bigger than the actual number of events held in the result set,
     * which is limited by the @num_events parameter passed to
     * zeitgeist_index_search().
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
        yield wait_for_proxy (search.callback);

        Variant result;
        uint matches;

        yield proxy.search (query, time_range.to_variant (),
            Events.to_variant (event_templates), offset, num_events,
            result_type, out result, out matches, cancellable);

        return new SimpleResultSet (Events.from_variant (result), matches);
    }

    /**
     * zeitgeist_index_search_with_relevancies:
     * @self: The #ZeitgeistIndex you want to query
     * @query: The search string to send to Zeitgeist
     * @time_range: Restrict matched events to ones within this time range. If
     *              you are not interested in restricting the timerange pass
     *              zeitgeist_time_range_new_anytime() as Zeitgeist will detect
     *              this and optimize the query accordingly
     * @event_templates: Restrict matched events to ones matching these
     *                   templates
     * @storage_state: Filter the events by availability of the storage medium.
     * @offset: Offset into the result set to read events from
     * @num_events: Maximal number of events to retrieve
     * @result_type: The #ZeitgeistResultType determining the sort order.
     *               You may pass #ZEITGEIST_RESULT_TYPE_RELEVANCY to this
     *               method to have the results ordered by relevancy calculated
     *               in relation to @query
     * @cancellable: A #GCancellable used to cancel the call or %NULL
     * @callback: A #GAsyncReadyCallback to invoke when the search results are
     *            ready
     * @user_data: User data to pass back with @callback
     *
     * Perform a full text search possibly restricted to a #ZeitgeistTimeRange
     * and/or set of event templates. As opposed to zeitgeist_index_search(),
     * this call will also return numeric relevancies of the events
     * in the #ZeitgeistResultSet.
     *
     * See zeitgeist_index_search() for more details on how to create the
     * query.
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
        yield wait_for_proxy (search_with_relevancies.callback);

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

        return new SimpleResultSet (Events.from_variant (result), matches);
    }

}

}

// vim:expandtab:ts=4:sw=4
