/* datamodel.vala
 *
 * Copyright © 2011 Collabora Ltd.
 *             By Seif Lotfy <seif@lotfy.com>
 *             By Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
 * Copyright © 2011 Manish Sinha <manishsinha@ubuntu.com>
 * Copyright © 2012 Canonical Ltd.
 *             By Siegfried-A. Gevatter <siegfried.gevatter@collabora.co.uk>
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
    //[DBus (name = "org.gnome.zeitgeist.DataModelError")]
    public errordomain DataModelError {
        INVALID_SIGNATURE,
        TOO_MANY_RESULTS
    }

    private void assert_sig (bool condition, string error_message)
        throws DataModelError
    {
        if (unlikely (!condition))
            throw new DataModelError.INVALID_SIGNATURE (error_message);
    }

    [CCode (type_signature = "(xx)")]
    public class TimeRange: Object
    {
        public int64 start { get; private set; }
        public int64 end { get; private set; }

        public TimeRange (int64 start_msec, int64 end_msec)
        {
            Object (start: start_msec, end: end_msec);
        }

        public TimeRange.anytime ()
        {
            Object (start: 0, end: int64.MAX);
        }

        public TimeRange.to_now ()
        {
            this (0, Timestamp.now ());
        }

        public TimeRange.from_now ()
        {
            this (Timestamp.now (), int64.MAX);
        }

        public TimeRange.from_variant (Variant variant)
            throws DataModelError
        {
            assert_sig (variant.get_type_string () == "(xx)",
                "Invalid D-Bus signature.");

            int64 start_msec = 0;
            int64 end_msec = 0;

            variant.get ("(xx)", &start_msec, &end_msec);

            this (start_msec, end_msec);
        }

        public Variant to_variant ()
        {
            return new Variant ("(xx)", start, end);
        }

        public TimeRange? intersect (TimeRange time_range)
        {
            var result = new TimeRange(0,0);
            if (start < time_range.start)
                if (end < time_range.start)
                    return null;
                else
                    result.start = time_range.start;
            else
                if (start > time_range.end)
                    return null;
                else
                    result.start = start;

            if (end < time_range.end)
                if (end < time_range.start)
                    return null;
                else
                    result.end = end;
            else
                if (start > time_range.end)
                    return null;
                else
                    result.end = time_range.end;
            return result;
        }
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
        LEAST_POPULAR_EVENT_ORIGIN           = 30; //   The last event of each
                                                   // different origin, ordered
                                                   // ascendingly by the
                                                   // popularity of the origin

        /*
         * Returns true if the results for the given result_type will be sorted
         * ascendantly by date, false if they'll be sorted descendingly.
         **/
        public static bool is_sort_order_asc (ResultType result_type)
        {
            switch (result_type)
            {
                // FIXME: Why are LEAST_POPULAR_* using ASC?
                case ResultType.LEAST_RECENT_EVENTS:
                case ResultType.LEAST_RECENT_EVENT_ORIGIN:
                case ResultType.LEAST_POPULAR_EVENT_ORIGIN:
                case ResultType.LEAST_RECENT_SUBJECTS:
                case ResultType.LEAST_POPULAR_SUBJECTS:
                case ResultType.LEAST_RECENT_CURRENT_URI:
                case ResultType.LEAST_POPULAR_CURRENT_URI:
                case ResultType.LEAST_RECENT_ACTOR:
                case ResultType.LEAST_POPULAR_ACTOR:
                case ResultType.OLDEST_ACTOR:
                case ResultType.LEAST_RECENT_ORIGIN:
                case ResultType.LEAST_POPULAR_ORIGIN:
                case ResultType.LEAST_RECENT_SUBJECT_INTERPRETATION:
                case ResultType.LEAST_POPULAR_SUBJECT_INTERPRETATION:
                case ResultType.LEAST_RECENT_MIMETYPE:
                case ResultType.LEAST_POPULAR_MIMETYPE:
                    return true;

                case ResultType.MOST_RECENT_EVENTS:
                case ResultType.MOST_RECENT_EVENT_ORIGIN:
                case ResultType.MOST_POPULAR_EVENT_ORIGIN:
                case ResultType.MOST_RECENT_SUBJECTS:
                case ResultType.MOST_POPULAR_SUBJECTS:
                case ResultType.MOST_RECENT_CURRENT_URI:
                case ResultType.MOST_POPULAR_CURRENT_URI:
                case ResultType.MOST_RECENT_ACTOR:
                case ResultType.MOST_POPULAR_ACTOR:
                case ResultType.MOST_RECENT_ORIGIN:
                case ResultType.MOST_POPULAR_ORIGIN:
                case ResultType.MOST_RECENT_SUBJECT_INTERPRETATION:
                case ResultType.MOST_POPULAR_SUBJECT_INTERPRETATION:
                case ResultType.MOST_RECENT_MIMETYPE:
                case ResultType.MOST_POPULAR_MIMETYPE:
                    return false;

                default:
                    warning ("Unrecognized ResultType: %u", (uint) result_type);
                    return true;
            }
        }
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

    private bool check_field_match (string? property,
            string? template_property, bool is_symbol = false,
            bool can_wildcard = false)
    {
        var matches = false;
        var is_negated = false;
        var parsed = template_property;

        if (parsed != null)
            is_negated = Utils.parse_negation (ref parsed);

        if (Utils.is_empty_string (parsed))
        {
            return true;
        }
        else if (parsed == property)
        {
            matches = true;
        }
        else if (is_symbol && property != null &&
            Symbol.get_all_parents (property).find_custom (parsed, strcmp) != null)
        {
            matches = true;
        }
        else if (can_wildcard && Utils.parse_wildcard (ref parsed))
        {
            if (property != null && property.has_prefix (parsed))
                matches = true;
        }

        return (is_negated) ? !matches : matches;
    }

    public class Event : Object
    {
        public const string SIGNATURE = "asaasay";

        private static StringChunk url_store;

        public uint32    id { get; set; }
        public int64     timestamp { get; set; }
        public string?   origin { get; set; }

        public string? actor
        {
            get { return _actor; }
            set { _actor = (value != null) ? url_store.insert_const (value) : null; }
        }
        public string? interpretation
        {
            get { return _interpretation; }
            set { _interpretation = (value != null) ? url_store.insert_const (value) : null; }
        }
        public string? manifestation
        {
            get { return _manifestation; }
            set { _manifestation = (value != null) ? url_store.insert_const (value) : null; }
        }

        private unowned string? _actor;
        private unowned string? _interpretation;
        private unowned string? _manifestation;

        public GenericArray<Subject> subjects { get; set; }
        public ByteArray? payload { get; set; }

        static construct
        {
            url_store = new StringChunk (4096);
        }

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

        public void take_subject (owned Subject subject)
        {
            subjects.add ((owned) subject);
        }

        public Event.full (string? interpretation=null,
            string? manifestation=null, string? actor=null,
            string? origin=null, ...)
        {
            this.interpretation = interpretation;
            this.manifestation = manifestation;
            this.actor = actor;
            this.origin = origin;

            // FIXME: We can't use this until Vala bug #647097 is fixed
            /*
            var subjects = va_list ();
            unowned Subject subject;
            while ((subject = subjects.arg ()) != null)
                add_subject (subject);
            */
        }

        public Event.from_variant (Variant event_variant) throws DataModelError {
            assert_sig (event_variant.get_type_string () == "(" +
                Utils.SIG_EVENT + ")", "Invalid D-Bus signature.");

            VariantIter iter = event_variant.iterator ();

            assert_sig (iter.n_children () >= 3, "Incomplete event struct.");
            VariantIter event_array = iter.next_value ().iterator ();
            VariantIter subjects_array = iter.next_value ().iterator ();
            Variant payload_variant = iter.next_value ();

            var event_props = event_array.n_children ();
            assert_sig (event_props >= 5, "Missing event information.");
            id = (uint32) uint64.parse (event_array.next_value().get_string ());
            var str_timestamp = event_array.next_value().get_string ();
            if (str_timestamp == "")
                timestamp = Timestamp.now ();
            else
                timestamp = int64.parse (str_timestamp);
            interpretation = event_array.next_value ().get_string ();
            manifestation = event_array.next_value ().get_string ();
            actor = event_array.next_value ().get_string ();
            // let's keep this compatible with older clients
            if (event_props >= 6)
                origin = event_array.next_value ().get_string ();
            else
                origin = "";

            for (int i = 0; i < subjects_array.n_children (); ++i) {
                Variant subject_variant = subjects_array.next_value ();
                subjects.add (new Subject.from_variant (subject_variant));
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
            var vb = new VariantBuilder (new VariantType ("("+Utils.SIG_EVENT+")"));

            vb.open (new VariantType ("as"));
            vb.add ("s", id == 0 ? "" : id.to_string ());
            vb.add ("s", timestamp.to_string ());
            vb.add ("s", interpretation != null ? interpretation : "");
            vb.add ("s", manifestation != null ? manifestation : "");
            vb.add ("s", actor != null ? actor : "");
            vb.add ("s", origin != null ? origin : "");
            vb.close ();

            vb.open (new VariantType ("aas"));
            for (int i = 0; i < subjects.length; ++i) {
                vb.add_value (subjects[i].to_variant ());
            }
            vb.close ();

            if (payload != null)
            {
                Variant payload_variant = Variant.new_from_data<ByteArray> (
                    new VariantType ("ay"), payload.data, false);
                // FIXME: somehow adding the payload_variant is not working
                vb.add_value (payload_variant);
            }
            else
            {
                vb.open (new VariantType ("ay"));
                vb.close ();
            }

            Variant event_variant = vb.end ().get_normal_form ();
            Variant ret = optimize_variant_allocation (event_variant);
            return ret;
        }

        private Variant optimize_variant_allocation (Variant event_variant) {
            // FIXME: this uses g_new0, we dont need the mem to be zero-filled
            uchar[] data = new uchar[event_variant.get_size ()];
            event_variant.store (data);
            unowned uchar[] data_copy = data;

            Variant ret = Variant.new_from_data (
                new VariantType ("("+Utils.SIG_EVENT+")"),
                data_copy, true, (owned) data);
            return ret;
        }

        public void debug_print ()
        {
            stdout.printf ("id: %d\t" +
                           "timestamp: %" + int64.FORMAT + "\n" +
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


        public bool matches_template (Event template_event)
        {
            /**
            Return True if this event matches *event_template*. The
            matching is done where unset fields in the template is
            interpreted as wild cards. Interpretations and manifestations
            are also matched if they are children of the types specified
            in `event_template`. If the template has more than one
            subject, this event matches if at least one of the subjects
            on this event matches any single one of the subjects on the
            template.
            */

            //Check if interpretation is child of template_event or same
            if (!check_field_match (this.interpretation, template_event.interpretation, true))
                return false;
            //Check if manifestation is child of template_event or same
            if (!check_field_match (this.manifestation, template_event.manifestation, true))
                return false;
            //Check if actor is equal to template_event actor
            if (!check_field_match (this.actor, template_event.actor, false, true))
                return false;
            //Check if origin is equal to template_event origin
            if (!check_field_match (this.origin, template_event.origin, false, true))
                return false;

            if (template_event.subjects.length == 0)
                return true;

            for (int i = 0; i < this.subjects.length; i++)
                for (int j = 0; j < template_event.subjects.length; j++)
                    if (this.subjects[i].matches_template (template_event.subjects[j]))
                        return true;

            return false;
        }

    }

    namespace Events
    {

        public static GenericArray<Event> from_variant (Variant vevents)
            throws DataModelError
        {
            GenericArray<Event> events = new GenericArray<Event> ();

            assert (vevents.get_type_string () == "a("+Utils.SIG_EVENT+")");

            foreach (Variant event in vevents)
            {
                events.add (new Event.from_variant (event));
            }

            return events;
        }

        public static Variant to_variant (GenericArray<Event?> events)
        {
            var vb = new VariantBuilder(new VariantType("a("+Utils.SIG_EVENT+")"));

            for (int i = 0; i < events.length; ++i)
            {
                if (events[i] != null)
                {
                    vb.add_value (events[i].to_variant ());
                }
                else
                {
                    vb.add_value (get_null_event_variant ());
                }
            }

            return vb.end ();
        }

        /* Same as to_variant but raises an exception if the variant size
         * exceeds `limit' bytes.
         * */
        public static Variant to_variant_with_limit (GenericArray<Event?> events,
            size_t limit=Utils.MAX_DBUS_RESULT_SIZE) throws DataModelError
        {
            var vb = new VariantBuilder(new VariantType("a("+Utils.SIG_EVENT+")"));

            size_t variant_size = 0;

            for (int i = 0; i < events.length; ++i)
            {
                Variant event_variant;

                if (events[i] != null)
                {
                    event_variant = events[i].to_variant ();
                }
                else
                {
                    event_variant = get_null_event_variant ();
                }

                variant_size += event_variant.get_size();
                if (variant_size > limit)
                {
                    size_t avg_event_size = variant_size / (i+1);
                    string error_message = ("Query exceeded size limit of % " +
                        size_t.FORMAT + "MiB (roughly ~%d events).").printf (
                            limit / 1024 / 1024, limit / avg_event_size);
                    warning (error_message);
                    throw new DataModelError.TOO_MANY_RESULTS (error_message);
                }

                vb.add_value (event_variant);
            }

            return vb.end ();
        }

        private static Variant get_null_event_variant ()
        {
            var vb = new VariantBuilder (new VariantType ("("+Utils.SIG_EVENT+")"));
            vb.open (new VariantType ("as"));
            vb.close ();
            vb.open (new VariantType ("aas"));
            vb.close ();
            vb.open (new VariantType ("ay"));
            vb.close ();
            return vb.end ();
        }

    }

    public class Subject : Object
    {
        private static StringChunk url_store;

        public string? uri { get; set; }
        public string? origin { get; set; }
        public string? text { get; set; }
        public string? storage { get; set; }
        // FIXME: current_uri is often the same as uri, we don't need to waste
        // memory for it
        public string? current_uri { get; set; }

        public string? mimetype
        {
            get { return _mimetype; }
            set { _mimetype = (value != null) ? url_store.insert_const (value) : null; }
        }
        public string? interpretation
        {
            get { return _interpretation; }
            set { _interpretation = (value != null) ? url_store.insert_const (value) : null; }
        }
        public string? manifestation
        {
            get { return _manifestation; }
            set { _manifestation = (value != null) ? url_store.insert_const (value) : null; }
        }

        private unowned string? _mimetype;
        private unowned string? _interpretation;
        private unowned string? _manifestation;

        static construct
        {
            url_store = new StringChunk (4096);
        }

        public Subject.full (string? uri=null,
            string? interpretation=null, string? manifestation=null,
            string? mimetype=null, string? origin=null, string? text=null,
            string? storage=null, string? current_uri=null)
        {
            this.interpretation = interpretation;
            this.manifestation = manifestation;
            this.mimetype = mimetype;
            this.origin = origin;
            this.text = text;
            this.storage = storage;
            this.current_uri = current_uri;
        }

        public Subject.from_variant (Variant subject_variant)
            throws DataModelError
        {
            VariantIter iter = subject_variant.iterator();

            var subject_props = iter.n_children ();
            assert_sig (subject_props >= 7, "Missing subject information");
            uri = iter.next_value().get_string ();
            interpretation = iter.next_value().get_string ();
            manifestation = iter.next_value().get_string ();
            origin = iter.next_value().get_string ();
            mimetype = iter.next_value().get_string ();
            text = iter.next_value().get_string ();
            storage = iter.next_value().get_string ();
            // let's keep this compatible with older clients
            if (subject_props >= 8)
                current_uri = iter.next_value().get_string ();
            else
                current_uri = "";
        }

        public Variant to_variant ()
        {
            /* The FAST version */
            char* ptr_arr[8];
            ptr_arr[0] = uri != null ? uri : "";
            ptr_arr[1] = interpretation != null ? interpretation : "";
            ptr_arr[2] = manifestation != null ? manifestation : "";
            ptr_arr[3] = origin != null ? origin : "";
            ptr_arr[4] = mimetype != null ? mimetype : "";
            ptr_arr[5] = text != null ? text : "";
            ptr_arr[6] = storage != null ? storage : "";
            ptr_arr[7] = current_uri != null ? current_uri : "";
            return new Variant.strv ((string[]) ptr_arr);
            /* The NICE version */
            /*
            var vb = new VariantBuilder (new VariantType ("as"));
            vb.add ("s", uri ?? "");
            vb.add ("s", interpretation ?? "");
            vb.add ("s", manifestation ?? "");
            vb.add ("s", origin ?? "");
            vb.add ("s", mimetype ?? "");
            vb.add ("s", text ?? "");
            vb.add ("s", storage ?? "");
            vb.add ("s", current_uri ?? "");

            return vb.end ();
            */
        }

        public bool matches_template (Subject template_subject)
        {
            /**
            Return True if this Subject matches *subject_template*. Empty
            fields in the template are treated as wildcards.
            Interpretations and manifestations are also matched if they are
            children of the types specified in `subject_template`.
            */
            if (!check_field_match (this.uri, template_subject.uri, false, true))
                return false;
            if (!check_field_match (this.current_uri, template_subject.current_uri, false, true))
                return false;
            if (!check_field_match (this.interpretation, template_subject.interpretation, true))
                return false;
            if (!check_field_match (this.manifestation, template_subject.manifestation, true))
                return false;
            if (!check_field_match (this.origin, template_subject.origin, false, true))
                return false;
            if (!check_field_match (this.mimetype, template_subject.mimetype, false, true))
                return false;

            return true;
        }

    }

}

// vim:expandtab:ts=4:sw=4
