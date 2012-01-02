/* sql.vala
 *
 * Copyright © 2011 Collabora Ltd.
 *             By Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
 *             By Seif Lotfy <seif@lotfy.com>
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

    public delegate void DeletionCallback (string table, int64 rowid);

    public class ZeitgeistDatabase : Object
    {

        public Sqlite.Statement event_insertion_stmt;
        public Sqlite.Statement id_retrieval_stmt;
        public Sqlite.Statement move_handling_stmt;
        public Sqlite.Statement payload_insertion_stmt;

        // The DB should be accessible from engine for statement preperations
        //  as well as allowing extensions to add tables to it.
        public Sqlite.Database database;

        private DeletionCallback? deletion_callback = null;

        public ZeitgeistDatabase () throws EngineError
        {
            message ("Opening DB from %s", Utils.get_database_file_path ());
            int rc = Sqlite.Database.open_v2 (
                Utils.get_database_file_path (),
                out database);
            assert_query_success (rc, "Can't open database");

            DatabaseSchema.ensure_schema (database);

            prepare_queries ();

            // Register a data change notification callback to look for
            // deletions, so we can keep the TableLookups up to date.
            database.update_hook (update_callback);
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
                        last_id = int.parse (values[0]);
                    return 0;
                }, null);
            assert_query_success (rc, "Can't query database");
            assert (last_id != -1);
            return last_id;
        }

        public void set_deletion_callback (owned DeletionCallback? callback)
        {
            deletion_callback = (owned) callback;
        }

        /**
         * Join all given event_ids into a comma-separated string suitable
         * for use in a SQL query like "WHERE id IN (...)".
         */
        public string get_sql_string_from_event_ids (uint32[] event_ids)
            requires (event_ids.length > 0)
        {
            var sql_condition = new StringBuilder ();
            sql_condition.append_printf ("%u", event_ids[0]);
            for (int i = 1; i < event_ids.length; ++i) {
                sql_condition.append_printf (", %u", event_ids[i]);
            }
            return sql_condition.str;
        }

        public TimeRange? get_time_range_for_event_ids (uint32[] event_ids)
            throws EngineError
        {
            if (event_ids.length == 0)
                return null;

            string sql = """
                SELECT MIN(timestamp), MAX(timestamp)
                FROM event
                WHERE id IN (%s)
                """.printf (get_sql_string_from_event_ids (event_ids));

            TimeRange? time_range = null;
            int rc = database.exec (sql,
                (n_columns, values, column_names) =>
                {
                    if (values[0] != null)
                    {
                        int64 start = int64.parse (values[0]);
                        int64 end = int64.parse (values[1]);
                        time_range = new TimeRange (start, end);
                    }
                    return 0;
                }, null);
            assert_query_success (rc, "SQL Error");

            return time_range;
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

            rc = stmt.step ();
            assert_query_success (rc, "SQL error", Sqlite.DONE);
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
            // SQLite connection is implicitly closed upon destruction
            database = null;
        }

#if EXPLAIN_QUERIES
        public void explain_query (Sqlite.Statement prepared_stmt)
            throws EngineError
        {
            int rc;
            Sqlite.Statement stmt;

            var explain_sql = "EXPLAIN QUERY PLAN %s".printf (prepared_stmt.sql ());

            rc = prepared_stmt.db_handle ().prepare_v2 (explain_sql, -1, out stmt);
            assert_query_success(rc, "SQL error");

            while ((rc = stmt.step()) == Sqlite.ROW)
            {
                int select_id = stmt.column_int (0);
                int order = stmt.column_int (1);
                int from = stmt.column_int (2);
                unowned string detail = stmt.column_text (3);

                print ("%d %d %d %s\n", select_id, order, from, detail);
            }
        }
#endif

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

            // Move handling statment
            sql = """
            UPDATE event
                SET subj_id_current=(SELECT id FROM uri WHERE value=?)
                    WHERE subj_id_current=(SELECT id FROM uri WHERE value=?)
                    AND interpretation!=? AND timestamp<?
            """;
            rc = database.prepare_v2 (sql, -1, out move_handling_stmt);
            assert_query_success (rc, "Move handling error");

            // Payload insertion statment
            sql = """
                INSERT INTO payload (value) VALUES (?)
            """;
            rc = database.prepare_v2 (sql, -1, out payload_insertion_stmt);
            assert_query_success (rc, "Payload insertion query error");
        }


        protected void update_callback (Sqlite.Action action,
            string dbname, string table, int64 rowid)
        {
            if (action != Sqlite.Action.DELETE)
                return;
            if (deletion_callback != null)
                deletion_callback (table, rowid);
            //interpretations_table
            // manifestations_
            //mimetypes_table - mimetype table
            // actors_  . actor table
            // FIXME!
            /*
            stdout.printf ("%s", dbname); // = main
            stdout.printf ("%s", table);
            stdout.printf ("%li", (long) rowid);
            */
        }

    }

}

// vim:expandtab:ts=4:sw=4
