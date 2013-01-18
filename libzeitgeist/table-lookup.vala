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
        unowned Zeitgeist.SQLite.Database database;
        unowned Sqlite.Database db;

        private string table;
        private HashTable<int, string> id_to_value;
        private HashTable<string, int> value_to_id;
        private Sqlite.Statement insertion_stmt;
        private Sqlite.Statement retrieval_stmt;

        public TableLookup (Database database, string table_name)
            throws EngineError
        {
            this.database = database;
            db = database.database;
            table = table_name;
            id_to_value = new HashTable<int, string>(direct_hash, direct_equal);
            value_to_id = new HashTable<string, int>(str_hash, str_equal);

            int rc;
            string sql;

            rc = db.exec ("SELECT id, value FROM " + table,
                (n_columns, values, column_names) =>
                {
                    id_to_value.insert (int.parse(values[0]), values[1]);
                    value_to_id.insert (values[1], int.parse(values[0]));
                    return 0;
                }, null);
            database.assert_query_success (rc,
                "Can't init %s table".printf (table));

            sql = "INSERT INTO " + table + " (value) VALUES (?)";
            rc = db.prepare_v2 (sql, -1, out insertion_stmt);
            database.assert_query_success (rc, "Error creating insertion_stmt");

            sql = "SELECT value FROM " + table + " WHERE id=?";
            rc = db.prepare_v2 (sql, -1, out retrieval_stmt);
            database.assert_query_success (rc, "Error creating retrieval_stmt");
        }

        /**
         * Searches the table for the given ID, returns -1 if not found.
         *
         * @see id_for_string
         */
        public int id_try_string (string name)
        {
            int id = value_to_id.lookup (name);
            if (id == 0)
                return -1;
            return id;
        }

        /**
         * Searches the table for the given ID, inserts a new one if not found.
         *
         * @see id_try_string
         *
         */
        public int id_for_string (string name) throws EngineError
        {
            int id = value_to_id.lookup (name);
            if (id == 0)
            {
                int rc;
                insertion_stmt.reset ();
                insertion_stmt.bind_text (1, name);
                rc = insertion_stmt.step ();
                database.assert_query_success (rc, "Error in id_for_string",
                    Sqlite.DONE);

                id = (int) db.last_insert_rowid ();

                id_to_value.insert (id, name);
                value_to_id.insert (name, id);
            }
            return id;
        }

        public unowned string? get_value (int id) throws EngineError
        {
            // When we fetch an event, it either was already in the database
            // at the time Zeitgeist started or it was inserted later -using
            // Zeitgeist-, so here we always have the data in memory already.
            if (id == 0)
                return null;
            unowned string val = id_to_value.lookup (id);
            if (val != null) return val;

            // Unless this is a standalone reader in a separate process, in
            // which case the values won't be kept updated, so we need to
            // query the DB if we don't find it.
            int rc;
            string? text = null;

            retrieval_stmt.reset ();
            retrieval_stmt.bind_int64 (1, id);
            if ((rc = retrieval_stmt.step()) == Sqlite.ROW)
            {
                text = retrieval_stmt.column_text (0);
                id_to_value.insert (id, text);
                value_to_id.insert (text, id);
                rc = retrieval_stmt.step ();
            }
            database.assert_query_success (rc, "Error in get_value",
                Sqlite.DONE);
            if (text == null)
            {
                critical ("Error getting data from table: %d, %s\n",
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
