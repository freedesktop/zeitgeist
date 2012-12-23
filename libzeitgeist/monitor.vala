/*
 * Copyright © 2012 Canonical Ltd.
 *             By Siegfried-A. Gevatter <siegfried.gevatter@collabora.co.uk>
 *
 * Based upon a C implementation (© 2010 Canonical Ltd) by:
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
 * Listens for updates to the Zeitgeist event log
 *
 * A #Monitor listens for updates to the Zeitgeist event log
 * matching a given set of templates and with timestamps in some predefined
 * time range.
 *
 * A monitor must be installed into the running Zeitgeist daemon by calling
 * zeitgeist_log_install_monitor(). The monitor will not emit any of the
 * ::events-added or ::events-deleted signals before this.
 */
public class Monitor : Object, RemoteMonitor
{

    private static int monitor_counter = 0;

    public TimeRange time_range {get; construct set;}
    public GenericArray<Event> event_templates {get; construct set;}

    // Client side D-Bus path the monitor lives under
    private ObjectPath monitor_path;

    /**
     * ZeitgeistMonitor::events-inserted:
     *
     * Emitted when events matching the event templates and with timestamps
     * within the time range of the monitor has been inserted into the log.
     *
     * @param time_range A #ZeitgeistTimeRange that specifies the minimum and
     *     maximum of the timestamps in @events
     * @param events A #ZeitgeistResultSet holding the "ZeitgeistEvent"s that
     *     have been inserted into the log
     */
    public signal void events_inserted (TimeRange time_range,
        ResultSet events);

    /**
     * ZeitgeistMonitor::events-deleted:
     *
     * Emitted when events with timestamps within the time range of this
     * monitor have been deleted from the log. Note that the deleted events
     * may not match the event templates for the monitor.
     *
     * @param time_range A #ZeitgeistTimeRange that specifies the minimum and
     *     maximum timestamps of the deleted events
     * @param event_ids A #GArray of #guint32<!-- -->s holding the IDs of the
     *     deleted events
     */
    public signal void events_deleted (TimeRange time_range,
        uint32[] event_ids);

    /**
     * zeitgeist_monitor_new
     *
     * Create a new monitor. Before you can receive signals from the monitor you
     * need to install it in the running Zeitgeist daemon by calling
     * zeitgeist_log_install_monitor().
     *
     * @param time_range The monitor will only listen for events with
     *     timestamps within this time range. Note that it is legal for
     *     applications to insert events that are "in the past".
     * @param event_templates A #GPtrArray of #ZeitgeistEvent<!-- -->s.
     *     Only listen for events that match any of these templates.
     *
     * @return A reference to a newly allocated monitor
     */
    public Monitor (TimeRange time_range, owned GenericArray<Event> event_templates)
    {
        this.time_range = time_range;
        this.event_templates = event_templates;
        this.monitor_path = new ObjectPath (
            "/org/gnome/zeitgeist/monitor/%i".printf (monitor_counter++));
    }

    public GenericArray<Event> get_templates ()
    {
        return event_templates;
    }

    public ObjectPath get_path ()
    {
        return monitor_path;
    }

    public async void notify_insert (
        Variant time_range,
        Variant events)
    {
        try
        {
            SimpleResultSet result_set = new SimpleResultSet (
                Events.from_variant (events));
            events_inserted (new TimeRange.from_variant (time_range),
                result_set);
        }
        catch (DataModelError err)
        {
            warning ("%s", err.message);
        }
    }

    public async void notify_delete (
        Variant time_range,
        uint32[] event_ids)
    {
        try
        {
            events_deleted (new TimeRange.from_variant (time_range),
                event_ids);
        }
        catch (DataModelError err)
        {
            warning ("%s", err.message);
        }
    }

}

}

// vim:expandtab:ts=4:sw=4
