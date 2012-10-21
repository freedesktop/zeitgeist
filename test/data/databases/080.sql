PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE uri
			(id INTEGER PRIMARY KEY, value VARCHAR UNIQUE);
INSERT INTO "uri" VALUES(1,'file:///tmp');
INSERT INTO "uri" VALUES(2,'http://www.google.de');
INSERT INTO "uri" VALUES(3,'belly');
INSERT INTO "uri" VALUES(5,'file:///tmp/foo.txt');
INSERT INTO "uri" VALUES(6,'big bang');
CREATE TABLE interpretation
			(id INTEGER PRIMARY KEY, value VARCHAR UNIQUE);
INSERT INTO "interpretation" VALUES(1,'stfu:OpenEvent');
INSERT INTO "interpretation" VALUES(2,'stfu:Document');
INSERT INTO "interpretation" VALUES(3,'stfu:ShalalalalaEvent');
INSERT INTO "interpretation" VALUES(4,'stfu:Image');
INSERT INTO "interpretation" VALUES(5,'stfu:FoobarEvent');
INSERT INTO "interpretation" VALUES(6,'stfu:Test');
CREATE TABLE manifestation
			(id INTEGER PRIMARY KEY, value VARCHAR UNIQUE);
INSERT INTO "manifestation" VALUES(1,'stfu:YourActivity');
INSERT INTO "manifestation" VALUES(2,'http://www.semanticdesktop.org/ontologies/2007/03/22/nfo#RemoteDataObject');
INSERT INTO "manifestation" VALUES(3,'stfu:BooActivity');
INSERT INTO "manifestation" VALUES(4,'stfu:Ethereal');
INSERT INTO "manifestation" VALUES(5,'stfu:SomeActivity');
CREATE TABLE mimetype
			(id INTEGER PRIMARY KEY, value VARCHAR UNIQUE);
INSERT INTO "mimetype" VALUES(1,'meat/raw');
INSERT INTO "mimetype" VALUES(2,'text/plain');
CREATE TABLE actor
			(id INTEGER PRIMARY KEY, value VARCHAR UNIQUE);
INSERT INTO "actor" VALUES(1,'firefox');
INSERT INTO "actor" VALUES(2,'geany');
INSERT INTO "actor" VALUES(3,'gedit');
CREATE TABLE text
			(id INTEGER PRIMARY KEY, value VARCHAR UNIQUE);
INSERT INTO "text" VALUES(1,'this item has not text... rly!');
CREATE TABLE payload
			(id INTEGER PRIMARY KEY, value BLOB);
CREATE TABLE storage
			(id INTEGER PRIMARY KEY,
			 value VARCHAR UNIQUE,
			 state INTEGER,
			 icon VARCHAR,
			 display_name VARCHAR);
INSERT INTO "storage" VALUES(1,'net',0,NULL,NULL);
INSERT INTO "storage" VALUES(2,'368c991f-8b59-4018-8130-3ce0ec944157',NULL,NULL,NULL);
CREATE TABLE event (
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
		);
INSERT INTO "event" VALUES(1,1347652042579,1,1,1,'',2,2,2,1,1,1,2,NULL,2);
INSERT INTO "event" VALUES(2,143,3,3,2,'',5,4,4,1,2,1,2,3,5);
INSERT INTO "event" VALUES(3,133,5,5,3,'',2,6,2,1,2,1,2,6,2);
CREATE TABLE schema_version
			(schema VARCHAR PRIMARY KEY ON CONFLICT REPLACE, version INT);
INSERT INTO "schema_version" VALUES('core',4);
CREATE UNIQUE INDEX uri_value ON uri(value);
CREATE UNIQUE INDEX interpretation_value
			ON interpretation(value);
CREATE UNIQUE INDEX manifestation_value
			ON manifestation(value);
CREATE UNIQUE INDEX mimetype_value
			ON mimetype(value);
CREATE UNIQUE INDEX actor_value
			ON actor(value);
CREATE UNIQUE INDEX text_value
			ON text(value);
CREATE UNIQUE INDEX storage_value
			ON storage(value);
CREATE INDEX event_id
			ON event(id);
CREATE INDEX event_timestamp
			ON event(timestamp);
CREATE INDEX event_interpretation
			ON event(interpretation);
CREATE INDEX event_manifestation
			ON event(manifestation);
CREATE INDEX event_actor
			ON event(actor);
CREATE INDEX event_origin
			ON event(origin);
CREATE INDEX event_subj_id
			ON event(subj_id);
CREATE INDEX event_subj_id_current
			ON event(subj_id_current);
CREATE INDEX event_subj_interpretation
			ON event(subj_interpretation);
CREATE INDEX event_subj_manifestation
			ON event(subj_manifestation);
CREATE INDEX event_subj_origin
			ON event(subj_origin);
CREATE INDEX event_subj_mimetype
			ON event(subj_mimetype);
CREATE INDEX event_subj_text
			ON event(subj_text);
CREATE INDEX event_subj_storage
			ON event(subj_storage);
CREATE TRIGGER fkdc_event_interpretation
				BEFORE DELETE ON event
				WHEN ((SELECT COUNT(*) FROM event WHERE interpretation=OLD.interpretation) < 2)
				BEGIN
					DELETE FROM interpretation WHERE id=OLD.interpretation;
				END;
CREATE TRIGGER fkdc_event_subj_interpretation
				BEFORE DELETE ON event
				WHEN ((SELECT COUNT(*) FROM event WHERE subj_interpretation=OLD.subj_interpretation) < 2)
				BEGIN
					DELETE FROM interpretation WHERE id=OLD.subj_interpretation;
				END;
CREATE TRIGGER fkdc_event_manifestation
				BEFORE DELETE ON event
				WHEN ((SELECT COUNT(*) FROM event WHERE manifestation=OLD.manifestation) < 2)
				BEGIN
					DELETE FROM manifestation WHERE id=OLD.manifestation;
				END;
CREATE TRIGGER fkdc_event_subj_manifestation
				BEFORE DELETE ON event
				WHEN ((SELECT COUNT(*) FROM event WHERE subj_manifestation=OLD.subj_manifestation) < 2)
				BEGIN
					DELETE FROM manifestation WHERE id=OLD.subj_manifestation;
				END;
CREATE TRIGGER fkdc_event_actor
				BEFORE DELETE ON event
				WHEN ((SELECT COUNT(*) FROM event WHERE actor=OLD.actor) < 2)
				BEGIN
					DELETE FROM actor WHERE id=OLD.actor;
				END;
CREATE TRIGGER fkdc_event_payload
				BEFORE DELETE ON event
				WHEN ((SELECT COUNT(*) FROM event WHERE payload=OLD.payload) < 2)
				BEGIN
					DELETE FROM payload WHERE id=OLD.payload;
				END;
CREATE TRIGGER fkdc_event_subj_mimetype
				BEFORE DELETE ON event
				WHEN ((SELECT COUNT(*) FROM event WHERE subj_mimetype=OLD.subj_mimetype) < 2)
				BEGIN
					DELETE FROM mimetype WHERE id=OLD.subj_mimetype;
				END;
CREATE TRIGGER fkdc_event_subj_text
				BEFORE DELETE ON event
				WHEN ((SELECT COUNT(*) FROM event WHERE subj_text=OLD.subj_text) < 2)
				BEGIN
					DELETE FROM text WHERE id=OLD.subj_text;
				END;
CREATE TRIGGER fkdc_event_subj_storage
				BEFORE DELETE ON event
				WHEN ((SELECT COUNT(*) FROM event WHERE subj_storage=OLD.subj_storage) < 2)
				BEGIN
					DELETE FROM storage WHERE id=OLD.subj_storage;
				END;
CREATE TRIGGER fkdc_event_uri_1
			BEFORE DELETE ON event
			WHEN ((
				SELECT COUNT(*)
				FROM event
				WHERE
					origin=OLD.subj_id
					OR subj_id=OLD.subj_id
					OR subj_id_current=OLD.subj_id
					OR subj_origin=OLD.subj_id
				) < 2)
			BEGIN
				DELETE FROM uri WHERE id=OLD.subj_id;
			END;
CREATE TRIGGER fkdc_event_uri_2
			BEFORE DELETE ON event
			WHEN ((
				SELECT COUNT(*)
				FROM event
				WHERE
					origin=OLD.subj_origin
					OR subj_id=OLD.subj_origin
					OR subj_id_current=OLD.subj_origin
					OR subj_origin=OLD.subj_origin
				) < 2)
			BEGIN
				DELETE FROM uri WHERE id=OLD.subj_origin;
			END;
CREATE TRIGGER fkdc_event_uri_3
			BEFORE DELETE ON event
			WHEN ((
				SELECT COUNT(*)
				FROM event
				WHERE
					origin=OLD.subj_id_current
					OR subj_id=OLD.subj_id_current
					OR subj_id_current=OLD.subj_id_current
					OR subj_origin=OLD.subj_id_current
				) < 2)
			BEGIN
				DELETE FROM uri WHERE id=OLD.subj_id_current;
			END;
CREATE TRIGGER fkdc_event_uri_4
			BEFORE DELETE ON event
			WHEN ((
				SELECT COUNT(*)
				FROM event
				WHERE
					origin=OLD.origin
					OR subj_id=OLD.origin
					OR subj_id_current=OLD.origin
					OR subj_origin=OLD.origin
				) < 2)
			BEGIN
				DELETE FROM uri WHERE id=OLD.origin;
			END;
CREATE VIEW event_view AS
			SELECT event.id,
				event.timestamp,
				event.interpretation,
				event.manifestation,
				event.actor,
				(SELECT value FROM payload WHERE payload.id=event.payload)
					AS payload,
				(SELECT value FROM uri WHERE uri.id=event.subj_id)
					AS subj_uri,
				event.subj_id, -- #this directly points to an id in the uri table
				event.subj_interpretation,
				event.subj_manifestation,
				event.subj_origin,
				(SELECT value FROM uri WHERE uri.id=event.subj_origin)
					AS subj_origin_uri,
				event.subj_mimetype,
				(SELECT value FROM text WHERE text.id = event.subj_text)
					AS subj_text,
				(SELECT value FROM storage
					WHERE storage.id=event.subj_storage) AS subj_storage,
				(SELECT state FROM storage
					WHERE storage.id=event.subj_storage) AS subj_storage_state,
				event.origin,
				(SELECT value FROM uri WHERE uri.id=event.origin)
					AS event_origin_uri,
				(SELECT value FROM uri WHERE uri.id=event.subj_id_current)
					AS subj_current_uri,
				event.subj_id_current
			FROM event
;
COMMIT;
