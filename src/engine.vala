/* zeitgeist-daemon.vala
 *
 * Copyright © 2011 Collabora Ltd.
 *             By Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
 *
 * Based upon a Python implementation (2009-2011) by:
 *  Markus Korn <thekorn@gmx.net>
 *  Mikkel Kamstrup Erlandsen <mikkel.kamstrup@gmail.com>
 *  Seif Lotfy <seif@lotfy.com>
 *  Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
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

public class Engine : Object
{

	Zeitgeist.SQLite.ZeitgeistDatabase database;
	uint32 last_id;

	public Engine () throws EngineError
	{
		database = new Zeitgeist.SQLite.ZeitgeistDatabase();
		last_id = database.get_last_id();
		
		// FIXME: initialize TableLookups
		// FIXME: load extensions
		
		stdout.printf("last_id: %u\n", last_id);
	}

	public GenericArray<Event> get_events(uint32 event_ids,
			BusName? sender=null)
	{
		var events = new GenericArray<Event>();
		return events;
	}

	// next_event_id(): last_id + 1; return last_id;
	// it's used in only one place, we can just inline it.

	/**
	 * Clear all resources Engine is using (close database connection,
	 * unload extensions, etc.).
	 *
	 * After executing this method on an Engine instance, no other function
	 * of said instance may be called.
	 */
	public void close ()
	{
		// FIXME: unload extensions
		database.close();
	}

}
