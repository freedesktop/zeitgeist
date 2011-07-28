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

using Zeitgeist.SQLite;

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
        get_events({ 202, 203, 204, 205, 206, 207, 208, 209 });
    }

    public GenericArray<Event> get_events(uint32[] event_ids,
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
            WHERE id > 201 AND id < 210
            """;
        
        if ((rc = db.prepare_v2 (sql, -1, out stmt)) == 1) {
            printerr ("SQL error: %d, %s\n", rc, db.errmsg ());
            throw new EngineError.DATABASE_ERROR("Fail.");
        }

        var events = new GenericArray<Event>();
        events.length = event_ids.length;

        int num_columns = stmt.column_count();
        while ((rc = stmt.step()) == Sqlite.ROW)
        {
            uint32 event_id = (uint32) uint64.parse(
                stmt.column_text (EventViewRows.ID));
            int index = search_event_ids_array(event_ids, event_id);
            assert (index >= 0);
            
            // FIXME: get real values from TableLookup
            
            Event event;
            if (events[index] != null)
            {
                // We already got this event before, so we only need to
                // take the missing subject data.
                event = events[index];
            }
            else
            {
                event = new Event ();
                event.id = event_id;
                event.timestamp = int64.parse(
                    stmt.column_text (EventViewRows.TIMESTAMP));
                event.interpretation = stmt.column_text (
                    EventViewRows.INTERPRETATION);
                event.manifestation = stmt.column_text (
                    EventViewRows.MANIFESTATION);
                event.actor = stmt.column_text (EventViewRows.ACTOR);
                event.origin = stmt.column_text (EventViewRows.ORIGIN);
                // FIXME: payload
                events[index] = event;
            }
            
            Subject subject = new Subject ();
            subject.uri = stmt.column_text (EventViewRows.SUBJECT_URI);
            subject.text = stmt.column_text (EventViewRows.SUBJECT_TEXT);
            subject.storage = stmt.column_text (EventViewRows.SUBJECT_STORAGE);
            subject.origin = stmt.column_text (EventViewRows.SUBJECT_ORIGIN_URI);
            subject.current_uri = stmt.column_text (
                EventViewRows.SUBJECT_CURRENT_URI);
            subject.interpretation = stmt.column_text (
                EventViewRows.SUBJECT_INTERPRETATION);
            subject.manifestation = stmt.column_text (
                EventViewRows.SUBJECT_MANIFESTATION);
            subject.mimetype = stmt.column_text (
                EventViewRows.SUBJECT_MIMETYPE);
            
            event.add_subject(subject);
        }
        if (rc != Sqlite.DONE) 
        {
            printerr ("Error: %d, %s\n", rc, db.errmsg ());
            // FIXME: throw some error??
        }
        
        for (int i = 0; i < event_ids.length; ++i)
        {
            events[i].debug_print ();
            stdout.printf ("\n");
        }

        return new events;
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

    private static int search_event_ids_array(uint32[] arr, uint32 needle)
    {
        for (int i = 0; i < arr.length; ++i)
            if (arr[i] == needle)
                return i;
        return -1;
    }

}

// vim:expandtab:ts=4:sw=4
