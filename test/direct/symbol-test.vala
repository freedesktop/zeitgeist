/* symbol-test.vala
 *
 * Copyright © 2012 Christian Dywan <christian@twotoasts.de>
 *
 * Based upon a C implementation (© 2010 Canonical Ltd) by:
 *  Michal Hruby <michal.mhr@gmail.com>
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

    Test.add_func ("/Symbols/NullNull", null_null_test);
    Test.add_func ("/Symbols/NullFirst", null_first_test);
    Test.add_func ("/Symbols/NullSecond", null_second_test);
    Test.add_func ("/Symbols/NotUri", not_uri_test);
    Test.add_func ("/Symbols/NotUriEqual", not_uri_equal_test);
    Test.add_func ("/Symbols/UriEqual", uri_equal_test);
    Test.add_func ("/Symbols/ValidParent", vector_image_media_test);
    Test.add_func ("/Symbols/ValidChild", media_vector_image_test);
    Test.add_func ("/Symbols/Unrelated", media_software_test);
    Test.add_func ("/Symbols/GetChildren", media_children_test);
    Test.add_func ("/Symbols/GetAllChildren", media_all_children_test);
    Test.add_func ("/Symbols/GetParents", vector_image_parents_test);
    Test.add_func ("/Symbols/SymbolInfo", media_complex_test);

    return Test.run ();
}

void null_null_test ()
{
    // shouldn't crash: null, null will hit assertions
    assert (!Symbol.is_a ("", ""));
}

void null_first_test ()
{
    assert (!Symbol.is_a ("", NFO.MEDIA));
}

void null_second_test ()
{
    assert (!Symbol.is_a (NFO.MEDIA, ""));
}

void not_uri_test ()
{
    assert (!Symbol.is_a ("first", "second"));
}

void not_uri_equal_test ()
{
    assert (!Symbol.is_a ("something", "something"));
}

void uri_equal_test ()
{
    assert (Symbol.is_a (NFO.AUDIO, NFO.AUDIO));
}

void vector_image_media_test ()
{
    assert (Symbol.is_a (NFO.VECTOR_IMAGE, NFO.MEDIA));
}

void media_vector_image_test ()
{
    assert (!Symbol.is_a (NFO.MEDIA, NFO.VECTOR_IMAGE));
}

void media_software_test ()
{
    assert (!Symbol.is_a (NFO.MEDIA, NFO.SOFTWARE));
}

void is_uri_valid (string uri)
{
    string SEM_D_URI = "http://www.semanticdesktop.org/ontologies";
    assert (uri != null && uri.has_prefix (SEM_D_URI));
    // string str = "%s".printf ("%s", uri);
}

void media_children_test ()
{
    var children = Symbol.get_children (NFO.MEDIA);
    assert_cmpuint (children.length (), CompareOperator.GT, 0);
    foreach (string uri in children)
        is_uri_valid (uri);
}

void media_all_children_test ()
{
    var children = Symbol.get_all_children (NFO.MEDIA);
    assert_cmpuint (children.length (), CompareOperator.GT, 0);
    foreach (string uri in children)
        is_uri_valid (uri);
}

void vector_image_parents_test ()
{
    var parents = Symbol.get_all_parents (NFO.VECTOR_IMAGE);
    assert_cmpuint (parents.length (), CompareOperator.GT, 0);
    foreach (string uri in parents)
        is_uri_valid (uri);
}

void media_complex_test ()
{
    var children = Symbol.get_children (NFO.MEDIA);
    var all_ch = Symbol.get_all_children (NFO.MEDIA);

    assert_cmpuint (children.length (), CompareOperator.GT, 0);
    assert_cmpuint (all_ch.length (), CompareOperator.GT, children.length ());

    foreach (string uri in children)
    {
        // check that it's also in all children
        assert (all_ch.find_custom (uri, strcmp) != null);
    }
}

// vim:expandtab:ts=4:sw=4
