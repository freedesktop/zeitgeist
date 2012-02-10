/* engine.vala
 *
 * Copyright © 2011 Collabora Ltd.
 *             By Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
 *             By Seif Lotfy <seif@lotfy.com>
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

using Zeitgeist;
using Zeitgeist.SQLite;

namespace Zeitgeist
{

public class Engine : DbReader
{

    public ExtensionStore extension_store;
    private ExtensionCollection extension_collection;

    private uint32 last_id;

    public Engine () throws EngineError
    {
        Object (database: new Zeitgeist.SQLite.Database ());

        // TODO: take care of this if we decide to subclass Engine
        // (we need to propagate the error, so it can't go to construct {})
        last_id = database.get_last_id ();
        extension_collection = new ExtensionCollection (this);
    }

    construct
    {
        extension_store = new ExtensionStore (this);
    }

    public string[] get_extension_names ()
    {
        return extension_collection.get_extension_names ();
    }

    public uint32[] insert_events (GenericArray<Event> events,
        BusName? sender=null) throws EngineError
    {
        extension_collection.call_pre_insert_events (events, sender);
        uint32[] event_ids = new uint32[events.length];
        database.begin_transaction ();
        for (int i = 0; i < events.length; ++i)
        {
            if (events[i] != null)
                event_ids[i] = insert_event (events[i], sender);
        }
        database.end_transaction ();
        extension_collection.call_post_insert_events (events, sender);
        return event_ids;
    }

    public uint32 insert_event (Event event,
        BusName? sender=null) throws EngineError
        requires (event.id == 0)
        requires (event.num_subjects () > 0)
    {
        event.id = ++last_id;

        // Make sure all the URIs, texts and storage are inserted
        {
            var uris = new GenericArray<string> ();
            var texts = new GenericArray<string> ();
            var storages = new GenericArray<string> ();
            var subj_uris = new SList<string> ();

            if (event.origin != "")
                uris.add (event.origin);

            // Iterate through subjects and check for validity
            for (int i = 0; i < event.num_subjects(); ++i)
            {
                unowned Subject subject = event.subjects[i];
                if (subj_uris.find_custom(subject.uri, strcmp) != null)
                {
                    // Events with two subjects with the same URI are not supported.
                    warning ("Events with two subjects with the same URI are not supported");
                    return 0;
                }
                subj_uris.append (subject.uri);

                uris.add (subject.uri);

                if (subject.current_uri == "" || subject.current_uri == null)
                    subject.current_uri = subject.uri;

                if (event.interpretation == ZG.MOVE_EVENT
                    && subject.uri == subject.current_uri)
                {
                    throw new EngineError.INVALID_ARGUMENT (
                        "Illegal event: unless event.interpretation is " +
                        "'MOVE_EVENT' then subject.uri and " +
                        "subject.current_uri have to be the same");
                }
                else if (event.interpretation != ZG.MOVE_EVENT
                    && subject.uri != subject.current_uri)
                {
                    throw new EngineError.INVALID_ARGUMENT (
                        "Redundant event: event.interpretation indicates " +
                        "the uri has been moved yet the subject.uri and " +
                        "subject.current_uri are identical");
                }

                uris.add (subject.current_uri);

                if (subject.origin != "")
                    uris.add (subject.origin);
                if (subject.text != "")
                    texts.add (subject.text);
                if (subject.storage != "")
                    storages.add (subject.storage);
            }

            try
            {
                if (uris.length > 0)
                    database.insert_or_ignore_into_table ("uri", uris);
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

        var payload_id = store_payload (event);

        // FIXME: Should we add something just like TableLookup but with LRU
        //        for those? Or is embedding the query faster? Needs testing!

        int rc;
        unowned Sqlite.Statement insert_stmt = database.event_insertion_stmt;

        // We need to call reset here (even if we do so again in the subjects
        // loop) since calling .bind_* after a .step() invocation is illegal.
        insert_stmt.reset ();

        insert_stmt.bind_int64 (1, event.id);
        insert_stmt.bind_int64 (2, event.timestamp);
        insert_stmt.bind_int64 (3,
            interpretations_table.get_id (event.interpretation));
        insert_stmt.bind_int64 (4,
            manifestations_table.get_id (event.manifestation));
        insert_stmt.bind_int64 (5, actors_table.get_id (event.actor));
        insert_stmt.bind_text (6, event.origin);
        insert_stmt.bind_int64 (7, payload_id);

        for (int i = 0; i < event.num_subjects(); ++i)
        {
            insert_stmt.reset();

            unowned Subject subject = event.subjects[i];

            // If subject manifestation and interpretation are not set,
            // we try to automatically determine them from the other data.

            if (subject.manifestation == "")
            {
                unowned string? manifestation = manifestation_for_uri (
                    subject.uri);
                if (manifestation != null)
                    subject.manifestation = manifestation;
            }

            if (subject.interpretation == "")
            {
                unowned string? interpretation = interpretation_for_mimetype (
                    subject.mimetype);
                if (interpretation != null)
                    subject.interpretation = interpretation;
            }

            insert_stmt.bind_text (8, subject.uri);
            insert_stmt.bind_text (9, subject.current_uri);
            insert_stmt.bind_int64 (10,
                interpretations_table.get_id (subject.interpretation));
            insert_stmt.bind_int64 (11,
                manifestations_table.get_id (subject.manifestation));
            insert_stmt.bind_text (12, subject.origin);
            insert_stmt.bind_int64 (13,
                mimetypes_table.get_id (subject.mimetype));
            insert_stmt.bind_text (14, subject.text);
            // FIXME: Consider a storages_table table. Too dangerous?
            insert_stmt.bind_text (15, subject.storage);

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

                if ((rc = retrieval_stmt.step ()) != Sqlite.ROW) {
                    warning ("SQL error: %d, %s\n", rc, db.errmsg ());
                    return 0;
                }

                return retrieval_stmt.column_int (0);
            }
        }

        if (event.interpretation == ZG.MOVE_EVENT)
        {
            handle_move_event (event);
        }

        return event.id;
    }

    public TimeRange? delete_events (uint32[] event_ids, BusName? sender)
        throws EngineError
        requires (event_ids.length > 0)
    {
        event_ids = extension_collection.call_pre_delete_events (
            event_ids, sender);

        TimeRange? time_range = database.get_time_range_for_event_ids (
            event_ids);

        string sql_event_ids = database.get_sql_string_from_event_ids (
            event_ids);

        if (time_range == null)
        {
            warning ("Tried to delete non-existing event(s): %s".printf (
                sql_event_ids));
            return null;
        }

        int rc = db.exec ("DELETE FROM event WHERE id IN (%s)".printf(
            sql_event_ids), null, null);
        database.assert_query_success (rc, "SQL Error");
        message ("Deleted %d (out of %d) events.".printf (
            db.changes(), event_ids.length));

        extension_collection.call_post_delete_events (event_ids, sender);

        return time_range;
    }

    /**
     * Clear all resources Engine is using (close database connection,
     * unload extensions, etc.).
     *
     * After executing this method on an Engine instance, no other function
     * of said instance may be called.
     */
    public override void close ()
    {
        // We delete the ExtensionCollection here so that it unloads
        // all extensions and they get a chance to access the database
        // (including through ExtensionStore) before it's closed.
        extension_collection = null;

        base.close ();
    }

    private void handle_move_event (Event event)
    {
        for (int i = 0; i < event.subjects.length; i++)
        {
            Subject subject = event.subjects[i];
            int rc;
            unowned Sqlite.Statement move_stmt = database.move_handling_stmt;
            move_stmt.reset();
            move_stmt.bind_text (1, subject.current_uri);
            move_stmt.bind_text (2, subject.uri);
            move_stmt.bind_text (3, event.interpretation);
            move_stmt.bind_int64 (4, event.timestamp);
            if ((rc = move_stmt.step()) != Sqlite.DONE) {
                if (rc != Sqlite.CONSTRAINT)
                {
                    warning ("SQL error: %d, %s\n", rc, db.errmsg ());
                }
            }
        }
    }

    private int64 store_payload (Event event)
    {
        /**
        * TODO: Right now payloads are not unique and every event has its
        * own one. We could optimize this to store those which are repeated
        * for different events only once, especially considering that
        * events cannot be modified once they've been inserted.
        */
        if (event.payload != null)
        {
            int rc;
            unowned Sqlite.Statement payload_insertion_stmt =
                database.payload_insertion_stmt;
            payload_insertion_stmt.reset ();
            payload_insertion_stmt.bind_blob (1, event.payload.data,
                event.payload.data.length);
            if ((rc = payload_insertion_stmt.step ()) != Sqlite.DONE)
                if (rc != Sqlite.CONSTRAINT)
                    warning ("SQL error: %d, %s\n", rc, db.errmsg ());

            return database.database.last_insert_rowid ();
        }
        return 0;
    }

}

}

// vim:expandtab:ts=4:sw=4
