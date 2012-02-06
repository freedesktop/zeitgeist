/* sql-schema.vala
 *
 * Copyright © 2011 Collabora Ltd.
 *             By Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
 * Copyright © 2011 Canonical Ltd.
 *             By Michal Hruby <michal.hruby@canonical.com>
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

namespace Zeitgeist.SQLite
{

    public class DatabaseSchema : Object
    {

        public const string CORE_SCHEMA = "core";
        public const int CORE_SCHEMA_VERSION = 5;

        public static void ensure_schema (Sqlite.Database database)
            throws EngineError
        {
            int schema_version = Utils.using_in_memory_database () ?
                -1 : get_schema_version (database);

            if (schema_version == -1)
            {
                // most likely a new DB
                create_schema (database);
            }
            else if (schema_version == 4)
            {
                // DB from latest Python Zeitgeist, which we can "upgrade"
                try
                {
                  Utils.backup_database ();
                }
                catch (Error backup_error)
                {
                    var msg = "Database backup failed: " + backup_error.message;
                    throw new EngineError.BACKUP_FAILED (msg);
                }
                create_schema (database);
            }
            else if (schema_version < CORE_SCHEMA_VERSION)
            {
                throw new EngineError.DATABASE_ERROR (
                    "Unable to upgrade from schema version %d".printf (
                        schema_version));
            }
        }

        public static int get_schema_version (Sqlite.Database database)
        {
          var sql = "SELECT version FROM schema_version WHERE schema='core'";
          int schema_version = -1;
          database.exec (sql,
              (n_cols, values, column_names) =>
              {
                  if (values[0] != null)
                  {
                      schema_version = int.parse (values[0]);
                  }
                  return 0;
              }, null);

          // we don't really care about the return value of exec, the result
          // will be -1 if something went wrong anyway
          debug ("schema_version is %d", schema_version);

          return schema_version;
        }

        public static void create_schema (Sqlite.Database database)
            throws EngineError
        {
            if (!Utils.using_in_memory_database ())
                FileUtils.chmod (Utils.get_database_file_path (), 0600);

            exec_query (database, "PRAGMA journal_mode = WAL");
            exec_query (database, "PRAGMA locking_mode = NORMAL");

            // URI
            exec_query (database, """
                CREATE TABLE IF NOT EXISTS uri (
                    id INTEGER PRIMARY KEY,
                    value VARCHAR UNIQUE
                )
                """);
            exec_query (database, """
                CREATE UNIQUE INDEX IF NOT EXISTS uri_value ON uri(value)
                """);

            // Interpretation
            exec_query (database, """
                CREATE TABLE IF NOT EXISTS interpretation (
                    id INTEGER PRIMARY KEY,
                    value VARCHAR UNIQUE
                )
                """);
            exec_query (database, """
                CREATE UNIQUE INDEX IF NOT EXISTS interpretation_value
                    ON interpretation(value)
                """);

            // Manifestation
            exec_query (database, """
                CREATE TABLE IF NOT EXISTS manifestation (
                    id INTEGER PRIMARY KEY,
                    value VARCHAR UNIQUE
                )
                """);
            exec_query (database, """
                CREATE UNIQUE INDEX IF NOT EXISTS manifestation_value
                    ON manifestation(value)
                """);

            // Mime-Type
            exec_query (database, """
                CREATE TABLE IF NOT EXISTS mimetype (
                    id INTEGER PRIMARY KEY,
                    value VARCHAR UNIQUE
                )
                """);
            exec_query (database, """
                CREATE UNIQUE INDEX IF NOT EXISTS mimetype_value
                    ON mimetype(value)
                """);

            // Actor
            exec_query (database, """
                CREATE TABLE IF NOT EXISTS actor (
                    id INTEGER PRIMARY KEY,
                    value VARCHAR UNIQUE
                )
                """);
            exec_query (database, """
                CREATE UNIQUE INDEX IF NOT EXISTS actor_value
                    ON actor(value)
                """);

            // Text
            exec_query (database, """
                CREATE TABLE IF NOT EXISTS text (
                    id INTEGER PRIMARY KEY,
                    value VARCHAR UNIQUE
                )
                """);
            exec_query (database, """
                CREATE UNIQUE INDEX IF NOT EXISTS text_value
                    ON text(value)
                """);

            // Payload
            // (There's no value index for payloads, they can only be fetched
            // by ID).
            exec_query (database, """
                CREATE TABLE IF NOT EXISTS payload
                    (id INTEGER PRIMARY KEY, value BLOB)
                """);

            // Storage
            exec_query (database, """
                CREATE TABLE IF NOT EXISTS storage (
                    id INTEGER PRIMARY KEY,
                    value VARCHAR UNIQUE,
                    state INTEGER,
                    icon VARCHAR,
                    display_name VARCHAR
                )
                """);
            exec_query (database, """
                CREATE UNIQUE INDEX IF NOT EXISTS storage_value
                    ON storage(value)
                """);

            // Event
            // This is the primary table for log statements. Note that:
            //  - event.id is NOT unique, each subject has a separate row;
            //  - timestamps are integers;
            //  - (event_)origin and subj_id_current are at the end of the
            //    table, for backwards-compatibility reasons.
            exec_query (database, """
                CREATE TABLE IF NOT EXISTS event (
                    id INTEGER,
                    timestamp INTEGER,
                    interpretation INTEGER,
                    manifestation INTEGER,
                    actor INTEGER,
                    payload INTEGER,
                    subj_id INTEGER,
                    subj_interpretation INTEGER,
                    subj_manifestation INTEGER,
                    subj_origin INTEGER,
                    subj_mimetype INTEGER,
                    subj_text INTEGER,
                    subj_storage INTEGER,
                    origin INTEGER,
                    subj_id_current INTEGER,
                    CONSTRAINT interpretation_fk
                        FOREIGN KEY(interpretation)
                        REFERENCES interpretation(id)
                        ON DELETE CASCADE,
                    CONSTRAINT manifestation_fk
                        FOREIGN KEY(manifestation)
                        REFERENCES manifestation(id)
                        ON DELETE CASCADE,
                    CONSTRAINT actor_fk
                        FOREIGN KEY(actor)
                        REFERENCES actor(id)
                        ON DELETE CASCADE,
                    CONSTRAINT origin_fk
                        FOREIGN KEY(origin)
                        REFERENCES uri(id)
                        ON DELETE CASCADE,
                    CONSTRAINT payload_fk
                        FOREIGN KEY(payload)
                        REFERENCES payload(id)
                        ON DELETE CASCADE,
                    CONSTRAINT subj_id_fk
                        FOREIGN KEY(subj_id)
                        REFERENCES uri(id)
                        ON DELETE CASCADE,
                    CONSTRAINT subj_id_current_fk
                        FOREIGN KEY(subj_id_current)
                        REFERENCES uri(id)
                        ON DELETE CASCADE,
                    CONSTRAINT subj_interpretation_fk
                        FOREIGN KEY(subj_interpretation)
                        REFERENCES interpretation(id)
                        ON DELETE CASCADE,
                    CONSTRAINT subj_manifestation_fk
                        FOREIGN KEY(subj_manifestation)
                        REFERENCES manifestation(id)
                        ON DELETE CASCADE,
                    CONSTRAINT subj_origin_fk
                        FOREIGN KEY(subj_origin)
                        REFERENCES uri(id)
                        ON DELETE CASCADE,
                    CONSTRAINT subj_mimetype_fk
                        FOREIGN KEY(subj_mimetype)
                        REFERENCES mimetype(id)
                        ON DELETE CASCADE,
                    CONSTRAINT subj_text_fk
                        FOREIGN KEY(subj_text)
                        REFERENCES text(id)
                        ON DELETE CASCADE,
                    CONSTRAINT subj_storage_fk
                        FOREIGN KEY(subj_storage)
                        REFERENCES storage(id)
                        ON DELETE CASCADE,
                    CONSTRAINT unique_event UNIQUE (timestamp, interpretation,
                        manifestation, actor, subj_id)
                )
                """);
            exec_query (database, """
                CREATE INDEX IF NOT EXISTS event_id
                    ON event(id)
                """);
            exec_query (database, """
                CREATE INDEX IF NOT EXISTS event_timestamp
                    ON event(timestamp)
                """);
            exec_query (database, """
                CREATE INDEX IF NOT EXISTS event_interpretation
                    ON event(interpretation)
                """);
            exec_query (database, """
                CREATE INDEX IF NOT EXISTS event_manifestation
                    ON event(manifestation)
                """);
            exec_query (database, """
                CREATE INDEX IF NOT EXISTS event_actor
                    ON event(actor)
                """);
            exec_query (database, """
                CREATE INDEX IF NOT EXISTS event_origin
                    ON event(origin)
                """);
            exec_query (database, """
                CREATE INDEX IF NOT EXISTS event_subj_id
                    ON event(subj_id)
                """);
            exec_query (database, """
                CREATE INDEX IF NOT EXISTS event_subj_id_current
                    ON event(subj_id_current)
                """);
            exec_query (database, """
                CREATE INDEX IF NOT EXISTS event_subj_interpretation
                    ON event(subj_interpretation)
                """);
            exec_query (database, """
                CREATE INDEX IF NOT EXISTS event_subj_manifestation
                    ON event(subj_manifestation)
                """);
            exec_query (database, """
                CREATE INDEX IF NOT EXISTS event_subj_origin
                    ON event(subj_origin)
                """);
            exec_query (database, """
                CREATE INDEX IF NOT EXISTS event_subj_mimetype
                    ON event(subj_mimetype)
                """);
            exec_query (database, """
                CREATE INDEX IF NOT EXISTS event_subj_text
                    ON event(subj_text)
                """);
            exec_query (database, """
                CREATE INDEX IF NOT EXISTS event_subj_storage
                    ON event(subj_storage)
                """);

            // TODO: create deletion triggers
            /*
            exec_query (database, """
                """);
            */

            // Extensions
            exec_query (database, """
                CREATE TABLE IF NOT EXISTS extensions_conf (
                    extension VARCHAR,
                    key VARCHAR,
                    value BLOB,
                    CONSTRAINT unique_extension UNIQUE (extension, key)
                )
                """);
            exec_query (database, """
                CREATE UNIQUE INDEX IF NOT EXISTS extensions_conf_key
                    ON extensions_conf (extension, key)
                """);

            // Performance note: the subqueries here are provided for lookup
            // only. For querying, use explicit "WHERE x IN (SELECT id ...)"
            // subqueries.
            exec_query (database, "DROP VIEW IF EXISTS event_view");
            exec_query (database, """
                CREATE VIEW IF NOT EXISTS event_view AS
                    SELECT event.id,
                        event.timestamp,
                        event.interpretation,
                        event.manifestation,
                        event.actor,
                        (SELECT value FROM payload
                            WHERE payload.id=event.payload)
                            AS payload,
                        (SELECT value FROM uri
                            WHERE uri.id=event.subj_id)
                            AS subj_uri,
                        event.subj_id, --//this points to an id in the uri table
                        event.subj_interpretation,
                        event.subj_manifestation,
                        event.subj_origin,
                        (SELECT value FROM uri
                            WHERE uri.id=event.subj_origin)
                            AS subj_origin_uri,
                        event.subj_mimetype,
                        (SELECT value FROM text
                            WHERE text.id = event.subj_text)
                            AS subj_text,
                        (SELECT value FROM storage
                            WHERE storage.id=event.subj_storage)
                            AS subj_storage,
                        (SELECT state FROM storage
                            WHERE storage.id=event.subj_storage)
                            AS subj_storage_state,
                        event.origin,
                        (SELECT value FROM uri
                            WHERE uri.id=event.origin)
                            AS event_origin_uri,
                        (SELECT value FROM uri
                            WHERE uri.id=event.subj_id_current)
                            AS subj_current_uri,
                        event.subj_id_current,
                        event.subj_text AS subj_text_id,
                        event.subj_storage AS subj_storage_id,
                        (SELECT value FROM actor
                            WHERE actor.id=event.actor)
                            AS actor_uri
                    FROM event
                """);

            // Set schema version
            exec_query (database, """
                CREATE TABLE IF NOT EXISTS schema_version (
                    schema VARCHAR PRIMARY KEY ON CONFLICT REPLACE,
                    version INT
                )
                """);

            /* The 'ON CONFLICT REPLACE' on the PK converts INSERT to UPDATE
             * when appriopriate */
            var schema_sql = "INSERT INTO schema_version VALUES ('%s', %d)"
                .printf (CORE_SCHEMA, CORE_SCHEMA_VERSION);
            exec_query (database, schema_sql);

        }

        /**
         * Execute the given SQL. If the query doesn't succeed, throw
         * an error.
         *
         * @param database the database on which to run the query
         * @param sql the SQL query to run
         */
        private static void exec_query (Sqlite.Database database,
            string sql) throws EngineError
        {
            int rc = database.exec (sql);
            if (rc != Sqlite.OK)
            {
                if (rc == Sqlite.CORRUPT)
                {
                    throw new EngineError.DATABASE_CORRUPT (database.errmsg ());
                }
                else
                {
                    const string fmt_str = "Can't create database: %d, %s\n\n" +
                        "Unable to execute SQL:\n%s";
                    var err_msg = fmt_str.printf (rc, database.errmsg (), sql);
                    throw new EngineError.DATABASE_ERROR (err_msg);
                }
            }
        }

    }

}
