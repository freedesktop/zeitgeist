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
{ // FIXME: increase indentation once we're ok with breaking 'bzr diff'

public class Engine : Object
{

    public Zeitgeist.SQLite.ZeitgeistDatabase database { get; private set; }
    private ExtensionCollection extension_collection;
    private unowned Sqlite.Database db;

    protected TableLookup interpretations_table;
    protected TableLookup manifestations_table;
    protected TableLookup mimetypes_table;
    protected TableLookup actors_table;

    private uint32 last_id;

    public Engine () throws EngineError
    {
        database = new Zeitgeist.SQLite.ZeitgeistDatabase ();
        database.set_deletion_callback (delete_from_cache);
        db = database.database;
        last_id = database.get_last_id ();

        interpretations_table = new TableLookup (database, "interpretation");
        manifestations_table = new TableLookup (database, "manifestation");
        mimetypes_table = new TableLookup (database, "mimetype");
        actors_table = new TableLookup (database, "actor");

        extension_collection = new ExtensionCollection (this);
    }

    public string[] get_extension_names ()
    {
        return extension_collection.get_extension_names ();
    }

    public GenericArray<Event?> get_events(uint32[] event_ids,
            BusName? sender=null) throws EngineError
    {
        // TODO: Consider if we still want the cache. This should be done
        //  once everything is working, since it adds unneeded complexity.
        //  It'd also benchmark it again first, we may have better options
        //  to enhance the performance of SQLite now, and event processing
        //  will be faster now being C.

        Sqlite.Statement stmt;
        int rc;

        if (event_ids.length == 0)
            return new GenericArray<Event?> ();
        var sql_event_ids = database.get_sql_string_from_event_ids (event_ids);
        string sql = """
            SELECT * FROM event_view
            WHERE id IN (%s)
            """.printf (sql_event_ids);

        rc = db.prepare_v2 (sql, -1, out stmt);
        database.assert_query_success (rc, "SQL error");

        var events = new HashTable<uint32, Event?> (direct_hash, direct_equal);

        while ((rc = stmt.step ()) == Sqlite.ROW)
        {
            uint32 event_id = (uint32) stmt.column_int64 (EventViewRows.ID);
            Event? event = events.lookup (event_id);
            if (event == null)
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

                // Load payload
                unowned uint8[] data = (uint8[])
                    stmt.column_blob(EventViewRows.PAYLOAD);
                data.length = stmt.column_bytes(EventViewRows.PAYLOAD);
                if (data != null)
                {
                    event.payload = new ByteArray();
                    event.payload.append(data);
                }
                events.insert (event_id, event);
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
            throw new EngineError.DATABASE_ERROR ("Error: %d, %s\n", 
                rc, db.errmsg ());
        }

        var results = new GenericArray<Event?> ();
        results.length = event_ids.length;
        int i = 0;
        foreach (var id in event_ids)
        {
            results.set(i++, events.lookup (id));
        }

        extension_collection.call_post_get_events (results, sender);

        return results;
    }

    public uint32[] find_event_ids (TimeRange time_range,
        GenericArray<Event> event_templates,
        uint storage_state, uint max_events, uint result_type,
        BusName? sender=null) throws EngineError
    {
        return find_event_ids_logic(time_range, event_templates, storage_state,
            max_events, result_type);
    }

    private uint32[] find_event_ids_logic (TimeRange time_range,
        GenericArray<Event> event_templates,
        uint storage_state, uint max_events, uint result_type,
        bool distinct = true, BusName? sender=null) throws EngineError
    {

        WhereClause where = new WhereClause (WhereClause.Type.AND);

        /**
         * We are using the unary operator here to tell SQLite to not use
         * the index on the timestamp column at the first place. This is a
         * "fix" for (LP: #672965) based on some benchmarks, which suggest
         * a performance win, but we might not oversee all implications.
         * (See http://www.sqlite.org/optoverview.html, section 6.0).
         *    -- Markus Korn, 29/11/2010
         */
        if (time_range.start != 0)
            where.add (("+timestamp >= %" + int64.FORMAT).printf(
                time_range.start));
        if (time_range.end != 0)
            where.add (("+timestamp <= %" + int64.FORMAT).printf(
                time_range.end));

        if (storage_state == StorageState.AVAILABLE ||
            storage_state == StorageState.NOT_AVAILABLE)
        {
            where.add ("(subj_storage_state=? OR subj_storage_state IS NULL)",
                storage_state.to_string ());
        }
        else if (storage_state != StorageState.ANY)
        {
            throw new EngineError.INVALID_ARGUMENT(
                "Unknown storage state '%u'".printf(storage_state));
        }

        WhereClause tpl_conditions = get_where_clause_from_event_templates (
            event_templates);
        where.extend (tpl_conditions);
        //if (!where.may_have_results ())
        //    return new uint32[0];

        string sql;
        if (distinct)
            sql = "SELECT DISTINCT id FROM event_view ";
        else
            sql = "SELECT id FROM event_view ";
        string where_sql = "";
        if (!where.is_empty ())
        {
            where_sql = "WHERE " + where.get_sql_conditions ();
        }

        switch (result_type)
        {
            case ResultType.MOST_RECENT_EVENTS:
                sql += where_sql + " ORDER BY timestamp DESC";
                break;
            case ResultType.LEAST_RECENT_EVENTS:
                sql += where_sql + " ORDER BY timestamp ASC";
                break;
            case ResultType.MOST_RECENT_EVENT_ORIGIN:
                sql += group_and_sort ("origin", where_sql, false);
                break;
            case ResultType.LEAST_RECENT_EVENT_ORIGIN:
                sql += group_and_sort ("origin", where_sql, true);
                break;
            case ResultType.MOST_POPULAR_EVENT_ORIGIN:
                sql += group_and_sort ("origin", where_sql, false, false);
                break;
            case ResultType.LEAST_POPULAR_EVENT_ORIGIN:
                sql += group_and_sort ("origin", where_sql, true, true);
                break;
            case ResultType.MOST_RECENT_SUBJECTS:
                sql += group_and_sort ("subj_id", where_sql, false);
                break;
            case ResultType.LEAST_RECENT_SUBJECTS:
                sql += group_and_sort ("subj_id", where_sql, true);
                break;
            case ResultType.MOST_POPULAR_SUBJECTS:
                sql += group_and_sort ("subj_id", where_sql, false, false);
                break;
            case ResultType.LEAST_POPULAR_SUBJECTS:
                sql += group_and_sort ("subj_id", where_sql, true, true);
                break;
            case ResultType.MOST_RECENT_CURRENT_URI:
                sql += group_and_sort ("subj_id_current", where_sql, false);
                break;
            case ResultType.LEAST_RECENT_CURRENT_URI:
                sql += group_and_sort ("subj_id_current", where_sql, true);
                break;
            case ResultType.MOST_POPULAR_CURRENT_URI:
                sql += group_and_sort ("subj_id_current", where_sql,
                    false, false);
                break;
            case ResultType.LEAST_POPULAR_CURRENT_URI:
                sql += group_and_sort ("subj_id_current", where_sql,
                    true, true);
                break;
            case ResultType.MOST_RECENT_ACTOR:
                sql += group_and_sort ("actor", where_sql, false);
                break;
            case ResultType.LEAST_RECENT_ACTOR:
                sql += group_and_sort ("actor", where_sql, true);
                break;
            case ResultType.MOST_POPULAR_ACTOR:
                sql += group_and_sort ("actor", where_sql, false, false);
                break;
            case ResultType.LEAST_POPULAR_ACTOR:
                sql += group_and_sort ("actor", where_sql, true, true);
                break;
            case ResultType.OLDEST_ACTOR:
                sql += group_and_sort ("actor", where_sql, true, null, "min");
                break;
            case ResultType.MOST_RECENT_ORIGIN:
                sql += group_and_sort ("subj_origin", where_sql, false);
                break;
            case ResultType.LEAST_RECENT_ORIGIN:
                sql += group_and_sort ("subj_origin", where_sql, true);
                break;
            case ResultType.MOST_POPULAR_ORIGIN:
                sql += group_and_sort ("subj_origin", where_sql, false, false);
                break;
            case ResultType.LEAST_POPULAR_ORIGIN:
                sql += group_and_sort ("subj_origin", where_sql, true, true);
                break;
            case ResultType.MOST_RECENT_SUBJECT_INTERPRETATION:
                sql += group_and_sort ("subj_interpretation", where_sql, false);
                break;
            case ResultType.LEAST_RECENT_SUBJECT_INTERPRETATION:
                sql += group_and_sort ("subj_interpretation", where_sql, true);
                break;
            case ResultType.MOST_POPULAR_SUBJECT_INTERPRETATION:
                sql += group_and_sort ("subj_interpretation", where_sql,
                    false, false);
                break;
            case ResultType.LEAST_POPULAR_SUBJECT_INTERPRETATION:
                sql += group_and_sort ("subj_interpretation", where_sql,
                    true, true);
                break;
            case ResultType.MOST_RECENT_MIMETYPE:
                sql += group_and_sort ("subj_mimetype", where_sql, false);
                break;
            case ResultType.LEAST_RECENT_MIMETYPE:
                sql += group_and_sort ("subj_mimetype", where_sql, true);
                break;
            case ResultType.MOST_POPULAR_MIMETYPE:
                sql += group_and_sort ("subj_mimetype", where_sql,
                    false, false);
                break;
            case ResultType.LEAST_POPULAR_MIMETYPE:
                sql += group_and_sort ("subj_mimetype", where_sql,
                    true, true);
                break;
            default:
                string error_message = "Invalid ResultType.";
                warning (error_message);
                throw new EngineError.INVALID_ARGUMENT (error_message);
        }

        if (max_events > 0)
            sql += " LIMIT %u".printf (max_events);

        int rc;
        Sqlite.Statement stmt;

        rc = db.prepare_v2 (sql, -1, out stmt);
        database.assert_query_success(rc, "SQL error");

        var arguments = where.get_bind_arguments ();
        for (int i = 0; i < arguments.length; ++i)
            stmt.bind_text (i + 1, arguments[i]);

        uint32[] event_ids = {};

        while ((rc = stmt.step()) == Sqlite.ROW)
        {
            var id = (uint32) uint64.parse(
                stmt.column_text (EventViewRows.ID));
            //if (!(id in event_ids))
            event_ids += id;
        }
        if (rc != Sqlite.DONE)
        {
            string error_message = "Error in find_event_ids: %d, %s".printf (
                rc, db.errmsg ());
            warning (error_message);
            throw new EngineError.DATABASE_ERROR (error_message);
        }

        return event_ids;
    }

    public GenericArray<Event?> find_events (TimeRange time_range,
        GenericArray<Event> event_templates,
        uint storage_state, uint max_events, uint result_type,
        BusName? sender=null) throws EngineError
    {
        return get_events (find_event_ids_logic (time_range, event_templates,
            storage_state, max_events, result_type, false));
    }

    private struct RelatedUri {
        public uint32 id;
        public int64 timestamp;
        public string uri;
        public int32 counter;
    }

    public string[] find_related_uris (TimeRange time_range,
        GenericArray<Event> event_templates,
        GenericArray<Event> result_event_templates,
        uint storage_state, uint max_results, uint result_type,
        BusName? sender=null) throws EngineError
    {
        /**
        * Return a list of subject URIs commonly used together with events
        * matching the given template, considering data from within the
        * indicated timerange.
        * Only URIs for subjects matching the indicated `result_event_templates`
        * and `result_storage_state` are returned.
        */
        if (result_type == ResultType.MOST_RECENT_EVENTS ||
            result_type == ResultType.LEAST_RECENT_EVENTS)
        {

            // We pick out the ids for relational event so we can set them as
            // roots the ids are taken from the events that match the
            // events_templates
            uint32[] ids = find_event_ids (time_range, event_templates,
                storage_state, 0, ResultType.LEAST_RECENT_EVENTS);

            if (event_templates.length > 0 && ids.length == 0)
            {
                throw new EngineError.INVALID_ARGUMENT (
                    "No results found for the event_templates");
            }

            // Pick out the result_ids for the filtered results we would like to
            // take into account the ids are taken from the events that match
            // the result_event_templates if no result_event_templates are set we
            // consider all results as allowed
            uint32[] result_ids;
            result_ids = find_event_ids (time_range, result_event_templates,
                storage_state, 0, ResultType.LEAST_RECENT_EVENTS);

            // From here we create several graphs with the maximum depth of 2
            // and push all the nodes and vertices (events) in one pot together

            uint32[] pot = new uint32[ids.length + result_ids.length];

            for (uint32 i=0; i < ids.length; i++)
                pot[i] = ids[i];
            for (uint32 i=0; i < result_ids.length; i++)
                pot[ids.length + i] = result_ids[ids.length + i];

            Sqlite.Statement stmt;

            var sql_event_ids = database.get_sql_string_from_event_ids (pot);
            string sql = """
               SELECT id, timestamp, subj_uri FROM event_view 
               WHERE id IN (%s) ORDER BY timestamp ASC
               """.printf (sql_event_ids);

            int rc = db.prepare_v2 (sql, -1, out stmt);

            database.assert_query_success(rc, "SQL error");

            // FIXME: fix this ugly code
            var temp_related_uris = new GenericArray<RelatedUri?>();

            while ((rc = stmt.step()) == Sqlite.ROW)
            {
                RelatedUri ruri = RelatedUri(){
                    id = (uint32) uint64.parse(stmt.column_text (0)),
                    timestamp = stmt.column_int64 (1),
                    uri = stmt.column_text (2),
                    counter = 0
                };
                temp_related_uris.add (ruri);
            }

            // RelatedUri[] related_uris = new RelatedUri[temp_related_uris.length];
            // for (int i=0; i<related_uris.length; i++)
            //    related_uris[i] = temp_related_uris[i];

            if (rc != Sqlite.DONE)
            {
                string error_message =
                    "Error in find_related_uris: %d, %s".printf (
                    rc, db.errmsg ());
                warning (error_message);
                throw new EngineError.DATABASE_ERROR (error_message);
            }

            var uri_counter = new HashTable<string, RelatedUri?>(
                str_hash, str_equal);

            for (int i = 0; i < temp_related_uris.length; i++)
            {
                var window = new GenericArray<unowned RelatedUri?>();

                bool count_in_window = false;
                for (int j = int.max (0, i - 5);
                    j < int.min (i, temp_related_uris.length);
                    j++)
                {
                    window.add(temp_related_uris[j]);
                    if (temp_related_uris[j].id in ids)
                        count_in_window = true;
                }

                if (count_in_window)
                {
                    for (int j = 0; j < window.length; j++)
                    {
                        if (uri_counter.lookup (window[j].uri) == null)
                        {
                            RelatedUri ruri = RelatedUri ()
                            {
                                id = window[j].id,
                                timestamp = window[j].timestamp,
                                uri = window[j].uri,
                                counter = 0
                            };
                            uri_counter.insert (window[j].uri, ruri);
                        }
                        uri_counter.lookup (window[j].uri).counter++;
                        if (uri_counter.lookup (window[j].uri).timestamp
                                < window[j].timestamp)
                        {
                            uri_counter.lookup (window[j].uri).timestamp =
                                window[j].timestamp;
                        }
                    }
                }
            }


            // We have the big hashtable with the structs, now we sort them by
            // most used and limit the result then sort again
            List<RelatedUri?> temp_ruris = new  List<RelatedUri?>();
            List<RelatedUri?> values = new List<RelatedUri?>();

            foreach (var uri in uri_counter.get_values())
                values.append(uri);

            values.sort ((a, b) => a.counter - b.counter);
            values.sort ((a, b) => {
                    int64 delta = a.timestamp - b.timestamp;
                    if (delta < 0) return 1;
                    else if (delta > 0) return -1;
                    else return 0;
                });

            foreach (RelatedUri ruri in values)
            {
                if (temp_ruris.length() < max_results)
                    temp_ruris.append(ruri);
                else
                    break;
            }

            // Sort by recency
            if (result_type == 1)
                temp_ruris.sort ((a, b) => {
                    int64 delta = a.timestamp - b.timestamp;
                    if (delta < 0) return 1;
                    else if (delta > 0) return -1;
                    else return 0;});

            string[] results = new string[temp_ruris.length()];

            int i = 0;
            foreach (var uri in temp_ruris)
            {
                results[i] = uri.uri;
                stdout.printf("%i %lld %s\n", uri.counter,
                    uri.timestamp,
                    uri.uri);
                i++;
            }

            return results;
        }
        else
        {
            throw new EngineError.DATABASE_ERROR ("Unsupported ResultType.");
        }
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

            if (event.origin != "")
                uris.add (event.origin);

            for (int i = 0; i < event.num_subjects(); ++i)
            {
                unowned Subject subject = event.subjects[i];
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

                if ((rc = retrieval_stmt.step()) != Sqlite.ROW) {
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
    public void close ()
    {
        database.close();
    }

    // Used by find_event_ids
    private string group_and_sort (string field, string where_sql,
        bool time_asc=false, bool? count_asc=null,
        string aggregation_type="max")
    {
        string time_sorting = (time_asc) ? "ASC" : "DESC";
        string aggregation_sql = "";
        string order_sql = "";

        if (count_asc != null)
        {
            aggregation_sql = ", COUNT(%s) AS num_events".printf (field);
            order_sql = "num_events %s,".printf ((count_asc) ? "ASC" : "DESC");
        }

        return """
            NATURAL JOIN (
                SELECT %s,
                %s(timestamp) AS timestamp
                %s
                FROM event_view %s
                GROUP BY %s)
            GROUP BY %s
            ORDER BY %s timestamp %s
            """.printf (
                field,
                aggregation_type,
                aggregation_sql,
                where_sql,
                field,
                field,
                order_sql, time_sorting);
    }

    // Used by find_event_ids
    private WhereClause get_where_clause_from_event_templates (
        GenericArray<Event> templates) throws EngineError
    {
        WhereClause where = new WhereClause (WhereClause.Type.OR);
        for (int i = 0; i < templates.length; ++i)
        {
            Event event_template = templates[i];
            where.extend (
                get_where_clause_from_event_template (event_template));
        }
        return where;
    }

    // Used by get_where_clause_from_event_templates
    private WhereClause get_where_clause_from_event_template (Event template)
        throws EngineError
    {
            WhereClause where = new WhereClause (WhereClause.Type.AND);

            // Event ID
            if (template.id != 0)
                where.add ("id=?", template.id.to_string());

            // Interpretation
            if (template.interpretation != "")
            {
                assert_no_wildcard ("interpretation", template.interpretation);
                WhereClause subwhere = get_where_clause_for_symbol (
                    "interpretation", template.interpretation,
                    interpretations_table);
                if (!subwhere.is_empty ())
                    where.extend (subwhere);
            }

            // Manifestation
            if (template.manifestation != "")
            {
                assert_no_wildcard ("manifestation", template.interpretation);
                WhereClause subwhere = get_where_clause_for_symbol (
                    "manifestation", template.manifestation,
                    manifestations_table);
                if (!subwhere.is_empty ())
                   where.extend (subwhere);
            }

            // Actor
            if (template.actor != "")
            {
                string val = template.actor;
                bool like = parse_wildcard (ref val);
                bool negated = parse_negation (ref val);

                if (like)
                    where.add_wildcard_condition ("actor", val, negated);
                else
                    where.add_match_condition ("actor",
                        actors_table.get_id (val), negated);
            }

            // Origin
            if (template.origin != "")
            {
                string val = template.origin;
                bool like = parse_wildcard (ref val);
                bool negated = parse_negation (ref val);

                if (like)
                    where.add_wildcard_condition ("origin", val, negated);
                else
                    where.add_text_condition ("event_origin_uri", val, negated);
            }

            for (int i = 0; i < template.num_subjects(); ++i)
            {
                Subject subject_template = template.subjects[i];

                // Subject interpretation
                if (subject_template.interpretation != "")
                {
                    assert_no_wildcard ("subject interpretation",
                        template.interpretation);
                    WhereClause subwhere = get_where_clause_for_symbol (
                        "subj_interpretation", subject_template.interpretation,
                        interpretations_table);
                    if (!subwhere.is_empty ())
                        where.extend (subwhere);
                }

                // Subject manifestation
                if (subject_template.manifestation != "")
                {
                    assert_no_wildcard ("subject manifestation",
                        subject_template.manifestation);
                    WhereClause subwhere = get_where_clause_for_symbol (
                        "subj_manifestation", subject_template.manifestation,
                        manifestations_table);
                    if (!subwhere.is_empty ())
                        where.extend (subwhere);
                }

                // Mime-Type
                if (subject_template.mimetype != "")
                {
                    string val = subject_template.mimetype;
                    bool like = parse_wildcard (ref val);
                    bool negated = parse_negation (ref val);

                    if (like)
                        where.add_wildcard_condition (
                            "subj_mimetype", val, negated);
                    else
                        where.add_match_condition ("subj_mimetype",
                            mimetypes_table.get_id (val), negated);
                }

                // URI
                if (subject_template.uri != "")
                {
                    string val = subject_template.uri;
                    bool like = parse_wildcard (ref val);
                    bool negated = parse_negation (ref val);

                    if (like)
                        where.add_wildcard_condition ("subj_id", val, negated);
                    else
                        where.add_text_condition ("subj_uri", val, negated);
                }

                // Origin
                if (subject_template.origin != "")
                {
                    string val = subject_template.origin;
                    bool like = parse_wildcard (ref val);
                    bool negated = parse_negation (ref val);

                    if (like)
                        where.add_wildcard_condition (
                            "subj_origin", val, negated);
                    else
                        where.add_text_condition (
                            "subj_origin_uri", val, negated);
                }

                // Text
                if (subject_template.text != "")
                {
                    // Negation and prefix search isn't supported for
                    // subject texts, but "!" and "*" are valid as
                    // plain text characters.
                    where.add_text_condition ("subj_text",
                        subject_template.text, false);
                }

                // Current URI
                if (subject_template.current_uri != "")
                {
                    string val = subject_template.current_uri;
                    bool like = parse_wildcard (ref val);
                    bool negated = parse_negation (ref val);

                    if (like)
                        where.add_wildcard_condition (
                            "subj_id_current", val, negated);
                    else
                        where.add_text_condition (
                            "subj_current_uri", val, negated);
                }

                // Subject storage
                if (subject_template.storage != "")
                {
                    string val = subject_template.storage;
                    assert_no_negation ("subject storage", val);
                    assert_no_wildcard ("subject storage", val);
                    where.add_text_condition ("subj_storage", val);
                }
            }

            return where;
    }

    // Used by get_where_clause_from_event_templates
    /**
     * Check if the value starts with the negation operator. If it does,
     * remove the operator from the value and return true. Otherwise,
     * return false.
     */
    public static bool parse_negation (ref string val)
    {
        if (!val.has_prefix ("!"))
            return false;
        val = val.substring (1); // FIXME: fix for unicode
        return true;
    }

    // Used by get_where_clause_from_event_templates
    /**
     * If the value starts with the negation operator, throw an
     * error.
     */
    protected void assert_no_negation (string field, string val)
        throws EngineError
    {
        if (!val.has_prefix ("!"))
            return;
        string error_message =
            "Field '%s' doesn't support negation".printf (field);
        warning (error_message);
        throw new EngineError.INVALID_ARGUMENT (error_message);
    }

    // Used by get_where_clause_from_event_templates
    /**
     * Check if the value ends with the wildcard character. If it does,
     * remove the wildcard character from the value and return true.
     * Otherwise, return false.
     */
    public static bool parse_wildcard (ref string val)
    {
        if (!val.has_suffix ("*"))
            return false;
        unowned uint8[] val_data = val.data;
        val_data[val_data.length-1] = '\0';
        return true;
    }

    // Used by get_where_clause_from_event_templates
    /**
     * If the value ends with the wildcard character, throw an error.
     */
    protected void assert_no_wildcard (string field, string val)
        throws EngineError
    {
        if (!val.has_suffix ("*"))
            return;
        string error_message =
            "Field '%s' doesn't support prefix search".printf (field);
        warning (error_message);
        throw new EngineError.INVALID_ARGUMENT (error_message);
    }

    protected WhereClause get_where_clause_for_symbol (string table_name,
        string symbol, TableLookup lookup_table) throws EngineError
    {
        string _symbol = symbol;
        bool negated = parse_negation (ref _symbol);
        List<unowned string> symbols = Symbol.get_all_children (symbol);
        symbols.prepend (_symbol);

        WhereClause subwhere = new WhereClause(
            WhereClause.Type.OR, negated);

        /*
        foreach (unowned string uri in symbols)
        {
            subwhere.add_match_condition (table_name,
                lookup_table.get_id (uri));
        }
        */
        if (symbols.length () == 1)
        {
            subwhere.add_match_condition (table_name,
                lookup_table.get_id (_symbol));
        }
        else
        {
            var sb = new StringBuilder ();
            foreach (string uri in symbols)
            {
                sb.append_printf ("%d,", lookup_table.get_id (uri));
            }
            sb.truncate (sb.len - 1);

            string sql = "%s %s IN (%s)".printf(table_name,
                (negated) ? "NOT": "", sb.str);
            subwhere.add(sql);
        }

        return subwhere;
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

    private void delete_from_cache (string table, int64 rowid)
    {
        TableLookup table_lookup;

        if (table == "interpretation")
            table_lookup = interpretations_table;
        else if (table == "manifestation")
            table_lookup = manifestations_table;
        else if (table == "mimetype")
            table_lookup = mimetypes_table;
        else if (table == "actor")
            table_lookup = actors_table;
        else
            return;

        table_lookup.remove((int) rowid);
    }

}

}

// vim:expandtab:ts=4:sw=4
