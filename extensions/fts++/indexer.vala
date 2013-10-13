/* zeitgeist-fts.vala
 *
 * Copyright © 2012 Canonical Ltd.
 * Copyright © 2012 Michal Hruby <michal.mhr@gmail.com>
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 */


using Zeitgeist;
using Zeitgeist.SQLite;

namespace Zeitgeist
{

    public class Indexer : Object
    {
        private bool is_read_only = false;
        private Sqlite.Database database;
        private const int DEFAULT_OPEN_FLAGS =
            Sqlite.OPEN_READWRITE | Sqlite.OPEN_CREATE;

        public Indexer () throws EngineError
        {
            database = null;
            setup_database ();
        }

        public Indexer.ready_only () throws EngineError
        {
        }

        private void setup_database ()
        {
            string database_path = "%s/%s".printf (Utils.get_data_path (),
                                                   "zgfts.sqlite");
            int flags = is_read_only ? Sqlite.OPEN_READONLY : DEFAULT_OPEN_FLAGS;
            int rc = Sqlite.Database.open_v2 (
                database_path,
                out database, flags);
            if (rc == Sqlite.OK)
            {
                DatabaseSchema.exec_query (database,
                """
                CREATE virtual TABLE IF NOT EXISTS events USING fts4
                (event_id, event_timestmap, event_actor, event_origin,
                 subj_current_uri, subj_origin, subj_text)
                """);
            }
        }

        public void index_events (GenericArray<Event> events)
        {
            for (var i=0; i<events.length; i++)
                for (var j=0; j<events[i].subjects.length; j++)
                {
                    //TODO: insert event here
                }
        }

        public void delete_events(uint32[] ids)
        {
        }

        public GenericArray<Event> search (string query_string,
                                           TimeRange time_range,
                                           GenericArray<Event> templates,
                                           uint offset,
                                           uint count,
                                           ResultType result_type,
                                           out uint32 matches)
        {
            GenericArray<Event> results = new GenericArray<Event> ();
            return results;
        }

        public GenericArray<Event> search_with_relevancies (
                                           string query_string,
                                           TimeRange time_range,
                                           GenericArray<Event> templates,
                                           StorageState storage_state,
                                           uint offset,
                                           uint count,
                                           ResultType result_type,
                                           out double[] relevancies,
                                           out uint32 matches)
        {
            GenericArray<Event> results = new GenericArray<Event> ();
            return results;
        }
    }

}

// vim:expandtab:ts=4:sw=4
