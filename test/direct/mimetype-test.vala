/* where-clause-test.vala
 *
 * Copyright © 2011-2012 Collabora Ltd.
 *             By Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
 * Copyright © 2010 Canonical, Ltd.
 *             By Mikkel Kamstrup Erlandsen <mikkel.kamstrup@canonical.com>
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

    Test.add_func ("/MimeType/basic", mime_type_basic_test);
    Test.add_func ("/MimeType/regex", mime_type_regex_test);
    Test.add_func ("/MimeType/none", mime_type_none_test);
    Test.add_func ("/MimeType/null", mime_type_null_test);
    Test.add_func ("/MimeType/register", mime_type_registration_test);

    Test.add_func ("/UriScheme/basic", uri_scheme_basic_test);
    Test.add_func ("/UriScheme/none", uri_scheme_none_test);
    Test.add_func ("/UriScheme/register", uri_scheme_registration_test);

    return Test.run ();
}

public void mime_type_basic_test ()
{
    assert_cmpstr (NFO.TEXT_DOCUMENT, CompareOperator.EQ,
        interpretation_for_mimetype ("text/plain"));
}

public void mime_type_regex_test ()
{
    // We should have a fallack for application/x-applix-*
    assert_cmpstr (NFO.DOCUMENT, CompareOperator.EQ,
        interpretation_for_mimetype ("application/x-applix-FOOBAR"));

    // Still application/x-applix-speadsheet should be a spreadsheet
    assert_cmpstr (NFO.SPREADSHEET, CompareOperator.EQ,
        interpretation_for_mimetype ("application/x-applix-spreadsheet"));
}

public void mime_type_none_test ()
{
    assert (interpretation_for_mimetype ("foo/bar") == null);
}

public void mime_type_null_test ()
{
    assert (interpretation_for_mimetype (null) == null);
}

public void mime_type_registration_test ()
{
    register_mimetype ("awesome/bird", "Bluebird");
    try
    {
        register_mimetype_regex ("everything/.*", "is nothing");
    } catch (RegexError e) {
        assert (false);
    }

    mime_type_basic_test ();
    mime_type_regex_test ();
    mime_type_none_test ();

    assert_cmpstr ("Bluebird", CompareOperator.EQ,
        interpretation_for_mimetype ("awesome/bird"));
    assert_cmpstr ("is nothing", CompareOperator.EQ,
        interpretation_for_mimetype ("everything/everywhere"));
}

public void uri_scheme_basic_test ()
{
    assert_cmpstr (NFO.FILE_DATA_OBJECT, CompareOperator.EQ,
        manifestation_for_uri ("file:///tmp/foo.txt"));
    assert_cmpstr (NFO.REMOTE_DATA_OBJECT, CompareOperator.EQ,
        manifestation_for_uri ("ftp://ftp.example.com"));
}

public void uri_scheme_none_test ()
{
    assert (manifestation_for_uri ("asdf://awesomehttp://") == null);
}

public void uri_scheme_registration_test ()
{
    register_uri_scheme ("42://", "the answer");

    uri_scheme_basic_test ();
    uri_scheme_none_test ();

    assert_cmpstr ("the answer", CompareOperator.EQ,
        manifestation_for_uri ("42://what is it?"));
}

// vim:expandtab:ts=4:sw=4
