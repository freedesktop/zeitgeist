/* event-cache.vala
 *
 * Copyright © 2012 Collabora Ltd.
 *             By Trever Fischer <trever.fischer@collabora.co.uk>
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
public class EventCache : Object
{

    private HashTable<uint32?, Event> cache_table;
    private Queue<uint32> lru_queue;
    private uint max_cache_size;

    construct
    {
        cache_table = new HashTable<uint32?, Event>(int_hash, int_equal);
        lru_queue = new Queue<uint32>();
        max_cache_size = 1024;
    }

    public Event? get_event(uint32 id)
    {
        Event? e = cache_table.get (id);
        if (e != null)
        {
            lru_queue.remove_all (id);
            lru_queue.push_tail (id);
        }
        return e;
    }

    public void cache_event(Event e)
    {
        cache_table.set (e.id, e);
        lru_queue.remove_all (e.id);
        lru_queue.push_tail (e.id);

        while (lru_queue.length > max_cache_size)
        {
            uint32 target = lru_queue.pop_head ();
            cache_table.remove (target);
        }
    }

    public uint size
    {
        get { return lru_queue.length; }
    }

    public uint max_size
    {
        get { return max_cache_size; }
        set { max_cache_size = value; }
    }
}

}

// vim:expandtab:ts=4:sw=4
