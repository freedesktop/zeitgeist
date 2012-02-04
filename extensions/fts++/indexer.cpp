/*
 * Copyright (C) 2012 Canonical Ltd
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
 *
 */

#include "indexer.h"
#include <xapian.h>
#include <queue>
#include <vector>

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

const std::string FTS_MAIN_DIR = "fts.index";
const std::string INDEX_VERSION = "1";

const int MAX_TERM_LENGTH = 245;

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

GPtrArray* Indexer::Search (const gchar *search_string,
                            ZeitgeistTimeRange *time_range,
                            GPtrArray *templates,
                            guint offset,
                            guint count,
                            ZeitgeistResultType result_type,
                            GError **error)
{
  GPtrArray *results = NULL;
  std::string query_string(search_string);

  if (templates && templates->len > 0)
  {
    // FIXME: query_string = CompileEventFilterQuery (templates);
  }

  // FIXME: time_range value query

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

      results = zeitgeist_db_reader_get_events (zg_reader,
                                                &event_ids[0],
                                                event_ids.size (),
                                                NULL,
                                                error);
    }
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
      g_message ("got id: %u", static_cast<unsigned>(unserialized));
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

  return results;
}

void Indexer::IndexEvent (ZeitgeistEvent *event)
{
  g_message ("Indexing event with ID: %u", zeitgeist_event_get_id (event));
}

} /* namespace */
