/* subject.vala
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

/**
 * Subject objects abstract Zeitgeist subjects
 *
 * In Zeitgeist terminology, a //subject// is something (a file, web page,
 * person, conversation, etc.) that was somehow involved or affected by
 * a {@link Event}.
 */
public class Subject : Object
{
    private static StringChunk url_store;

    public string? uri { get; set; }
    public string? origin { get; set; }
    public string? text { get; set; }
    public string? storage { get; set; }
    // FIXME: current_{uri,origin} are often the same as uri, we don't
    // need to waste memory for them
    public string? current_uri { get; set; }
    public string? current_origin { get; set; }

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

    /** 
     * Create a new Subject structure with predefined data
     * @param uri The URI or URL of the subject
     * @param interpretation The interpretation type of the subject.
     * @param manifestation The manifestation type of the subject.
     * @param mimetype The mimetype of the subject. Eg. <emphasis>text/plain</emphasis>
     * @param origin The origin of the subject.
     * @param text A small textual representation of the subject suitable for display
     * @param storage String identifier for the storage medium the subject is on.
     *
     * @return A newly create {@link Subject} instance. The returned subject will
     *          have a floating reference which will be consumed if you pass the
     *          event to any of the methods provided by this library (like
     *          adding it to an event).
     */
    public Subject.full (string? uri=null,
        string? interpretation=null, string? manifestation=null,
        string? mimetype=null, string? origin=null, string? text=null,
        string? storage=null)
    {
        this.uri = uri;
        this.interpretation = interpretation;
        this.manifestation = manifestation;
        this.mimetype = mimetype;
        this.origin = origin;
        this.text = text;
        this.storage = storage;
    }

    /** 
     * Create a new Subject structure to describe a move event
     *
     * @param source_uri The URI or URL of the subject
     * @param source_origin The URI or URL of the subject
     * @param destination_uri The URI or URL of the subject
     * @param destination_origin The URI or URL of the subject
     * @param interpretation The interpretation type of the subject.
     * @param manifestation The manifestation type of the subject.
     * @param mimetype The mimetype of the subject. Eg. <emphasis>text/plain</emphasis>
     * @param text A small textual representation of the subject suitable for display
     * @param storage String identifier for the storage medium the subject is on.
     *
     * @return A newly create {@link Subject} instance. The returned subject will
     *          have a floating reference which will be consumed if you pass the
     *          event to any of the methods provided by this library (like
     *          adding it to an event).
     */
    public Subject.move_event (
        string? source_uri=null, string? source_origin=null,
        string? destination_uri=null, string? destination_origin=null,
        string? interpretation, string? manifestation=null,
        string? mimetype=null, string? text=null, string? storage=null)
    {
        this.uri = source_uri;
        this.origin = source_origin;
        this.current_uri = destination_uri;
        this.current_origin = destination_origin;
        this.interpretation = interpretation;
        this.manifestation = manifestation;
        this.mimetype = mimetype;
        this.text = text;
        this.storage = storage;
    }

    
    /** 
     * Create a new Subject structure from predefined {@link GLib.Variant} data
     *
     * @param subject_variant A {@link GLib.Variant} decscribing the subject data.
     *
     * @return A newly create {@link Subject} instance. The returned subject will
     *          have a floating reference which will be consumed if you pass the
     *          event to any of the methods provided by this library (like
     *          adding it to an event).
     */
    public Subject.from_variant (Variant subject_variant)
        throws DataModelError
    {
        VariantIter iter = subject_variant.iterator();

        var subject_props = iter.n_children ();
        Utils.assert_sig (subject_props >= 7, "Missing subject information");
        uri = next_string_or_null (iter);
        interpretation = next_string_or_null (iter);
        manifestation = next_string_or_null (iter);
        origin = next_string_or_null (iter);
        mimetype = next_string_or_null (iter);
        text = next_string_or_null (iter);
        storage = next_string_or_null (iter);
        // let's keep this compatible with older clients
        if (subject_props >= 8)
            current_uri = next_string_or_null (iter);
        if (subject_props >= 9)
            current_origin = next_string_or_null (iter);
    }

    public Variant to_variant ()
    {
        /* The FAST version */
        char* ptr_arr[9];
        ptr_arr[0] = uri != null ? uri : "";
        ptr_arr[1] = interpretation != null ? interpretation : "";
        ptr_arr[2] = manifestation != null ? manifestation : "";
        ptr_arr[3] = origin != null ? origin : "";
        ptr_arr[4] = mimetype != null ? mimetype : "";
        ptr_arr[5] = text != null ? text : "";
        ptr_arr[6] = storage != null ? storage : "";
        ptr_arr[7] = current_uri != null ? current_uri : "";
        ptr_arr[8] = current_origin != null ? current_origin : "";
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
        vb.add ("s", current_origin ?? "");

        return vb.end ();
        */
    }

    /**
     * @return true if this Subject matches *subject_template*. Empty
     * fields in the template are treated as wildcards.
     * Interpretations and manifestations are also matched if they are
     * children of the types specified in `subject_template`.
     * @param template_subject a {@link Subject}
    */
    public bool matches_template (Subject template_subject)
    {
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
        if (!check_field_match (this.current_origin, template_subject.current_origin, false, true))
            return false;
        if (!check_field_match (this.mimetype, template_subject.mimetype, false, true))
            return false;

        return true;
    }

}

}

// vim:expandtab:ts=4:sw=4
