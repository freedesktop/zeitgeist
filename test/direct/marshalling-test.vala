/* marshalling-test.vala
 *
 * Copyright © 2011 Michal Hruby <michal.mhr@gmail.com>
 * Copyright © 2011 Canonical Ltd.
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
using Assertions;

int main (string[] argv)
{
    Test.init (ref argv);

    Test.add_func ("/Marshalling/subjects", subject_test);
    Test.add_func ("/Marshalling/event", event_test);
    Test.add_func ("/Marshalling/events", events_test);
    Test.add_func ("/Marshalling/timerange", timerange_test);
    Test.add_func ("/Marshalling/corrupt_events", corrupt_events_test);
    Test.add_func ("/Marshalling/corrupt_subjects", corrupt_subjects_test);
    Test.add_func ("/Marshalling/corrupt_timerange", corrupt_timerange_test);

    return Test.run ();
}

Subject create_subject ()
{
    var s = new Subject ();
    s.uri = "scheme:///uri";
    s.interpretation = "subject_interpretation_uri";
    s.manifestation = "subject_manifestation_uri";
    s.mimetype = "text/plain";
    s.origin = "scheme:///";
    s.text = "Human readable text";
    s.storage = "";
    s.current_uri = "scheme:///uri";

    return s;
}

Event create_event ()
{
    var e = new Event ();
    e.id = 1234;
    e.timestamp = 1234567890L;
    e.interpretation = "interpretation_uri";
    e.manifestation = "manifestation_uri";
    e.actor = "test.desktop";
    e.origin = "source";

    return e;
}

void subject_test ()
{
    for (int i = 0; i < 1000; i++)
    {
        Variant vsubject = create_subject ().to_variant ();
        var subject = new Subject.from_variant (vsubject);
        warn_if_fail (subject != null);
    }
}

void event_test ()
{
    for (int i = 0; i < 1000; i++)
    {
        Variant vevent = create_event ().to_variant ();
        var event = new Event.from_variant (vevent);
        warn_if_fail (event != null);
    }
}

void events_test ()
{
    GenericArray<Event> events = new GenericArray<Event> ();
    for (int i = 0; i < 1000; i++)
    {
        var e = create_event ();
        e.add_subject (create_subject ());
        events.add (e);
    }

    Variant vevents = Events.to_variant (events);

    var demarshalled = Events.from_variant (vevents);
    assert_cmpint (demarshalled.length, CompareOperator.EQ, 1000);
}

void timerange_test ()
{
    for (int64 i = 0; i < 1000; i++)
    {
        Variant v = new Variant("(xx)", i, i+42);
        TimeRange timerange = new TimeRange.from_variant (v);
        assert_cmpint ((int) timerange.start, CompareOperator.EQ, (int)i);
        assert_cmpint ((int) timerange.end, CompareOperator.EQ, (int)i+42);
    }
}

void corrupt_events_test ()
{
    // Let's just try to parse some crap and see that it does not crash :)
    Variant v = new Variant ("(s)", "Zeitgeist is so awesome");
    bool error_thrown = false;
    try
    {
        new Event.from_variant (v);
    }
    catch (DataModelError.INVALID_SIGNATURE err) {
        error_thrown = true;
    }
    assert (error_thrown);
}

void corrupt_subjects_test ()
{
    Variant v;
    string[] arr;
    bool error_thrown;

    // Parse a valid subject variant
    arr = { "uri", "interpretation", "manifestation", "origin",
        "mimetype", "text", "storage", "current_uri" };
    v = new Variant.strv (arr);
    new Subject.from_variant (v);

    // Another valid variant, but this time without current_uri
    arr = { "uri", "interpretation", "manifestation", "origin",
        "mimetype", "text", "storage" };
    v = new Variant.strv (arr);
    new Subject.from_variant (v);

    // And this one is not valid :(
    arr = { "uri", "interpretation", "manifestation", "origin",
        "mimetype", "text" };
    v = new Variant.strv (arr);
    error_thrown = false;
    try
    {
        new Subject.from_variant (v);
    }
    catch (DataModelError err)
    {
        assert (err is DataModelError.INVALID_SIGNATURE);
        error_thrown = true;
    }
    assert (error_thrown);

    // Those one is just insane :)
    v = new Variant ("(x)", 42);
    error_thrown = false;
    try
    {
        new Subject.from_variant (v);
    }
    catch (DataModelError.INVALID_SIGNATURE err)
    {
        error_thrown = true;
    }
    assert (error_thrown);
}

void corrupt_timerange_test ()
{
    Variant v = new Variant ("(s)", "oh noes, what is this?");
    bool error_thrown = false;
    try
    {
        new TimeRange.from_variant (v);
    }
    catch (DataModelError.INVALID_SIGNATURE err)
    {
        error_thrown = true;
    }
}

// vim:expandtab:ts=4:sw=4
