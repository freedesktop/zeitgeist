/* extension.vala
 *
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

namespace Zeitgeist.Extension
{
    /**
     * Base class for all extensions
     *
     * FIXME: figure out what to do with this. I don't really see
     *        what the point for it is, since D-Bus accessible stuff is
     *        usually exported on a new interface. --RainCT
     * Every extension has to define a list of accessible methods as
     * 'PUBLIC_METHODS'. The constructor of an Extension object takes the
     * engine object it extends as the only argument.
     * ---
     *
     * In addition each extension has a set of hooks to control how events are
     * inserted and retrieved from the log. These hooks can either block the
     * event completely, modify it, or add additional metadata to it.
     */
    public abstract class Extension : Object
    {
        /**
         * This method gets called before Zeitgeist stops.
         * 
         * Execution of this method isn't guaranteed, and you shouldn't do
         * anything slow in there.
         */
        public abstract void unload();
    
        /**
         * Hook applied to all events before they are inserted into the
         * log. The returned event is progressively passed through all
         * extensions before the final result is inserted.
         *
         * To block an event completely simply return null.
         * The event may also be modified or completely substituted for
         * another event.
         *
         * The default implementation of this method simply returns the
         * event as is.
         *
         * @param event: A Event instance
         * @param sender: The D-Bus bus name of the client
         * @returns: The filtered event instance to insert into the log
         */
        public abstract Event pre_insert_event(Event event, BusName sender);
    
        /**
         * Hook applied to all events after they are inserted into the log.
         * 
         * @param event: A Event instance
         * @param sender: The D-Bus bus name of the client
         * @returns: Nothing
         */
        public abstract void post_insert_event(Event event, BusName sender);
    
        /**
         * Hook applied to all events before they are returned to a client.
         * The event returned from this method is progressively passed
         * through all extensions before they final result is returned to
         * the client.
         *
         * To prevent an event from ever leaving the server process simply
         * return null. The event may also be changed in place
         * or fully substituted for another event.
         *
         * The default implementation of this method simply returns the
         * event as is.
         *
         * @param event: A Eventinstance or None
         * @param sender: The D-Bus bus name of the client
         * @returns: The filtered event instance as the client should see it
         */
        public abstract Event get_event(Event event, BusName sender);
    
        /**
         * Hook applied after events have been deleted from the log.
         *
         * @param ids: A list of event ids for the events that has been deleted
         * @param sender: The unique DBus name for the client triggering the delete
         * @returns: Nothing
         */
        public abstract void post_delete_events(uint32[] ids, BusName sender);
    
        /**
         * Hook applied before events are deleted from the log.
         *
         * @param ids: A list of event ids for the events requested to be deleted
         * @param sender: The unique DBus name for the client triggering the delete
         * @returns: The filtered list of event ids which should be deleted
         */
        public abstract Event pre_delete_events(uint32[] ids, BusName sender);
    }
}
// vim:expandtab:ts=4:sw=4
