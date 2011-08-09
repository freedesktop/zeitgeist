/* where-clause-test.vala
 *
 * Copyright © 2011 Collabora Ltd.
 *             By Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
 *
 * Based upon a Python implementation (2009-2011) by:
 *  Markus Korn <thekorn@gmx.net>
 *  Mikkel Kamstrup Erlandsen <mikkel.kamstrup@gmail.com>
 *  Seif Lotfy <seif@lotfy.com>
 *  Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
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

    Test.add_func ("/WhereClause/basic", basic_test);

    Test.run ();
}

public void basic_test ()
{
    Zeitgeist.WhereClause wc;

    wc = new Zeitgeist.WhereClause (Zeitgeist.WhereClause.Type.AND);
    wc.add ("1st condition");
    wc.add ("2nd condition");
    assert (wc.get_sql_conditions () == "(1st condition AND 2nd condition)");

    wc = new Zeitgeist.WhereClause (Zeitgeist.WhereClause.Type.OR);
    wc.add ("1st condition");
    wc.add ("2nd condition");
    assert (wc.get_sql_conditions () == "(1st condition OR 2nd condition)");

    wc = new Zeitgeist.WhereClause (Zeitgeist.WhereClause.Type.AND, true);
    wc.add ("some condition");
    assert (wc.get_sql_conditions () == "NOT (some condition)");
}
