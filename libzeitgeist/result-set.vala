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
     * @param self The #ZeitgeistResultSet to get the size of
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
     * @param self The #ZeitgeistResultSet to get the number of estimated
     *     matches on
     * @return The number of events that matched the query
     */
    public abstract uint estimated_matches ();

    /**
     * Get the event at the current cursor position.
     *
     * To retrieve the current event and advance the cursor position call
     * zeitgeist_result_set_next() in stead of this method.
     *
     * @param self The #ZeitgeistResultSet to get an event from
     *
     * @return The #ZeitgeistEvent at the current cursor position
     */
     public abstract Event peek ();

    /**
     * Set the cursor position. Following calls to zeitgeist_result_set_peek()
     * or zeitgeist_result_set_next() will read the event at position @pos.
     *
     * @param self The #ZeitgeistResultSet to seek in
     * @param pos The position to seek to
     */
     public abstract void seek (uint pos);

    /**
     * Get the current position of the cursor.
     *
     * @param self The #ZeitgeistResultSet to check the cursor position for
     *
     * @return The current position of the cursor
     */
    public abstract uint tell ();

    /**
     * Get an iterator object
     * @param self The #ZeitgeistResultSet to seek in
     */
    public ResultSet iterator () {
        return this;
    }

    public abstract Event? next_value ();

    public abstract bool has_next();

    public Event? next ()
    {
        return next_value ();
    }
}

}

// vim:expandtab:ts=4:sw=4
