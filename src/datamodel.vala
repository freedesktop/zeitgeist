/* zeitgeist-daemon.vala
 *
 * Copyright © 2011 Collabora Ltd.
 *             By Seif Lotfy <seif@lotfy.com>
 *             By Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 */

public enum ResultType {
	MostRecentEvents, //0, All events with the most recent events first
	LeastRecentEvents, //1, All events with the oldest ones first"
	MostRecentSubjects, //2, One event for each subject only,
											// ordered with the most recent events first
	LeastRecentSubjects, //3, One event for each subject only,
											// ordered with oldest events first
	MostPopularSubjects, //4, One event for each subject only, 
											// orderedby the popularity of the subject
	LeastPopularSubjects, //5, One event for each subject only, 
											// orderedascendingly by popularity of the subject
	MostPopularActor, //6, The last event of each different actor, 
											// orderedby the popularity of the actor
	LeastPopularActor, //7, The last event of each different actor, 
											// orderedascendingly by the popularity of the actor
	MostRecentActor, //8, The Actor that has been used to most recently
	LeastRecentActor, //9, The Actor that has been used to least recently
	MostRecentOrigin, //10, The last event of each different subject origin
	LeastRecentOrigin, //11, The last event of each different subject origin, 
											// orderedby least recently used first
	MostPopularOrigin, //12, The last event of each different subject origin, 
											// orderedby the popularity of the origins")
	LeastPopularOrigin, //13, The last event of each different subject origin, 
											// orderedascendingly by the popularity of the origin
	OldestActor, //14, The first event of each different actor 
	MostRecentSubjectInterpretation, //15, One event for each subject interpretation only, 
											// orderedwith the most recent events first
	LeastRecentSubjectInterpretation, //16, One event for each subject interpretation only, 
											// orderedwith the least recent events first
	MostPopularSubjectInterpretation, //17, One event for each subject interpretation only, 
											// orderedby the popularity of the subject interpretation
	LeastPopularSubjectInterpretation, //18, One event for each subject interpretation only, 
											// orderedascendingly by popularity of the subject interpretation
	MostRecentMimeType, //19, One event for each mimetype only 
											// orderedwith the most recent events first
	LeastRecentMimeType, //20, One event for each mimetype only 
											// orderedwith the least recent events first
	MostPopularMimeType, //21, One event for each mimetype only 
											// orderedby the popularity of the mimetype
	LeastPopularMimeType, //22, One event for each mimetype only 
											// orderedascendingly by popularity of the mimetype
	MostRecentCurrentUri, //23, One event for each subject only by current_uri instead of uri 
											// orderedwith the most recent events first
	LeastRecentCurrentUri, //24, One event for each subject only by current_uri instead of uri 
											// orderedwith oldest events first
	MostPopularCurrentUri, //25, One event for each subject only by current_uri instead of uri 
											// orderedby the popularity of the subject
	LeastPopularCurrentUri, //26, One event for each subject only by current_uri instead of uri 
											// orderedascendingly by popularity of the subject
	MostRecentEventOrigin, //27, The last event of each different origin 
	LeastRecentEventOrigin, //28, The last event of each different origin, 
											// orderedby least recently used first
	MostPopularEventOrigin, //29, The last event of each different origin, 
											// orderedby the popularity of the origins
	LeastPopularEventOrigin, //30, The last event of each different origin, 
											// orderedascendingly by the popularity of the origin
}

public class Event : Object {

	uint32?   id;
	int64     timestamp;
	string    interpretation;
	string    manifestation;
	string    actor;
	string    origin;
	
	Subject[] subjects;
	uint8[]   payload;

	public Event.from_variant (Variant event_variant) {
		stdout.printf("VAR: %u\n\n", event_variant.get_uint32());
	}

}

public class Subject : Object {
	string uri;
	string interpretation;
	string manifestation;
	string mimetype;
	string origin;
	string text;
	string storage;
}
