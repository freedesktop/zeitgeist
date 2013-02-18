/* event-test.vala
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
    Test.init (ref argv);

    Test.add_func ("/Event/CreateEmpty", create_empty_test);
    Test.add_func ("/Event/CreateFull", create_full_test);
    Test.add_func ("/Event/ActorFromAppInfo", actor_from_app_info_test);
    Test.add_func ("/Event/FromVariant", from_variant_test);
    Test.add_func ("/Event/FromVariantWithNewFields", from_variant_with_new_fields_test);
    Test.add_func ("/Event/EmptyToFromVariant", empty_to_from_variant_test);
    Test.add_func ("/Event/WithOneSubjectToFromVariant", with_one_subject_to_from_variant_test);
    Test.add_func ("/Event/3EventsToFromVariant", three_events_to_from_variant_test);
    Test.add_func ("/Event/0EventsToFromVariant", zero_events_to_from_variant_test);

    return Test.run ();
}

void create_empty_test ()
{
    var ev = new Event ();

    assert (ev.id == 0);
    assert (ev.timestamp == 0);
    assert_cmpstr (ev.interpretation, OperatorType.EQUAL, null);
    assert_cmpstr (ev.manifestation, OperatorType.EQUAL, null);
    assert_cmpstr (ev.actor, OperatorType.EQUAL, null);
    assert_cmpstr (ev.origin, OperatorType.EQUAL, null);
    assert_cmpint (ev.num_subjects (), OperatorType.EQUAL, 0);
    assert (ev.payload == null);
}

void create_full_test ()
{
    var ev = new Event.full (
        ZG.ACCESS_EVENT, ZG.USER_ACTIVITY, "application://firefox.desktop", null);
    ev.take_subject (new Subject.full ("http://example.com",
            NFO.WEBSITE, NFO.REMOTE_DATA_OBJECT,
            "text/html", "http://example.com", "example.com", "net"));
    ev.add_subject (new Subject ());

    assert (ev.id == 0);
    assert (ev.timestamp == 0);
    assert_cmpstr (ev.interpretation, OperatorType.EQUAL, ZG.ACCESS_EVENT);
    assert_cmpstr (ev.manifestation, OperatorType.EQUAL, ZG.USER_ACTIVITY);
    assert_cmpstr (ev.actor, OperatorType.EQUAL, "application://firefox.desktop");
    assert_cmpstr (ev.origin, OperatorType.EQUAL, null);
    assert_cmpint (ev.num_subjects (), OperatorType.EQUAL, 2);
    assert (ev.payload == null);

    var su = ev.subjects[1];
    assert_cmpstr (su.uri, OperatorType.EQUAL, null);
    assert_cmpstr (su.interpretation, OperatorType.EQUAL, null);
    assert_cmpstr (su.manifestation, OperatorType.EQUAL, null);
    assert_cmpstr (su.mimetype, OperatorType.EQUAL, null);
    assert_cmpstr (su.origin, OperatorType.EQUAL, null);
    assert_cmpstr (su.text, OperatorType.EQUAL, null);
    assert_cmpstr (su.storage, OperatorType.EQUAL, null);
    assert_cmpstr (su.current_uri, OperatorType.EQUAL, null);
}

void actor_from_app_info_test ()
{
    var appinfo = new DesktopAppInfo.from_filename (Zeitgeist.Tests.DIR + "/test.desktop");
    assert (appinfo is AppInfo);

    var ev = new Event ();
    ev.set_actor_from_app_info (appinfo);
    assert_cmpstr (ev.actor, OperatorType.EQUAL, "application://test.desktop");
}

void from_variant_test ()
{
    var b = new VariantBuilder (new VariantType ("(" + Utils.SIG_EVENT + ")"));

    // Build event data
    b.open (new VariantType ("as"));
    b.add ("s", "27");
    b.add ("s", "68");
    b.add ("s", ZG.ACCESS_EVENT);
    b.add ("s", ZG.USER_ACTIVITY);
    b.add ("s", "application://foo.desktop");
    b.close ();

    // Build subjects
    b.open (new VariantType ("aas"));
        b.open (new VariantType ("as"));
        b.add ("s", "file:///tmp/foo.txt");
        b.add ("s", NFO.DOCUMENT);
        b.add ("s", NFO.FILE_DATA_OBJECT);
        b.add ("s", "file://tmp");
        b.add ("s", "text/plain");
        b.add ("s", "foo.text");
        b.add ("s", "36e5604e-7e1b-4ebd-bb6a-184c6ea99627");
        b.close ();
    b.close ();

    // Build playload
    b.open (new VariantType ("ay"));
    b.add ("y", 1);
    b.add ("y", 2);
    b.add ("y", 3);
    b.close ();

    var @var = b.end ();
    Event ev;
    try
    {
        ev = new Event.from_variant (@var);
    }
    catch (Zeitgeist.DataModelError error)
    {
        GLib.error (error.message);
    }

    assert (ev.id == 27);
    assert (ev.timestamp == 68);
    assert_cmpstr (ev.interpretation, OperatorType.EQUAL, ZG.ACCESS_EVENT);
    assert_cmpstr (ev.manifestation, OperatorType.EQUAL, ZG.USER_ACTIVITY);
    assert_cmpstr (ev.actor, OperatorType.EQUAL, "application://foo.desktop");
    assert_cmpstr (ev.origin, OperatorType.EQUAL, null);
    assert_cmpint (ev.num_subjects (), OperatorType.EQUAL, 1);

    var su = ev.subjects[0];
    assert_cmpstr (su.uri, OperatorType.EQUAL, "file:///tmp/foo.txt");
    assert_cmpstr (su.interpretation, OperatorType.EQUAL, NFO.DOCUMENT);
    assert_cmpstr (su.manifestation, OperatorType.EQUAL, NFO.FILE_DATA_OBJECT);
    assert_cmpstr (su.mimetype, OperatorType.EQUAL, "text/plain");
    assert_cmpstr (su.origin, OperatorType.EQUAL, "file://tmp");
    assert_cmpstr (su.storage, OperatorType.EQUAL, "36e5604e-7e1b-4ebd-bb6a-184c6ea99627");

    var payload = ev.payload;
    assert (payload != null);
    assert_cmpuint (payload.len, OperatorType.EQUAL, 3);
    assert_cmpint (payload.data[0], OperatorType.EQUAL, 1);
    assert_cmpint (payload.data[1], OperatorType.EQUAL, 2);
    assert_cmpint (payload.data[2], OperatorType.EQUAL, 3);
}

void from_variant_with_new_fields_test ()
{
    var b = new VariantBuilder (new VariantType ("(" + Utils.SIG_EVENT + ")"));

    // Build event data
    b.open (new VariantType ("as"));
    b.add ("s", "27");
    b.add ("s", "68");
    b.add ("s", ZG.ACCESS_EVENT);
    b.add ("s", ZG.USER_ACTIVITY);
    b.add ("s", "application://foo.desktop");
    b.add ("s", "origin");
    b.close ();

    // Build subjects
    b.open (new VariantType ("aas"));
        b.open (new VariantType ("as"));
        b.add ("s", "file:///tmp/foo.txt");
        b.add ("s", NFO.DOCUMENT);
        b.add ("s", NFO.FILE_DATA_OBJECT);
        b.add ("s", "file:///tmp");
        b.add ("s", "text/plain");
        b.add ("s", "foo.text");
        b.add ("s", "36e5604e-7e1b-4ebd-bb6a-184c6ea99627");
        b.add ("s", "file:///tmp/current.txt");
        b.add ("s", "file:///tmp1");
        b.close ();
    b.close ();

    // Build playload
    b.open (new VariantType ("ay"));
    b.add ("y", 1);
    b.add ("y", 2);
    b.add ("y", 3);
    b.close ();

    var @var = b.end ();
    Event ev;
    try
    {
        ev = new Event.from_variant (@var);
    }
    catch (Zeitgeist.DataModelError error)
    {
        GLib.error (error.message);
    }

    assert (ev.id == 27);
    assert (ev.timestamp == 68);
    assert_cmpstr (ev.interpretation, OperatorType.EQUAL, ZG.ACCESS_EVENT);
    assert_cmpstr (ev.manifestation, OperatorType.EQUAL, ZG.USER_ACTIVITY);
    assert_cmpstr (ev.actor, OperatorType.EQUAL, "application://foo.desktop");
    assert_cmpstr (ev.origin, OperatorType.EQUAL, "origin");
    assert_cmpint (ev.num_subjects (), OperatorType.EQUAL, 1);

    var su = ev.subjects[0];
    assert_cmpstr (su.uri, OperatorType.EQUAL, "file:///tmp/foo.txt");
    assert_cmpstr (su.interpretation, OperatorType.EQUAL, NFO.DOCUMENT);
    assert_cmpstr (su.manifestation, OperatorType.EQUAL, NFO.FILE_DATA_OBJECT);
    assert_cmpstr (su.mimetype, OperatorType.EQUAL, "text/plain");
    assert_cmpstr (su.origin, OperatorType.EQUAL, "file:///tmp");
    assert_cmpstr (su.text, OperatorType.EQUAL, "foo.text");
    assert_cmpstr (su.storage, OperatorType.EQUAL, "36e5604e-7e1b-4ebd-bb6a-184c6ea99627");
    assert_cmpstr (su.current_uri, OperatorType.EQUAL, "file:///tmp/current.txt");
    assert_cmpstr (su.current_origin, OperatorType.EQUAL, "file:///tmp1");

    var payload = ev.payload;
    assert (payload != null);
    assert_cmpuint (payload.len, OperatorType.EQUAL, 3);
    assert_cmpint (payload.data[0], OperatorType.EQUAL, 1);
    assert_cmpint (payload.data[1], OperatorType.EQUAL, 2);
    assert_cmpint (payload.data[2], OperatorType.EQUAL, 3);

}

void empty_to_from_variant_test ()
{
    var orig = new Event ();
    orig.timestamp = Timestamp.from_now();
    Event marshalled;
    try
    {
        marshalled = new Event.from_variant (orig.to_variant ());
    }
    catch (Zeitgeist.DataModelError error)
    {
        GLib.error (error.message);
    }

    assert (marshalled.id == 0);
    assert (marshalled.timestamp == orig.timestamp);
    assert_cmpstr (marshalled.interpretation, OperatorType.EQUAL, null);
    assert_cmpstr (marshalled.manifestation, OperatorType.EQUAL, null);
    assert_cmpstr (marshalled.actor, OperatorType.EQUAL, null);
    assert_cmpstr (marshalled.origin, OperatorType.EQUAL, null);
    assert_cmpint (marshalled.num_subjects (), OperatorType.EQUAL, 0);
    assert (marshalled.payload == null);
}

void with_one_subject_to_from_variant_test ()
{
    var orig = new Event.full (
        ZG.ACCESS_EVENT, ZG.USER_ACTIVITY,
        "application://firefox.desktop", "origin");
    orig.take_subject (new Subject.full ("http://example.com",
        NFO.WEBSITE, NFO.REMOTE_DATA_OBJECT,
        "text/html", "http://example.com", "example.com", "net"));
    orig.subjects[0].current_uri = "http://current-example.com";

    var payload = new ByteArray ();
    uint8[] byte = { 255 };
    payload.append (byte);
    orig.payload = payload;

    var marshalled = new Event.from_variant (orig.to_variant ());

    assert (marshalled.id == 0);
    assert_cmpstr (marshalled.interpretation, OperatorType.EQUAL, ZG.ACCESS_EVENT);
    assert_cmpstr (marshalled.manifestation, OperatorType.EQUAL, ZG.USER_ACTIVITY);
    assert_cmpstr (marshalled.actor, OperatorType.EQUAL, "application://firefox.desktop");
    assert_cmpstr (marshalled.origin, OperatorType.EQUAL, "origin");
    assert_cmpint (marshalled.num_subjects (), OperatorType.EQUAL, 1);

    payload = marshalled.payload;
    assert (payload != null);
    assert (payload.len == 1);
    assert (payload.data[0] == 255);

    var su = marshalled.subjects[0];
    assert_cmpstr (su.uri, OperatorType.EQUAL, "http://example.com");
    assert_cmpstr (su.interpretation, OperatorType.EQUAL, NFO.WEBSITE);
    assert_cmpstr (su.manifestation, OperatorType.EQUAL, NFO.REMOTE_DATA_OBJECT);
    assert_cmpstr (su.mimetype, OperatorType.EQUAL, "text/html");
    assert_cmpstr (su.origin, OperatorType.EQUAL, "http://example.com");
    assert_cmpstr (su.text, OperatorType.EQUAL, "example.com");
    assert_cmpstr (su.storage, OperatorType.EQUAL, "net");
    assert_cmpstr (su.current_uri, OperatorType.EQUAL, "http://current-example.com");
}

void three_events_to_from_variant_test ()
{
    var events = new GenericArray<Event?> ();
    events.add (new Event ());
    events.add (new Event ());
    events.add (new Event ());

    var vevents = Events.to_variant (events);
    assert (vevents.n_children () == 3);

    events = Events.from_variant (vevents);
    assert (events.length == 3);
    assert (events.get (0) is Event);
    assert (events.get (1) is Event);
    assert (events.get (2) is Event);

}

void zero_events_to_from_variant_test ()
{
    var events = new GenericArray<Event?> ();
    var vevents = Events.to_variant (events);
    assert (vevents.n_children () == 0);
    events = Events.from_variant (vevents);
    assert_cmpint (events.length, OperatorType.EQUAL, 0);
}

// vim:expandtab:ts=4:sw=4
