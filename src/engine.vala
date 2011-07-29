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
    unowned Sqlite.Database db;
    
    TableLookup interpretations_table;
    TableLookup manifestations_table;
    TableLookup mimetypes_table;
    TableLookup actors_table;
    
    uint32 last_id;

    public Engine () throws EngineError
    {
        database = new Zeitgeist.SQLite.ZeitgeistDatabase();
        db = database.database;
        last_id = database.get_last_id();
        
        interpretations_table = new TableLookup(database, "interpretation");
        manifestations_table = new TableLookup(database, "manifestation");
        mimetypes_table = new TableLookup(database, "mimetype");
        actors_table = new TableLookup(database, "actor");
        
        // FIXME: load extensions
    }

    public GenericArray<Event> get_events(uint32[] event_ids,
            BusName? sender=null) throws EngineError
    {
        // TODO: Consider if we still want the cache. This should be done
        //  once everything is working, since it adds unneeded complexity.
        //  It'd also benchmark it again first, we may have better options
        //  to enhance the performance of SQLite now, and event processing
        //  will be faster now being C.
        
        Sqlite.Statement stmt;
        int rc;
        
        assert (event_ids.length > 0);
        var sql_condition = new StringBuilder ();
        sql_condition.append (event_ids[0].to_string());
        for (int i = 1; i < event_ids.length; ++i) {
            sql_condition.append (", ");
            sql_condition.append (event_ids[i].to_string());
        }
        string sql = """
            SELECT * FROM event_view
            WHERE id IN (""" + sql_condition.str + """)
            """;

        rc = db.prepare_v2 (sql, -1, out stmt);
        database.assert_query_success(rc, "SQL error");

        var events = new GenericArray<Event>();
        events.length = event_ids.length;

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
                event.timestamp = stmt.column_int64 (EventViewRows.TIMESTAMP);
                event.interpretation = interpretations_table.get_value (
                    stmt.column_int (EventViewRows.INTERPRETATION));
                event.manifestation = manifestations_table.get_value (
                    stmt.column_int (EventViewRows.MANIFESTATION));
                event.actor = actors_table.get_value (
                    stmt.column_int (EventViewRows.ACTOR));
                event.origin = stmt.column_text (
                    EventViewRows.EVENT_ORIGIN_URI);
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
            subject.interpretation = interpretations_table.get_value (
                stmt.column_int (EventViewRows.SUBJECT_INTERPRETATION));
            subject.manifestation = manifestations_table.get_value (
                stmt.column_int (EventViewRows.SUBJECT_MANIFESTATION));
            subject.mimetype = mimetypes_table.get_value (
                stmt.column_int (EventViewRows.SUBJECT_MIMETYPE));
            
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

        // FIXME: make sure nulls become NULL_EVENT
        // FIXME: what happens if a query requests the same element in
        //        more than one place?

        return events;
    }

    public uint32[] insert_events (GenericArray<Event> events,
        BusName? sender=null) throws EngineError
    {
        uint32[] event_ids = new uint32[events.length];
        database.begin_transaction();
        for (int i = 0; i < events.length; ++i)
        {
            event_ids[i] = insert_event (events[i], sender);
            print("%u\n", event_ids[i]);
        }
        database.end_transaction();
        return event_ids;
    }

    public uint32 insert_event (Event event,
        BusName? sender=null)
    {
        assert (event.id == 0);
        assert (event.num_subjects () > 0);
        // FIXME: make sure event timestamp is sane
        
        /* FIXME:
        if (event.interpretation == interpretation.MOVE_EVENT)
        {
            // check all subjects for uri != current_uri
        }
        else
        {
            // check all subjects for uri == current_uri
        }
        */

        event.id = ++last_id;

        // FIXME: call pre_insert extension hooks
        //        if afterwards event == null, return and ignore the event

        // FIXME: store the payload
        // payload_id = store_payload (event);

        // Make sure all the URIs, mimetypes, texts and storage are inserted
        {
            var uris = new GenericArray<string> ();
            var mimetypes = new GenericArray<string> ();
            var texts = new GenericArray<string> ();
            var storages = new GenericArray<string> ();

            if (event.origin != "")
                uris.add (event.origin);

            for (int i = 0; i < event.num_subjects(); ++i)
            {
                unowned Subject subject = event.subjects[i];
                uris.add (subject.uri);
                uris.add (subject.current_uri);
                if (subject.origin != "")
                    uris.add (subject.origin);
                if (subject.mimetype != "")
                    mimetypes.add (subject.mimetype);
                if (subject.text != "")
                    texts.add (subject.text);
                if (subject.storage != "")
                    storages.add (subject.storage);
            }

            try
            {
                if (uris.length > 0)
                    database.insert_or_ignore_into_table ("uri", uris);
                if (mimetypes.length > 0)
                    database.insert_or_ignore_into_table ("mimetype", mimetypes);
                if (texts.length > 0)
                    database.insert_or_ignore_into_table ("text", texts);
                if (storages.length > 0)
                    database.insert_or_ignore_into_table ("storage", storages);
            }
            catch (EngineError e)
            {
                warning ("Can't insert data for event: " + e.message);
                return 0;
            }
        }

        // FIXME: Should we add something just like TableLookup but with LRU
        //        for those? Or is embedding the query faster? Needs testing!

        int rc;
        unowned Sqlite.Statement insert_stmt = database.event_insertion_stmt;

        insert_stmt.bind_int64 (1, event.id);
        insert_stmt.bind_int64 (2, event.timestamp);
        insert_stmt.bind_int64 (3,
            interpretations_table.get_id (event.interpretation));
        insert_stmt.bind_int64 (4,
            manifestations_table.get_id (event.manifestation));
        insert_stmt.bind_int64 (5, actors_table.get_id (event.actor));
        insert_stmt.bind_text (6, event.origin);
        insert_stmt.bind_int64 (7, 0 /*payload_id*/);

        for (int i = 0; i < event.num_subjects(); ++i)
        {
            insert_stmt.reset();
            
            unowned Subject subject = event.subjects[i];
            
            insert_stmt.bind_text (8, subject.uri);
            insert_stmt.bind_text (9, subject.current_uri);
            insert_stmt.bind_int64 (10,
                interpretations_table.get_id (subject.interpretation));
            insert_stmt.bind_int64 (11,
                manifestations_table.get_id (subject.manifestation));
            insert_stmt.bind_text (12, subject.origin);
            insert_stmt.bind_int64 (13,
                mimetypes_table.get_id (subject.mimetype));
            // FIXME: Consider a storages_table table. Too dangerous?
            insert_stmt.bind_text (14, subject.storage);
            
            if ((rc = insert_stmt.step()) != Sqlite.DONE) {
                if (rc != Sqlite.CONSTRAINT)
                {
                    warning ("SQL error: %d, %s\n", rc, db.errmsg ());
                    return 0;
                }
                // This event was already registered.
                // Rollback last_id and return the ID of the original event
                --last_id;

                unowned Sqlite.Statement retrieval_stmt =
                    database.id_retrieval_stmt;

                retrieval_stmt.reset ();

                retrieval_stmt.bind_int64 (1, event.timestamp);
                retrieval_stmt.bind_int64 (2,
                    interpretations_table.get_id (event.interpretation));
                retrieval_stmt.bind_int64 (3,
                    manifestations_table.get_id (event.manifestation));
                retrieval_stmt.bind_int64 (4, actors_table.get_id (event.actor));
                
                if ((rc = retrieval_stmt.step()) != Sqlite.ROW) {
                    warning ("SQL error: %d, %s\n", rc, db.errmsg ());
                    return 0;
                }
                
                return retrieval_stmt.column_int (0);
            }
        }

        /*
        if (event.interpretation == MOVE_EVENT)
        {
            handle_move_event (event);
        }
        */

        return event.id;
    }

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
