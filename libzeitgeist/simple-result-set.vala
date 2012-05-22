/* simple-result-set.vala
 *
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

internal class SimpleResultSet : Object, ResultSet
{

    private GenericArray<Event> events;
    private uint num_estimated_matches;
    private uint cursor;

    internal SimpleResultSet (GenericArray<Event> events)
    {
        this.events = events;
        num_estimated_matches = events.length;
        cursor = 0;
    }

    public uint size ()
    {
        return events.length;
    }

    public uint estimated_matches ()
    {
        return num_estimated_matches;
    }

    public Event next ()
    {
        return events.get (cursor++);
    }

    public bool has_next ()
    {
        return cursor < events.length;
    }

    public Event peek ()
    {
        return events.get (cursor);
    }

    public void seek (uint pos)
    {
        cursor = pos;
    }

    public uint tell ()
    {
        return cursor;
    }

}

}

// vim:expandtab:ts=4:sw=4
