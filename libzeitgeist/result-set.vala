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

/**
 * SECTION:zeitgeist-result-set
 * @short_description: Cursor-like interface for results sets
 * @include: zeitgeist.h
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

namespace Zeitgeist
{

public interface ResultSet : Object
{

    /**
     * zeitgeist_result_set_size:
     * @self: The #ZeitgeistResultSet to get the size of
     *
     * Get the number of #ZeitgeistEvent<!-- -->s held in a #ZeitgeistResultSet.
     * Unlike the number obtained from zeitgeist_result_set_estimated_matches() the
     * size of the result set is always equal to the number of times you can call
     * zeitgeist_result_set_next().
     *
     * Returns: The number of events held in the result set
     */
    public abstract uint size ();

    /**
     * zeitgeist_result_set_estimated_matches:
     * @self: The #ZeitgeistResultSet to get the number of estimated matches on
     *
     * FIXME: this is not true for _find_events/_get_events():
     * Get an estimated total number of matches that would have been for the query
     * that generated the result set had it not been restricted in size.
     *
     * For zeitgeist_log_find_events() and zeitgeist_log_get_events() this will
     * always be the same as zeitgeist_result_set_size(). For cases like
     * zeitgeist_index_search() where you specify a subset of the hits to retrieve
     * the estimated match count will often be bigger than the result set size.
     *
     * Returns: The number of events that matched the query
     */
    public abstract uint estimated_matches ();

    /**
     * zeitgeist_result_set_next:
     * @self: The #ZeitgeistResultSet to get an event from
     *
     * Get the current event from the result set and advance the cursor.
     * To ensure that calls to this method will succeed you can call
     * zeitgeist_result_set_has_next().
     *
     * To retrieve the current event without advancing the cursor call
     * zeitgeist_result_set_peek() in stead of this method.
     *
     * Returns: The #ZeitgeistEvent at the current cursor position
     */
    public abstract Event next ();

    /**
     * zeitgeist_result_set_has_next:
     * @self: The #ZeitgeistResultSet to check
     *
     * Check if a call to zeitgeist_result_set_next() will succeed.
     *
     * Returns: %TRUE if and only if more events can be retrieved by calling
     *          zeitgeist_result_set_next()
     */
    public abstract bool has_next ();

    /**
     * zeitgeist_result_set_peek:
     * @self: The #ZeitgeistResultSet to get an event from
     *
     * Get the event at the current cursor position.
     *
     * To retrieve the current event and advance the cursor position call
     * zeitgeist_result_set_next() in stead of this method.
     *
     * Returns: The #ZeitgeistEvent at the current cursor position
     */
     public abstract Event peek ();

    /**
     * zeitgeist_result_set_seek:
     * @self: The #ZeitgeistResultSet to seek in
     * @pos: The position to seek to
     *
     * Set the cursor position. Following calls to zeitgeist_result_set_peek()
     * or zeitgeist_result_set_next() will read the event at position @pos.
     */
     public abstract void seek (uint pos);

    /**
     * zeitgeist_result_set_tell:
     * @self: The #ZeitgeistResultSet to check the cursor position for
     *
     * Get the current position of the cursor.
     *
     * Returns: The current position of the cursor
     */
    public abstract uint tell ();

}

}

// vim:expandtab:ts=4:sw=4