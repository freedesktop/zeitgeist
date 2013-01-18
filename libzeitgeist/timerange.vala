/* timerange.vala
 *
 * Copyright © 2011-2012 Collabora Ltd.
 *             By Seif Lotfy <seif@lotfy.com>
 *             By Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
 * Copyright © 2011 Michal Hruby <michal.mhr@gmail.com>
 * Copyright © 2012 Canonical Ltd.
 *             By Siegfried-A. Gevatter <siegfried.gevatter@collabora.co.uk>
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
 * Immutable representation of an interval in time, marked by a
 * beginning and an end
 *
 * A light, immutable, encapsulation of an interval in time, marked by
 * a beginning and an end.
 */
[CCode (type_signature = "(xx)")]
public class TimeRange: Object
{
    public int64 start { get; private set; }
    public int64 end   { get; private set; }

    /**
     * @param start_msec starting timestamp in number of milliseconds
     *        since the Unix Epoch
     * @param end_msec ending timestamp in number of milliseconds
     *        since the Unix Epoch
     * @return a newly allocated ZeitgeistTimeRange. Free with
     *        g_object_unref()
     */
    public TimeRange (int64 start_msec, int64 end_msec)
    {
        start = start_msec;
        end = end_msec;
    }

    /**
     * @return a new time range starting from the beginning of the Unix
     *         Epoch stretching to the end of time
     */
    public TimeRange.anytime ()
    {
        this (0, int64.MAX);
    }

    /**
     * @return a new time range starting from the beggining of the
     *         Unix Epoch ending a the moment of invocation
     */
    public TimeRange.to_now ()
    {
        this (0, Timestamp.from_now ());
    }

    /**
     * @return a new time range starting from the moment of invocation
     *         to the end of time
     */
    public TimeRange.from_now ()
    {
        this (Timestamp.from_now (), int64.MAX);
    }

    /**
     * Create a #TimeRange from a variant.
     *
     * @param variant a variant representing a #TimeRange
     * @return a new time range starting from the moment of invocation
     *         to the end of time
     */
    public TimeRange.from_variant (Variant variant)
        throws DataModelError
    {
        Utils.assert_sig (variant.get_type_string () == "(xx)",
            "Invalid D-Bus signature.");

        int64 start_msec = 0;
        int64 end_msec = 0;

        variant.get ("(xx)", &start_msec, &end_msec);

        this (start_msec, end_msec);
    }

    /**
     * @return a new variant holding the time range
     */
    public Variant to_variant ()
    {
        return new Variant ("(xx)", start, end);
    }

    /**
     * Check whether two time ranges are intersecting.
     *
     * @param time_range the second time range to compare with
     * @return a new time range representing the intersection
     */
    public TimeRange? intersect (TimeRange time_range)
    {
        var result = new TimeRange(0,0);
        if (start < time_range.start)
            if (end < time_range.start)
                return null;
            else
                result.start = time_range.start;
        else
            if (start > time_range.end)
                return null;
            else
                result.start = start;

        if (end < time_range.end)
            if (end < time_range.start)
                return null;
            else
                result.end = end;
        else
            if (start > time_range.end)
                return null;
            else
                result.end = time_range.end;
        return result;
    }
}

}

// vim:expandtab:ts=4:sw=4
