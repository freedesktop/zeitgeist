/* event.vala
 *
 * Copyright © 2011-2012 Collabora Ltd.
 *             By Seif Lotfy <seif@lotfy.com>
 *             By Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
 * Copyright © 2011 Manish Sinha <manishsinha@ubuntu.com>
 * Copyright © 2011 Michal Hruby <michal.mhr@gmail.com>
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

using Zeitgeist;

namespace Zeitgeist
{

// Also used in subject.vala
private string? next_string_or_null (VariantIter iter)
{
    string text = iter.next_value ().get_string ();
    if (text != "")
        return text;
    return null;
}

// Also used in subject.vala
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

/**
 * Event objects abstract Zeitgeist events
 *
 * The Event class is one of the primary elements for communicating
 * with the Zeitgeist daemon. Events serve two purposes
 * Unsurprisingly, they represent events that have happened, but they
 * can also act as templates. See also {@link Subject}.
 *
 * An event in the Zeitgeist world is characterized by two main
 * properties. "What happened", also called the interpretation, and
 * "How did it happen", also called the manifestation. Besides these
 * properties, an event also has an actor which identifies the party
 * responsible for triggering the event which in most cases will be
 * an application. Lastly there is an event timestamp and an event ID.
 * The timestamp is calculated as the number of milliseconds since the
 * Unix epoch and the event ID is a number assigned to the event by
 * the Zeitgeist engine when it's logged. These five properties are
 * collectively known as the event metadata.
 *
 * An event must also describe what it happened to. For this we have
 * event subjects. Most events have one subject, but they may also
 * have more. The metadata of the subjects are recorded at the time
 * of logging, and are encapsulated by the #Subject class. It's
 * important to understand that it's just the subject metadata at the
 * time of logging, not necessarily the subject metadata as it exists
 * right now.
 *
 * In addition to the listed properties, events may also carry a free
 * form binary payload. The usage of this is application specific and
 * is generally useless unless you have some contextual information to
 * figure out what's in it.
 *
 * A large part of the Zeitgeist query and monitoring API revolves
 * around a concept of template matching. A query is simply a list of
 * event templates that you want to look for in the log. An unset
 * property on an event template indicates that anything is allowed in
 * that field. If the property is set it indicates that the property
 * must be an exact match, unless a special operator is used.
 */
public class Event : Object
{
    public const string SIGNATURE = "asaasay";

    private static StringChunk url_store;

    public uint32  id { get; set; }
    public int64   timestamp { get; set; }
    public string? origin { get; set; }

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

    public Subject get_subject(int index)
    {
        return subjects[index];
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

        // Requires Vala bug #620675 - fixed as of 2012-07-30
        var subjects = va_list ();
        unowned Subject subject;
        while ((subject = subjects.arg ()) != null)
            add_subject (subject);
    }

    public Event.from_variant (Variant event_variant) throws DataModelError {
        Utils.assert_sig (event_variant.get_type_string () == "(" +
            Utils.SIG_EVENT + ")", "Invalid D-Bus signature.");

        VariantIter iter = event_variant.iterator ();

        Utils.assert_sig (iter.n_children () >= 3, "Incomplete event struct.");
        VariantIter event_array = iter.next_value ().iterator ();
        VariantIter subjects_array = iter.next_value ().iterator ();
        Variant payload_variant = iter.next_value ();

        var event_props = event_array.n_children ();

        if (event_props == 0)
        {
            throw new DataModelError.NULL_EVENT ("This is an empty event.");
        }

        Utils.assert_sig (event_props >= 5, "Missing event information.");
        id = (uint32) uint64.parse (event_array.next_value().get_string ());
        var str_timestamp = event_array.next_value().get_string ();
        if (str_timestamp != "")
            timestamp = int64.parse (str_timestamp);
        else
            timestamp = Timestamp.from_now ();
        interpretation = next_string_or_null (event_array);
        manifestation = next_string_or_null (event_array);
        actor = next_string_or_null (event_array);
        // let's keep this compatible with older clients
        if (event_props >= 6)
            origin = next_string_or_null (event_array);

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

    public void set_actor_from_app_info (AppInfo info)
    {
        if (info.get_id () != null)
        {
            actor = "application://" + info.get_id ();
        }
        else
        {
            string? path = null;
            if (info is DesktopAppInfo)
                path = (info as DesktopAppInfo).filename;

            if (path != null)
            {
                actor = "application://" + Path.get_basename (path);
            }
            else if (info.get_name () != null)
            {
                actor = "application://" + info.get_name () + ".desktop";
            }
        }
    }

    public Variant to_variant ()
    {
        var vb = new VariantBuilder (new VariantType ("("+Utils.SIG_EVENT+")"));

        vb.open (new VariantType ("as"));
        vb.add ("s", id == 0 ? "" : id.to_string ());
        vb.add ("s", timestamp != 0 ? timestamp.to_string () : "");
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
                new VariantType ("ay"), payload.data, false, payload);
            vb.add_value (payload_variant);
        }
        else
        {
            vb.open (new VariantType ("ay"));
            vb.close ();
        }

        Variant event_variant = vb.end ().get_normal_form ();
        //Variant ret = optimize_variant_allocation (event_variant);
        return event_variant;
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
                           "    current_origin: %s\n" +
                           "    storage: %s\n",
                           i, s.uri, s.interpretation, s.manifestation,
                           s.mimetype, s.origin, s.text, s.current_uri,
                           s.current_origin, s.storage);
        }
        if (payload != null)
            stdout.printf ("payload: %u bytes", payload.len);
        else
            stdout.printf ("payload: (null)\n");
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

    public static GenericArray<Event?> from_variant (Variant vevents)
        throws DataModelError
    {
        GenericArray<Event?> events = new GenericArray<Event> ();

        assert (vevents.get_type_string () == "a("+Utils.SIG_EVENT+")");
        foreach (Variant vevent in vevents)
        {
            Event? event = null;
            try
            {
                event = new Event.from_variant (vevent);
            }
            catch (DataModelError err)
            {
                if (!(err is DataModelError.NULL_EVENT))
                    throw err;
            }
            events.add (event);
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

}

// vim:expandtab:ts=4:sw=4
