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

public class Monitor : Object
{

    private static int monitor_counter = 0;

    private TimeRange time_range;
    private GenericArray<Event> templates;

    // Client side D-Bus path the monitor lives under
    private string monitor_path;

    public signal void events_inserted (TimeRange time_range,
        GenericArray<Event> events);
    public signal void events_deleted (TimeRange time_range,
        GenericArray<uint32> event_ids);

    public Monitor (TimeRange time_range, GenericArray<Event> event_templates)
    {
        this.time_range = time_range;
        this.templates = event_templates;
        this.monitor_path = "/org/gnome/zeitgeist/monitor/%i".printf (
            monitor_counter++);
    }

    public TimeRange get_time_range ()
    {
        return time_range;
    }

    public GenericArray<Event> get_templates ()
    {
        return templates;
    }

    public string get_path ()
    {
        return "FIXME";
    }

}

}
