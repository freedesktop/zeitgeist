/* query-operators-test.vala
 *
 * Copyright © 2011 Collabora Ltd.
 *             By Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
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

void main (string[] args)
{

    Test.init (ref args);

    // Do not abort on warning()s.
    Log.set_always_fatal (LogLevelFlags.LEVEL_CRITICAL);

    Test.add_func ("/ParseNegation/main", parse_negation_test);
    Test.add_func ("/ParseWildcard/main", parse_wildcard_test);

    Test.run ();
}

private class PublicEngine : Engine
{
    public bool PUBLIC_parse_negation (string field, ref string val)
        throws EngineError
    {
        return parse_negation(field, ref val);
    }

    public bool PUBLIC_parse_wildcard (string field, ref string val)
        throws EngineError
    {
        return parse_wildcard(field, ref val);
    }
}

public void parse_negation_test ()
{
    PublicEngine engine = new PublicEngine();
    string val;

    // Test string without a negation
    val = "no negation";
    assert (engine.PUBLIC_parse_negation ("mimetype", ref val) == false);
    assert (val == "no negation");

    // Test "text" field string with negation character (should be ignored)
    val = "!something";
    assert (engine.PUBLIC_parse_negation ("text", ref val) == false);
    assert (val == "!something");

    // Test string with a valid negation
    val = "!negation";
    assert (engine.PUBLIC_parse_negation ("mimetype", ref val) == true);
    assert (val == "negation");

    // Test wildcard in string that doesn't support it
    val = "!negation";
    try
    {
        engine.PUBLIC_parse_negation ("unsupported", ref val);
        assert_not_reached();
    }
    catch (EngineError.INVALID_ARGUMENT e)
    {
    }

    // Test wildcard character in meaningless position in string that
    // doesn't support wildcards
    val = "some ! chars";
    assert (engine.PUBLIC_parse_negation ("unsupported", ref val) == false);
    assert (val == "some ! chars");
}

public void parse_wildcard_test ()
{
    PublicEngine engine = new PublicEngine();
    string val;

    // Test string without a wildcard
    val = "no wildcard";
    assert (engine.PUBLIC_parse_wildcard ("mimetype", ref val) == false);
    assert (val == "no wildcard");

    // Test "text" field string with wildcard character (should be ignored)
    val = "something*";
    assert (engine.PUBLIC_parse_wildcard ("text", ref val) == false);
    assert (val == "something*");

    // Test string with a valid wildcard
    val = "yes wildcar*";
    assert (engine.PUBLIC_parse_wildcard ("mimetype", ref val) == true);
    assert (val == "yes wildcar");

    // Test wildcard in string that doesn't support it
    val = "another wildcard *";
    try
    {
        engine.PUBLIC_parse_wildcard ("unsupported", ref val);
        assert_not_reached();
    }
    catch (EngineError.INVALID_ARGUMENT e)
    {
    }

    // Test wildcard character in meaningless position in string that
    // doesn't support wildcards
    val = "some * chars";
    assert (engine.PUBLIC_parse_wildcard ("unsupported", ref val) == false);
    assert (val == "some * chars");
}
