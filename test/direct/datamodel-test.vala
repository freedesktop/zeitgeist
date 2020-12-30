/* datamodel-test.vala
 *
 * Copyright © 2012 Canonical Ltd.
 *             By Siegfried-A. Gevatter <siegfried.gevatter@collabora.co.uk>
 *             By Seif Lotfy <seif@lotfy.com>
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

    Test.add_func ("/Datamodel/MatchesTemplate/anything", matches_template_anything_test);
    Test.add_func ("/Datamodel/MatchesTemplate/foreach", foreach_test);

    return Test.run ();
}

void matches_template_anything_test ()
{
    // Let's get a template with everything null
    var templ = new Event.full ();
    var event = new Event.full ("interp", "manif", "actor", "origin");

    // Test with zero subjects
    assert (templ.matches_template (templ));
    assert (event.matches_template (templ));

    var subject = new Subject.full ();
    event.add_subject (subject);

    // Test with one subject
    assert (event.matches_template (templ));

    var subject2 = new Subject.full ("uri", "interp", "manif", "mimetype",
        "origin", "text", "storage");
    event.add_subject (subject2);

    // Test with two subjects
    assert (event.matches_template (templ));

    // Let's ensure that empty strings are also working...
    templ.interpretation = "";
    assert (event.matches_template (templ));

    // As well as just a wildcard
    templ.actor = "*";
    assert (event.matches_template (templ));

    // FIXME: figure out how we want to treat multiple subjects in the template

    // Now check something that doesn't match
    templ.manifestation = "No thanks!";
    assert (!event.matches_template (templ));
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

void foreach_test ()
{
    GenericArray<Event> events = new GenericArray<Event> ();
    for (int i = 0; i < 1000; i++)
    {
        var e = create_event ();
        e.id = i;
        e.add_subject (create_subject ());
        events.add (e);
    }

    SimpleResultSet result_set = new SimpleResultSet (events);
    int i = 0;
    foreach (Event e in result_set)
    {
        assert_cmpint ((int) e.id, CompareOperator.EQ, i);
        i++;
    }

}

// vim:expandtab:ts=4:sw=4
