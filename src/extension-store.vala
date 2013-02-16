/* extension-store.vala
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

namespace Zeitgeist
{
    public class ExtensionStore : Object
    {

        private Zeitgeist.SQLite.Database database;
        private unowned Sqlite.Database db;
        private Sqlite.Statement storage_stmt;
        private Sqlite.Statement retrieval_stmt;

        public ExtensionStore (Zeitgeist.Engine engine) {
            database = engine.database;
            db = database.database;
            try
            {
                prepare_queries ();
            }
            catch (Error err)
            {
                warning ("%s", err.message);
            }
        }

        private void prepare_queries () throws EngineError
        {
            int rc;
            string sql;

            // Prepare storage query
            sql = """
                INSERT OR REPLACE INTO extensions_conf (
                    extension, key, value
                ) VALUES (
                    ?, ?, ?
                )""";
            rc = database.database.prepare_v2 (sql, -1, out storage_stmt);
            database.assert_query_success (rc, "Storage query error");

            // Prepare retrieval query
            sql = """
                SELECT value
                FROM extensions_conf
                WHERE extension=? AND key=?
                """;
            rc = database.database.prepare_v2 (sql, -1, out retrieval_stmt);
            database.assert_query_success (rc, "Retrieval query error");
        }

        /**
         * Store the given Variant under the given (extension, key)
         * identifier, replacing any previous value.
         */
        public void store (string extension, string key, Variant data)
        {
            int rc;
            storage_stmt.reset ();
            storage_stmt.bind_text (1, extension);
            storage_stmt.bind_text (2, key);
            storage_stmt.bind_blob (3, data.get_data (), (int) data.get_size ());

            if ((rc = storage_stmt.step ()) != Sqlite.DONE)
            {
                try
                {
                    database.assert_not_corrupt (rc);
                }
                catch (EngineError err) { }
                warning ("SQL error: %d, %s", rc, db.errmsg ());
            }
        }

        /**
         * Retrieve a previously stored value.
         */
        public Variant? retrieve (string extension, string key, VariantType format)
        {
            retrieval_stmt.reset ();
            retrieval_stmt.bind_text (1, extension);
            retrieval_stmt.bind_text (2, key);

            int rc = retrieval_stmt.step ();
            if (rc != Sqlite.ROW)
            {
                if (rc != Sqlite.DONE)
                {
                    try
                    {
                        database.assert_not_corrupt (rc);
                    }
                    catch (EngineError err) { }
                    warning ("SQL error: %d, %s", rc, db.errmsg ());
                }
                return null;
            }

            unowned uchar[] blob;
            blob = (uchar[]) retrieval_stmt.column_blob (0);
            blob.length = retrieval_stmt.column_bytes (0);

            Variant? data = null;
            if (blob != null)
            {
                ByteArray byte_array = new ByteArray.sized (blob.length);
                byte_array.append (blob);

                data = Variant.new_from_data<ByteArray> (format,
                    byte_array.data, false, byte_array);
            }

            retrieval_stmt.reset ();
            return data;
        }

    }
}

// vim:expandtab:ts=4:sw=4
