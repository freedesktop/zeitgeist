# upgrading from db version 3 to 4

# Changes:
#
# * Appends to new rows to the 'storage' table that is needed by the new
#   storagemonitor extension. This is actually backwards compatible.

from zeitgeist.datamodel import StorageState

def run(cursor):
	# Add the new columns for the storage table
	cursor.execute ("ALTER TABLE storage ADD COLUMN icon VARCHAR")
	cursor.execute ("ALTER TABLE storage ADD COLUMN display_name VARCHAR")
	
	# Add the default storage mediums 'UNKNOWN' and 'local' and set them
	# as always available
	cursor.execute("INSERT INTO storage (value, state) VALUES ('unknown', ?)", (StorageState.Available,))
	unknown_storage_rowid = cursor.lastrowid
	cursor.execute("INSERT INTO storage (value, state) VALUES ('local', ?)", (StorageState.Available,))
	
	# Set all subjects that are already in the DB to have 'unknown' storage
	# That way they will always be marked as available. We don't have a chance
	# of properly backtracking all items, so we use this as a clutch
	cursor.execute("UPDATE event SET subj_storage=? WHERE subj_storage IS NULL", (unknown_storage_rowid, ))

	# Add new colums to the events table: subj_current_id and (event) origin
	# Since SQLite doesn't support "ALTER TABLE ... ADD CONSTRAINT" we have
	# to create the table anew. See: http://www.sqlite.org/faq.html#q11
	cursor.execute("ALTER TABLE event RENAME TO event_old");
	cursor.execute("""
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
			CONSTRAINT interpretation_fk FOREIGN KEY(interpretation)
				REFERENCES interpretation(id) ON DELETE CASCADE,
			CONSTRAINT manifestation_fk FOREIGN KEY(manifestation)
				REFERENCES manifestation(id) ON DELETE CASCADE,
			CONSTRAINT actor_fk FOREIGN KEY(actor)
				REFERENCES actor(id) ON DELETE CASCADE,
			CONSTRAINT origin_fk FOREIGN KEY(origin)
				REFERENCES uri(id) ON DELETE CASCADE,
			CONSTRAINT payload_fk FOREIGN KEY(payload)
				REFERENCES payload(id) ON DELETE CASCADE,
			CONSTRAINT subj_id_fk FOREIGN KEY(subj_id)
				REFERENCES uri(id) ON DELETE CASCADE,
			CONSTRAINT subj_id_current_fk FOREIGN KEY(subj_id_current)
				REFERENCES uri(id) ON DELETE CASCADE,
			CONSTRAINT subj_interpretation_fk FOREIGN KEY(subj_interpretation)
				REFERENCES interpretation(id) ON DELETE CASCADE,
			CONSTRAINT subj_manifestation_fk FOREIGN KEY(subj_manifestation)
				REFERENCES manifestation(id) ON DELETE CASCADE,
			CONSTRAINT subj_origin_fk FOREIGN KEY(subj_origin)
				REFERENCES uri(id) ON DELETE CASCADE,
			CONSTRAINT subj_mimetype_fk FOREIGN KEY(subj_mimetype)
				REFERENCES mimetype(id) ON DELETE CASCADE,
			CONSTRAINT subj_text_fk FOREIGN KEY(subj_text)
				REFERENCES text(id) ON DELETE CASCADE,
			CONSTRAINT subj_storage_fk FOREIGN KEY(subj_storage)
				REFERENCES storage(id) ON DELETE CASCADE,
			CONSTRAINT unique_event UNIQUE (timestamp, interpretation, manifestation, actor, subj_id)
		)
		""")
	cursor.execute("""
		CREATE INDEX IF NOT EXISTS event_origin
			ON event(origin)""")
	cursor.execute("""
		CREATE INDEX IF NOT EXISTS event_subj_id_current
			ON event(subj_id_current)""")
	# Copy the old data over. Additionally, we initialize subj_id_current to
	# the same value as in subj_id.
	cursor.execute("""
		INSERT INTO event
		SELECT
			id, timestamp, interpretation, manifestation, actor, NULL,
			payload, subj_id, subj_id AS subj_id_current, subj_interpretation,
			subj_manifestation, subj_origin, subj_mimetype, subj_text,
			subj_storage
		FROM event_old
		""")
	# Finally, delete the old table
	cursor.execute("DROP TABLE event_old")

	# Delete triggers that have changed (they'll be created anew
	# in sql.create_db()
	cursor.execute("DROP TRIGGER IF EXISTS fkdc_event_uri_1")
	cursor.execute("DROP TRIGGER IF EXISTS fkdc_event_uri_2")
	
	cursor.connection.commit()
