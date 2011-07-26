/* zeitgeist-daemon.vala
 *
 * Copyright © 2011 Collabora Ltd.
 *             By Seif Lotfy <seif@lotfy.com>
 *             By Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
 * Copyright © 2011 Manish Sinha <manishsinha@ubuntu.com>
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
	MostRecentEvents,					// 0	All events with the most recent
										//		events first
	LeastRecentEvents,					// 1	All events with the oldest ones
										//		first
	MostRecentSubjects,					// 2	One event for each subject only,
										//		ordered with the most recent
										//		events first
	LeastRecentSubjects, 				// 3	One event for each subject only,
										//		ordered with oldest events first
	MostPopularSubjects, 				// 4	One event for each subject only,
										//		ordered by the popularity of the
										//		subject
	LeastPopularSubjects,				// 5	One event for each subject only,
										//		ordered ascendingly by
										//		popularity of the subject
	MostPopularActor,					// 6	The last event of each different
										//		actor ordered by the popularity
										//		of the actor
	LeastPopularActor, 					// 7	The last event of each different
										//		actor, ordered ascendingly by
										//		the popularity of the actor
	MostRecentActor,					// 8	The actor that has been used to
										//		most recently
	LeastRecentActor,					// 9	The actor that has been used to
										//		least recently
	MostRecentOrigin,					// 10	The last event of each different
										//		subject origin.
	LeastRecentOrigin,					// 11	The last event of each different
										//		subject origin, ordered by least
										//		recently used first
	MostPopularOrigin,					// 12	The last event of each different
										//		subject origin, ordered by the
										//		popularity of the origins")
	LeastPopularOrigin,					// 13	The last event of each different
										//		subject origin, ordered
										//		ascendingly by the popularity
										//		of the origin
	OldestActor,						// 14	The first event of each
										//		different actor
	MostRecentSubjectInterpretation,	// 15	One event for each subject
										//		interpretation only, ordered
										//		with the most recent events
										//		first
	LeastRecentSubjectInterpretation,	// 16	One event for each subject
										//		interpretation only, ordered
										//		with the least recent events
										//		first
	MostPopularSubjectInterpretation,	// 17	One event for each subject
										//		interpretation only, ordered by
										//		the popularity of the subject
										//		interpretation
	LeastPopularSubjectInterpretation,	// 18	One event for each subject
										//		interpretation only, ordered
										//		ascendingly by popularity of
										//		the subject interpretation
	MostRecentMimeType,					// 19	One event for each mimetype only
										//		ordered with the most recent
										//		events first
	LeastRecentMimeType,				// 20	One event for each mimetype only
										//		ordered with the least recent
										//		events first
	MostPopularMimeType,				// 21	One event for each mimetype only
										//		ordered by the popularity of the
										//		mimetype
	LeastPopularMimeType,				// 22	One event for each mimetype only
										//		ordered ascendingly by
										//		popularity of the mimetype
	MostRecentCurrentUri,				// 23	One event for each subject only
										//		by current_uri instead of uri
										//		ordered with the most recent
										//		events first
	LeastRecentCurrentUri,				// 24	One event for each subject only
										//		by current_uri instead of uri
										//		ordered with oldest events first
	MostPopularCurrentUri,				// 25	One event for each subject only
										//		by current_uri instead of uri
										//		ordered by the popularity of the
										//		subject
	LeastPopularCurrentUri,				// 26	One event for each subject only
										//		by current_uri instead of uri
										//		ordered ascendingly by
										//		popularity of the subject
	MostRecentEventOrigin,				// 27	The last event of each different
										//		origin
	LeastRecentEventOrigin,				// 28	The last event of each different
										//		origin, ordered by least
										//		recently used first
	MostPopularEventOrigin,				// 29	The last event of each different
										//		origin ordered by the popularity
										//		of the origins
	LeastPopularEventOrigin,			// 30	The last event of each different
										//		origin, ordered ascendingly by
										//		the popularity of the origin
}

/*
 * An enumeration class used to define how query results should
 * be returned from the Zeitgeist engine.
 */
public enum RelevantResultType
{
	Recent = 0, 		// All uris with the most recent uri first
	Related = 1, 		// All uris with the most related one first
}

/* 
 * Enumeration class defining the possible values for the storage
 * state of an event subject.
 * 
 * The StorageState enumeration can be used to control whether or
 * not matched events must have their subjects available to the user.
 * Fx. not including deleted files, files on unplugged USB drives,
 * files available only when a network is available etc.
 */
public enum StorageState
{
	NotAvailable = 0, 	// The storage medium of the events
						// subjects must not be available to the user
	Available = 1, 		// The storage medium of all event subjects
						// must be immediately available to the user
	Any = 2				// The event subjects may or may not be available
}

public class Event : Object
{
	public uint32    id { get; set; }
	public int64     timestamp { get; set; }
	public string    interpretation { get; set; }
	public string    manifestation { get; set; }
	public string    actor { get; set; }
	public string    origin { get; set; }
	
	public GenericArray<Subject> subjects { get; set; }
	public ByteArray payload { get; set; }

	public Event.from_variant (Variant event_variant) { // (asaasay)
		VariantIter iter = event_variant.iterator();
		
		assert (iter.n_children() == 3);
		VariantIter event_array = iter.next_value().iterator();
		VariantIter subjects_array = iter.next_value().iterator();
		VariantIter payload_array = iter.next_value().iterator();
		
		assert (event_array.n_children() >= 6);
		id = (uint32) event_array.next_value();
		timestamp = (int64) event_array.next_value();
		interpretation = (string) event_array.next_value();
		manifestation = (string) event_array.next_value();
		actor = (string) event_array.next_value();
		origin = (string) event_array.next_value();
		
		subjects = new GenericArray<Subject>();
		for (int i = 0; i < subjects_array.n_children(); ++i) {
			Variant subject_variant = subjects_array.next_value();
			subjects.add(new Subject.from_variant(subject_variant));
		}
		
		// Parse payload...
	}

}

public class Subject : Object {

	public string uri { get; set; }
	public string interpretation { get; set; }
	public string manifestation { get; set; }
	public string mimetype { get; set; }
	public string origin { get; set; }
	public string text { get; set; }
	public string storage { get; set; }

	public Subject.from_variant (Variant subject_variant) {
		VariantIter iter = subject_variant.iterator();
		
		assert (iter.n_children() >= 8);
		uri = (string) iter.next_value();
		interpretation = (string) iter.next_value();
		manifestation = (string) iter.next_value();
		mimetype = (string) iter.next_value();
		origin = (string) iter.next_value();
		text = (string) iter.next_value();
		storage = (string) iter.next_value();
	}

}
