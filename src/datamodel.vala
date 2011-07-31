/* datamodel.vala
 *
 * Copyright © 2011 Collabora Ltd.
 *             By Seif Lotfy <seif@lotfy.com>
 *             By Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
 * Copyright © 2011 Manish Sinha <manishsinha@ubuntu.com>
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

namespace Zeitgeist
{

    public struct TimeRange
    {
        int64 start;
        int64 end;
    }

    public enum ResultType
    {
        MOST_RECENT_EVENTS                   = 0,  //   All events with the most
                                                   // recent events first
        LEAST_RECENT_EVENTS                  = 1,  //   All events with the oldest
                                                   // ones first
        MOST_RECENT_SUBJECTS                 = 2,  //   One event for each subject
                                                   // only, ordered with the
                                                   // most recent events first
        LEAST_RECENT_SUBJECTS                = 3,  //   One event for each subject
                                                   // only, ordered with oldest
                                                   // events first
        MOST_POPULAR_SUBJECTS                = 4,  //   One event for each subject
                                                   // only, ordered by the
                                                   // popularity of the subject
        LEAST_POPULAR_SUBJECTS               = 5,  //   One event for each subject
                                                   // only, ordered ascendingly
                                                   // by popularity of the
                                                   // subject
        MOST_POPULAR_ACTOR                   = 6,  //   The last event of each
                                                   // different actor ordered
                                                   // by the popularity of the
                                                   // actor
        LEAST_POPULAR_ACTOR                  = 7,  //   The last event of each
                                                   // different actor, ordered
                                                   // ascendingly by the
                                                   // popularity of the actor
        MOST_RECENT_ACTOR                    = 8,  //   The actor that has been used
                                                   // to most recently
        LEAST_RECENT_ACTOR                   = 9,  //   The actor that has been used
                                                   // to least recently
        MOST_RECENT_ORIGIN                   = 10, //   The last event of each
                                                   // different subject origin.
        LEAST_RECENT_ORIGIN                  = 11, //   The last event of each
                                                   // different subject origin,
                                                   // ordered by least
                                                   // recently used first
        MOST_POPULAR_ORIGIN                  = 12, //   The last event of each
                                                   // different subject origin,
                                                   // ordered by the
                                                   // popularity of the origins
        LEAST_POPULAR_ORIGIN                 = 13, //   The last event of each
                                                   // different subject origin,
                                                   // ordered ascendingly by
                                                   // the popularity of the
                                                   // origin
        OLDEST_ACTOR                         = 14, //   The first event of each
                                                   // different actor
        MOST_RECENT_SUBJECT_INTERPRETATION   = 15, //   One event for each subject
                                                   // interpretation only,
                                                   // ordered with the most
                                                   // recent events first
        LEAST_RECENT_SUBJECT_INTERPRETATION  = 16, //   One event for each subject
                                                   // interpretation only,
                                                   // ordered with the least
                                                   // recent events first
        MOST_POPULAR_SUBJECT_INTERPRETATION  = 17, //   One event for each subject
                                                   // interpretation only,
                                                   // ordered by the popularity
                                                   // of the subject
                                                   // interpretation
        LEAST_POPULAR_SUBJECT_INTERPRETATION = 18, //   One event for each subject
                                                   // interpretation only,
                                                   // ordered ascendingly by
                                                   // popularity of the subject
                                                   // interpretation
        MOST_RECENT_MIMETYPE                 = 19, //   One event for each mimetype
                                                   // only ordered with the
                                                   // most recent events first
        LEAST_RECENT_MIMETYPE                = 20, //   One event for each mimetype
                                                   // only ordered with the
                                                   // least recent events first
        MOST_POPULAR_MIMETYPE                = 21, //   One event for each mimetype
                                                   // only ordered by the
                                                   // popularity of the mimetype
        LEAST_POPULAR_MIMETYPE               = 22, //   One event for each mimetype
                                                   // only ordered ascendingly
                                                   // by popularity of the
                                                   // mimetype
        MOST_RECENT_CURRENT_URI              = 23, //   One event for each subject
                                                   // only by current_uri
                                                   // instead of uri ordered
                                                   // with the most recent
                                                   // events first
        LEAST_RECENT_CURRENT_URI             = 24, // One event for each subject
                                                   // only by current_uri
                                                   // instead of uri ordered
                                                   // with oldest events first
        MOST_POPULAR_CURRENT_URI             = 25, //   One event for each subject
                                                   // only by current_uri
                                                   // instead of uri ordered
                                                   // by the popularity of the
                                                   // subject
        LEAST_POPULAR_CURRENT_URI            = 26, //   One event for each subject
                                                   // only by current_uri
                                                   // instead of uri
                                                   // ordered ascendingly by
                                                   // popularity of the subject
        MOST_RECENT_EVENT_ORIGIN             = 27, //   The last event of each
                                                   // different origin
        LEAST_RECENT_EVENT_ORIGIN            = 28, //   The last event of each
                                                   // different origin, ordered
                                                   // by least recently used
                                                   // first
        MOST_POPULAR_EVENT_ORIGIN           = 29, //   The last event of each
                                                   // different origin ordered
                                                   // by the popularity of the
                                                   // origins
        LEAST_POPULAR_EVENT_ORIGIN           = 30, //   The last event of each
                                                   // different origin, ordered
                                                   // ascendingly by the
                                                   // popularity of the origin
    }

    /*
     * An enumeration class used to define how query results should
     * be returned from the Zeitgeist engine.
     */
    public enum RelevantResultType
    {
        RECENT  = 0, // All uris with the most recent uri first
        RELATED = 1, // All uris with the most related one first
    }

    /**
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
        NOT_AVAILABLE   = 0, // The storage medium of the events
                             // subjects must not be available to the user
        AVAILABLE       = 1, // The storage medium of all event subjects
                             // must be immediately available to the user
        ANY             = 2  // The event subjects may or may not be available
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
        public ByteArray? payload { get; set; }

        construct
        {
            subjects = new GenericArray<Subject> ();
        }

        public int num_subjects ()
        {
            return subjects.length;
        }

        public void add_subject (Subject subject)
        {
            subjects.add (subject);
        }

        public Event.from_variant (Variant event_variant) { // (asaasay)
            assert (event_variant.get_type_string () == "(asaasay)");

            VariantIter iter = event_variant.iterator();
            
            assert (iter.n_children() == 3);
            VariantIter event_array = iter.next_value().iterator();
            VariantIter subjects_array = iter.next_value().iterator();
            Variant payload_variant = iter.next_value ();

            var event_props = event_array.n_children ();
            assert (event_props >= 5);
            id = (uint32) uint64.parse ((string) event_array.next_value());
            timestamp = int64.parse ((string) event_array.next_value());
            interpretation = (string) event_array.next_value();
            manifestation = (string) event_array.next_value();
            actor = (string) event_array.next_value();
            // let's keep this compatible with older clients
            if (event_props >= 6) origin = (string) event_array.next_value();
            
            for (int i = 0; i < subjects_array.n_children(); ++i) {
                Variant subject_variant = subjects_array.next_value();
                subjects.add(new Subject.from_variant(subject_variant));
            }
            
            // Parse payload...
            uint payload_length = (uint) payload_variant.n_children ();
            if (payload_length > 0)
            {
                payload = new ByteArray.sized (payload_length);
                unowned uint8[] data = (uint8[]?) payload_variant.get_data ();
                data.length = (int) payload_length;
                payload.append (data);
            }
        }

        public Variant to_variant ()
        {
            var vb = new VariantBuilder(new VariantType("(asaasay)"));
            
            vb.open(new VariantType("as"));
            vb.add("s", id.to_string ());
            vb.add("s", timestamp.to_string ());
            vb.add("s", interpretation);
            vb.add("s", manifestation);
            vb.add("s", actor);
            vb.add("s", origin);
            vb.close();
            
            vb.open(new VariantType("aas"));
            for (int i = 0; i < subjects.length; ++i) {
                vb.add_value(subjects[i].to_variant());
            }
            vb.close();
            
            vb.open(new VariantType("ay"));
            // payload...
            if (payload != null)
            {
                Variant payload_variant = Variant.new_from_data<ByteArray> (
                    new VariantType ("ay"), payload.data, false, payload);
                vb.add_value (payload_variant);
            }
            vb.close();

            return vb.end();
        }

        public void debug_print ()
        {
            stdout.printf ("id: %d\t" +
                           "timestamp: %li\n" +
                           "actor: %s\n" +
                           "interpretation: %s\n" +
                           "manifestation: %s\n" +
                           "origin: %s\n" +
                           "num subjects: %d\n",
                           id, timestamp, actor, interpretation,
                           manifestation, origin, subjects.length);
            for (int i = 0; i < subjects.length; i++)
            {
                var s = subjects[i];
                stdout.printf ("  Subject #%d:\n" +
                               "    uri: %s\n" +
                               "    interpretation: %s\n" +
                               "    manifestation: %s\n" +
                               "    mimetype: %s\n" +
                               "    origin: %s\n" +
                               "    text: %s\n" +
                               "    current_uri: %s\n" +
                               "    storage: %s\n",
                               i, s.uri, s.interpretation, s.manifestation,
                               s.mimetype, s.origin, s.text, s.current_uri,
                               s.storage);
            }

        }

    }

    namespace Events
    {

        public static GenericArray<Event> from_variant (Variant vevents)
        {
            GenericArray<Event> events = new GenericArray<Event> ();

            assert (vevents.get_type_string () == "a(asaasay)");

            foreach (Variant event in vevents)
            {
                events.add (new Event.from_variant (event));
            }

            return events;
        }

        public static Variant to_variant (GenericArray<Event> events)
        {
            var vb = new VariantBuilder(new VariantType("a(asaasay)"));

            vb.open(new VariantType("a(asaasay)"));
            for (int i = 0; i < events.length; ++i)
                vb.add_value (events[i].to_variant ());
            vb.close();

            return vb.end();
        }

    }

    public class Subject : Object
    {

        public string uri { get; set; }
        public string interpretation { get; set; }
        public string manifestation { get; set; }
        public string mimetype { get; set; }
        public string origin { get; set; }
        public string text { get; set; }
        public string storage { get; set; }
        public string current_uri { get; set; }

        public Subject.from_variant (Variant subject_variant)
        {
            VariantIter iter = subject_variant.iterator();
            
            var subject_props = iter.n_children ();
            assert (subject_props >= 7);
            uri = (string) iter.next_value();
            interpretation = (string) iter.next_value();
            manifestation = (string) iter.next_value();
            origin = (string) iter.next_value();
            mimetype = (string) iter.next_value();
            text = (string) iter.next_value();
            storage = (string) iter.next_value();
            // let's keep this compatible with older clients
            if (subject_props >= 8) current_uri = (string) iter.next_value();
        }

        public Variant to_variant()
        {
            var vb = new VariantBuilder(new VariantType("as"));
            vb.open(new VariantType("as"));
            vb.add("s", uri);
            vb.add("s", interpretation);
            vb.add("s", manifestation);
            vb.add("s", origin);
            vb.add("s", mimetype);
            vb.add("s", text);
            vb.add("s", storage);
            vb.add("s", current_uri);
            vb.close();
            return vb.end();
        }

    }

}

// vim:expandtab:ts=4:sw=4
