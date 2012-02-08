/*
 * Copyright (C) 2012 Canonical Ltd
 *               2012 Mikkel Kamstrup Erlandsen
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 3 as
 * published by the Free Software Foundation.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 * Authored by Michal Hruby <michal.hruby@canonical.com>
 *             Mikkel Kamstrup Erlandsen <mikkel.kamstrup@gmail.com>
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

#define QUERY_PARSER_FLAGS \
  Xapian::QueryParser::FLAG_PHRASE | Xapian::QueryParser::FLAG_BOOLEAN | \
  Xapian::QueryParser::FLAG_PURE_NOT | Xapian::QueryParser::FLAG_LOVEHATE | \
  Xapian::QueryParser::FLAG_WILDCARD

const std::string FTS_MAIN_DIR = "ftspp.index";

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
      this->db = new Xapian::WritableDatabase (path,
                                               Xapian::DB_CREATE_OR_OPEN);
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

  return true;
}

/**
 * Clear the index and create a new empty one
 */
void Indexer::DropIndex ()
{
  this->db->close ();
  delete this->db;
  this->db = NULL;

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

void Indexer::Flush ()
{
  db->flush ();
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
      val = zeitgeist_subject_get_uri (subject);
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
    val = zeitgeist_subject_get_uri (subject);
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

void Indexer::IndexText (std::string const& text)
{
  // FIXME: ascii folding!
  tokenizer->index_text (text, 5);
}

void Indexer::IndexUri (std::string const& uri, std::string const& origin)
{
  GFile *f = g_file_new_for_uri (uri.c_str ());

  gchar *scheme = g_file_get_uri_scheme (f);
  g_return_if_fail (scheme != NULL);

  std::string scheme_str(scheme);
  g_free (scheme);

  if (scheme_str == "file")
  {
    // get_parse_name will convert escaped characters to UTF-8, but only for
    // the "file" scheme, so using it elsewhere won't be of much help
    gchar *pn = g_file_get_parse_name (f);
    gchar *basename = g_path_get_basename (pn);

    // FIXME: remove unscores, CamelCase and process digits
    tokenizer->index_text (basename, 5);
    tokenizer->index_text (basename, 5, "N");

    double weight = 5.0;
    // this should be equal to origin, but we already got a nice utf-8 display
    // name, so we'll use that
    gchar *dir = g_path_get_dirname (pn);
    std::string path_component (dir);
    g_free (dir);

    while (path_component.length () > 2) // FIXME: add a limit?
    {
      gchar *name = g_path_get_basename (path_component.c_str ());

      weight /= 1.5;
      tokenizer->index_text (name, static_cast<unsigned> (weight));

      dir = g_path_get_dirname (path_component.c_str ());
      path_component = dir;
      g_free (dir);
      g_free (name);
    }

    g_free (basename);
    g_free (pn);
  }
  else if (scheme_str == "mailto")
  {
    // mailto:username@server.com
    size_t scheme_len = scheme_str.length () + 1;
    size_t at_pos = uri.find ('@', scheme_len);
    if (at_pos == std::string::npos) return;

    tokenizer->index_text (uri.substr (scheme_len, at_pos - scheme_len), 5);
    tokenizer->index_text (uri.substr (at_pos + 1), 1);
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
      std::string stripped (uri, 0, question_mark - 1);
      basename = g_path_get_basename (stripped.c_str ());
    }
    else
    {
      basename = g_file_get_basename (f);
    }

    // step 2) unescape and check that it's valid utf8
    gchar *unescaped_basename = g_uri_unescape_string (basename, "");
    
    if (g_utf8_validate (unescaped_basename, -1, NULL))
    {
      // FIXME: remove unscores, CamelCase and process digits
      tokenizer->index_text (unescaped_basename, 5);
      tokenizer->index_text (unescaped_basename, 5, "N");
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
  else
  {
    // FIXME!
  }

  g_object_unref (f);
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

  // FIXME: ascii folding somewhere

  val = g_app_info_get_display_name (ai);
  if (val && val[0] != '\0')
  {
    std::string display_name (val);
    tokenizer->index_text (display_name, name_weight);
    tokenizer->index_text (display_name, name_weight, "A");
  }

  val = g_desktop_app_info_get_generic_name (dai);
  if (val && val[0] != '\0')
  {
    std::string generic_name (val);
    tokenizer->index_text (generic_name, name_weight);
    tokenizer->index_text (generic_name, name_weight, "A");
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

GPtrArray* Indexer::Search (const gchar *search_string,
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
    std::string query_string(search_string);

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

    // FIXME: which result types coalesce?
    guint maxhits = count * 3;

    if (result_type == 100)
    {
      enquire->set_sort_by_relevance ();
    }
    else
    {
      enquire->set_sort_by_value (VALUE_TIMESTAMP, true);
    }

    g_debug ("query: %s", query_string.c_str ());
    Xapian::Query q(query_parser->parse_query (query_string, QUERY_PARSER_FLAGS));
    enquire->set_query (q);
    Xapian::MSet hits (enquire->get_mset (offset, maxhits));
    Xapian::doccount hitcount = hits.get_matches_estimated ();

    if (result_type == 100)
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
        ZeitgeistTimeRange *time_range = zeitgeist_time_range_new_anytime ();
        results = zeitgeist_db_reader_find_events (zg_reader,
                                                   time_range,
                                                   event_templates,
                                                   ZEITGEIST_STORAGE_STATE_ANY,
                                                   0,
                                                   result_type,
                                                   NULL,
                                                   error);

        g_object_unref (time_range);
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
    g_warning ("Failed to index event: %s", e.get_msg ().c_str ());
    g_set_error_literal (error,
                         ZEITGEIST_ENGINE_ERROR,
                         ZEITGEIST_ENGINE_ERROR_DATABASE_ERROR,
                         e.get_msg ().c_str ());
  }

  return results;
}

void Indexer::IndexEvent (ZeitgeistEvent *event)
{
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

      val = zeitgeist_subject_get_uri (subject);
      if (val == NULL || val[0] == '\0') continue;

      std::string uri(val);

      if (uri.length () > 512)
      {
        g_warning ("URI too long (%lu). Discarding:\n%s",
                   uri.length (), uri.substr (0, 32).c_str ());
        return; // FIXME: ignore this event completely.. really?
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
      else
      {
        IndexUri (uri, origin);
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
  db->set_metadata (key, value);
}

gboolean Indexer::ClearFailedLookupsCb ()
{
  failed_lookups.clear ();

  clear_failed_id = 0;
  return FALSE;
}

} /* namespace */
