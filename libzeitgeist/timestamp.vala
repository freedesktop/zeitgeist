/* timestamp.vala
 *
 * Copyright © 2012 Collabora Ltd.
 *             By Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
 * Copyright © 2010 Canonical, Ltd.
 *             By Mikkel Kamstrup Erlandsen <mikkel.kamstrup@canonical.com>
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

/**
 * Convenience functions for dealing with timestamps and dates
 *
 * include: zeitgeist.h
 *
 * A suite of convenience functions for dealing with timestamps and dates.
 *
 * Zeitgeist timestamps are represented as ''gint64''s with the number
 * of milliseconds since the Unix Epoch.
 */
namespace Zeitgeist.Timestamp
{
    /**
     * A second represented as a Zeitgeist timestamp (ie. 1000ms)
     */
    public const int64 SECOND = 1000;

    /**
     * A minute represented as a Zeitgeist timestamp (ie. 60000ms)
     */
    public const int64 MINUTE = 60000;

    /**
     * An hour represented as a Zeitgeist timestamp (ie. 3600000ms)
     */
    public const int64 HOUR = 3600000;

    /**
     * A day represented as a Zeitgeist timestamp (ie. 86400000ms)
     */
    public const int64 DAY = 86400000;

    /**
     * A week represented as a Zeitgeist timestamp (ie. 604800000ms)
     */
    public const int64 WEEK = 604800000;

    /**
     * A year represented as a Zeitgeist timestamp (ie. 31556952000ms).
     * Be warned that a year is not 365 days, but in fact 365.2425 days,
     * to account for leap years.
     */
    public const int64 YEAR = 31556952000;

    /**
     * Convert a {@link GLib.TimeVal} to an amount of milliseconds since
     * the Unix Epoch
     *
     * @param timeval time to convert
     *
     * @return number of milliseconds since the Unix Epoch
     */
    public int64 from_timeval (TimeVal timeval)
    {
        var m_seconds = (int64) timeval.tv_sec * 1000;
        return m_seconds + ((int64) timeval.tv_usec / 1000);
    }

    /**
     * Write a Zeitgeist timestamp to a {@link GLib.TimeVal} instance.
     * Note that Zeitgeist uses only a millisecond resolution, whereas
     * {@link GLib.TimeVal} has microsecond resolution. This means that
     * the lower three digits of @tv.tv_usec will always be 0.
     *
     * @param timestamp to convert
     *
     * @return the equivalent {@link GLib.TimeVal} instance.
     */
    public TimeVal to_timeval (int64 timestamp)
    {
        TimeVal timeval = TimeVal();
        timeval.tv_sec = (long) (timestamp / 1000);
        timeval.tv_usec = (long) ((timestamp % 1000) * 1000);
        return timeval;
    }

    /**
     * Return the current timestamp in milliseconds.
     *
     * @return the timestamp for the current system time, in milliseconds
     *         since the Unix Epoch
     */
    public int64 from_now ()
    {
        return get_real_time () / 1000;
    }

    /**
     * Parse a timestamp from an ISO8601-encoded string.
     *
     * @param datetime a string containing an ISO8601-conforming datetime
     *
     * @return the timestamp represented by the given string, or -1 if
     *         it can't be parsed
     */
    public int64 from_iso8601 (string datetime)
    {
        TimeVal timeval = TimeVal();
        if (timeval.from_iso8601 (datetime))
            return from_timeval (timeval);
        else
            return -1;
    }

    /**
     * Convert a timestamp to a human-readable ISO8601 format
     *
     * @param timestamp a timestamp in milliseconds since the Unix Epoch
     *
     * @return a newly allocated string containing the ISO8601 version of
     *         the given timestamp
     */
    public string to_iso8601 (int64 timestamp)
    {
        TimeVal timeval = to_timeval (timestamp);
        return timeval.to_iso8601 ();
    }

    /**
     * Convert a ''GDate'' to a Zeitgeist timestamp
     *
     * @param date the date to convert
     *
     * @return the given date expressed as a timestamp in milliseconds since
     *         the Epoch. The timestamp is guaranteed to be roudned off to the
     *         midnight of the given date.
     */
    public int64 from_date (Date date)
    {
        int64 julian = date.get_julian ();
        return prev_midnight (julian*DAY - 1969*YEAR);
    }

    /**
     * Convert a day, month, year tuple into a Zeitgeist timestamp
     *
     * @param day the day of the month
     * @param month the month of the year
     * @param year the year
     *
     * @return the given date (rounded off to the midnight), expressed as
     *         a timestamp in milliseconds since the Epoch, or -1 in case
     *         the provided parameters don't constitute a valid date.
     */
    public int64 from_dmy (DateDay day, DateMonth month, DateYear year)
    {
        Date date = Date ();
        date.set_dmy (day, month, year);
        return from_date (date);
    }

    /**
     * Write a timestamp to a {@link GLib.Date} structure
     *
     * @param timestamp to convert
     * @return {@link GLib.Date} initialized to the given timestamp
     */
    public Date to_date (int64 timestamp)
    {
        Date date = Date ();
        TimeVal timeval = to_timeval (timestamp);
        date.set_time_val (timeval);
        return date;
    }

    /**
     * Calculate the timestamp for the next midnight after the given timestamp.
     *
     * If is is already midnight (down to the millisecond), this method will
     * return the value for the next midnight. In other words, you can call
     * this method recursively in order to iterate, forwards in time, over
     * midnights.
     *
     * @param timestamp the Zeitgeist timestamp to find the next midnight for
     *
     * @return the timestamp for the next midnight after the given timestamp
     */
    public int64 next_midnight (int64 timestamp)
    {
        int64 remainder = timestamp % DAY;
        if (remainder == 0)
            return timestamp + DAY;
        else
            return (timestamp - remainder) + DAY;
    }

    /**
     * Calculate the timestamp for the midnight just before the given
     * timestamp.
     *
     * If is is already midnight (down to the millisecond), this method will
     * return the value for the previous midnight. In other words, you can
     * call this method recursively in order to iterate, backwards in time,
     * over midnights.
     *
     * @param timestamp the Zeitgeist timestamp to find the previous
     *        midnight for
     *
     * @return the timestamp for the midnight just before the given timestamp
     */
    public int64 prev_midnight (int64 timestamp)
    {
        int64 remainder = timestamp % DAY;
        if (remainder == 0)
            return timestamp - DAY;
        else
            return (timestamp - remainder);
    }

}

// vim:expandtab:ts=4:sw=4
