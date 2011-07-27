/* engine.vala
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
		
		// FIXME: tmp:
		get_events({1,2,3});
	}

	public Event[] get_events(uint32[] event_ids,
			BusName? sender=null) throws EngineError
	{
		// TODO: Consider if we still want the cache. This should be done
		//  once everything is working, since it adds unneeded complexity.
		//  It'd also benchmark it again first, we may have better options
		//  to enhance the performance of SQLite now, and event processing
		//  will be faster now being C.
		
		unowned Sqlite.Database db = database.database;
		Sqlite.Statement stmt;
		int rc;
		
		string sql = """
			SELECT * FROM event_view
			WHERE id < 1000
			""";
		
		if ((rc = db.prepare_v2 (sql, -1, out stmt)) == 1) {
			printerr ("SQL error: %d, %s\n", rc, db.errmsg ());
			throw new EngineError.DATABASE_ERROR("Fail.");
		}

		var events = new GenericArray<uint32>();

		int num_columns = stmt.column_count();
		while ((rc = stmt.step()) == Sqlite.ROW)
		{
			for (int i = 0; i < num_columns; i++)
			{
				if (stmt.column_name (i) == "id") {
					string txt = stmt.column_text (i);
					//print ("%s = %s\n", stmt.column_name (i), txt);
				}
			}
		}
		if (rc != Sqlite.DONE) 
		{
			printerr ("Error: %d, %s\n", rc, db.errmsg ());
			// FIXME: throw some error??
		}
		/*
		for row in rows:
			// Assumption: all rows of a same event for its different
			// subjects are in consecutive order.
			event = get_event_from_row(row)
			if event: // ??
				// Check for existing event.id in event to tattach
				// other subjects to it
				if event.id not in events:
					events[event.id] = event
				else:
					event = events[event.id]
				subject = get_subject_from_row(row)
				if subject: // ??
					event.add_subject(subject)
					// FIXME: call extension 'get_event' hooks
		*/
		
		return new Event[0];
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
