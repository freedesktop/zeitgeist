/* mimetype.vala
 *
 * Copyright © 2011 Collabora Ltd.
 *             By Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
 * Copyright © 2010 Canonical, Ltd.
 *             By Mikkel Kamstrup Erlandsen <mikkel.kamstrup@canonical.com>
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
     * Mime-Type mapping and URI comprehension
     */

    private static bool mimetypes_loaded = false;
    private static bool schemes_loaded = false;

    private static HashTable<string, string>? mimetypes = null;
    private static SList<MimeRegex?> mimetypes_regexs;
    private static SList<UriScheme?> schemes;

    [Compact]
    private class MimeRegex
    {
        public Regex regex;
        public string interpretation_uri;

        public MimeRegex (string mimetype_regex, string interpretation_uri)
            throws RegexError
        {
            this.regex = new Regex (mimetype_regex, 0, 0);
            this.interpretation_uri = interpretation_uri;
        }
    }

    [Compact]
    private class UriScheme
    {
        public string uri_scheme;
        public string manifestation_uri;

        public UriScheme (string uri_scheme, string manifestation_uri)
        {
            this.uri_scheme = uri_scheme;
            this.manifestation_uri = manifestation_uri;
        }
    }

    /**
     * zeitgeist_register_mimetype:
     *
     * Associate a MIME-type with a given interpretation type. Registered
     * MIME-types can be looked up with zeitgeist_interpretation_for_mimetype().
     *
     * You can register a regular expression as mimetype if instead of this
     * function you invoke zeitgeist_register_mimetype_regex().
     *
     * MIME-types are first looked up by their exact name and then if none is
     * found the regular expressions will be checked as fallbacks.
     *
     * This library will install a wide range a common mimetypes for you, so
     * unless you have very specific needs you will normally not have to call
     * this function.
     *
     * @param mimetype  A MIME-type string. Eg. //text/plain//
     * @param interpretation_uri A URI defining the subject interpretation
     *     type to associate with "mimetype"
     */
    public void register_mimetype (string mimetype, string interpretation_uri)
    {
        if (mimetypes == null)
            mimetypes = new HashTable<string, string>(str_hash, str_equal);

        mimetypes.insert (mimetype, interpretation_uri);
    }

    /**
     * zeitgeist_register_mimetype_regex:
     *
     * Associate a range of MIME-types with a given interpretation type.
     * Registered MIME-types can be looked up with
     * zeitgeist_interpretation_for_mimetype().
     *
     * If you only need to register one specific MIME-type, it is more efficient
     * to use zeitgeist_register_mimetype() instead of this function.
     *
     * MIME-types are first looked up by their exact name and then if none is
     * found the regular expressions will be checked as fallbacks.
     *
     * This library will install a wide range a common mimetypes for you, so
     * unless you have very specific needs you will normally not have to call
     * this function.
     *
     * @param mimetype_regex A regular expression matching a certain range of
     *     mimetypes. Eg. //text/.* // to match all //text// subtypes.
     * @param interpretation_uri A URI defining the subject interpretation
     *     type to associate with the matched MIME-types
     */
    public void register_mimetype_regex (string mimetype_regex,
        string interpretation_uri)
    {
        try
        {
            var entry = new MimeRegex (mimetype_regex, interpretation_uri);
            mimetypes_regexs.append ((owned) entry);
        } catch (RegexError e) {
            warning ("Couldn't register mimetype regex: %s", e.message);
        }
    }

    /**
     * zeitgeist_interpretation_for_mimetype:
     *
     * Look up the subject interpretation type associated with @mimetype.
     *
     * @param mimetype A MIME-type string. Eg. //text/plain//
     *
     * @return A URI defining the subject interpretation type associated with
     *     "mimetype" or %NULL in case "mimetype" is unknown
     */
    public unowned string? interpretation_for_mimetype (string? mimetype)
    {
        ensure_mimetypes_loaded ();

        if (mimetype == null)
            return null;

        unowned string? interpretation = mimetypes.lookup (mimetype);
        if (interpretation != null)
            return interpretation;

        foreach (unowned MimeRegex mime_regex in mimetypes_regexs)
        {
            if (mime_regex.regex.match (mimetype, 0))
                return mime_regex.interpretation_uri;
        }

        return null;
    }

    /**
     * zeitgeist_register_uri_scheme:
     *
     * Associate a URI scheme with a given subject manifestation type.
     * You can find the manifestation type of a given URI by passing it to
     * zeitgeist_manifestation_for_uri().
     *
     * This library will install a range a common URI schemes for you, so unless
     * you have very specific needs you will normally not have to call this
     * function.
     *
     * @param uri_scheme A URI scheme such as //http:\/\///
     * @param manifestation_type A URI defining the subject manifestation type
     *     to associate with "uri_scheme"
     */
    public void register_uri_scheme (string uri_scheme,
        string manifestation_type)
    {
        var scheme = new UriScheme (uri_scheme, manifestation_type);
        schemes.append ((owned) scheme);
    }

    /**
     * zeitgeist_manifestation_for_uri
     *
     * Look up a subject manifestation type for a given URI. Eg. if you pass in
     * //file:\/\/\/tmp/foo.txt// you will get back
     * ZEITGEIST_NFO_FILE_DATA_OBJECT.
     *
     * @param uri An URI
     *
     * @return A subject manifestation type for @uri or %NULL in case no
     *     suitable manifestation type is known
     */
    public unowned string? manifestation_for_uri (string uri) {
        ensure_schemes_loaded ();

        foreach (unowned UriScheme scheme in schemes)
        {
            if (uri.has_prefix (scheme.uri_scheme))
                return scheme.manifestation_uri;
        }

        return null;
    }

    private static void ensure_mimetypes_loaded ()
    {
        if (mimetypes_loaded)
            return;

        register_mimetype ("application/ecmascript", NFO.SOURCE_CODE);
        register_mimetype ("application/javascript", NFO.SOURCE_CODE);
        register_mimetype ("application/json", NFO.SOURCE_CODE);
        register_mimetype ("application/ms-excel", NFO.SPREADSHEET);
        register_mimetype ("application/ms-powerpoint", NFO.PRESENTATION);
        register_mimetype ("application/msexcel", NFO.SPREADSHEET);
        register_mimetype ("application/msword", NFO.PAGINATED_TEXT_DOCUMENT);
        register_mimetype ("application/ogg", NFO.AUDIO);
        register_mimetype ("application/pdf", NFO.PAGINATED_TEXT_DOCUMENT);
        register_mimetype ("application/postscript", NFO.PAGINATED_TEXT_DOCUMENT);
        register_mimetype ("application/ps", NFO.PAGINATED_TEXT_DOCUMENT);
        register_mimetype ("application/rtf", NFO.PAGINATED_TEXT_DOCUMENT);
        register_mimetype ("application/soap+xml", NFO.SOURCE_CODE);
        register_mimetype ("application/vnd.corel-draw", NFO.VECTOR_IMAGE);
        register_mimetype ("application/vnd.ms-excel", NFO.SPREADSHEET);
        register_mimetype ("application/vnd.ms-powerpoint", NFO.PRESENTATION);
        register_mimetype ("application/x-7z-compressed", NFO.ARCHIVE);
        register_mimetype ("application/x-abiword", NFO.PAGINATED_TEXT_DOCUMENT);
        register_mimetype ("application/x-applix-presents", NFO.PRESENTATION);
        register_mimetype ("application/x-applix-spreadsheet", NFO.SPREADSHEET);
        register_mimetype ("application/x-applix-word", NFO.PAGINATED_TEXT_DOCUMENT);
        register_mimetype ("application/x-archive", NFO.ARCHIVE);
        register_mimetype ("application/x-bzip", NFO.ARCHIVE);
        register_mimetype ("application/x-bzip-compressed-tar", NFO.ARCHIVE);
        register_mimetype ("application/x-cd-image", NFO.FILESYSTEM_IMAGE);
        register_mimetype ("application/x-compressed-tar", NFO.ARCHIVE);
        register_mimetype ("application/x-csh", NFO.SOURCE_CODE);
        register_mimetype ("application/x-deb", NFO.SOFTWARE);
        register_mimetype ("application/x-designer", NFO.SOURCE_CODE);
        register_mimetype ("application/x-desktop", NFO.SOFTWARE);
        register_mimetype ("application/x-dia-diagram", NFO.SOURCE_CODE);
        register_mimetype ("application/x-executable", NFO.SOFTWARE);
        register_mimetype ("application/x-fluid", NFO.SOURCE_CODE);
        register_mimetype ("application/x-glade", NFO.SOURCE_CODE);
        register_mimetype ("application/x-gnucash", NFO.SPREADSHEET);
        register_mimetype ("application/x-gnumeric", NFO.SPREADSHEET);
        register_mimetype ("application/x-gzip", NFO.ARCHIVE);
        register_mimetype ("application/x-java-archive", NFO.SOURCE_CODE);
        register_mimetype ("application/x-javascript", NFO.SOURCE_CODE);
        register_mimetype ("application/x-killustrator", NFO.VECTOR_IMAGE);
        register_mimetype ("application/x-kpresenter", NFO.PRESENTATION);
        register_mimetype ("application/x-kspread", NFO.SPREADSHEET);
        register_mimetype ("application/x-kword", NFO.PAGINATED_TEXT_DOCUMENT);
        register_mimetype ("application/x-lzma", NFO.ARCHIVE);
        register_mimetype ("application/x-lzma-compressed-tar", NFO.ARCHIVE);
        register_mimetype ("application/x-m4", NFO.SOURCE_CODE);
        register_mimetype ("application/x-ms-dos-executable", NFO.SOFTWARE);
        register_mimetype ("application/x-perl", NFO.SOURCE_CODE);
        register_mimetype ("application/x-php", NFO.SOURCE_CODE);
        register_mimetype ("application/x-rpm", NFO.SOFTWARE);
        register_mimetype ("application/x-ruby", NFO.SOURCE_CODE);
        register_mimetype ("application/x-shellscript", NFO.SOURCE_CODE);
        register_mimetype ("application/x-shockwave-flash", NFO.EXECUTABLE);
        register_mimetype ("application/x-sql", NFO.SOURCE_CODE);
        register_mimetype ("application/x-stuffit", NFO.ARCHIVE);
        register_mimetype ("application/xhtml+xml", NFO.SOURCE_CODE);
        register_mimetype ("application/xml", NFO.SOURCE_CODE);
        register_mimetype ("application/xml-dtd", NFO.SOURCE_CODE);
        register_mimetype ("application/zip", NFO.ARCHIVE);
        register_mimetype ("audio/x-scpls", NFO.MEDIA_LIST);
        register_mimetype ("image/gif", NFO.RASTER_IMAGE);
        register_mimetype ("image/jpeg", NFO.RASTER_IMAGE);
        register_mimetype ("image/pjpeg", NFO.RASTER_IMAGE);
        register_mimetype ("image/png", NFO.RASTER_IMAGE);
        register_mimetype ("image/svg+xml", NFO.VECTOR_IMAGE);
        register_mimetype ("image/tiff", NFO.RASTER_IMAGE);
        register_mimetype ("image/vnd.microsoft.icon", NFO.ICON);
        register_mimetype ("image/x-xcf", NFO.RASTER_IMAGE);
        register_mimetype ("inode/directory", NFO.FOLDER);
        register_mimetype ("message/alternative", NMO.EMAIL);
        register_mimetype ("message/partial", NMO.EMAIL);
        register_mimetype ("message/related", NMO.EMAIL);
        register_mimetype ("text/css", NFO.SOURCE_CODE);
        register_mimetype ("text/csv", NFO.TEXT_DOCUMENT);
        register_mimetype ("text/html", NFO.HTML_DOCUMENT);
        register_mimetype ("text/javascript", NFO.SOURCE_CODE);
        register_mimetype ("text/plain", NFO.TEXT_DOCUMENT);
        register_mimetype ("text/vcard", NCO.CONTACT);
        register_mimetype ("text/x-c", NFO.SOURCE_CODE);
        register_mimetype ("text/x-c++", NFO.SOURCE_CODE);
        register_mimetype ("text/x-c++src", NFO.SOURCE_CODE);
        register_mimetype ("text/x-chdr", NFO.SOURCE_CODE);
        register_mimetype ("text/x-copying", NFO.SOURCE_CODE);
        register_mimetype ("text/x-credits", NFO.SOURCE_CODE);
        register_mimetype ("text/x-csharp", NFO.SOURCE_CODE);
        register_mimetype ("text/x-csrc", NFO.SOURCE_CODE);
        register_mimetype ("text/x-dsrc", NFO.SOURCE_CODE);
        register_mimetype ("text/x-eiffel", NFO.SOURCE_CODE);
        register_mimetype ("text/x-gettext-translation", NFO.SOURCE_CODE);
        register_mimetype ("text/x-gettext-translation-template", NFO.SOURCE_CODE);
        register_mimetype ("text/x-haskell", NFO.SOURCE_CODE);
        register_mimetype ("text/x-idl", NFO.SOURCE_CODE);
        register_mimetype ("text/x-java", NFO.SOURCE_CODE);
        register_mimetype ("text/x-jquery-tmpl", NFO.SOURCE_CODE);
        register_mimetype ("text/x-latex", NFO.SOURCE_CODE);
        register_mimetype ("text/x-lisp", NFO.SOURCE_CODE);
        register_mimetype ("text/x-lua", NFO.SOURCE_CODE);
        register_mimetype ("text/x-m4", NFO.SOURCE_CODE);
        register_mimetype ("text/x-makefile", NFO.SOURCE_CODE);
        register_mimetype ("text/x-objcsrc", NFO.SOURCE_CODE);
        register_mimetype ("text/x-ocaml", NFO.SOURCE_CODE);
        register_mimetype ("text/x-pascal", NFO.SOURCE_CODE);
        register_mimetype ("text/x-patch", NFO.SOURCE_CODE);
        register_mimetype ("text/x-python", NFO.SOURCE_CODE);
        register_mimetype ("text/x-sql", NFO.SOURCE_CODE);
        register_mimetype ("text/x-tcl", NFO.SOURCE_CODE);
        register_mimetype ("text/x-tex", NFO.SOURCE_CODE);
        register_mimetype ("text/x-troff", NFO.SOURCE_CODE);
        register_mimetype ("text/x-vala", NFO.SOURCE_CODE);
        register_mimetype ("text/x-vhdl", NFO.SOURCE_CODE);
        register_mimetype ("text/xml", NFO.SOURCE_CODE);

        register_mimetype_regex (".*/x-dvi", NFO.PAGINATED_TEXT_DOCUMENT);
        register_mimetype_regex ("application/vnd.ms-excel.*", NFO.SPREADSHEET);
        register_mimetype_regex ("application/vnd.ms-powerpoint.*", NFO.PRESENTATION);
        register_mimetype_regex ("application/vnd.oasis.opendocument.graphics.*", NFO.VECTOR_IMAGE);
        register_mimetype_regex ("application/vnd.oasis.opendocument.presentation.*", NFO.PRESENTATION);
        register_mimetype_regex ("application/vnd.oasis.opendocument.spreadsheet.*", NFO.SPREADSHEET);
        register_mimetype_regex ("application/vnd.oasis.opendocument.text.*", NFO.PAGINATED_TEXT_DOCUMENT);
        register_mimetype_regex ("application/vnd.openxmlformats-officedocument.presentationml.presentation.*", NFO.PRESENTATION);
        register_mimetype_regex ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.*", NFO.SPREADSHEET);
        register_mimetype_regex ("application/vnd.openxmlformats-officedocument.wordprocessingml.document.*", NFO.PAGINATED_TEXT_DOCUMENT);
        register_mimetype_regex ("application/vnd\\..*", NFO.DOCUMENT);
        register_mimetype_regex ("application/x-applix-.*", NFO.DOCUMENT);
        register_mimetype_regex ("audio/.*", NFO.AUDIO);
        register_mimetype_regex ("image/.*", NFO.IMAGE);
        register_mimetype_regex ("video/.*", NFO.VIDEO);

        mimetypes_loaded = true;
    }

    private static void ensure_schemes_loaded ()
    {
        if (schemes_loaded)
            return;

        register_uri_scheme ("file://", NFO.FILE_DATA_OBJECT);
        register_uri_scheme ("http://", NFO.WEB_DATA_OBJECT);
        register_uri_scheme ("https://", NFO.WEB_DATA_OBJECT);
        register_uri_scheme ("ssh://", NFO.REMOTE_DATA_OBJECT);
        register_uri_scheme ("sftp://", NFO.REMOTE_DATA_OBJECT);
        register_uri_scheme ("ftp://", NFO.REMOTE_DATA_OBJECT);
        register_uri_scheme ("dav://", NFO.REMOTE_DATA_OBJECT);
        register_uri_scheme ("davs://", NFO.REMOTE_DATA_OBJECT);
        register_uri_scheme ("smb://", NFO.REMOTE_DATA_OBJECT);

        schemes_loaded = true;
    }

}

// vim:expandtab:ts=4:sw=4
