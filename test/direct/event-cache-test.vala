/* event-cache-test.vala
 *
 * Copyright © 2012 Collabora Ltd.
 *             By Trever Fischer <trever.fischer@collabora.co.uk>
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

int main (string[] args)
{
    Test.init (ref args);
    Log.set_always_fatal (LogLevelFlags.LEVEL_CRITICAL);

    Test.add_func("/EventCache/basic", basic_test);
    Test.add_func("/EventCache/size", size_test);
    Test.add_func("/EventCache/expiration", expiration_test);

    return Test.run ();
}

public void basic_test ()
{
    EventCache c = new EventCache ();
    for (int i = 0; i<1024; i++)
    {
        Event e = new Event();
        e.id = i;
        c.cache_event (e);
    }
    assert (c.size == 1024);
}

public void size_test ()
{
    EventCache c = new EventCache ();
    c.max_size = 5;
    for (int i = 0; i<2048; i++)
    {
        Event e = new Event();
        e.id = i;
        c.cache_event (e);
    }

    assert (c.size == 5);
}

public void expiration_test ()
{
    EventCache c = new EventCache ();
    c.max_size = 5;
    for (int i = 0; i < 5; i++)
    {
        Event e = new Event();
        e.id = i;
        c.cache_event (e);
    }

    // Refresh the LRU stamp for #0, so #30 expires #1
    c.get_event(0);
    Event e = new Event();
    e.id = 30;
    c.cache_event (e);

    assert(c.get_event(0) != null);
    assert(c.get_event(1) == null);
    assert(c.get_event(30) != null);
}

// vim:expandtab:ts=4:sw=4
