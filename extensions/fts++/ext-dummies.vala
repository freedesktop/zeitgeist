/* ext-dummies.vala
 *
 * Copyright © 2011-2012 Michal Hruby <michal.mhr@gmail.com>
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

namespace Zeitgeist
{
    public class ExtensionCollection : Object
    {
        public unowned Engine engine { get; construct; }

        public ExtensionCollection (Engine engine)
        {
            Object (engine: engine);
        }

        public string[] get_extension_names ()
        {
            string[] result = {};
            return result;
        }

        public void call_pre_insert_events (GenericArray<Event?> events,
            BusName? sender)
        {
        }

        public void call_post_insert_events (GenericArray<Event?> events,
            BusName? sender)
        {
        }

        public unowned uint32[] call_pre_delete_events (uint32[] event_ids,
            BusName? sender)
        {
            return event_ids;
        }

        public void call_post_delete_events (uint32[] event_ids,
            BusName? sender)
        {
        }
    }

    public class ExtensionStore : Object
    {
        public unowned Engine engine { get; construct; }

        public ExtensionStore (Engine engine)
        {
            Object (engine: engine);
        }
    }

}

// vim:expandtab:ts=4:sw=4
