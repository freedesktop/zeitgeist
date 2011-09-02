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
    Test.add_func ("/ParseNegation/assert", assert_no_negation_test);
    Test.add_func ("/ParseWildcard/main", parse_wildcard_test);
	Test.add_func ("/ParseWildlcard/assert", assert_no_wildcard_test);

    Test.run ();
}

private class PublicEngine : Zeitgeist.Engine
{
    public bool PUBLIC_parse_negation (ref string val)
    {
        return parse_negation (ref val);
    }

	public void PUBLIC_assert_no_negation (string field, string val)
		throws Zeitgeist.EngineError
	{
		assert_no_negation (field, val);
	}

    public bool PUBLIC_parse_wildcard (ref string val)
    {
        return parse_wildcard (ref val);
    }

	public void PUBLIC_assert_no_wildcard (string field, string val)
		throws Zeitgeist.EngineError
	{
		assert_no_wildcard (field, val);
	}

}

public void parse_negation_test ()
{
    PublicEngine engine = new PublicEngine ();
    string val;

    // Test string without a negation
    val = "no negation";
    assert (engine.PUBLIC_parse_negation (ref val) == false);
    assert (val == "no negation");

    // Test string with a valid negation
    val = "!negation";
    assert (engine.PUBLIC_parse_negation (ref val) == true);
    assert (val == "negation");

    // Test negation character in a meaningless position
    val = "some ! chars";
    assert (engine.PUBLIC_parse_negation (ref val) == false);
    assert (val == "some ! chars");
}

public void assert_no_negation_test ()
{
	PublicEngine engine = new PublicEngine ();

	engine.PUBLIC_assert_no_negation ("field name", "good");
	engine.PUBLIC_assert_no_negation ("field name", "good!");
	engine.PUBLIC_assert_no_negation ("field name", "go!od");

	try
	{
		engine.PUBLIC_assert_no_negation ("field name", "!bad");
		assert_not_reached ();
	}
	catch (Zeitgeist.EngineError.INVALID_ARGUMENT e)
	{
	}
}

public void parse_wildcard_test ()
{
    PublicEngine engine = new PublicEngine ();
    string val;

    // Test string without a wildcard
    val = "no wildcard";
    assert (engine.PUBLIC_parse_wildcard (ref val) == false);
    assert (val == "no wildcard");

    // Test string with a valid wildcard
    val = "yes wildcar*";
    assert (engine.PUBLIC_parse_wildcard (ref val) == true);
    assert (val == "yes wildcar");

    // Test wildcard character in a meaningless position
    val = "some * chars";
    assert (engine.PUBLIC_parse_wildcard ( ref val) == false);
    assert (val == "some * chars");
}


public void assert_no_wildcard_test ()
{
	PublicEngine engine = new PublicEngine ();

	engine.PUBLIC_assert_no_wildcard ("field name", "good");
	engine.PUBLIC_assert_no_wildcard ("field name", "*good");
	engine.PUBLIC_assert_no_wildcard ("field name", "go*od");

	try
	{
		engine.PUBLIC_assert_no_wildcard ("field name", "bad*");
		assert_not_reached ();
	}
	catch (Zeitgeist.EngineError.INVALID_ARGUMENT e)
	{
	}
}
