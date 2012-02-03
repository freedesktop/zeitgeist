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

#define FILTER_PREFIX_EVENT_INTERPRETATION "ZGEI"
#define FILTER_PREFIX_EVENT_MANIFESTATION "ZGEM"
#define FILTER_PREFIX_ACTOR "ZGA"
#define FILTER_PREFIX_SUBJECT_URI "ZGSU"
#define FILTER_PREFIX_SUBJECT_INTERPRETATION "ZGSI"
#define FILTER_PREFIX_SUBJECT_MANIFESTATION "ZGSM"
#define FILTER_PREFIX_SUBJECT_ORIGIN "ZGSO"
#define FILTER_PREFIX_SUBJECT_MIMETYPE "ZGST"
#define FILTER_PREFIX_SUBJECT_STORAGE "ZGSS"
#define FILTER_PREFIX_XDG_CATEGORY "AC"

#define VALUE_EVENT_ID 0
#define VALUE_TIMESTAMP 1

#define QUERY_PARSER_FLAGS \
  Xapian::QueryParser::FLAG_PHRASE | Xapian::QueryParser::FLAG_BOOLEAN | \
  Xapian::QueryParser::FLAG_PURE_NOT | Xapian::QueryParser::FLAG_LOVEHATE | \
  Xapian::QueryParser::FLAG_WILDCARD

#define FTS_MAIN_DIR "fts.index"
#define INDEX_VERSION "1"

#define MAX_TERM_LENGTH 245

struct Task
{
  virtual bool Process (ZeitgeistIndexer *indexer) = 0;
};

struct IndexEventsTask : Task
{
  GPtrArray *events;
  guint index;

  IndexEventsTask (GPtrArray *event_arr) : events (event_arr), index (0) {}
  ~IndexEventsTask ()
  {
    g_ptr_array_unref (events);
  }

  bool Process (ZeitgeistIndexer *indexer);
};

struct _ZeitgeistIndexer
{
  ZeitgeistDbReader       *zg_reader;

  Xapian::Database        *db;
  Xapian::QueryParser     *query_parser;
  Xapian::Enquire         *enquire;
  Xapian::TermGenerator   *tokenizer;

  typedef std::queue<Task*> TaskQueue;
  TaskQueue                queued_tasks;
  guint                    processing_source_id;

  _ZeitgeistIndexer (ZeitgeistDbReader *reader)
    : zg_reader (reader)
    , db (NULL)
    , query_parser (NULL)
    , enquire (NULL)
    , tokenizer (NULL)
    , processing_source_id (0)
  { }

  ~_ZeitgeistIndexer ()
  {
    if (tokenizer) delete tokenizer;
    if (enquire) delete enquire;
    if (query_parser) delete query_parser;
    if (db) delete db;

    if (processing_source_id != 0)
    {
      g_source_remove (processing_source_id);
    }
  }

  void Initialize (GError **error);
  void CheckIndex ();
  void Reindex ();

  void PushTask (Task* task);
  static gboolean ProcessTasks (ZeitgeistIndexer *indexer);

  void IndexEvent (ZeitgeistEvent *event);
  void DeleteEvent (guint32 event_id);

  GPtrArray* Search (const gchar *search_string,
                     ZeitgeistTimeRange *time_range,
                     GPtrArray *templates,
                     guint offset,
                     guint count,
                     ZeitgeistResultType result_type,
                     GError **error);
};

void ZeitgeistIndexer::Initialize (GError **error)
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
                                      FTS_MAIN_DIR, NULL);
      this->db = new Xapian::WritableDatabase (path,
                                               Xapian::DB_CREATE_OR_OPEN);
      g_free (path);
    }

    this->tokenizer = new Xapian::TermGenerator;
    this->query_parser = new Xapian::QueryParser;
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

    CheckIndex ();
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

void ZeitgeistIndexer::CheckIndex ()
{
  std::string db_version (db->get_metadata ("fts_index_version"));
  if (db_version != INDEX_VERSION)
  {
    g_message ("Index must be upgraded. Doing full rebuild");
    Reindex ();
  }
  else if (db->get_doccount () == 0)
  {
    g_message ("Empty index detected. Doing full rebuild");
    Reindex ();
  }
}

void ZeitgeistIndexer::PushTask (Task* task)
{
  queued_tasks.push (task);

  if (processing_source_id == 0)
  {
    processing_source_id =
      g_idle_add ((GSourceFunc) ZeitgeistIndexer::ProcessTasks, this);
  }
}

gboolean ZeitgeistIndexer::ProcessTasks (ZeitgeistIndexer *indexer)
{
  Task *task;

  task = indexer->queued_tasks.front ();
  bool done = !task->Process (indexer);

  if (done)
  {
    indexer->queued_tasks.pop ();
    delete task;
  }
  else return TRUE;

  bool all_done = indexer->queued_tasks.empty ();
  if (all_done) indexer->processing_source_id = 0;

  return all_done ? FALSE : TRUE;
}

void ZeitgeistIndexer::Reindex ()
{
  this->db->close ();
  delete this->db;
  this->db = NULL;

  // forget any queued tasks
  while (!queued_tasks.empty ())
  {
    delete queued_tasks.front ();
    queued_tasks.pop ();
  }

  if (processing_source_id)
  {
    g_source_remove (processing_source_id);
    processing_source_id = 0;
  }

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
                                      FTS_MAIN_DIR, NULL);
      this->db = new Xapian::WritableDatabase (path,
                                               Xapian::DB_CREATE_OR_OPEN);
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
  
  GError *error = NULL;
  GPtrArray *events;
  GPtrArray *templates = g_ptr_array_new ();
  ZeitgeistTimeRange *time_range = zeitgeist_time_range_new_anytime ();

  g_debug ("asking reader for all events");
  events = zeitgeist_db_reader_find_events (zg_reader,
                                            time_range,
                                            templates,
                                            ZEITGEIST_STORAGE_STATE_ANY,
                                            0,
                                            ZEITGEIST_RESULT_TYPE_MOST_RECENT_EVENTS,
                                            NULL,
                                            &error);

  if (error)
  {
    g_warning ("%s", error->message);
    g_error_free (error);
  }
  else
  {
    g_debug ("reader returned %u events", events->len);

    PushTask (new IndexEventsTask (events));
  }

  g_object_unref (time_range);
  g_ptr_array_unref (templates);
}

GPtrArray* ZeitgeistIndexer::Search (const gchar *search_string,
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

void ZeitgeistIndexer::IndexEvent (ZeitgeistEvent *event)
{
  g_message ("Indexing event with ID: %u", zeitgeist_event_get_id (event));
}

bool IndexEventsTask::Process (ZeitgeistIndexer *indexer)
{
  int processed = 0;
  // process a bunch of events at one time
  for ( ; index < events->len; index++)
  {
    indexer->IndexEvent ((ZeitgeistEvent*) g_ptr_array_index (events, index));
    if (processed++ >= 32) break;
  }

  return index < events->len;
}

/* -------------------- Public methods -------------------- */
ZeitgeistIndexer*
zeitgeist_indexer_new (ZeitgeistDbReader *reader, GError **error)
{
  g_return_val_if_fail (ZEITGEIST_IS_DB_READER (reader), NULL);
  ZeitgeistIndexer *indexer;

  g_message ("Initializing Indexer...");
  g_setenv ("XAPIAN_CJK_NGRAM", "1", TRUE);
  indexer = new ZeitgeistIndexer (reader);
  indexer->Initialize (error);

  if (indexer->db == NULL)
  {
    // Initialize() threw an error
    delete indexer;
    return NULL;
  }

  return indexer;
}

void
zeitgeist_indexer_free (ZeitgeistIndexer* indexer)
{
  g_return_if_fail (indexer != NULL);

  delete indexer;
}

GPtrArray* zeitgeist_indexer_search (ZeitgeistIndexer *indexer,
                                     const gchar *search_string,
                                     ZeitgeistTimeRange *time_range,
                                     GPtrArray *templates,
                                     guint offset,
                                     guint count,
                                     ZeitgeistResultType result_type,
                                     GError **error)
{
  GPtrArray *results;
  g_return_val_if_fail (indexer != NULL, NULL);
  g_return_val_if_fail (search_string != NULL, NULL);

  results = indexer->Search (search_string, time_range, 
                             templates, offset, count, result_type, error);

  return results;
}

