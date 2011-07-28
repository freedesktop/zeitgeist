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

        private HashTable<int, string> id_to_value;
        private HashTable<string, int> value_to_id;

        public TableLookup (ZeitgeistDatabase database, string table_name)
        {
            db = database.database;
            id_to_value = new HashTable<int, string>(direct_hash, direct_equal);
            value_to_id = new HashTable<string, int>(str_hash, str_equal);
            
            int rc = db.exec ("SELECT id, value FROM " + table_name,
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
            int? id = value_to_id.lookup (name);
            if (id == null)
            {
                // FIXME
                /*if name in self:
                    return super(TableLookup, self).__getitem__(name)
                try:
                    self._cursor.execute(
                    "INSERT INTO %s (value) VALUES (?)" % self._table, (name,))
                    id = self._cursor.lastrowid
                except sqlite3.IntegrityError:
                    # This shouldn't happen, but just in case
                    # FIXME: Maybe we should remove it?
                    id = self._cursor.execute("SELECT id FROM %s WHERE value=?"
                        % self._table, (name,)).fetchone()[0]
                # If we are here it's a newly inserted value, insert it into cache
                self[name] = id
                self._inv_dict[id] = name
                return id*/
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
