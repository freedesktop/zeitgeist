/* enumerations.vala
 *
 * Copyright © 2011-2012 Collabora Ltd.
 *          By Seif Lotfy <seif@lotfy.com>
 *          By Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
 * Copyright © 2011 Manish Sinha <manishsinha@ubuntu.com>
 * Copyright © 2011 Michal Hruby <michal.mhr@gmail.com>
 * Copyright © 2012 Canonical Ltd.
 *          By Siegfried-A. Gevatter <siegfried.gevatter@collabora.co.uk>
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

/**
 * Errors which can be thrown when asynchronously querying for {@link Event}s.
 */
[DBus (name = "org.gnome.zeitgeist.DataModelError")]
public errordomain DataModelError {
    /**
     * Signature sent over DBus is invalid.
     */
    INVALID_SIGNATURE,
    /**
     * {@link Event} is NULL.
     */
    NULL_EVENT,
    /**
     * Query return too many {@link Event}s.
     */
    TOO_MANY_RESULTS
}

/**
 * ZeitgeistResultType
 *
 * Used to control how the query results are grouped and sorted.
 * See zeitgeist_log_find_events(), zeitgeist_log_find_event_ids(), and
 * zeitgeist_index_search().
 */

public enum ResultType
{
    /**
     * All events with the most recent events first
     */
    MOST_RECENT_EVENTS                   = 0,
    /**
     * All events with the oldest
     */
    LEAST_RECENT_EVENTS                  = 1,
    /**
     * One event for each subject only, ordered with the most recent events first
     */
    MOST_RECENT_SUBJECTS                 = 2,
    /**
     * One event for each subject, only, ordered with oldest events first
     */
    LEAST_RECENT_SUBJECTS                = 3,
    /**
     * One event for each subject only, ordered by the popularity of the subject
     */
    MOST_POPULAR_SUBJECTS                = 4,
    /**
     * One event for each subject only, ordered ascendingly by popularity of the subject
     */
    LEAST_POPULAR_SUBJECTS               = 5,
    /**
     * The last event of each different actor ordered by the popularity of the actor
     */
    MOST_POPULAR_ACTOR                   = 6,
    /**
     * The last event of each different actor, ordered ascendingly by the popularity of the actor
     */
    LEAST_POPULAR_ACTOR                  = 7,
    /**
     * The actor that has been used to most recently
     */
    MOST_RECENT_ACTOR                    = 8,
    /**
     * The actor that has been used to least recently
     */
    LEAST_RECENT_ACTOR                   = 9,
    /**
     * The last event of each different subject origin.
     */
    MOST_RECENT_ORIGIN                   = 10,
    /**
     * The last event of each different subject origin, ordered by least recently used first
     */
    LEAST_RECENT_ORIGIN                  = 11,
    /**
     * The last event of each different subject origin, ordered by the popularity of the origins
     */
    MOST_POPULAR_ORIGIN                  = 12,
    /**
     * The last event of each different subject origin, ordered ascendingly by the popularity of the origin
     */
    LEAST_POPULAR_ORIGIN                 = 13,
    /**
     * The first event of each different actor
     */
    OLDEST_ACTOR                         = 14,
    /**
     * One event for each subject interpretation only, ordered with the most recent events first
     */
    MOST_RECENT_SUBJECT_INTERPRETATION   = 15,
    /**
     * One event for each subject interpretation only, ordered with the least recent events first
     */
    LEAST_RECENT_SUBJECT_INTERPRETATION  = 16,
    /**
     * One event for each subject interpretation only, ordered by the popularity of the subject interpretation
     */
    MOST_POPULAR_SUBJECT_INTERPRETATION  = 17,
    /**
     * One event for each subject interpretation only, ordered ascendingly by popularity of the subject interpretation
     */
    LEAST_POPULAR_SUBJECT_INTERPRETATION = 18,
    /**
     * One event for each mimetype only ordered with the most recent events first
     */
    MOST_RECENT_MIMETYPE                 = 19,
    /**
     * One event for each mimetype only ordered with the least recent events first
     */
    LEAST_RECENT_MIMETYPE                = 20,
    /**
     * One event for each mimetype only ordered by the popularity of the mimetype
     */
    MOST_POPULAR_MIMETYPE                = 21,
    /**
     * One event for each mimetype only ordered ascendingly by popularity of the mimetype
     */
    LEAST_POPULAR_MIMETYPE               = 22,
    /**
     * One event for each subject only by current_uri instead of uri ordered with the most recent events first
     */
    MOST_RECENT_CURRENT_URI              = 23,
    /**
     *  One event for each subject only by current_uri instead of uri ordered with oldest events first
     */
    LEAST_RECENT_CURRENT_URI             = 24,
    /**
     * One event for each subject only by current_uri instead of uri ordered by the popularity of the subject
     */
    MOST_POPULAR_CURRENT_URI             = 25,
    /**
     * One event for each subject only by current_uri instead of uri ordered ascendingly by popularity of the subject
     */
    LEAST_POPULAR_CURRENT_URI            = 26,
    /**
     * The last event of each different origin
     */
    MOST_RECENT_EVENT_ORIGIN             = 27,
    /**
     * The last event of each different origin, ordered by least recently used first
     */
    LEAST_RECENT_EVENT_ORIGIN            = 28,
    /**
     * The last event of each different origin ordered by the popularity of the origins
     */
    MOST_POPULAR_EVENT_ORIGIN            = 29,
    /**
     * The last event of each different origin, ordered ascendingly by the popularity of the origin
     */
    LEAST_POPULAR_EVENT_ORIGIN           = 30,
    /**
     * The last event of each different subject origin.
     */
    MOST_RECENT_CURRENT_ORIGIN           = 31,
    /**
     * The last event of each different subject origin, ordered by least recently used first
     */
    LEAST_RECENT_CURRENT_ORIGIN          = 32,
    /**
     * The last event of each different subject origin, ordered by the popularity of the origins
     */
    MOST_POPULAR_CURRENT_ORIGIN          = 33,
    /**
     * The last event of each different subject origin, ordered ascendingly by the popularity of the origin
     */
    LEAST_POPULAR_CURRENT_ORIGIN         = 34,
    /**
     * Only allowed on zeitgeist_index_search(). Events are sorted by query relevancy
     */
    RELEVANCY                            = 100;

    /**
     * @param result_type A {@link ResultType}
     *
     * @return true if the results for the given result_type will be sorted
     * ascendantly by date, false if they'll be sorted descendingly.
     */
    public static bool is_sort_order_asc (ResultType result_type)
    {
        switch (result_type)
        {
            // FIXME: Why are LEAST_POPULAR_* using ASC?
            case ResultType.LEAST_RECENT_EVENTS:
            case ResultType.LEAST_RECENT_EVENT_ORIGIN:
            case ResultType.LEAST_POPULAR_EVENT_ORIGIN:
            case ResultType.LEAST_RECENT_SUBJECTS:
            case ResultType.LEAST_POPULAR_SUBJECTS:
            case ResultType.LEAST_RECENT_CURRENT_URI:
            case ResultType.LEAST_POPULAR_CURRENT_URI:
            case ResultType.LEAST_RECENT_ACTOR:
            case ResultType.LEAST_POPULAR_ACTOR:
            case ResultType.OLDEST_ACTOR:
            case ResultType.LEAST_RECENT_ORIGIN:
            case ResultType.LEAST_POPULAR_ORIGIN:
            case ResultType.LEAST_RECENT_CURRENT_ORIGIN:
            case ResultType.LEAST_POPULAR_CURRENT_ORIGIN:
            case ResultType.LEAST_RECENT_SUBJECT_INTERPRETATION:
            case ResultType.LEAST_POPULAR_SUBJECT_INTERPRETATION:
            case ResultType.LEAST_RECENT_MIMETYPE:
            case ResultType.LEAST_POPULAR_MIMETYPE:
                return true;

            case ResultType.MOST_RECENT_EVENTS:
            case ResultType.MOST_RECENT_EVENT_ORIGIN:
            case ResultType.MOST_POPULAR_EVENT_ORIGIN:
            case ResultType.MOST_RECENT_SUBJECTS:
            case ResultType.MOST_POPULAR_SUBJECTS:
            case ResultType.MOST_RECENT_CURRENT_URI:
            case ResultType.MOST_POPULAR_CURRENT_URI:
            case ResultType.MOST_RECENT_ACTOR:
            case ResultType.MOST_POPULAR_ACTOR:
            case ResultType.MOST_RECENT_ORIGIN:
            case ResultType.MOST_POPULAR_ORIGIN:
            case ResultType.MOST_RECENT_CURRENT_ORIGIN:
            case ResultType.MOST_POPULAR_CURRENT_ORIGIN:
            case ResultType.MOST_RECENT_SUBJECT_INTERPRETATION:
            case ResultType.MOST_POPULAR_SUBJECT_INTERPRETATION:
            case ResultType.MOST_RECENT_MIMETYPE:
            case ResultType.MOST_POPULAR_MIMETYPE:
            case ResultType.RELEVANCY:
                return false;

            default:
                warning ("Unrecognized ResultType: %u", (uint) result_type);
                return true;
        }
    }
}

/*
 * An enumeration class used to define how query results should
 * be returned from the Zeitgeist engine.
 */
public enum RelevantResultType
{
    /**
     * All uris with the most recent uri first
     */
    RECENT  = 0,
    /**
     * All uris with the most related one first
     */
    RELATED = 1,
}

/**
 * Enumeration class defining the possible values for the storage
 * state of an event subject.
 *
 * The StorageState enumeration can be used to control whether or
 * not matched events must have their subjects available to the user.
 * Fx. not including deleted files, files on unplugged USB drives,
 * files available only when a network is available etc.
 */
public enum StorageState
{
    /**
     * The storage medium of the events subjects must not be available to the user
     */
    NOT_AVAILABLE   = 0,
    /**
     * The storage medium of all event subjects must be immediately available to the user
     */
    AVAILABLE       = 1,
    /**
     * The event subjects may or may not be available
     */
    ANY             = 2
}

}

// vim:expandtab:ts=4:sw=4
