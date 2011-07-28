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
        // FIXME: use StringBuilder and insert numbers directly, since they
        // are injection-safe and we can't reuse the query anyway
        string sql_condition = "?";
        for (int i = 1; i < event_ids.length; ++i)
            sql_condition += ", ?";
        string sql = """
            SELECT * FROM event_view
            WHERE id IN (""" + sql_condition + """)
            """;

        if ((rc = db.prepare_v2 (sql, -1, out stmt)) != Sqlite.OK) {
            printerr ("SQL error: %d, %s\n", rc, db.errmsg ());
            throw new EngineError.DATABASE_ERROR("Fail.");
        }

        for (int i = 0; i < event_ids.length; ++i)
            stmt.bind_int64(i+1, event_ids[i]);

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

        // FIXME: Move this into insert_events to get more performance doing
        //        them all at once? This needs some testing.
        // make sure all URIs, mimetypes, texts and storages are inserted

        var uris = new GenericArray<string> ();
        if (event.origin != "")
            uris.add (event.origin);
        for (int i = 0; i < event.num_subjects(); ++i)
        {
            unowned Subject subject = event.subjects[i];
            uris.add(subject.uri);
            uris.add(subject.current_uri);
            if (subject.origin != "")
                uris.add(subject.origin);
        }
        string sql1 = "INSERT OR IGNORE INTO uri (value) ...";

        // FIXME: Should we add something just like TableLookup but with LRU
        //        for those? Or is embedding the query faster? Needs testing!

        // FIXME: we can reuse this query for all insertions! move this into
        //        something running at startup so it's done only once.
        Sqlite.Statement insertion_query;

        string sql = """
            INSERT INTO event (
                id, timestamp, interpretation, manifestation, actor,
                origin, payload, subj_id, subj_id_current,
                subj_interpretation, subj_manifestation, subj_origin,
                subj_mimetype, subj_text, subj_storage
            ) VALUES (
                ?, ?, ?, ?, ?,
                (SELECT id FROM uri WHERE value=?),
                ?,
                (SELECT id FROM uri WHERE value=?),
                (SELECT id FROM uri WHERE value=?),
                ?, ?,
                (SELECT id FROM uri WHERE value=?),
                ?,
                (SELECT id FROM text WHERE value=?),
                (SELECT id from storage WHERE value=?)
            )""";

        int rc;
        if ((rc = db.prepare_v2 (sql, -1, out insertion_query)) != Sqlite.OK) {
            warning ("SQL error: %d, %s\n", rc, db.errmsg ());
            return 0;
        }
        // ---

        insertion_query.clear_bindings();

        insertion_query.bind_int64 (1, event.id);
        insertion_query.bind_int64 (2, event.timestamp);
        insertion_query.bind_int64 (3,
            interpretations_table.get_id (event.interpretation));
        insertion_query.bind_int64 (4,
            manifestations_table.get_id (event.manifestation));
        insertion_query.bind_int64 (5, actors_table.get_id (event.actor));
        insertion_query.bind_text (6, event.origin);
        insertion_query.bind_int64 (7, 0 /*payload_id*/);

        for (int i = 0; i < event.num_subjects(); ++i)
        {
            insertion_query.reset();
            
            unowned Subject subject = event.subjects[i];
            
            insertion_query.bind_text (8, subject.uri);
            insertion_query.bind_text (9, subject.current_uri);
            insertion_query.bind_int64 (10,
                interpretations_table.get_id (subject.interpretation));
            insertion_query.bind_int64 (11,
                manifestations_table.get_id (subject.manifestation));
            insertion_query.bind_text (12, subject.origin);
            insertion_query.bind_int64 (13,
                mimetypes_table.get_id (subject.mimetype));
            // FIXME: Consider a storages_table table. Too dangerous?
            insertion_query.bind_text (14, subject.storage);
            
            if (insertion_query.step() != Sqlite.DONE) {
                warning ("SQL error: %d, %s\n", rc, db.errmsg ());
                return 0;
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
