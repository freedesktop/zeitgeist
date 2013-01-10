/*
 * Copyright © 2012 Canonical Ltd.
 *             By Siegfried-A. Gevatter <siegfried.gevatter@collabora.co.uk>
 *
 * Based upon a C implementation (© 2009 Canonical Ltd) by:
 *  Mikkel Kamstrup Erlandsen <mikkel.kamstrup@canonical.com>
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
 * Cursor-like interface for results sets
 *
 * include: zeitgeist.h
 *
 * Interface for results returned by zeitgeist_log_find_events(),
 * zeitgeist_log_get_events(), and zeitgeist_index_search().
 *
 * This interface utilizes a cursor-like metaphor. You advance the cursor
 * by calling zeitgeist_result_set_next() or adjust it manually by calling
 * zeitgeist_result_set_seek().
 *
 * Calling zeitgeist_result_set_next() will also return the event at the
 * current cursor position. You may retrieve the current event without advancing
 * the cursor by calling zeitgeist_result_set_peek().
 *
 */
public interface ResultSet : Object
{

    /**
     * Get the number of #ZeitgeistEvent<!-- -->s held in a #ZeitgeistResultSet.
     * Unlike the number obtained from zeitgeist_result_set_estimated_matches() the
     * size of the result set is always equal to the number of times you can call
     * zeitgeist_result_set_next().
     *
     * @return The number of events held in the result set
     */
    public abstract uint size ();

    /**
     * Get the total number of matches that would have been for the query
     * that generated the result set had it not been restricted in size.
     * For FTS the number of matches is estimated.
     *
     * For zeitgeist_log_find_events() and zeitgeist_log_get_events() this will
     * always be the same as zeitgeist_result_set_size(). For cases like
     * zeitgeist_index_search() where you specify a subset of the hits to retrieve
     * the estimated match count will often be bigger than the result set size.
     *
     * @return The number of events that matched the query
     */
    public abstract uint estimated_matches ();

    /**
     * Get the current event from the result set and advance the cursor. To
     * ensure that calls to this method will succeed you can call
     * zeitgeist_result_set_has_next().
     *
     * @return The #ZeitgeistEvent at the current cursor position, or NULL
     *         if there are no events left.
     */
     public abstract Event? next_value ();

    /**
     * Check if a call to zeitgeist_result_set_next() will succeed.
     *
     * @return TRUE if and only if more events can be retrieved
     *         by calling zeitgeist_result_set_next()
     */
    public abstract bool has_next ();

    /**
     * Get the current position of the cursor.
     *
     * @return The current position of the cursor
     */
    public abstract uint tell ();

    /**
     * Resets the result set to start iterating it again from scratch.
     *
     */
    public abstract void reset ();

    /**
     * Do not use this method! It is only for use by Vala.
     */
    public ResultSet iterator ()
    {
        // Damn you Vala. Why is Iterator<> in Gee?
        return this;
    }
}

}

// vim:expandtab:ts=4:sw=4
