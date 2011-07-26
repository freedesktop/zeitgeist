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
 
 
public abstract class Extension: Object
{
    public abstract void unload();

    public abstract Event pre_insert_event(Event event, BusName sender);

    public abstract void post_insert_event(Event event, BusName sender);

    public abstract Event get_event(Event event, BusName sender);

    public abstract void post_delete_events(Event event, BusName sender);

    public abstract Event pre_delete_events(Event event, BusName sender);
}
