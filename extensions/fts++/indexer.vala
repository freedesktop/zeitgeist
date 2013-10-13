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

namespace Zeitgeist
{

    public class Indexer : Object
    {

        public Indexer () throws EngineError
        {
        }

        public void index_events (GenericArray<Event> events)
        {
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
