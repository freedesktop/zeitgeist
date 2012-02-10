/* table-lookup.vala
 *
 * Copyright © 2011 Collabora Ltd.
 *             By Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
 *
 * Based upon a Python implementation (2009-2011) by:
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

namespace Zeitgeist.SQLite
{

    public class TableLookup : Object
    {

        unowned Sqlite.Database db;

        private string table;
        private HashTable<int, string> id_to_value;
        private HashTable<string, int> value_to_id;
        private Sqlite.Statement insertion_stmt;

        public TableLookup (Database database, string table_name)
        {
            db = database.database;
            table = table_name;
            id_to_value = new HashTable<int, string>(direct_hash, direct_equal);
            value_to_id = new HashTable<string, int>(str_hash, str_equal);

            int rc;

            rc = db.exec ("SELECT id, value FROM " + table,
                (n_columns, values, column_names) =>
                {
                    id_to_value.insert (int.parse(values[0]), values[1]);
                    value_to_id.insert (values[1], int.parse(values[0]));
                    return 0;
                }, null);
            if (rc != Sqlite.OK)
            {
                critical ("Can't init %s table: %d, %s\n", table,
                    rc, db.errmsg ());
            }

            string sql = "INSERT INTO " + table + " (value) VALUES (?)";
            rc = db.prepare_v2 (sql, -1, out insertion_stmt);
            if (rc != Sqlite.OK)
            {
                critical ("SQL error: %d, %s\n", rc, db.errmsg ());
            }
        }

        public int get_id (string name)
        {
            int id = value_to_id.lookup (name);
            if (id == 0)
            {
                int rc;
                insertion_stmt.reset ();
                insertion_stmt.bind_text (1, name);
                if ((rc = insertion_stmt.step ()) != Sqlite.DONE)
                {
                    critical ("SQL error: %d, %s\n", rc, db.errmsg ());
                }

                id = (int) db.last_insert_rowid ();

                id_to_value.insert (id, name);
                value_to_id.insert (name, id);
            }
            return id;
        }

        public unowned string get_value (int id)
        {
            // When we fetch an event, it either was already in the database
            // at the time Zeitgeist started or it was inserted later -using
            // Zeitgeist-, so here we always have the data in memory already.
            unowned string val = id_to_value.lookup (id);
            if (val != null) return val;

            // The above statement isn't exactly true. If this is a standalone
            // reader in a separate process, the values won't be kept updated
            // so we need to query the DB if we don't find it.
            int rc;

            rc = db.exec ("SELECT value FROM %s WHERE id=%d".printf (table, id),
                (n_columns, values, column_names) =>
                {
                    id_to_value.insert (id, values[0]);
                    value_to_id.insert (values[0], id);
                    return 0;
                }, null);
            if (rc != Sqlite.OK)
            {
                critical ("Can't get data from table %s: %d, %s\n", table,
                    rc, db.errmsg ());
            }
            return id_to_value.lookup (id);
        }

        public void remove (int id)
        {
            string name = id_to_value.lookup (id);
            id_to_value.remove (id);
            value_to_id.remove (name);
        }

    }

}

// vim:expandtab:ts=4:sw=4
