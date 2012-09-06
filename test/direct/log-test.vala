/* log-test.vala
 *
 * Copyright © 2012 Christian Dywan <christian@twotoasts.de>
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

using Zeitgeist;
using Assertions;

int main (string[] argv)
{
    Environment.set_variable ("XDG_DATA_DIRS", test_dir (), true);
    Test.init (ref argv);

    Test.add_func ("/Log/InsertGetDelete", insert_get_delete_test);
    Test.add_func ("/Log/GetDefault", get_default_test);

    return Test.run ();
}

void events_received (Zeitgeist.Log log, AsyncResult res)
{
    ResultSet events;
    try {
        events = log.get_events.finish (res);
    }
    catch (Error error) {
        critical ("Failed to get events: %s", error.message);
        return;
    }
    /* Assert that we got what we expected, and collect the event ids,
     * so we can delete the events */
    assert (expected_events.length == events.size);
    assert (expected_events.length == events.estimated_matches);
    // TODO
 
}

void events_inserted (Zeitgeist.Log log, AsyncResult res)
{
    uint32[] event_ids;
    try {
        event_ids = log.insert_events_from_ptrarray.finish (res);
    }
    catch (Error error) {
        critical ("Failed to insert events: %s", error.message);
        return;
    }
    assert (expected_events.length == event_ids.length);
    log.get_events.begin (event_ids, null, events_received);
}

bool quit_main_loop ()
{
    new MainLoop (MainContext.default ()).quit ();
    return false;
}

void insert_get_delete_test ()
{
    var expected_events = new GenericArray<Event> ();
    var ev = new Event ();
    var su = new Subject ();
    ev.add_subject (su);
    expected_events.add (ev);
    ev.interpretation = "foo://Interp";
    ev.manifestation = "foo://Manif";
    ev.actor = "app://firefox.desktop";

    su.uri = "file:///tmp/bar.txt";
    su.interpretation = "foo://TextDoc";
    su.manifestation = "foo://File";
    su.mimetype = "text/plain";
    su.origin = "file:///tmp";
    su.text = "bar.txt";
    su.storage = "bfb486f6-f5f8-4296-8871-0cc749cf8ef7";

    /* This method call now owns all events, subjects, and the events array */
    Zeitgeist.Log.get_default ().insert_events_from_ptrarray.begin (
        expected_events, null, events_inserted);
    assert (expected_events.length == 1);

    Timeout.add_seconds (1, quit_main_loop);
    new MainLoop (MainContext.default ()).run ();
}

void get_default_test ()
{
    var log1 = Zeitgeist.Log.get_default ();
    var log2 = Zeitgeist.Log.get_default ();
    assert (log1 == log2);
}

// vim:expandtab:ts=4:sw=4
