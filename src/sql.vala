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

using Sqlite;
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

        // FIXME: Should this be accessible from engine.vala or not?
        //  Probably it should, since otherwise there won't be much
        //  functionallity left for engine.vala.
        public Database database;

        public ZeitgeistDatabase () throws EngineError
        {
            string sqlite_filepath = Constants.DATABASE_FILE_PATH;
            
            int rc = Database.open_v2(
                sqlite_filepath,
                out database);
            assert_query_success(rc, "Can't open database");
            
            // FIXME: check DB integrity, create it if needed, etc.
        }

        public uint32 get_last_id () throws EngineError
        {
            int last_id = -1;
            int rc = database.exec ("SELECT MAX(id) FROM event",
                (n_columns, values, column_names) =>
                {
                    last_id = int.parse(values[0]);
                    return 0;
                }, null);
            assert_query_success(rc, "Can't query database");
            assert (last_id != -1);
            return last_id;
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
         **/
        private void assert_query_success (int rc, string msg) throws EngineError
        {
            if (rc != Sqlite.OK)
            {
                stderr.printf ("%s: %d, %s\n", msg, rc, database.errmsg ());
                throw new EngineError.DATABASE_ERROR("Fail.");
            }
        }

    }

}

// vim:expandtab:ts=4:sw=4
