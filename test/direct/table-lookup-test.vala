/* where-clause-test.vala
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

using Zeitgeist;
using Zeitgeist.SQLite;
using Assertions;

int main (string[] args)
{
    Test.init (ref args);

    // Do not abort on warning()s.
    GLib.Log.set_always_fatal (LogLevelFlags.LEVEL_CRITICAL);

    // This test will use the database, make sure it won't mess up
    // the system.
    assert (Environment.set_variable(
        "ZEITGEIST_DATA_PATH", "/tmp/zeitgeist-tests", true));
    assert (Environment.set_variable(
        "ZEITGEIST_DATABASE_PATH", ":memory:", true));

    Test.add_func ("/WhereClause/basic", basic_test);
    Test.add_func ("/WhereClause/delete_hook", engine_test);
    Test.add_func ("/WhereClause/get_value_query", get_value_with_query_test);

    return Test.run ();
}

private class PublicEngine : Zeitgeist.Engine
{
    public TableLookup get_actors_table_lookup ()
    {
        return actors_table;
    }
}

public void basic_test ()
{
    Database database = new Zeitgeist.SQLite.Database ();
    unowned Sqlite.Database db = database.database;
    TableLookup table_lookup = new TableLookup (database, "actor");

    int id = table_lookup.id_for_string ("1st-actor");
    assert_cmpint (table_lookup.id_for_string ("2nd-actor"), CompareOperator.EQ, id+1);
    assert_cmpint (table_lookup.id_for_string ("1st-actor"), CompareOperator.EQ, id);

    int rc = db.exec ("DELETE FROM actor WHERE value='1st-actor'");
    assert (rc == Sqlite.OK);

    table_lookup.remove (1);
    assert_cmpint (table_lookup.id_for_string ("2nd-actor"), CompareOperator.EQ, id+1);
    assert_cmpint (table_lookup.id_for_string ("1st-actor"), CompareOperator.EQ, id+2);
}

public void get_value_with_query_test ()
{
    Database database = new Zeitgeist.SQLite.Database ();
    unowned Sqlite.Database db = database.database;
    TableLookup table_lookup = new TableLookup (database, "actor");

    int rc = db.exec ("INSERT INTO actor (id, value) VALUES (100, 'new-actor')");
    assert (rc == Sqlite.OK);

    assert_cmpstr (table_lookup.get_value (100), CompareOperator.EQ, "new-actor");
}

public void engine_test ()
{
    PublicEngine engine = new PublicEngine ();
    Database database = engine.database;
    unowned Sqlite.Database db = database.database;
    TableLookup table_lookup = engine.get_actors_table_lookup();

    assert_cmpint (table_lookup.id_for_string ("something"), CompareOperator.EQ, 1);

    // Since we're running with Engine, this should trigger the deletion
    // callback, which in turn should fix the cache (LP: #598666).
    int rc = db.exec ("DELETE FROM actor WHERE value='something'");
    assert (rc == Sqlite.OK);

    assert_cmpint (table_lookup.id_for_string ("something"), CompareOperator.EQ, 2);
}

// vim:expandtab:ts=4:sw=4
