/* table-lookup.vala
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

namespace Zeitgeist.SQLite
{

    public class TableLookup : Object
    {

        unowned Sqlite.Database db;

        string table;
        private HashTable<int, string> id_to_value;
        private HashTable<string, int> value_to_id;

        public TableLookup (ZeitgeistDatabase database, string table_name)
        {
            db = database.database;
            table = table_name;
            id_to_value = new HashTable<int, string>(direct_hash, direct_equal);
            value_to_id = new HashTable<string, int>(str_hash, str_equal);
            
            int rc = db.exec ("SELECT id, value FROM " + table,
                (n_columns, values, column_names) =>
                {
                    id_to_value.insert (int.parse(values[0]), values[1]);
                    value_to_id.insert (values[1], int.parse(values[0]));
                    return 0;
                }, null);
            if (rc != Sqlite.OK)
            {
                critical ("Can't init tables: %d, %s\n", rc, db.errmsg ());
            }
            
            /* FIXME: add this:
            cursor.execute("""
                CREATE TEMP TRIGGER update_cache_%(table)s
                BEFORE DELETE ON %(table)s
                BEGIN
                    INSERT INTO _fix_cache VALUES ("%(table)s", OLD.id);
                END;
                """ % {"table": table})
            */
        }

        public int get_id (string name)
        {
            int id = value_to_id.lookup (name);
            print("pre --> %d\n", id);
            if (id == 0)
            {
                int rc;
                Sqlite.Statement stmt;
                
                string sql = "INSERT INTO " + table + " (value) VALUES (?)";
                if ((rc = db.prepare_v2 (sql, -1, out stmt)) != Sqlite.OK) {
                    critical ("SQL error: %d, %s\n", rc, db.errmsg ());
                }
                
                stmt.bind_text(1, name);
                if (stmt.step() != Sqlite.DONE) {
                    critical ("SQL error: %d, %s\n", rc, db.errmsg ());
                }
                
                id = (int) db.last_insert_rowid();
                
                id_to_value.insert (id, name);
                value_to_id.insert (name, id);
                print("ID --> %d\n", id);
            }
            return id;
        }

        public string get_value (int id)
        {
            // When we fetch an event, it either was already in the database
            // at the time Zeitgeist started or it was inserted later -using
            // Zeitgeist-, so here we always have the data in memory already.
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
