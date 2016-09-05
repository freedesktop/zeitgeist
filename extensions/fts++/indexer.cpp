/*
 * Copyright © 2012 Canonical Ltd.
 *             By Michal Hruby <michal.hruby@canonical.com>
 * Copyright © 2012 Mikkel Kamstrup Erlandsen
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
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

#include "indexer.h"
#include "stringutils.h"
#include <xapian.h>
#include <queue>
#include <vector>

#include <gio/gio.h>
#include <gio/gdesktopappinfo.h>

namespace ZeitgeistFTS {

const std::string FILTER_PREFIX_EVENT_INTERPRETATION = "ZGEI";
const std::string FILTER_PREFIX_EVENT_MANIFESTATION = "ZGEM";
const std::string FILTER_PREFIX_ACTOR = "ZGA";
const std::string FILTER_PREFIX_SUBJECT_URI = "ZGSU";
const std::string FILTER_PREFIX_SUBJECT_INTERPRETATION = "ZGSI";
const std::string FILTER_PREFIX_SUBJECT_MANIFESTATION = "ZGSM";
const std::string FILTER_PREFIX_SUBJECT_ORIGIN = "ZGSO";
const std::string FILTER_PREFIX_SUBJECT_MIMETYPE = "ZGST";
const std::string FILTER_PREFIX_SUBJECT_STORAGE = "ZGSS";
const std::string FILTER_PREFIX_XDG_CATEGORY = "AC";

const Xapian::valueno VALUE_EVENT_ID = 0;
const Xapian::valueno VALUE_TIMESTAMP = 1;
const Xapian::valueno VALUE_URI_HASH = 2;
const Xapian::valueno VALUE_ORIGIN_HASH = 3;

#define QUERY_PARSER_FLAGS \
  Xapian::QueryParser::FLAG_PHRASE | Xapian::QueryParser::FLAG_BOOLEAN | \
  Xapian::QueryParser::FLAG_PURE_NOT | Xapian::QueryParser::FLAG_LOVEHATE | \
  Xapian::QueryParser::FLAG_WILDCARD

const std::string FTS_MAIN_DIR = "fts.index";
const int RELEVANCY_RESULT_TYPE = 100;
const int HASH_LENGTH = 16;

void Indexer::Initialize (GError **error)
{
  try
  {
    if (zeitgeist_utils_using_in_memory_database ())
    {
      this->db = new Xapian::WritableDatabase;
      this->db->add_database (Xapian::InMemory::open ());
    }
    else
    {
      gchar *path = g_build_filename (zeitgeist_utils_get_data_path (),
                                      FTS_MAIN_DIR.c_str (), NULL);
      try
      {
        this->db = new Xapian::WritableDatabase (path,
                                                 Xapian::DB_CREATE_OR_OPEN);
      }
      catch (const Xapian::DatabaseCorruptError &xp_error)
      {
        g_message ("Database is corrupt (%s). Overwriting...",
            xp_error.get_msg ().c_str ());
        this->db = new Xapian::WritableDatabase (path,
                                                 Xapian::DB_CREATE_OR_OVERWRITE);
      }
      catch (const Xapian::DatabaseOpeningError &xp_error)
      {
        g_message ("Database is corrupt (%s). Overwriting...",
            xp_error.get_msg ().c_str ());
        this->db = new Xapian::WritableDatabase (path,
                                                 Xapian::DB_CREATE_OR_OVERWRITE);
      }
      g_free (path);
    }

    this->tokenizer = new Xapian::TermGenerator ();
    this->query_parser = new Xapian::QueryParser ();
    this->query_parser->add_prefix ("name", "N");
    this->query_parser->add_prefix ("title", "N");
    this->query_parser->add_prefix ("site", "S");
    this->query_parser->add_prefix ("app", "A");
    this->query_parser->add_boolean_prefix ("zgei",
        FILTER_PREFIX_EVENT_INTERPRETATION);
    this->query_parser->add_boolean_prefix ("zgem", 
        FILTER_PREFIX_EVENT_MANIFESTATION);
    this->query_parser->add_boolean_prefix ("zga", FILTER_PREFIX_ACTOR);
    this->query_parser->add_prefix ("zgsu", FILTER_PREFIX_SUBJECT_URI);
    this->query_parser->add_boolean_prefix ("zgsi",
        FILTER_PREFIX_SUBJECT_INTERPRETATION);
    this->query_parser->add_boolean_prefix ("zgsm",
        FILTER_PREFIX_SUBJECT_MANIFESTATION);
    this->query_parser->add_prefix ("zgso", FILTER_PREFIX_SUBJECT_ORIGIN);
    this->query_parser->add_boolean_prefix ("zgst",
        FILTER_PREFIX_SUBJECT_MIMETYPE);
    this->query_parser->add_boolean_prefix ("zgss",
        FILTER_PREFIX_SUBJECT_STORAGE);
    this->query_parser->add_prefix ("category", FILTER_PREFIX_XDG_CATEGORY);

    this->query_parser->add_valuerangeprocessor (
        new Xapian::NumberValueRangeProcessor (VALUE_EVENT_ID, "id"));
    this->query_parser->add_valuerangeprocessor (
        new Xapian::NumberValueRangeProcessor (VALUE_TIMESTAMP, "ms", false));

    this->query_parser->set_default_op (Xapian::Query::OP_AND);
    this->query_parser->set_database (*this->db);

    this->enquire = new Xapian::Enquire (*this->db);
    
    g_assert (g_checksum_type_get_length (G_CHECKSUM_MD5) == HASH_LENGTH);
    this->checksum = g_checksum_new (G_CHECKSUM_MD5);
    if (!this->checksum) g_critical ("GChecksum initialization failed.");

    GError *error = NULL;
    /* we need to be careful with what we log, for example ubuntuone logs its
     * weird uids and that screws up the index */
    this->uri_schemes_regex = g_regex_new (
        "(file|http[s]?|[s]?ftp|ssh|smb|dav[s]?|application)$", G_REGEX_OPTIMIZE,
        (GRegexMatchFlags) 0, &error);

    if (error)
      g_critical ("Unable to initialize uri scheme regex: %s", error->message);
  }
  catch (const Xapian::Error &xp_error)
  {
    g_set_error_literal (error,
                         ZEITGEIST_ENGINE_ERROR,
                         ZEITGEIST_ENGINE_ERROR_DATABASE_ERROR,
                         xp_error.get_msg ().c_str ());
    this->db = NULL;
  }
}

gint64 Indexer::GetZeitgeistCreationDate ()
{
  ZeitgeistSQLiteDatabase *database = zeitgeist_db_reader_get_database (
      zg_reader);
  return zeitgeist_sq_lite_database_schema_get_creation_date (
      database->database);
}

/**
 * Returns true if and only if the index is good.
 * Otherwise the index should be rebuild.
 */
bool Indexer::CheckIndex ()
{
  std::string db_version (db->get_metadata ("fts_index_version"));
  if (db_version != INDEX_VERSION)
  {
    g_message ("Index must be upgraded. Doing full rebuild");
    return false;
  }
  else if (db->get_doccount () == 0)
  {
    g_message ("Empty index detected. Doing full rebuild");
    return false;
  }

  // Get stored Zeitgeist DB creation date
  gint64 metadata_date;
  std::string metadata_date_str (db->get_metadata ("zg_db_creation_date"));
  if (metadata_date_str.empty ())
    metadata_date = -1;
  else
    metadata_date = g_ascii_strtoll (metadata_date_str.c_str (), NULL, 0);

  // In case the Zeitgeist DB is newer than Xapian, we need to re-build.
  // This may happen if the Zeitgeist DB gets corrupt and is re-created
  // from scratch.
  gint64 database_creation_date = GetZeitgeistCreationDate ();
  if (database_creation_date != metadata_date)
  {
    g_message ("Zeitgeist database has been replaced. Doing full rebuild");
    return false;
  }

  return true;
}

/**
 * Clear the index and create a new empty one
 */
void Indexer::DropIndex ()
{
  try
  {
    if (this->db != NULL)
    {
      this->db->close ();
      delete this->db;
      this->db = NULL;
    }

    if (this->enquire != NULL)
    {
      delete this->enquire;
      this->enquire = NULL;
    }

    if (zeitgeist_utils_using_in_memory_database ())
    {
      this->db = new Xapian::WritableDatabase;
      this->db->add_database (Xapian::InMemory::open ());
    }
    else
    {
      gchar *path = g_build_filename (zeitgeist_utils_get_data_path (),
                                      FTS_MAIN_DIR.c_str (), NULL);
      this->db = new Xapian::WritableDatabase (path,
                                               Xapian::DB_CREATE_OR_OVERWRITE);
      // FIXME: leaks on error
      g_free (path);
    }

    this->query_parser->set_database (*this->db);
    this->enquire = new Xapian::Enquire (*this->db);
  }
  catch (const Xapian::Error &xp_error)
  {
    g_error ("Error ocurred during database reindex: %s",
             xp_error.get_msg ().c_str ());
  }
}

void Indexer::Commit ()
{
  try
  {
    db->commit ();
  }
  catch (Xapian::Error const& e)
  {
    g_warning ("Failed to commit changes: %s", e.get_msg ().c_str ());
  }
}

std::string Indexer::ExpandType (std::string const& prefix,
                                 const gchar* unparsed_uri)
{
  gchar* uri = g_strdup (unparsed_uri);
  gboolean is_negation = zeitgeist_utils_parse_negation (&uri);
  gboolean noexpand = zeitgeist_utils_parse_noexpand (&uri);

  std::string result;
  GList *symbols = NULL;
  symbols = g_list_append (symbols, uri);
  if (!noexpand)
  {
    GList *children = zeitgeist_symbol_get_all_children (uri);
    symbols = g_list_concat (symbols, children);
  }

  for (GList *iter = symbols; iter != NULL; iter = iter->next)
  {
    result += prefix + std::string((gchar*) iter->data);
    if (iter->next != NULL) result += " OR ";
  }

  g_list_free (symbols);
  g_free (uri);

  if (is_negation) result = "NOT (" + result + ")";

  return result;
}

std::string Indexer::CompileEventFilterQuery (GPtrArray *templates)
{
  std::vector<std::string> query;

  for (unsigned i = 0; i < templates->len; i++)
  {
    const gchar* val;
    std::vector<std::string> tmpl;
    ZeitgeistEvent *event = (ZeitgeistEvent*) g_ptr_array_index (templates, i);

    val = zeitgeist_event_get_interpretation (event);
    if (val && val[0] != '\0')
      tmpl.push_back (ExpandType ("zgei:", val));

    val = zeitgeist_event_get_manifestation (event);
    if (val && val[0] != '\0')
      tmpl.push_back (ExpandType ("zgem:", val));

    val = zeitgeist_event_get_actor (event);
    if (val && val[0] != '\0')
      tmpl.push_back ("zga:" + StringUtils::MangleUri (val));

    GPtrArray *subjects = zeitgeist_event_get_subjects (event);
    for (unsigned j = 0; j < subjects->len; j++)
    {
      ZeitgeistSubject *subject = (ZeitgeistSubject*) g_ptr_array_index (subjects, j);
      // For backwards compatibility, we still check URI
      val = zeitgeist_subject_get_uri (subject);
      if (!val || val[0] == '\0')
          val = zeitgeist_subject_get_current_uri (subject);
      if (val && val[0] != '\0')
        tmpl.push_back ("zgsu:" + StringUtils::MangleUri (val));

      val = zeitgeist_subject_get_interpretation (subject);
      if (val && val[0] != '\0')
        tmpl.push_back (ExpandType ("zgsi:", val));

      val = zeitgeist_subject_get_manifestation (subject);
      if (val && val[0] != '\0')
        tmpl.push_back (ExpandType ("zgsm:", val));

      val = zeitgeist_subject_get_origin (subject);
      if (val && val[0] != '\0')
        tmpl.push_back ("zgso:" + StringUtils::MangleUri (val));

      val = zeitgeist_subject_get_mimetype (subject);
      if (val && val[0] != '\0')
        tmpl.push_back (std::string ("zgst:") + val);

      val = zeitgeist_subject_get_storage (subject);
      if (val && val[0] != '\0')
        tmpl.push_back (std::string ("zgss:") + val);
    }

    if (tmpl.size () == 0) continue;

    std::string event_query ("(");
    for (int i = 0; i < tmpl.size (); i++)
    {
      event_query += tmpl[i];
      if (i < tmpl.size () - 1) event_query += ") AND (";
    }
    query.push_back (event_query + ")");
  }

  if (query.size () == 0) return std::string ("");

  std::string result;
  for (int i = 0; i < query.size (); i++)
  {
    result += query[i];
    if (i < query.size () - 1) result += " OR ";
  }
  return result;
}

std::string Indexer::CompileTimeRangeFilterQuery (gint64 start, gint64 end)
{
  // let's use gprinting to be safe
  gchar *q = g_strdup_printf ("%" G_GINT64_FORMAT "..%" G_GINT64_FORMAT "ms",
                              start, end);
  std::string query (q);
  g_free (q);

  return query;
}

/**
 * Adds the filtering rules to the doc. Filtering rules will
 * not affect the relevancy ranking of the event/doc
 */
void Indexer::AddDocFilters (ZeitgeistEvent *event, Xapian::Document &doc)
{
  const gchar* val;

  val = zeitgeist_event_get_interpretation (event);
  if (val && val[0] != '\0')
    doc.add_boolean_term (StringUtils::Truncate (FILTER_PREFIX_EVENT_INTERPRETATION + val));

  val = zeitgeist_event_get_manifestation (event);
  if (val && val[0] != '\0')
    doc.add_boolean_term (StringUtils::Truncate (FILTER_PREFIX_EVENT_MANIFESTATION + val));

  val = zeitgeist_event_get_actor (event);
  if (val && val[0] != '\0')
    doc.add_boolean_term (StringUtils::Truncate (FILTER_PREFIX_ACTOR + StringUtils::MangleUri (val)));

  GPtrArray *subjects = zeitgeist_event_get_subjects (event);
  for (unsigned j = 0; j < subjects->len; j++)
  {
    ZeitgeistSubject *subject = (ZeitgeistSubject*) g_ptr_array_index (subjects, j);
    val = zeitgeist_subject_get_current_uri (subject);
    if (val && val[0] != '\0')
      doc.add_boolean_term (StringUtils::Truncate (FILTER_PREFIX_SUBJECT_URI + StringUtils::MangleUri (val)));

    val = zeitgeist_subject_get_interpretation (subject);
    if (val && val[0] != '\0')
      doc.add_boolean_term (StringUtils::Truncate (FILTER_PREFIX_SUBJECT_INTERPRETATION + val));

    val = zeitgeist_subject_get_manifestation (subject);
    if (val && val[0] != '\0')
      doc.add_boolean_term (StringUtils::Truncate (FILTER_PREFIX_SUBJECT_MANIFESTATION + val));

    val = zeitgeist_subject_get_origin (subject);
    if (val && val[0] != '\0')
      doc.add_boolean_term (StringUtils::Truncate (FILTER_PREFIX_SUBJECT_ORIGIN + StringUtils::MangleUri (val)));

    val = zeitgeist_subject_get_mimetype (subject);
    if (val && val[0] != '\0')
      doc.add_boolean_term (StringUtils::Truncate (FILTER_PREFIX_SUBJECT_MIMETYPE + val));

    val = zeitgeist_subject_get_storage (subject);
    if (val && val[0] != '\0')
      doc.add_boolean_term (StringUtils::Truncate (FILTER_PREFIX_SUBJECT_STORAGE + val));
  }
}

std::string Indexer::PreprocessString (std::string const& input)
{
  if (input.empty ()) return input;

  std::string result (StringUtils::RemoveUnderscores (input));
  // a simple heuristic for the uncamelcaser
  size_t num_digits = StringUtils::CountDigits (result);
  if (result.length () > 5 && num_digits < result.length () / 2)
  {
    // FIXME: handle non-digit ids somehow as well (like rNsGg / yJuSB)
    // FIXME: process digits?, atm they stay attached to the text
    result = StringUtils::UnCamelcase (result);
  }

  std::string folded (StringUtils::AsciiFold (result));
  if (!folded.empty ())
  {
    result += ' ';
    result += folded;
  }

#ifdef DEBUG_PREPROCESSING
  if (input != result)
    g_debug ("processed: %s\n-> %s", input.c_str (), result.c_str ());
#endif

  return result;
}

void Indexer::IndexText (std::string const& text)
{
  tokenizer->index_text (text, 5);
  // this is by definition already a human readable display string,
  // so it shouldn't need removal of underscores and uncamelcase
  tokenizer->index_text (StringUtils::AsciiFold (text), 5);
}

bool Indexer::IndexUri (std::string const& uri, std::string const& origin)
{
  GFile *f = g_file_new_for_uri (uri.c_str ());

  gchar *scheme = g_file_get_uri_scheme (f);
  if (scheme == NULL)
  {
    g_warning ("Invalid URI: %s", uri.c_str ());
    g_object_unref (f);
    return false;
  }

  std::string scheme_str(scheme);
  g_free (scheme);

  // do we support this scheme?
  if (!g_regex_match (uri_schemes_regex, scheme_str.c_str (),
        (GRegexMatchFlags) 0, NULL))
  {
    g_object_unref (f);
    return false;
  }

  if (scheme_str == "file")
  {
    // FIXME: special case some typical filenames (like photos)
    // examples of typical filenames from cameras:
    //    P07-08-08_16.25.JPG
    //    P070608_18.54.JPG
    //    P180308_22.27[1].jpg
    //    P6220111.JPG
    //    PC220006.JPG
    //    DSCN0149.JPG
    //    DSC01166.JPG
    //    SDC12583.JPG
    //    IMGP3199.JPG
    //    IMGP1251-4.jpg
    //    IMG_101_8987.JPG
    //    10052010152.jpg
    //    4867_93080512835_623012835_1949065_8351752_n.jpg
    //    2011-05-29 10.49.37.jpg
    //    V100908_11.24.AVI
    //    video-2011-05-29-15-14-58.mp4

    // get_parse_name will convert escaped characters to UTF-8, but only for
    // the "file" scheme, so using it elsewhere won't be of much help

    gchar *pn = g_file_get_parse_name (f);
    gchar *basename = g_path_get_basename (pn);

    // remove unscores, CamelCase and process digits
    std::string processed (PreprocessString (basename));
    tokenizer->index_text (processed, 5);
    tokenizer->index_text (processed, 5, "N");

    g_free (basename);
    // limit the directory indexing to just a few levels
    //  (the original formula was weight = 5.0 / (1.5^n)
    unsigned path_weights[] = { 3, 2, 1, 0 };
    unsigned weight_index = 0;

    // this should be equal to origin, but we already got a nice utf-8 display
    // name, so we'll use that
    gchar *dir = g_path_get_dirname (pn);
    std::string path_component (dir);
    g_free (dir);
    g_free (pn);

    while (path_component.length () > 2 &&
        weight_index < G_N_ELEMENTS (path_weights))
    {
      // if this is already home directory we don't want it
      if (path_component == home_dir_path) break;

      gchar *name = g_path_get_basename (path_component.c_str ());

      // un-underscore, uncamelcase, ascii fold
      processed = PreprocessString (name);
      tokenizer->index_text (processed, path_weights[weight_index++]);

      dir = g_path_get_dirname (path_component.c_str ());
      path_component = dir;
      g_free (dir);
      g_free (name);
    }
  }
  else if (scheme_str == "mailto")
  {
    // mailto:username@server.com
    size_t scheme_len = scheme_str.length () + 1;
    size_t at_pos = uri.find ('@', scheme_len);
    if (at_pos != std::string::npos)
    {
      tokenizer->index_text (uri.substr (scheme_len, at_pos - scheme_len), 5);
      tokenizer->index_text (uri.substr (at_pos + 1), 1);
    }
  }
  else if (scheme_str.compare (0, 4, "http") == 0)
  {
    // http / https - we'll index just the basename of the uri (minus query
    // part) and the hostname/domain

    // step 1) strip query part
    gchar *basename;
    size_t question_mark = uri.find ('?');
    if (question_mark != std::string::npos)
    {
      std::string stripped (uri, 0, question_mark);
      basename = g_path_get_basename (stripped.c_str ());
    }
    else
    {
      // g_file_get_basename would unescape the uri, we don't want that here
      basename = g_path_get_basename (uri.c_str ());
    }

    // step 2) unescape and check that it's valid utf8
    gchar *unescaped_basename = g_uri_unescape_string (basename, "");
    
    if (g_utf8_validate (unescaped_basename, -1, NULL))
    {
      // remove unscores, CamelCase and process digits
      std::string processed (PreprocessString (unescaped_basename));
      tokenizer->index_text (processed, 5);
      tokenizer->index_text (processed, 5, "N");
    }

    // and also index hostname (taken from origin field if possible)
    std::string host_str (origin.empty () ? uri : origin);
    size_t hostname_start = host_str.find ("://");
    if (hostname_start != std::string::npos)
    {
      std::string hostname (host_str, hostname_start + 3);
      size_t slash_pos = hostname.find ("/");
      if (slash_pos != std::string::npos) hostname.resize (slash_pos);

      // support IDN
      if (g_hostname_is_ascii_encoded (hostname.c_str ()))
      {
        gchar *printable_hostname = g_hostname_to_unicode (hostname.c_str ());
        if (printable_hostname != NULL) hostname = printable_hostname;
        g_free (printable_hostname);
      }

      tokenizer->index_text (hostname, 2);
      tokenizer->index_text (hostname, 2, "N");
      tokenizer->index_text (hostname, 2, "S");
    }

    g_free (unescaped_basename);
    g_free (basename);
  }
  else if (scheme_str == "data")
  {
    // we *really* don't want to index anything with this scheme
  }
  // how about special casing (s)ftp and ssh?
  else
  {
    std::string authority, path, query;
    StringUtils::SplitUri (uri, authority, path, query);

    if (!path.empty ())
    {
      gchar *basename = g_path_get_basename (path.c_str ());
      gchar *unescaped_basename = g_uri_unescape_string (basename, "");

      if (g_utf8_validate (unescaped_basename, -1, NULL))
      {
        std::string capped (StringUtils::Truncate (unescaped_basename, 30));
        tokenizer->index_text (capped, 5);
        tokenizer->index_text (capped, 5, "N");
      }

      // FIXME: rest of the path?
      g_free (unescaped_basename);
      g_free (basename);
    }

    if (!authority.empty ())
    {
      std::string capped (StringUtils::Truncate (authority, 30));

      tokenizer->index_text (capped, 2);
      tokenizer->index_text (capped, 2, "N");
      tokenizer->index_text (capped, 2, "S");
    }
  }

  g_object_unref (f);

  return true;
}

bool Indexer::IndexActor (std::string const& actor, bool is_subject)
{
  GDesktopAppInfo *dai = NULL;
  // check the cache first
  GAppInfo *ai = app_info_cache[actor];

  if (ai == NULL)
  {
    // check also the failed cache
    if (failed_lookups.count (actor) != 0) return false;

    // and now try to load from the disk
    if (g_path_is_absolute (actor.c_str ()))
    {
      dai = g_desktop_app_info_new_from_filename (actor.c_str ());
    }
    else if (g_str_has_prefix (actor.c_str (), "application://"))
    {
      dai = g_desktop_app_info_new (actor.substr (14).c_str ());
    }

    if (dai != NULL)
    {
      ai = G_APP_INFO (dai);
      app_info_cache[actor] = ai;
    }
    else
    {
      // cache failed lookup
      failed_lookups.insert (actor);
      if (clear_failed_id == 0)
      {
        // but clear the failed cache in 30 seconds
        clear_failed_id = g_timeout_add_seconds (30,
            (GSourceFunc) &Indexer::ClearFailedLookupsCb, this);
      }
    }
  }
  else
  {
    dai = G_DESKTOP_APP_INFO (ai);
  }

  if (dai == NULL)
  {
    g_warning ("Unable to get info on %s", actor.c_str ());
    return false;
  }

  const gchar *val;
  unsigned name_weight = is_subject ? 5 : 2;
  unsigned comment_weight = 2;

  val = g_app_info_get_display_name (ai);
  if (val && val[0] != '\0')
  {
    std::string display_name (PreprocessString (val));

    tokenizer->index_text (display_name, name_weight);
    tokenizer->index_text (display_name, name_weight, "A");
  }

  val = g_desktop_app_info_get_generic_name (dai);
  if (val && val[0] != '\0')
  {
    // this shouldn't need uncamelcasing
    std::string generic_name (val);
    std::string generic_name_folded (StringUtils::AsciiFold (generic_name));

    tokenizer->index_text (generic_name, name_weight);
    tokenizer->index_text (generic_name, name_weight, "A");
    tokenizer->index_text (generic_name_folded, name_weight);
    tokenizer->index_text (generic_name_folded, name_weight, "A");
  }

  if (!is_subject) return true;
  // the rest of the code only applies to events with application subject uris:
  // index the comment field, add category terms, index keywords

  val = g_app_info_get_description (ai);
  if (val && val[0] != '\0')
  {
    std::string comment (val);
    tokenizer->index_text (comment, comment_weight);
    tokenizer->index_text (comment, comment_weight, "A");
  }

  val = g_desktop_app_info_get_categories (dai);
  if (val && val[0] != '\0')
  {
    gchar **categories = g_strsplit (val, ";", 0);
    Xapian::Document doc(tokenizer->get_document ());
    for (gchar **iter = categories; *iter != NULL; ++iter)
    {
      // FIXME: what if this isn't ascii? but it should, that's what
      // the fdo menu spec says
      gchar *category = g_ascii_strdown (*iter, -1);
      doc.add_boolean_term (FILTER_PREFIX_XDG_CATEGORY + category);
      g_free (category);
    }
    g_strfreev (categories);
  }

  return true;
}

std::string Indexer::CompileQueryString (const gchar *search_string,
                                         ZeitgeistTimeRange *time_range,
                                         GPtrArray *templates)
{
  std::string query_string (search_string);

  if (templates && templates->len > 0)
  {
    std::string filters (CompileEventFilterQuery (templates));
    query_string = "(" + query_string + ") AND (" + filters + ")";
  }

  if (time_range)
  {
    gint64 start_time = zeitgeist_time_range_get_start (time_range);
    gint64 end_time = zeitgeist_time_range_get_end (time_range);

    if (start_time > 0 || end_time < G_MAXINT64)
    {
      std::string time_filter (CompileTimeRangeFilterQuery (start_time, end_time));
      query_string = "(" + query_string + ") AND (" + time_filter + ")";
    }
  }

  g_debug ("query: %s", query_string.c_str ());
  return query_string;
}

// FIXME: this is missing the Storage State parameter
GPtrArray* Indexer::Search (const gchar *search,
                            ZeitgeistTimeRange *time_range,
                            GPtrArray *templates,
                            guint offset,
                            guint count,
                            ZeitgeistResultType result_type,
                            guint *matches,
                            GError **error)
{
  GPtrArray *results = NULL;
  try
  {
    std::string query_string (CompileQueryString (search, time_range, templates));

    // When sorting by some result types, we need to fetch some extra events
    // from the Xapian index because the final result set will be coalesced
    // on some property of the event
    guint maxhits;
    if (result_type == RELEVANCY_RESULT_TYPE ||
        result_type == ZEITGEIST_RESULT_TYPE_MOST_RECENT_EVENTS ||
        result_type == ZEITGEIST_RESULT_TYPE_LEAST_RECENT_EVENTS ||
        result_type == ZEITGEIST_RESULT_TYPE_MOST_RECENT_SUBJECTS ||
        result_type == ZEITGEIST_RESULT_TYPE_LEAST_RECENT_SUBJECTS ||
        result_type == ZEITGEIST_RESULT_TYPE_MOST_POPULAR_SUBJECTS ||
        result_type == ZEITGEIST_RESULT_TYPE_LEAST_POPULAR_SUBJECTS ||
        result_type == ZEITGEIST_RESULT_TYPE_MOST_RECENT_ORIGIN ||
        result_type == ZEITGEIST_RESULT_TYPE_LEAST_RECENT_ORIGIN ||
        result_type == ZEITGEIST_RESULT_TYPE_MOST_POPULAR_ORIGIN ||
        result_type == ZEITGEIST_RESULT_TYPE_LEAST_POPULAR_ORIGIN)
    {
      maxhits = count;
    }
    else
    {
      maxhits = count * 3;
    }

    if (result_type == RELEVANCY_RESULT_TYPE)
    {
      enquire->set_sort_by_relevance ();
    }
    else
    {
      bool reversed_sort = not
          zeitgeist_result_type_is_sort_order_asc (result_type);
      enquire->set_sort_by_value (VALUE_TIMESTAMP, reversed_sort);
    }

    if (result_type == ZEITGEIST_RESULT_TYPE_MOST_RECENT_SUBJECTS ||
        result_type == ZEITGEIST_RESULT_TYPE_LEAST_RECENT_SUBJECTS ||
        result_type == ZEITGEIST_RESULT_TYPE_MOST_POPULAR_SUBJECTS ||
        result_type == ZEITGEIST_RESULT_TYPE_LEAST_POPULAR_SUBJECTS)
    {
      enquire->set_collapse_key (VALUE_URI_HASH);
    }
    else if (result_type == ZEITGEIST_RESULT_TYPE_MOST_RECENT_ORIGIN ||
        result_type == ZEITGEIST_RESULT_TYPE_LEAST_RECENT_ORIGIN ||
        result_type == ZEITGEIST_RESULT_TYPE_MOST_POPULAR_ORIGIN ||
        result_type == ZEITGEIST_RESULT_TYPE_LEAST_POPULAR_ORIGIN)
    {
      enquire->set_collapse_key (VALUE_ORIGIN_HASH);
    }
    else if (result_type == ZEITGEIST_RESULT_TYPE_MOST_RECENT_EVENTS ||
        result_type == ZEITGEIST_RESULT_TYPE_LEAST_RECENT_EVENTS)
    {
      enquire->set_collapse_key (VALUE_EVENT_ID);
    }

    Xapian::Query q(query_parser->parse_query (query_string, QUERY_PARSER_FLAGS));
    enquire->set_query (q);
    Xapian::MSet hits (enquire->get_mset (offset, maxhits));
    Xapian::doccount hitcount = hits.get_matches_estimated ();

    if (result_type == RELEVANCY_RESULT_TYPE)
    {
      std::vector<unsigned> event_ids;
      for (Xapian::MSetIterator iter = hits.begin (); iter != hits.end (); ++iter)
      {
        Xapian::Document doc(iter.get_document ());
        double unserialized =
          Xapian::sortable_unserialise(doc.get_value (VALUE_EVENT_ID));
        event_ids.push_back (static_cast<unsigned>(unserialized));
      }

      results = zeitgeist_db_reader_get_events (zg_reader,
                                                &event_ids[0],
                                                event_ids.size (),
                                                NULL,
                                                error);
    }
    else
    {
      GPtrArray *event_templates;
      event_templates = g_ptr_array_new_with_free_func (g_object_unref);
      for (Xapian::MSetIterator iter = hits.begin (); iter != hits.end (); ++iter)
      {
        Xapian::Document doc(iter.get_document ());
        double unserialized =
          Xapian::sortable_unserialise(doc.get_value (VALUE_EVENT_ID));
        // this doesn't need ref sinking, does it?
        ZeitgeistEvent *event = zeitgeist_event_new ();
        zeitgeist_event_set_id (event, static_cast<unsigned>(unserialized));
        g_ptr_array_add (event_templates, event);
      }

      if (event_templates->len > 0)
      {
        results = zeitgeist_db_reader_find_events (zg_reader,
                                                   time_range,
                                                   event_templates,
                                                   ZEITGEIST_STORAGE_STATE_ANY,
                                                   0,
                                                   result_type,
                                                   NULL,
                                                   error);
      }
      else
      {
        results = g_ptr_array_new ();
      }

      g_ptr_array_unref (event_templates);
    }

    if (matches)
    {
      *matches = hitcount;
    }
  }
  catch (Xapian::Error const& e)
  {
    g_warning ("Failed to search index: %s", e.get_msg ().c_str ());
    g_set_error_literal (error,
                         ZEITGEIST_ENGINE_ERROR,
                         ZEITGEIST_ENGINE_ERROR_DATABASE_ERROR,
                         e.get_msg ().c_str ());
  }

  return results;
}

static guint32*
find_event_ids_for_combined_template (ZeitgeistDbReader *zg_reader,
                                      ZeitgeistWhereClause *query_clause, // steals
                                      GPtrArray *event_templates, // steals
                                      guint count,
                                      ZeitgeistResultType result_type,
                                      gint *event_ids_length,
                                      GError **error)
{
  g_return_val_if_fail (error == NULL || (error && *error == NULL), NULL);

  ZeitgeistWhereClause *uri_where;
  uri_where = zeitgeist_db_reader_get_where_clause_from_event_templates (
      zg_reader, event_templates, error);
  g_ptr_array_unref (event_templates);

  zeitgeist_where_clause_extend (query_clause, uri_where);
  g_object_unref (G_OBJECT (uri_where));

  guint32 *event_ids;
  event_ids = zeitgeist_db_reader_find_event_ids_for_clause (zg_reader,
      query_clause, count, result_type, event_ids_length, error);

  g_object_unref (query_clause);

  return event_ids;
}

static GPtrArray*
find_events_for_result_type_and_ids (ZeitgeistDbReader *zg_reader,
                                     ZeitgeistTimeRange *time_range,
                                     GPtrArray *templates,
                                     ZeitgeistStorageState storage_state,
                                     unsigned count,
                                     ZeitgeistResultType result_type,
                                     std::vector<unsigned> const& event_ids,
                                     std::map<unsigned, gdouble> &relevancy_map,
                                     GError **error)
{
  GPtrArray *results = NULL;
  results = zeitgeist_db_reader_get_events (zg_reader,
                                            const_cast<unsigned*>(&event_ids[0]),
                                            event_ids.size (),
                                            NULL,
                                            error);

  if (error && *error) return NULL;

  if (result_type == ZEITGEIST_RESULT_TYPE_MOST_RECENT_EVENTS ||
      result_type == ZEITGEIST_RESULT_TYPE_LEAST_RECENT_EVENTS)
    return results;

  if (result_type == ZEITGEIST_RESULT_TYPE_MOST_RECENT_SUBJECTS ||
      result_type == ZEITGEIST_RESULT_TYPE_LEAST_RECENT_SUBJECTS ||
      result_type == ZEITGEIST_RESULT_TYPE_MOST_POPULAR_SUBJECTS ||
      result_type == ZEITGEIST_RESULT_TYPE_LEAST_POPULAR_SUBJECTS)
  {
    // need to get the uris from the events and do another find_events call
    GPtrArray *event_templates;
    event_templates = g_ptr_array_new_with_free_func (g_object_unref);
    std::map<std::string, unsigned> remapper;

    for (unsigned i = 0; i < results->len; i++)
    {
      ZeitgeistEvent* original_event = (ZeitgeistEvent*) results->pdata[i];
      unsigned event_id = zeitgeist_event_get_id (original_event);
      GPtrArray *subjects = zeitgeist_event_get_subjects (original_event);
      if (subjects == NULL) continue;
      for (unsigned j = 0; j < subjects->len; j++)
      {
        const gchar *subj_uri = zeitgeist_subject_get_current_uri (
                (ZeitgeistSubject*) subjects->pdata[j]);
        if (subj_uri == NULL) continue;
        remapper[subj_uri] = event_id;
        ZeitgeistEvent *event = zeitgeist_event_new ();
        ZeitgeistSubject *subject = zeitgeist_subject_new ();
        zeitgeist_subject_set_current_uri (subject, subj_uri);
        zeitgeist_event_take_subject (event, subject);
        g_ptr_array_add (event_templates, event);
      }
    }

    g_ptr_array_unref (results);

    // construct custom where clause which combines the original template
    // with the uris we found
    ZeitgeistWhereClause *where;
    where = zeitgeist_db_reader_get_where_clause_for_query (zg_reader,
        time_range, templates, storage_state, error);

    guint32 *real_event_ids;
    gint real_event_ids_length;

    real_event_ids = find_event_ids_for_combined_template (zg_reader,
        where, event_templates, count, result_type, &real_event_ids_length,
        error);

    if (error && *error) return NULL;

    results = zeitgeist_db_reader_get_events (zg_reader,
                                              real_event_ids,
                                              real_event_ids_length,
                                              NULL,
                                              error);

    g_free (real_event_ids);
    real_event_ids = NULL;

    if (error && *error) return NULL;

    // the event ids might have changed, we need to update the relevancy_map
    for (unsigned i = 0; i < results->len; i++)
    {
      ZeitgeistEvent* original_event = (ZeitgeistEvent*) results->pdata[i];
      unsigned event_id = zeitgeist_event_get_id (original_event);
      GPtrArray *subjects = zeitgeist_event_get_subjects (original_event);
      if (subjects == NULL) continue;
      for (unsigned j = 0; j < subjects->len; j++)
      {
        const gchar *subj_uri = zeitgeist_subject_get_current_uri (
                (ZeitgeistSubject*) subjects->pdata[j]);
        if (subj_uri == NULL) continue;
        relevancy_map[event_id] = relevancy_map[remapper[subj_uri]];
      }
    }

  }
  else if (result_type == ZEITGEIST_RESULT_TYPE_MOST_RECENT_ORIGIN ||
      result_type == ZEITGEIST_RESULT_TYPE_LEAST_RECENT_ORIGIN ||
      result_type == ZEITGEIST_RESULT_TYPE_MOST_POPULAR_ORIGIN ||
      result_type == ZEITGEIST_RESULT_TYPE_LEAST_POPULAR_ORIGIN)
  {
    // need to get the origins from the events and do another find_events call
    GPtrArray *event_templates;
    event_templates = g_ptr_array_new_with_free_func (g_object_unref);
    std::map<std::string, unsigned> remapper;

    for (unsigned i = 0; i < results->len; i++)
    {
      ZeitgeistEvent* original_event = (ZeitgeistEvent*) results->pdata[i];
      unsigned event_id = zeitgeist_event_get_id (original_event);
      GPtrArray *subjects = zeitgeist_event_get_subjects (original_event);
      if (subjects == NULL) continue;
      for (unsigned j = 0; j < subjects->len; j++)
      {
        const gchar *subj_origin = zeitgeist_subject_get_origin ((ZeitgeistSubject*) subjects->pdata[j]);
        if (subj_origin == NULL) continue;
        remapper[subj_origin] = event_id;
        ZeitgeistEvent *event = zeitgeist_event_new ();
        ZeitgeistSubject *subject = zeitgeist_subject_new ();
        zeitgeist_subject_set_origin (subject, subj_origin);
        zeitgeist_event_take_subject (event, subject);
        g_ptr_array_add (event_templates, event);
      }
    }

    g_ptr_array_set_free_func (results, g_object_unref);
    g_ptr_array_unref (results);

    // construct custom where clause which combines the original template
    // with the origins we found
    ZeitgeistWhereClause *where;
    where = zeitgeist_db_reader_get_where_clause_for_query (zg_reader,
        time_range, templates, storage_state, error);

    guint32 *real_event_ids;
    gint real_event_ids_length;

    real_event_ids = find_event_ids_for_combined_template (zg_reader,
        where, event_templates, count, result_type, &real_event_ids_length,
        error);

    if (error && *error) return NULL;

    results = zeitgeist_db_reader_get_events (zg_reader,
                                              real_event_ids,
                                              real_event_ids_length,
                                              NULL,
                                              error);

    if (error && *error) return NULL;

    g_free (real_event_ids);
    real_event_ids = NULL;

    // the event ids might have changed, we need to update the relevancy_map
    for (unsigned i = 0; i < results->len; i++)
    {
      ZeitgeistEvent* original_event = (ZeitgeistEvent*) results->pdata[i];
      unsigned event_id = zeitgeist_event_get_id (original_event);
      GPtrArray *subjects = zeitgeist_event_get_subjects (original_event);
      if (subjects == NULL) continue;
      for (unsigned j = 0; j < subjects->len; j++)
      {
        const gchar *subj_origin = zeitgeist_subject_get_origin ((ZeitgeistSubject*) subjects->pdata[j]);
        if (subj_origin == NULL) continue;
        relevancy_map[event_id] = relevancy_map[remapper[subj_origin]];
      }
    }

  }

  return results;
}

GPtrArray* Indexer::SearchWithRelevancies (const gchar *search,
                                           ZeitgeistTimeRange *time_range,
                                           GPtrArray *templates,
                                           ZeitgeistStorageState storage_state,
                                           guint offset,
                                           guint count,
                                           ZeitgeistResultType result_type,
                                           gdouble **relevancies,
                                           gint *relevancies_size,
                                           guint *matches,
                                           GError **error)
{
  GPtrArray *results = NULL;
  try
  {
    std::string query_string (CompileQueryString (search, time_range, templates));

    guint maxhits = count;

    if (storage_state != ZEITGEIST_STORAGE_STATE_ANY)
    {
      // FIXME: add support for this by grabing (un)available storages
      // from the storage table and appending them to the query
      g_set_error_literal (error,
                           ZEITGEIST_ENGINE_ERROR,
                           ZEITGEIST_ENGINE_ERROR_INVALID_ARGUMENT,
                           "Only ANY storage state is supported");
      return NULL;
    }

    bool reversed_sort = not
        zeitgeist_result_type_is_sort_order_asc (result_type);

    if (result_type == RELEVANCY_RESULT_TYPE)
    {
      enquire->set_sort_by_relevance ();
    }
    else if (result_type == ZEITGEIST_RESULT_TYPE_MOST_RECENT_EVENTS ||
        result_type == ZEITGEIST_RESULT_TYPE_LEAST_RECENT_EVENTS)
    {
      enquire->set_sort_by_relevance_then_value (VALUE_TIMESTAMP, reversed_sort);
      enquire->set_collapse_key (VALUE_EVENT_ID);
    }
    else if (result_type == ZEITGEIST_RESULT_TYPE_MOST_RECENT_SUBJECTS ||
        result_type == ZEITGEIST_RESULT_TYPE_LEAST_RECENT_SUBJECTS ||
        result_type == ZEITGEIST_RESULT_TYPE_MOST_POPULAR_SUBJECTS ||
        result_type == ZEITGEIST_RESULT_TYPE_LEAST_POPULAR_SUBJECTS)
    {
      enquire->set_sort_by_relevance_then_value (VALUE_TIMESTAMP, reversed_sort);
      enquire->set_collapse_key (VALUE_URI_HASH);
    }
    else if (result_type == ZEITGEIST_RESULT_TYPE_MOST_RECENT_ORIGIN ||
        result_type == ZEITGEIST_RESULT_TYPE_LEAST_RECENT_ORIGIN ||
        result_type == ZEITGEIST_RESULT_TYPE_MOST_POPULAR_ORIGIN ||
        result_type == ZEITGEIST_RESULT_TYPE_LEAST_POPULAR_ORIGIN)
    {
      enquire->set_sort_by_relevance_then_value (VALUE_TIMESTAMP, reversed_sort);
      enquire->set_collapse_key (VALUE_ORIGIN_HASH);
    }
    else
    {
      g_set_error_literal (error,
                           ZEITGEIST_ENGINE_ERROR,
                           ZEITGEIST_ENGINE_ERROR_INVALID_ARGUMENT,
                           "Requested result type is not supported");
      return NULL;
    }

    Xapian::Query q(query_parser->parse_query (query_string, QUERY_PARSER_FLAGS));
    enquire->set_query (q);
    Xapian::MSet hits (enquire->get_mset (offset, maxhits));
    Xapian::doccount hitcount = hits.get_matches_estimated ();

    if (result_type == RELEVANCY_RESULT_TYPE)
    {
      std::vector<unsigned> event_ids;
      std::vector<gdouble> relevancy_arr;
      Xapian::MSetIterator iter, end;
      for (iter = hits.begin (), end = hits.end (); iter != end; ++iter)
      {
        Xapian::Document doc(iter.get_document ());
        double unserialized =
          Xapian::sortable_unserialise (doc.get_value (VALUE_EVENT_ID));
        unsigned event_id = static_cast<unsigned>(unserialized);
        event_ids.push_back (event_id);

        double rank = iter.get_percent () / 100.;
        relevancy_arr.push_back (rank);
      }

      results = zeitgeist_db_reader_get_events (zg_reader,
                                                &event_ids[0],
                                                event_ids.size (),
                                                NULL,
                                                error);

      if (error && *error) return NULL;

      if (results->len != relevancy_arr.size ())
      {
        g_warning ("Results don't match relevancies!");
        g_set_error_literal (error,
                             ZEITGEIST_ENGINE_ERROR,
                             ZEITGEIST_ENGINE_ERROR_DATABASE_ERROR,
                             "Internal database error");
        g_ptr_array_set_free_func (results, g_object_unref);
        g_ptr_array_unref (results);
        return NULL;
      }

      if (relevancies)
      {
        *relevancies = (gdouble*) g_memdup (&relevancy_arr[0],
                                            sizeof (gdouble) * results->len);
      }
      if (relevancies_size)
      {
        *relevancies_size = relevancy_arr.size ();
      }
    }
    else
    {
      std::vector<unsigned> event_ids;
      std::map<unsigned, gdouble> relevancy_map;
      Xapian::MSetIterator iter, end;
      for (iter = hits.begin (), end = hits.end (); iter != end; ++iter)
      {
        Xapian::Document doc(iter.get_document ());
        double unserialized =
          Xapian::sortable_unserialise (doc.get_value (VALUE_EVENT_ID));
        unsigned event_id = static_cast<unsigned>(unserialized);

        event_ids.push_back (event_id);

        double rank = iter.get_percent () / 100.;
        if (rank > relevancy_map[event_id])
        {
          relevancy_map[event_id] = rank;
        }
      }

      results = find_events_for_result_type_and_ids (zg_reader, time_range,
                                                     templates, storage_state,
                                                     count, result_type,
                                                     event_ids,
                                                     relevancy_map, error);

      if (error && *error) return NULL;

      if (results == NULL)
      {
        results = g_ptr_array_new ();
        if (relevancies) *relevancies = NULL;
        if (relevancies_size) *relevancies_size = 0;
      }
      else
      {
        if (relevancies)
        {
          *relevancies = g_new (gdouble, results->len);
          for (unsigned i = 0; i < results->len; i++)
          {
            ZeitgeistEvent *event = (ZeitgeistEvent*) g_ptr_array_index (results, i);
            (*relevancies)[i] = relevancy_map[zeitgeist_event_get_id (event)];
          }
        }

        if (relevancies_size)
        {
          *relevancies_size = results->len;
        }
      }
    }

    if (matches)
    {
      *matches = hitcount;
    }
  }
  catch (Xapian::Error const& e)
  {
    g_warning ("Failed to search index: %s", e.get_msg ().c_str ());
    g_set_error_literal (error,
                         ZEITGEIST_ENGINE_ERROR,
                         ZEITGEIST_ENGINE_ERROR_DATABASE_ERROR,
                         e.get_msg ().c_str ());
  }

  return results;
}

static void
get_digest_for_uri (GChecksum *checksum, const gchar *uri,
                    guint8 *digest, gsize *digest_size)
{
  g_checksum_update (checksum, (guchar *) uri, -1);
  g_checksum_get_digest (checksum, digest, digest_size);
  g_checksum_reset (checksum);
  g_assert (digest_size == NULL || *digest_size == HASH_LENGTH);
}

static bool
CheckEventBlacklisted (ZeitgeistEvent *event)
{
  // Blacklist Ubuntu One events...
  const gchar *actor;
  actor = zeitgeist_event_get_actor (event);
  if (g_strcmp0(actor, "dbus://com.ubuntuone.SyncDaemon.service") == 0)
    return true;
  if (g_strcmp0(actor, "dbus://org.desktopcouch.CouchDB.service") == 0)
    return true;

  return false;
}

void Indexer::IndexEvent (ZeitgeistEvent *event)
{
  if (blacklisting_enabled and CheckEventBlacklisted (event))
    return;

  try
  {
    const gchar *val;
    guint event_id = zeitgeist_event_get_id (event);
    g_return_if_fail (event_id > 0);

    g_debug ("Indexing event with ID: %u", event_id);

    Xapian::Document doc;
    doc.add_value (VALUE_EVENT_ID,
                   Xapian::sortable_serialise (static_cast<double>(event_id)));
    doc.add_value (VALUE_TIMESTAMP,
                   Xapian::sortable_serialise (static_cast<double>(zeitgeist_event_get_timestamp (event))));

    tokenizer->set_document (doc);

    val = zeitgeist_event_get_actor (event);
    if (val && val[0] != '\0')
    {
      // it's nice that searching for "gedit" will find all files you worked
      // with in gedit, but the relevancy has to be low
      IndexActor (val, false);
    }

    GPtrArray *subjects = zeitgeist_event_get_subjects (event);
    for (unsigned i = 0; i < subjects->len; i++)
    {
      ZeitgeistSubject *subject;
      subject = (ZeitgeistSubject*) g_ptr_array_index (subjects, i);

      // We use current_uri (vs. uri) where since we care about real stuff,
      // not whatever happened some time ago.
      //
      // This will most likely still be the same as URI (unless something
      // triggers a reindexation of the DB), but at least MOVE_EVENTS
      // will have the updated URI.
      val = zeitgeist_subject_get_current_uri (subject);
      if (val == NULL || val[0] == '\0') continue;

      std::string uri(val);

      if (uri.length () > 512)
      {
        g_warning ("URI too long (%lu). Discarding:\n%s",
                   uri.length (), uri.substr (0, 32).c_str ());
        return; // ignore this event completely...
      }

      guint8 uri_hash[HASH_LENGTH + 1];
      gsize hash_size = HASH_LENGTH;

      // We need the subject URI so we can use Xapian's collapse key feature
      // for *_SUBJECT grouping. However, to save space, we'll just save a hash.
      // A better option would be using URI's id, but for that we'd need a SQL
      // query that'd be subject to races.
      // FIXME(?): This doesn't work for events with multiple subjects.
      get_digest_for_uri (checksum, uri.c_str (), uri_hash, &hash_size);
      doc.add_value (VALUE_URI_HASH, std::string((char *) uri_hash, hash_size));

      size_t colon_pos = uri.find (':');
      // FIXME: current_origin once we have that
      val = zeitgeist_subject_get_origin (subject);
      // make sure the schemas of the URI and origin are the same
      if (val && colon_pos != std::string::npos && strncmp (uri.c_str (), val, colon_pos+1) == 0)
      {
        hash_size = HASH_LENGTH;
        get_digest_for_uri (checksum, val, uri_hash, &hash_size);
        doc.add_value (VALUE_ORIGIN_HASH, std::string((char *) uri_hash, hash_size));
      }

      val = zeitgeist_subject_get_text (subject);
      if (val && val[0] != '\0')
      {
        IndexText (val);
      }

      val = zeitgeist_subject_get_origin (subject);
      std::string origin (val != NULL ? val : "");

      if (uri.compare (0, 14, "application://") == 0)
      {
        if (!IndexActor (uri, true))
          IndexUri (uri, origin);
      }
      else if (!IndexUri (uri, origin))
      {
        // unsupported uri scheme
        return;
      }
    }

    AddDocFilters (event, doc);

    this->db->add_document (doc);
  }
  catch (Xapian::Error const& e)
  {
    g_warning ("Failed to index event: %s", e.get_msg ().c_str ());
  }
}

void Indexer::DeleteEvent (guint32 event_id)
{
  g_debug ("Deleting event with ID: %u", event_id);

  try
  {
    std::string id(Xapian::sortable_serialise (static_cast<double>(event_id)));
    Xapian::Query query (Xapian::Query::OP_VALUE_RANGE, VALUE_EVENT_ID, id, id);

    enquire->set_query(query);
    Xapian::MSet mset = enquire->get_mset(0, 10);

    Xapian::doccount total = mset.get_matches_estimated();
    if (total > 1)
    {
      g_warning ("More than one event found with id '%s", id.c_str ());
    }
    else if (total == 0)
    {
      g_warning ("No event for id '%s'", id.c_str ());
      return;
    }

    Xapian::MSetIterator i, end;
    for (i= mset.begin(), end = mset.end(); i != end; i++)
    {
      db->delete_document (*i);
    }
  }
  catch (Xapian::Error const& e)
  {
    g_warning ("Failed to delete event '%u': %s",
               event_id, e.get_msg().c_str ());
  }
}

void Indexer::SetDbMetadata (std::string const& key, std::string const& value)
{
  try
  {
    db->set_metadata (key, value);
  }
  catch (Xapian::Error const& e)
  {
    g_warning ("Failed to set metadata: %s", e.get_msg ().c_str ());
  }
}

gboolean Indexer::ClearFailedLookupsCb ()
{
  failed_lookups.clear ();

  clear_failed_id = 0;
  return FALSE;
}

} /* namespace */
