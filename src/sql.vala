/* sql.vala
 *
 * Copyright © 2011 Collabora Ltd.
 *             By Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
 * Copyright © 2011 Manish Sinha <manishsinha@ubuntu.com>
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

namespace Zeitgeist.SQLite
{

    public enum EventViewRows
    {
        ID,
        TIMESTAMP,
        INTERPRETATION,
        MANIFESTATION,
        ACTOR,
        PAYLOAD,
        SUBJECT_URI,
        SUBJECT_ID,
        SUBJECT_INTERPRETATION,
        SUBJECT_MANIFESTATION,
        SUBJECT_ORIGIN,
        SUBJECT_ORIGIN_URI,
        SUBJECT_MIMETYPE,
        SUBJECT_TEXT,
        SUBJECT_STORAGE,
        SUBJECT_STORAGE_STATE,
        ORIGIN,
        EVENT_ORIGIN_URI,
        SUBJECT_CURRENT_URI,
        SUBJECT_ID_CURRENT
    }

    public class ZeitgeistDatabase : Object
    {

        public Sqlite.Statement event_insertion_stmt;
        public Sqlite.Statement id_retrieval_stmt;

        // FIXME: Should this be accessible from engine.vala or not?
        //  Probably it should, since otherwise there won't be much
        //  functionallity left for engine.vala.
        public Sqlite.Database database;

        public ZeitgeistDatabase () throws EngineError
        {
            int rc = Sqlite.Database.open_v2(
                Constants.DATABASE_FILE_PATH,
                out database);
            assert_query_success(rc, "Can't open database");

            DatabaseSchema.ensure_schema(database);

            prepare_queries ();
        }

        public uint32 get_last_id () throws EngineError
        {
            int last_id = -1;
            int rc = database.exec ("SELECT MAX(id) FROM event",
                (n_columns, values, column_names) =>
                {
                    if (values[0] == null)
                        last_id = 0;
                    else
                        last_id = int.parse(values[0]);
                    return 0;
                }, null);
            assert_query_success(rc, "Can't query database");
            assert (last_id != -1);
            return last_id;
        }

        public void insert_or_ignore_into_table (string table_name,
            GenericArray<string> values) throws EngineError
        {
            int rc;

            assert (values.length > 0);
            var sql = new StringBuilder ();
            sql.append ("INSERT OR IGNORE INTO ");
            sql.append (table_name);
            sql.append (" (value) SELECT ?");
            for (int i = 1; i < values.length; ++i)
                sql.append (" UNION SELECT ?");

            Sqlite.Statement stmt;
            rc = database.prepare_v2 (sql.str, -1, out stmt);
            assert_query_success (rc, "SQL error");

            for (int i = 0; i < values.length; ++i)
                stmt.bind_text (i+1, values[i]);

            rc = stmt.step();
            assert_query_success(rc, "SQL error", Sqlite.DONE);
        }

        public void begin_transaction () throws EngineError
        {
            int rc = database.exec ("BEGIN");
            assert_query_success (rc, "Can't start transaction");
        }

        public void end_transaction () throws EngineError
        {
            int rc = database.exec ("COMMIT");
            assert_query_success (rc, "Can't commit transaction");
        }

        public void close ()
            {
            // FIXME: make sure symbol tables are consistent (ie.
            //        _fix_cache is empty)
            
            // SQLite connection is implicitly closed upon destruction
            database = null;
        }

        /**
         * Ensure `rc' is SQLITE_OK. If it isn't, print an error message
         * and throw an error.
         *
         * @param rc error code returned by a SQLite call
         * @param msg message to print if `rc' indicates an error
         * @throws EngineError
         */
        public void assert_query_success (int rc, string msg,
            int success_code=Sqlite.OK) throws EngineError
        {
            if (rc != success_code)
            {
                string error_message = "%s: %d, %s".printf(
                    msg, rc, database.errmsg ());
                warning ("%s\n", error_message);
                throw new EngineError.DATABASE_ERROR (error_message);
            }
        }

        private void prepare_queries () throws EngineError
        {
            int rc;
            string sql;

            // Event insertion statement
            sql = """
                INSERT INTO event (
                    id, timestamp, interpretation, manifestation, actor,
                    origin, payload, subj_id, subj_id_current,
                    subj_interpretation, subj_manifestation, subj_origin,
                    subj_mimetype, subj_text, subj_storage
                ) VALUES (
                    ?, ?, ?, ?, ?,
                    (SELECT id FROM uri WHERE value=?),
                    ?,
                    (SELECT id FROM uri WHERE value=?),
                    (SELECT id FROM uri WHERE value=?),
                    ?, ?,
                    (SELECT id FROM uri WHERE value=?),
                    ?,
                    (SELECT id FROM text WHERE value=?),
                    (SELECT id FROM storage WHERE value=?)
                )""";

            rc = database.prepare_v2 (sql, -1, out event_insertion_stmt);
            assert_query_success (rc, "Insertion query error");

            // Event ID retrieval statement
            sql = """
                SELECT id FROM event
                WHERE timestamp=? AND interpretation=? AND
                    manifestation=? AND actor=?
                """;
            rc = database.prepare_v2 (sql, -1, out id_retrieval_stmt);
            assert_query_success (rc, "Event ID retrieval query error");
        }

    }

}

// vim:expandtab:ts=4:sw=4
