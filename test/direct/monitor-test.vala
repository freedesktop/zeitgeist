/* monitor-test.vala
 *
 * Copyright © 2012 Christian Dywan <christian@twotoasts.de>
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
using Assertions;

int main (string[] argv)
{
    Test.init (ref argv);

    Test.add_func ("/Monitor/Create", monitor_create_test);

    return Test.run ();
}

void monitor_create_test ()
{
    var event_templates = new GenericArray<Event> ();
    var mon = new Monitor (new TimeRange (27, 68), event_templates);
    assert (27 == mon.time_range.start);
    assert (68 == mon.time_range.end);

    assert (event_templates == mon.get_templates());
}

// vim:expandtab:ts=4:sw=4
