/* datamodel-test.vala
 *
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
using Assertions;

int main (string[] argv)
{
    Test.init (ref argv);

    Test.add_func ("/Datasource/CreateEmpty", create_empty_test);
    Test.add_func ("/Datasource/CreateFull", create_full_test);
    Test.add_func ("/Datasource/ToFromVariant", to_from_variant_test);

    return Test.run ();
}

void create_empty_test ()
{
    var src = new DataSource ();
    assert_cmpstr (src.unique_id, CompareOperator.EQ, null);
    assert_cmpstr (src.name, CompareOperator.EQ, null);
    assert_cmpstr (src.description, CompareOperator.EQ, null);
    assert (src.event_templates == null);
    assert (src.running == false);
    assert (src.timestamp == 0);
    assert (src.enabled == true);
}

void create_full_test ()
{
    var src = new DataSource.full ("my-id", "my-name", "my-desc", null);

    assert_cmpstr (src.unique_id, CompareOperator.EQ, "my-id");
    assert_cmpstr (src.name, CompareOperator.EQ, "my-name");
    assert_cmpstr (src.description, CompareOperator.EQ, "my-desc");
    assert (src.event_templates == null);
    assert (src.running == false);
    assert (src.timestamp ==  0);
    assert (src.enabled == true);

    var now = Timestamp.from_now ();
    src.running = true;
    src.timestamp = now;
    src.enabled = false;
    assert (src.running == true);
    assert (src.timestamp == now);
    assert (src.enabled == false);

    var event_templates = new GenericArray<Event> ();
    event_templates.add (new Event ());
    src.event_templates = event_templates;
    assert (src.event_templates == event_templates);
}

void to_from_variant_test ()
{
    var orig = new DataSource.full ("my-id", "my-name", "my-desc", null);
    var now = Timestamp.from_now ();
    orig.timestamp = now;

    var event_templates = new GenericArray<Event> ();
    event_templates.add (new Event ());
    orig.event_templates = event_templates;

    var src = new DataSource.from_variant (orig.to_variant ());
    assert_cmpstr (src.unique_id, CompareOperator.EQ, "my-id");
    assert_cmpstr (src.name, CompareOperator.EQ, "my-name");
    assert_cmpstr (src.description, CompareOperator.EQ, "my-desc");
    assert (src.event_templates != null);
    assert (src.running == false);
    assert (src.timestamp == now);
    assert (src.enabled == true);

    event_templates = src.event_templates;
    assert_cmpint (event_templates.length, CompareOperator.EQ, 1);
    assert (event_templates.get (0) is Event);
}

// vim:expandtab:ts=4:sw=4
