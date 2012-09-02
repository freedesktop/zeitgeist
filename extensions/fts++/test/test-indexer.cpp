/*
 * Copyright © 2012 Mikkel Kamstrup Erlandsen <mikkel.kamstrup@gmail.com>
 * Copyright © 2012 Canonical Ltd.
 *             By Siegfried-A. Gevatter <siegfried.gevatter@collabora.co.uk>
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

#include <glib-object.h>

#include "stringutils.h"
#include "fts.h"
#include <zeitgeist-internal.h>

using namespace ZeitgeistFTS;

typedef struct
{
  ZeitgeistDbReader *db;
  ZeitgeistIndexer *indexer;
} Fixture;

static void setup    (Fixture *fix, gconstpointer data);
static void teardown (Fixture *fix, gconstpointer data);

static void
setup (Fixture *fix, gconstpointer data)
{
  // use in-memory databases for both zg db and fts db
  GError *error = NULL;
  g_setenv ("ZEITGEIST_DATABASE_PATH", ":memory:", TRUE);
  fix->db = ZEITGEIST_DB_READER (zeitgeist_engine_new (&error));

  if (error)
  {
    g_warning ("%s", error->message);
    return;
  }

  fix->indexer = zeitgeist_indexer_new (fix->db, &error);
  if (error)
  {
    g_warning ("%s", error->message);
    return;
  }
}

static void
teardown (Fixture *fix, gconstpointer data)
{
  zeitgeist_indexer_free (fix->indexer);
  g_object_unref (fix->db);
}

static void
assert_nth_result_has_id (GPtrArray* results, guint n, guint32 event_id)
{
  g_assert_cmpuint (n, <, results->len);
  ZeitgeistEvent *event = (ZeitgeistEvent*) results->pdata[n];
  g_assert (event);
  g_assert_cmpuint (zeitgeist_event_get_id (event), ==, event_id);
}

// This function only supports events with a single subject,
// since that's enough for the tests in this file.
static void
assert_nth_result_has_text (GPtrArray* results, int n, const char *text)
{
  g_assert_cmpuint (n, <, results->len);
  ZeitgeistEvent *event = (ZeitgeistEvent*) results->pdata[n];
  g_assert (event);
  g_assert_cmpint (zeitgeist_event_num_subjects (event), ==, 1);
  ZeitgeistSubject *subject = (ZeitgeistSubject*)
    g_ptr_array_index (zeitgeist_event_get_subjects (event), 0);
  g_assert (subject);
  g_assert_cmpstr (zeitgeist_subject_get_text (subject), ==, text);
}

// This function only supports events with a single subject,
// since that's enough for the tests in this file.
static void
assert_nth_result_has_uri (GPtrArray* results, int n, const char *text)
{
  g_assert_cmpuint (n, <, results->len);
  ZeitgeistEvent *event = (ZeitgeistEvent*) results->pdata[n];
  g_assert (event);
  g_assert_cmpint (zeitgeist_event_num_subjects (event), ==, 1);
  ZeitgeistSubject *subject = (ZeitgeistSubject*)
    g_ptr_array_index (zeitgeist_event_get_subjects (event), 0);
  g_assert (subject);
  g_assert_cmpstr (zeitgeist_subject_get_uri (subject), ==, text);
}

static ZeitgeistEvent* create_test_event1 (void)
{
  ZeitgeistEvent *event = zeitgeist_event_new ();
  ZeitgeistSubject *subject = zeitgeist_subject_new ();
  
  zeitgeist_subject_set_interpretation (subject, ZEITGEIST_NFO_RASTER_IMAGE);
  zeitgeist_subject_set_manifestation (subject, ZEITGEIST_NFO_REMOTE_DATA_OBJECT);
  zeitgeist_subject_set_uri (subject, "http://example.com/image.jpg");
  zeitgeist_subject_set_text (subject, "text");
  zeitgeist_subject_set_mimetype (subject, "image/png");

  zeitgeist_event_set_interpretation (event, ZEITGEIST_ZG_ACCESS_EVENT);
  zeitgeist_event_set_manifestation (event, ZEITGEIST_ZG_USER_ACTIVITY);
  zeitgeist_event_set_actor (event, "application://firefox.desktop");
  zeitgeist_event_add_subject (event, subject);

  g_object_unref (subject);
  return event;
}

static ZeitgeistEvent* create_test_event2 (void)
{
  ZeitgeistEvent *event = zeitgeist_event_new ();
  ZeitgeistSubject *subject = zeitgeist_subject_new ();
  
  zeitgeist_subject_set_interpretation (subject, ZEITGEIST_NFO_WEBSITE);
  zeitgeist_subject_set_manifestation (subject, ZEITGEIST_NFO_REMOTE_DATA_OBJECT);
  zeitgeist_subject_set_uri (subject, "http://example.com/I%20Love%20Wikis");
  zeitgeist_subject_set_text (subject, "Example.com Wiki Page. Kanji is awesome 漢字");
  zeitgeist_subject_set_mimetype (subject, "text/html");

  zeitgeist_event_set_interpretation (event, ZEITGEIST_ZG_ACCESS_EVENT);
  zeitgeist_event_set_manifestation (event, ZEITGEIST_ZG_USER_ACTIVITY);
  zeitgeist_event_set_actor (event, "application://firefox.desktop");
  zeitgeist_event_add_subject (event, subject);

  g_object_unref (subject);
  return event;
}

static ZeitgeistEvent* create_test_event3 (void)
{
  ZeitgeistEvent *event = zeitgeist_event_new ();
  ZeitgeistSubject *subject = zeitgeist_subject_new ();
  
  zeitgeist_subject_set_interpretation (subject, ZEITGEIST_NFO_WEBSITE);
  zeitgeist_subject_set_manifestation (subject, ZEITGEIST_NFO_REMOTE_DATA_OBJECT);
  // Greek IDN - stands for http://παράδειγμα.δοκιμή
  zeitgeist_subject_set_uri (subject, "http://xn--hxajbheg2az3al.xn--jxalpdlp/");
  zeitgeist_subject_set_text (subject, "IDNwiki");
  zeitgeist_subject_set_mimetype (subject, "text/html");

  zeitgeist_event_set_interpretation (event, ZEITGEIST_ZG_ACCESS_EVENT);
  zeitgeist_event_set_manifestation (event, ZEITGEIST_ZG_USER_ACTIVITY);
  zeitgeist_event_set_actor (event, "application://firefox.desktop");
  zeitgeist_event_add_subject (event, subject);

  g_object_unref (subject);
  return event;
}

static ZeitgeistEvent* create_test_event4 (void)
{
  ZeitgeistEvent *event = zeitgeist_event_new ();
  ZeitgeistSubject *subject = zeitgeist_subject_new ();
  
  zeitgeist_subject_set_interpretation (subject, ZEITGEIST_NFO_PRESENTATION);
  zeitgeist_subject_set_manifestation (subject, ZEITGEIST_NFO_FILE_DATA_OBJECT);
  zeitgeist_subject_set_uri (subject, "file:///home/username/Documents/my_fabulous_presentation.pdf");
  zeitgeist_subject_set_text (subject, "test texts");
  zeitgeist_subject_set_mimetype (subject, "application/pdf");

  zeitgeist_event_set_interpretation (event, ZEITGEIST_ZG_MODIFY_EVENT);
  zeitgeist_event_set_manifestation (event, ZEITGEIST_ZG_USER_ACTIVITY);
  zeitgeist_event_set_actor (event, "application://libreoffice-impress.desktop");
  zeitgeist_event_add_subject (event, subject);

  g_object_unref (subject);
  return event;
}

static ZeitgeistEvent* create_test_event5 (void)
{
  ZeitgeistEvent *event = zeitgeist_event_new ();
  ZeitgeistSubject *subject = zeitgeist_subject_new ();
  
  zeitgeist_subject_set_interpretation (subject, ZEITGEIST_NFO_SOURCE_CODE);
  zeitgeist_subject_set_manifestation (subject, ZEITGEIST_NFO_FILE_DATA_OBJECT);
  zeitgeist_subject_set_uri (subject, "file:///home/username/projects/GLibSignalImplementation.cpp");
  zeitgeist_subject_set_text (subject, "Because c++ is awesome");
  zeitgeist_subject_set_mimetype (subject, "text/x-c++src");

  zeitgeist_event_set_interpretation (event, ZEITGEIST_ZG_CREATE_EVENT);
  zeitgeist_event_set_manifestation (event, ZEITGEIST_ZG_USER_ACTIVITY);
  zeitgeist_event_set_actor (event, "application://gedit.desktop");
  zeitgeist_event_add_subject (event, subject);

  g_object_unref (subject);
  return event;
}

static ZeitgeistEvent* create_test_event6 (void)
{
  ZeitgeistEvent *event = zeitgeist_event_new ();
  ZeitgeistSubject *subject = zeitgeist_subject_new ();
  
  zeitgeist_subject_set_interpretation (subject, ZEITGEIST_NFO_PRESENTATION);
  zeitgeist_subject_set_manifestation (subject, ZEITGEIST_NFO_FILE_DATA_OBJECT);
  zeitgeist_subject_set_uri (subject, "file:///home/username/Documents/CamelCasePresentation.pdf");
  zeitgeist_subject_set_text (subject, NULL);
  zeitgeist_subject_set_mimetype (subject, "application/pdf");

  zeitgeist_event_set_interpretation (event, ZEITGEIST_ZG_MODIFY_EVENT);
  zeitgeist_event_set_manifestation (event, ZEITGEIST_ZG_USER_ACTIVITY);
  zeitgeist_event_set_actor (event, "application://libreoffice-impress.desktop");
  zeitgeist_event_add_subject (event, subject);

  g_object_unref (subject);
  return event;
}

static ZeitgeistEvent* create_test_event7 (void)
{
  ZeitgeistEvent *event = zeitgeist_event_new ();
  ZeitgeistSubject *subject = zeitgeist_subject_new ();
  
  zeitgeist_subject_set_interpretation (subject, ZEITGEIST_NFO_PRESENTATION);
  zeitgeist_subject_set_manifestation (subject, ZEITGEIST_NFO_FILE_DATA_OBJECT);
  zeitgeist_subject_set_uri (subject, "file:///home/username/directory-with-dashes/and.dot/%C4%8C%20some-intl/CamelCasePresentation.pdf");
  zeitgeist_subject_set_text (subject, "some more texts");
  zeitgeist_subject_set_mimetype (subject, "application/pdf");

  zeitgeist_event_set_interpretation (event, ZEITGEIST_ZG_MODIFY_EVENT);
  zeitgeist_event_set_manifestation (event, ZEITGEIST_ZG_USER_ACTIVITY);
  zeitgeist_event_set_actor (event, "application://libreoffice-impress.desktop");
  zeitgeist_event_add_subject (event, subject);

  g_object_unref (subject);
  return event;
}

static ZeitgeistEvent* create_test_event8 (void)
{
  ZeitgeistEvent *event = zeitgeist_event_new ();
  ZeitgeistSubject *subject = zeitgeist_subject_new ();
  
  zeitgeist_subject_set_interpretation (subject, ZEITGEIST_NFO_PRESENTATION);
  zeitgeist_subject_set_manifestation (subject, ZEITGEIST_NFO_FILE_DATA_OBJECT);
  zeitgeist_subject_set_uri (subject, "file:///home/username/Documents/my_fabulous_presentation.pdf");
  zeitgeist_subject_set_current_uri (subject, "file:///home/username/Awesome.pdf");
  zeitgeist_subject_set_text (subject, "some more textt about a presentation or something");
  zeitgeist_subject_set_mimetype (subject, "application/pdf");

  zeitgeist_event_set_interpretation (event, ZEITGEIST_ZG_MOVE_EVENT);
  zeitgeist_event_set_manifestation (event, ZEITGEIST_ZG_USER_ACTIVITY);
  zeitgeist_event_set_actor (event, "application://nautilus.desktop");
  zeitgeist_event_add_subject (event, subject);

  g_object_unref (subject);
  return event;
}

static ZeitgeistEvent* create_test_event_simple (const char *uri, const char *text)
{
  ZeitgeistEvent *event = zeitgeist_event_new ();
  ZeitgeistSubject *subject = zeitgeist_subject_new ();
  
  zeitgeist_subject_set_interpretation (subject, ZEITGEIST_NFO_DOCUMENT);
  zeitgeist_subject_set_manifestation (subject, ZEITGEIST_NFO_FILE_DATA_OBJECT);
  zeitgeist_subject_set_uri (subject, uri);
  zeitgeist_subject_set_text (subject, text);
  zeitgeist_subject_set_mimetype (subject, "text/plain");

  zeitgeist_event_set_interpretation (event, ZEITGEIST_ZG_ACCESS_EVENT);
  zeitgeist_event_set_manifestation (event, ZEITGEIST_ZG_USER_ACTIVITY);
  zeitgeist_event_set_actor (event, "application://gedit.desktop");
  zeitgeist_event_add_subject (event, subject);

  g_object_unref (subject);
  return event;
}

static void
process_pending (Fixture *fix)
{
  while (zeitgeist_indexer_has_pending_tasks (fix->indexer))
  {
    zeitgeist_indexer_process_task (fix->indexer);
  }
}

// Steals the event, ref it if you want to keep it
static guint
index_event (Fixture *fix, ZeitgeistEvent *event)
{
  GPtrArray *events;
  guint event_id = 0;
  guint *event_ids;
  int num_events_inserted;

  zeitgeist_event_set_timestamp (event, zeitgeist_timestamp_from_now ());
  // add event to DBs
  events = g_ptr_array_new ();
  g_ptr_array_add (events, event);
  event_ids = zeitgeist_engine_insert_events (ZEITGEIST_ENGINE (fix->db),
                                              events, NULL,
                                              &num_events_inserted, NULL);
  g_assert_cmpint (1, ==, num_events_inserted);
  event_id = *event_ids;
  g_ptr_array_unref (events);

  events = g_ptr_array_new_with_free_func (g_object_unref);
  g_ptr_array_add (events, event); // steal event ref
  zeitgeist_indexer_index_events (fix->indexer, events);
  g_ptr_array_unref (events);

  process_pending (fix);

  // sleep for 1 msec to make sure the next event will have a
  // different timestamp
  g_usleep (1000);

  return event_id;
}

static GPtrArray*
search_simple (Fixture *fix, const char *text, GPtrArray *templates,
        ZeitgeistResultType result_type, guint *matches)
{
  if (!templates) templates = g_ptr_array_new ();
  return zeitgeist_indexer_search (fix->indexer,
                            text,
                            zeitgeist_time_range_new_anytime (),
                            templates,
                            0, // offset
                            10, // count
                            result_type,
                            matches,
                            NULL);
}

static GPtrArray*
search_with_count (Fixture *fix, const char *text, GPtrArray *templates,
        ZeitgeistResultType result_type, guint offset, guint count,
        guint *matches)
{
  if (!templates) templates = g_ptr_array_new ();
  return zeitgeist_indexer_search (fix->indexer,
                            text,
                            zeitgeist_time_range_new_anytime (),
                            templates,
                            offset,
                            count,
                            result_type,
                            matches,
                            NULL);
}

static GPtrArray*
search_with_relevancies_simple (Fixture *fix, const char *text,
        GPtrArray *templates, ZeitgeistResultType result_type,
        gdouble **relevancies, gint *relevancies_size, guint *matches)
{
  if (!templates) templates = g_ptr_array_new ();
  return zeitgeist_indexer_search_with_relevancies (fix->indexer,
                            text,
                            zeitgeist_time_range_new_anytime (),
                            templates,
                            ZEITGEIST_STORAGE_STATE_ANY,
                            0, // offset
                            10, // count
                            result_type,
                            relevancies,
                            relevancies_size,
                            matches,
                            NULL);
}

static void
test_simple_query (Fixture *fix, gconstpointer data)
{
  guint matches;
  guint event_id;
 
  // add test events to DBs
  event_id = index_event (fix, create_test_event1 ());
  index_event (fix, create_test_event2 ());
  index_event (fix, create_test_event3 ());
  index_event (fix, create_test_event4 ());

  GPtrArray *results = search_simple (fix, "text", NULL,
          ZEITGEIST_RESULT_TYPE_MOST_RECENT_EVENTS, &matches);

  g_assert_cmpuint (matches, >, 0);
  g_assert_cmpuint (results->len, ==, 1);
  assert_nth_result_has_id (results, 0, event_id);
  assert_nth_result_has_text (results, 0, "text");
}

static void
test_simple_query_empty_database (Fixture *fix, gconstpointer data)
{
  guint matches;

  GPtrArray *results = search_simple (fix,
          "NothingWillEverMatchThisMwhahahaha", NULL,
          ZEITGEIST_RESULT_TYPE_MOST_RECENT_EVENTS, &matches);

  g_assert_cmpuint (matches, ==, 0);
  g_assert_cmpuint (results->len, ==, 0);
}

static void
test_simple_query_no_results (Fixture *fix, gconstpointer data)
{
  // add test events to DBs
  index_event (fix, create_test_event1 ());
  index_event (fix, create_test_event2 ());
  index_event (fix, create_test_event3 ());
  index_event (fix, create_test_event4 ());

  test_simple_query_empty_database (fix, data);
}

static void
test_simple_recognize_schemas (Fixture *fix, gconstpointer data)
{
  guint matches;

  // add test events to DBs
  index_event (fix, create_test_event_simple ("file://a.ok", "getme1"));
  index_event (fix, create_test_event_simple ("ubuntuone://a.bad", "getme2"));

  GPtrArray *results = search_simple (fix, "getme*", NULL,
          ZEITGEIST_RESULT_TYPE_MOST_RECENT_EVENTS, &matches);

  g_assert_cmpuint (matches, >, 0);
  g_assert_cmpuint (results->len, ==, 1);
  assert_nth_result_has_text (results, 0, "getme1");
}

static void
test_simple_with_filter (Fixture *fix, gconstpointer data)
{
  guint matches;
  ZeitgeistEvent* event;

  // add test events to DBs
  index_event (fix, create_test_event1 ());
  index_event (fix, create_test_event2 ());

  GPtrArray *filters = g_ptr_array_new_with_free_func (g_object_unref);
  event = zeitgeist_event_new ();
  zeitgeist_event_set_interpretation (event, ZEITGEIST_NFO_DOCUMENT);
  g_ptr_array_add (filters, event); // steals ref

  GPtrArray *results = search_simple (fix, "text", filters,
          ZEITGEIST_RESULT_TYPE_MOST_RECENT_EVENTS, &matches);

  g_assert_cmpuint (results->len, ==, 0);
  g_assert_cmpuint (matches, ==, 0);
}

static void
test_simple_with_valid_filter (Fixture *fix, gconstpointer data)
{
  guint matches;
  guint event_id;
  ZeitgeistEvent* event;
  ZeitgeistSubject *subject;

  // add test events to DBs
  event_id = index_event (fix, create_test_event1 ());
  index_event (fix, create_test_event2 ());

  GPtrArray *filters = g_ptr_array_new_with_free_func (g_object_unref);
  event = zeitgeist_event_new ();
  subject = zeitgeist_subject_new ();
  zeitgeist_subject_set_interpretation (subject, ZEITGEIST_NFO_IMAGE);
  zeitgeist_event_add_subject (event, subject);
  g_ptr_array_add (filters, event); // steals ref

  GPtrArray *results = search_simple (fix, "text", filters,
          ZEITGEIST_RESULT_TYPE_MOST_RECENT_EVENTS, &matches);

  g_assert_cmpuint (matches, >, 0);
  g_assert_cmpuint (results->len, ==, 1);
  assert_nth_result_has_id (results, 0, event_id);
  assert_nth_result_has_text (results, 0, "text");
}

static void
test_simple_negation (Fixture *fix, gconstpointer data)
{
  guint matches;
  ZeitgeistEvent* event;
  ZeitgeistSubject *subject;

  // add test events to DBs
  index_event (fix, create_test_event1 ());
  index_event (fix, create_test_event2 ());

  GPtrArray *filters = g_ptr_array_new_with_free_func (g_object_unref);
  event = zeitgeist_event_new ();
  subject = zeitgeist_subject_new ();
  zeitgeist_subject_set_interpretation (subject, "!" ZEITGEIST_NFO_IMAGE);
  zeitgeist_event_add_subject (event, subject);
  g_ptr_array_add (filters, event); // steals ref

  GPtrArray *results = search_simple (fix, "text", filters,
          ZEITGEIST_RESULT_TYPE_MOST_RECENT_EVENTS, &matches);

  g_assert_cmpuint (matches, ==, 0);
  g_assert_cmpuint (results->len, ==, 0);
}

static void
test_simple_noexpand (Fixture *fix, gconstpointer data)
{
  guint matches;
  ZeitgeistEvent* event;
  ZeitgeistSubject *subject;

  // add test events to DBs
  index_event (fix, create_test_event1 ());
  index_event (fix, create_test_event2 ());

  GPtrArray *filters = g_ptr_array_new_with_free_func (g_object_unref);
  event = zeitgeist_event_new ();
  subject = zeitgeist_subject_new ();
  zeitgeist_subject_set_interpretation (subject, "+" ZEITGEIST_NFO_IMAGE);
  zeitgeist_event_add_subject (event, subject);
  g_ptr_array_add (filters, event); // steals ref

  GPtrArray *results = search_simple (fix, "text", filters,
          ZEITGEIST_RESULT_TYPE_MOST_RECENT_EVENTS, &matches);

  g_assert_cmpuint (matches, ==, 0);
  g_assert_cmpuint (results->len, ==, 0);
}

static void
test_simple_noexpand_valid (Fixture *fix, gconstpointer data)
{
  guint matches;
  guint event_id;
  ZeitgeistEvent* event;
  ZeitgeistSubject *subject;

  // add test events to DBs
  event_id = index_event (fix, create_test_event1 ());
  index_event (fix, create_test_event2 ());

  GPtrArray *filters = g_ptr_array_new_with_free_func (g_object_unref);
  event = zeitgeist_event_new ();
  subject = zeitgeist_subject_new ();
  zeitgeist_subject_set_interpretation (subject, "+"ZEITGEIST_NFO_RASTER_IMAGE);
  zeitgeist_event_add_subject (event, subject);
  g_ptr_array_add (filters, event); // steals ref

  GPtrArray *results = search_simple (fix, "text", filters,
          ZEITGEIST_RESULT_TYPE_MOST_RECENT_EVENTS, &matches);

  g_assert_cmpuint (matches, >, 0);
  g_assert_cmpuint (results->len, ==, 1);
  assert_nth_result_has_id (results, 0, event_id);
  assert_nth_result_has_text (results, 0, "text");
}

static void
test_simple_url_unescape (Fixture *fix, gconstpointer data)
{
  guint matches;
  guint event_id;
  ZeitgeistEvent* event;
  ZeitgeistSubject *subject;

  // add test events to DBs
  index_event (fix, create_test_event1 ());
  event_id = index_event (fix, create_test_event2 ());

  GPtrArray *filters = g_ptr_array_new_with_free_func (g_object_unref);
  event = zeitgeist_event_new ();
  subject = zeitgeist_subject_new ();
  zeitgeist_subject_set_interpretation (subject, ZEITGEIST_NFO_WEBSITE);
  zeitgeist_event_add_subject (event, subject);
  g_ptr_array_add (filters, event); // steals ref

  GPtrArray *results = search_simple (fix, "love", filters,
          ZEITGEIST_RESULT_TYPE_MOST_RECENT_EVENTS, &matches);

  g_assert_cmpuint (matches, >, 0);
  g_assert_cmpuint (results->len, ==, 1);
  assert_nth_result_has_id (results, 0, event_id);
  assert_nth_result_has_text (results, 0,
          "Example.com Wiki Page. Kanji is awesome 漢字");
}

static void
test_simple_underscores (Fixture *fix, gconstpointer data)
{
  guint matches;
  guint event_id;
  ZeitgeistEvent* event;
  ZeitgeistSubject *subject;

  // add test events to DBs
  index_event (fix, create_test_event1 ());
  index_event (fix, create_test_event2 ());
  index_event (fix, create_test_event3 ());
  event_id = index_event (fix, create_test_event4 ());

  GPtrArray *results = search_simple (fix, "fabulo*", NULL,
          ZEITGEIST_RESULT_TYPE_MOST_RECENT_EVENTS, &matches);

  g_assert_cmpuint (matches, >, 0);
  g_assert_cmpuint (results->len, ==, 1);
  assert_nth_result_has_id (results, 0, event_id);
}

static void
test_simple_escaped_string (Fixture *fix, gconstpointer data) // (LP: #594171)
{
  guint matches;
  guint event_id;
  ZeitgeistEvent* event;
  GPtrArray* results;

  // add test events to DBs
  const char uri[] = "http://encodings.com/percentage-%25-is-fun";
  const char text[] = "%25 is the encoding for a percentage";
  event_id = index_event (fix, create_test_event_simple (uri, text));

  // Search for MostPopularSubjects
  results = search_simple (fix, "percentage", NULL,
          ZEITGEIST_RESULT_TYPE_MOST_POPULAR_SUBJECTS, &matches);

  g_assert_cmpuint (matches, >, 0);
  g_assert_cmpuint (results->len, ==, 1);
  assert_nth_result_has_id (results, 0, event_id);
  assert_nth_result_has_uri (results, 0, uri);
  assert_nth_result_has_text (results, 0, text);
}

static void
test_simple_camelcase (Fixture *fix, gconstpointer data)
{
  guint matches;
  guint event_id;
  ZeitgeistEvent* event;
  ZeitgeistSubject *subject;

  // add test events to DBs
  index_event (fix, create_test_event1 ());
  index_event (fix, create_test_event2 ());
  index_event (fix, create_test_event3 ());
  index_event (fix, create_test_event4 ());
  event_id = index_event (fix, create_test_event5 ());

  GPtrArray *results = search_simple (fix, "signal", NULL,
          ZEITGEIST_RESULT_TYPE_MOST_RECENT_EVENTS, &matches);

  g_assert_cmpuint (matches, >, 0);
  g_assert_cmpuint (results->len, ==, 1);
  assert_nth_result_has_id (results, 0, event_id);
}

static void
test_simple_dashes_prefix (Fixture *fix, gconstpointer data)
{
  guint matches;
  guint event_id;
  ZeitgeistEvent* event;
  ZeitgeistSubject *subject;

  // add test events to DBs
  index_event (fix, create_test_event1 ());
  index_event (fix, create_test_event2 ());
  index_event (fix, create_test_event3 ());
  index_event (fix, create_test_event4 ());
  index_event (fix, create_test_event5 ());
  index_event (fix, create_test_event6 ());
  event_id = index_event (fix, create_test_event7 ());

  GPtrArray *event_template = g_ptr_array_new ();
  event = zeitgeist_event_new ();
  subject = zeitgeist_subject_new ();
  zeitgeist_subject_set_uri (subject,
      "file:///home/username/directory-with-dashes/*");
  zeitgeist_event_add_subject (event, subject);
  g_ptr_array_add (event_template, event);

  GPtrArray *results = search_simple (fix, "pdf", event_template,
          ZEITGEIST_RESULT_TYPE_MOST_RECENT_EVENTS, &matches);

  g_assert_cmpuint (matches, >, 0);
  g_assert_cmpuint (results->len, ==, 1);
  assert_nth_result_has_id (results, 0, event_id);
}

static void
test_simple_dots_prefix (Fixture *fix, gconstpointer data)
{
  guint matches;
  guint event_id;
  ZeitgeistEvent* event;
  ZeitgeistSubject *subject;

  // add test events to DBs
  index_event (fix, create_test_event1 ());
  index_event (fix, create_test_event2 ());
  index_event (fix, create_test_event3 ());
  index_event (fix, create_test_event4 ());
  index_event (fix, create_test_event5 ());
  index_event (fix, create_test_event6 ());
  event_id = index_event (fix, create_test_event7 ());

  GPtrArray *event_template = g_ptr_array_new ();
  event = zeitgeist_event_new ();
  subject = zeitgeist_subject_new ();
  zeitgeist_subject_set_uri (subject,
      "file:///home/username/directory-with-dashes/and.dot/*");
  zeitgeist_event_add_subject (event, subject);
  g_ptr_array_add (event_template, event);

  GPtrArray *results = search_simple (fix, "pdf", event_template,
          ZEITGEIST_RESULT_TYPE_MOST_RECENT_EVENTS, &matches);

  g_assert_cmpuint (matches, >, 0);
  g_assert_cmpuint (results->len, ==, 1);
  assert_nth_result_has_id (results, 0, event_id);
}

static void
test_simple_intl_prefix (Fixture *fix, gconstpointer data)
{
  guint matches;
  guint event_id;
  ZeitgeistEvent* event;
  ZeitgeistSubject *subject;

  // add test events to DBs
  index_event (fix, create_test_event1 ());
  index_event (fix, create_test_event2 ());
  index_event (fix, create_test_event3 ());
  index_event (fix, create_test_event4 ());
  index_event (fix, create_test_event5 ());
  index_event (fix, create_test_event6 ());
  event_id = index_event (fix, create_test_event7 ());

  GPtrArray *event_template = g_ptr_array_new ();
  event = zeitgeist_event_new ();
  subject = zeitgeist_subject_new ();
  zeitgeist_subject_set_uri (subject,
      "file:///home/username/directory-with-dashes/and.dot/%C4%8C*");
  zeitgeist_event_add_subject (event, subject);
  g_ptr_array_add (event_template, event);

  GPtrArray *results = search_simple (fix, "pdf", event_template,
          ZEITGEIST_RESULT_TYPE_MOST_RECENT_EVENTS, &matches);

  g_assert_cmpuint (matches, >, 0);
  g_assert_cmpuint (results->len, ==, 1);
  assert_nth_result_has_id (results, 0, event_id);
}

static void
test_simple_cjk (Fixture *fix, gconstpointer data)
{
  guint matches;
  guint event_id;
  ZeitgeistEvent* event;
  ZeitgeistSubject *subject;

  // add test events to DBs
  index_event (fix, create_test_event1 ());
  event_id = index_event (fix, create_test_event2 ());

  GPtrArray *results = search_simple (fix, "漢*", NULL,
          ZEITGEIST_RESULT_TYPE_MOST_RECENT_EVENTS, &matches);

  g_assert_cmpuint (matches, >, 0);
  g_assert_cmpuint (results->len, ==, 1);
  assert_nth_result_has_id (results, 0, event_id);
  assert_nth_result_has_text (results, 0,
          "Example.com Wiki Page. Kanji is awesome 漢字");
}

static void
test_simple_idn_support (Fixture *fix, gconstpointer data)
{
  guint matches;
  guint event_id;
  ZeitgeistEvent* event;
  ZeitgeistSubject *subject;

  // add test events to DBs
  index_event (fix, create_test_event1 ());
  index_event (fix, create_test_event2 ());
  event_id = index_event (fix, create_test_event3 ());

  GPtrArray *results = search_simple (fix, "παράδειγμα", NULL,
          ZEITGEIST_RESULT_TYPE_MOST_RECENT_EVENTS, &matches);

  g_assert_cmpuint (matches, >, 0);
  g_assert_cmpuint (results->len, ==, 1);
  assert_nth_result_has_id (results, 0, event_id);
  assert_nth_result_has_text (results, 0, "IDNwiki");
}

static void
test_simple_relevancies_query (Fixture *fix, gconstpointer data)
{
  guint matches;
  guint event_id;
  gdouble *relevancies;
  gint relevancies_size;
  ZeitgeistEvent* event;
 
  // add test events to DBs
  event_id = index_event (fix, create_test_event1 ());
  index_event (fix, create_test_event2 ());
  index_event (fix, create_test_event3 ());
  index_event (fix, create_test_event4 ());

  GPtrArray *results = search_with_relevancies_simple (fix, "text", NULL,
          ZEITGEIST_RESULT_TYPE_MOST_RECENT_SUBJECTS,
          &relevancies, &relevancies_size, &matches);

  g_assert_cmpuint (matches, >, 0);
  g_assert_cmpuint (results->len, ==, 1);
  g_assert_cmpint (relevancies_size, ==, 1);
  g_assert_cmpfloat (relevancies[0], >=, 1.0);
  assert_nth_result_has_id (results, 0, event_id);
  assert_nth_result_has_text (results, 0, "text");
}

static void
test_simple_relevancies_subject_query (Fixture *fix, gconstpointer data)
{
  guint matches;
  gdouble *relevancies;
  gint relevancies_size;
  guint event_id4, event_id5, event_id6;
 
  // add test events to DBs
  index_event (fix, create_test_event1 ());
  index_event (fix, create_test_event2 ());
  index_event (fix, create_test_event3 ());
  event_id4 = index_event (fix, create_test_event4 ());
  usleep (50000);
  event_id5 = index_event (fix, create_test_event5 ());
  usleep (50000);
  event_id6 = index_event (fix, create_test_event6 ());

  GPtrArray *results = search_with_relevancies_simple (fix, "user*", NULL,
          ZEITGEIST_RESULT_TYPE_MOST_RECENT_SUBJECTS,
          &relevancies, &relevancies_size, &matches);

  g_assert_cmpuint (matches, >, 0);
  g_assert_cmpuint (results->len, ==, 3);
  g_assert_cmpint (relevancies_size, ==, 3);

  // we're creating event 6 after 5 and 4, so it has to be more recent (but it seems
  // that number of terms indexed matters as well, so careful with the relevancies)
  assert_nth_result_has_id (results, 0, event_id6);
}

static void
test_simple_move_event (Fixture *fix, gconstpointer data)
{
  guint matches;
  guint event_id;
  ZeitgeistEvent* event;
 
  // add test events to DBs
  index_event (fix, create_test_event1 ());
  index_event (fix, create_test_event4 ());
  event_id = index_event (fix, create_test_event8 ());

  GPtrArray *results = search_simple (fix, "awesome", NULL,
          ZEITGEIST_RESULT_TYPE_MOST_RECENT_EVENTS, &matches);

  g_assert_cmpuint (matches, >, 0);
  g_assert_cmpuint (results->len, ==, 1);
  assert_nth_result_has_id (results, 0, event_id);
}

static void
test_query_most_recent (Fixture *fix, gconstpointer data)
{
  guint matches;
  guint event_id1, event_id2, event_id3, event_id4;
  ZeitgeistEvent* event;
  GPtrArray* results;
  gdouble *relevancies;
  gint relevancies_size;
 
  // add test events to DBs
  event_id1 = index_event (fix, create_test_event1 ());
  event_id2 = index_event (fix, create_test_event2 ());
  event_id3 = index_event (fix, create_test_event3 ());
  event_id4 = index_event (fix, create_test_event4 ());

  for (int i = 0; i < 4; ++i)
  {
    if (i == 0)
    {
      // Search for MostRecentEvents
      results = search_simple (fix, "*text*", NULL,
              ZEITGEIST_RESULT_TYPE_MOST_RECENT_EVENTS, &matches);
    }
    else if (i == 1)
    {
      // Search for MostRecentSubjects
      results = search_simple (fix, "*text*", NULL,
              ZEITGEIST_RESULT_TYPE_MOST_RECENT_SUBJECTS, &matches);
    }
    else if (i == 2)
    {
      // SearchWithRelevancies for MostRecentEvents
      GPtrArray *results = search_with_relevancies_simple (fix, "*text*", NULL,
          ZEITGEIST_RESULT_TYPE_MOST_RECENT_EVENTS,
          &relevancies, &relevancies_size, &matches);
    }
    else
    {
      // SearchWithRelevancies for MostRecentSubjects
      GPtrArray *results = search_with_relevancies_simple (fix, "*text*", NULL,
          ZEITGEIST_RESULT_TYPE_MOST_RECENT_SUBJECTS,
          &relevancies, &relevancies_size, &matches);
    }

    g_assert_cmpuint (matches, >, 0);
    g_assert_cmpuint (results->len, ==, 2);
    assert_nth_result_has_id (results, 0, event_id4);
    assert_nth_result_has_id (results, 1, event_id1);
  }
}

static void
test_query_least_recent (Fixture *fix, gconstpointer data)
{
  guint matches;
  guint event_id1, event_id2, event_id3, event_id4;
  ZeitgeistEvent* event;
  GPtrArray* results;
  gdouble *relevancies;
  gint relevancies_size;
 
  // add test events to DBs
  event_id1 = index_event (fix, create_test_event1 ());
  event_id2 = index_event (fix, create_test_event2 ());
  event_id3 = index_event (fix, create_test_event3 ());
  event_id4 = index_event (fix, create_test_event4 ());

  for (int i = 0; i < 4; ++i)
  {
    if (i == 0)
    {
      // Search for LeastRecentEvents
      results = search_simple (fix, "*text*", NULL,
              ZEITGEIST_RESULT_TYPE_LEAST_RECENT_EVENTS, &matches);
    }
    else if (i == 1)
    {
      // Search for LeastRecentSubjects
      results = search_simple (fix, "*text*", NULL,
              ZEITGEIST_RESULT_TYPE_LEAST_RECENT_SUBJECTS, &matches);
    }
    else if (i == 2)
    {
      // SearchWithRelevancies for LeastRecentEvents
      GPtrArray *results = search_with_relevancies_simple (fix, "*text*", NULL,
          ZEITGEIST_RESULT_TYPE_LEAST_RECENT_EVENTS,
          &relevancies, &relevancies_size, &matches);
    }
    else
    {
      // SearchWithRelevancies for LeastRecentSubjects
      GPtrArray *results = search_with_relevancies_simple (fix, "*text*", NULL,
          ZEITGEIST_RESULT_TYPE_LEAST_RECENT_SUBJECTS,
          &relevancies, &relevancies_size, &matches);
    }

    g_assert_cmpuint (matches, >, 0);
    g_assert_cmpuint (results->len, ==, 2);
    assert_nth_result_has_id (results, 0, event_id1);
    assert_nth_result_has_id (results, 1, event_id4);
  }
}

static void
test_query_sort_order (Fixture *fix, gconstpointer data)
{
  guint matches;
  guint event_id1, event_id2, event_id3, event_id4;
  ZeitgeistEvent* event;
  GPtrArray* results;
 
  // add test events to DBs
  event_id1 = index_event (fix, create_test_event_simple ("file://uri1", "!sort"));
  event_id2 = index_event (fix, create_test_event_simple ("file://uri2", "+sort"));
  event_id3 = index_event (fix, create_test_event_simple ("file://uri3", "-sort"));

  // Get the single most recent event
  results = search_with_count (fix, "sort!", NULL,
          ZEITGEIST_RESULT_TYPE_MOST_RECENT_EVENTS, 0, 1, &matches);

  g_assert_cmpuint (matches, >, 0);
  g_assert_cmpuint (results->len, ==, 1);
  assert_nth_result_has_id (results, 0, event_id3);
  assert_nth_result_has_text (results, 0, "-sort");

  // Get the single least recent event
  results = search_with_count (fix, "sort!", NULL,
          ZEITGEIST_RESULT_TYPE_LEAST_RECENT_EVENTS, 0, 1, &matches);

  g_assert_cmpuint (matches, >, 0);
  g_assert_cmpuint (results->len, ==, 1);
  assert_nth_result_has_id (results, 0, event_id1);
  assert_nth_result_has_text (results, 0, "!sort");
}

static void
test_query_with_duplicates (Fixture *fix, gconstpointer data)
{
  guint matches;
  guint event_id1, event_id2, event_id3, event_id4;
  ZeitgeistEvent* event;
  GPtrArray* results;
 
  // add test events to DBs
  const char uri1[] = "file:///home/fibonacci/test.py";
  const char uri2[] = "file:///home/fibonacci/win.txt";
  event_id1 = index_event (fix, create_test_event_simple (uri1, "test"));
  event_id2 = index_event (fix, create_test_event_simple (uri1, "test"));
  event_id3 = index_event (fix, create_test_event_simple (uri2, "test"));
  event_id4 = index_event (fix, create_test_event_simple (uri1, "test"));

  // Search for MostRecentEvents
  results = search_simple (fix, "test", NULL,
          ZEITGEIST_RESULT_TYPE_MOST_RECENT_EVENTS, &matches);

  g_assert_cmpuint (matches, >, 0);
  g_assert_cmpuint (results->len, ==, 4);
  assert_nth_result_has_id (results, 0, event_id4);
  assert_nth_result_has_id (results, 1, event_id3);
  assert_nth_result_has_id (results, 2, event_id2);
  assert_nth_result_has_id (results, 3, event_id1);

  // Search for MostRecentSubjects
  results = search_simple (fix, "test", NULL,
          ZEITGEIST_RESULT_TYPE_MOST_RECENT_SUBJECTS, &matches);

  g_assert_cmpuint (matches, >, 0);
  g_assert_cmpuint (results->len, ==, 2);
  assert_nth_result_has_id (results, 0, event_id4);
  assert_nth_result_has_id (results, 1, event_id3);

  // FIXME: these fail
/*
  // Search for MostPopularSubjects
  results = search_simple (fix, "test", NULL,
          ZEITGEIST_RESULT_TYPE_MOST_POPULAR_SUBJECTS, &matches);

  g_assert_cmpuint (matches, >, 0);
  g_assert_cmpuint (results->len, ==, 2);
  assert_nth_result_has_id (results, 0, event_id4);
  assert_nth_result_has_id (results, 1, event_id3);

  // Search for LeastPopularSubjects
  results = search_simple (fix, "test", NULL,
          ZEITGEIST_RESULT_TYPE_LEAST_POPULAR_SUBJECTS, &matches);

  g_assert_cmpuint (matches, >, 0);
  g_assert_cmpuint (results->len, ==, 2);
  assert_nth_result_has_id (results, 0, event_id3);
  assert_nth_result_has_id (results, 1, event_id4); // or event_id1 until stuff gets fixed
*/
}

static void
test_query_most_popular_subjects (Fixture *fix, gconstpointer data)
{
  guint matches;
  guint event_id1, event_id2, event_id3, event_id4, event_id5,
        event_id6, event_id7, event_id8, event_id9;
  ZeitgeistEvent* event;
  GPtrArray* results;
 
  // add test events to DBs
  const char uri1[] = "file:///file1.txt";
  const char uri2[] = "file:///file2.txt";
  const char uri3[] = "file:///file3.txt";
  event_id1 = index_event (fix, create_test_event_simple (uri1, "test"));
  event_id2 = index_event (fix, create_test_event_simple (uri1, "test"));
  event_id3 = index_event (fix, create_test_event_simple (uri2, "test"));
  event_id4 = index_event (fix, create_test_event_simple (uri1, "test"));
  event_id5 = index_event (fix, create_test_event_simple (uri3, "test"));
  event_id6 = index_event (fix, create_test_event_simple (uri2, "test"));
  event_id7 = index_event (fix, create_test_event_simple (uri1, "test"));
  event_id8 = index_event (fix, create_test_event_simple (uri3, "test"));
  event_id9 = index_event (fix, create_test_event_simple (uri3, "test"));

  // Search for MostPopularSubjects
  results = search_simple (fix, "test", NULL,
          ZEITGEIST_RESULT_TYPE_MOST_POPULAR_SUBJECTS, &matches);

  g_assert_cmpuint (matches, >, 0);
  g_assert_cmpuint (results->len, ==, 3);
  assert_nth_result_has_id (results, 0, event_id7);
  assert_nth_result_has_id (results, 1, event_id9);
  assert_nth_result_has_id (results, 2, event_id6);
}

static void
test_index_ignore_ubuntu_one (Fixture *fix, gconstpointer data)
{
  guint matches;
  ZeitgeistEvent *event;
  GPtrArray *results;

  // add test events to DBs
  index_event (fix, create_test_event_simple ("ubuntuone:uuid", "failme"));
  event = create_test_event_simple ("file:///nice%20uri", "failme");
  zeitgeist_event_set_actor (event, "dbus://com.ubuntuone.SyncDaemon.service");
  index_event (fix, event);

  results = search_simple (fix, "failme", NULL,
          ZEITGEIST_RESULT_TYPE_MOST_RECENT_EVENTS, &matches);

  g_assert_cmpuint (results->len, ==, 0);

  // disabling blacklisting
  g_setenv ("ZEITGEIST_FTS_DISABLE_EVENT_BLACKLIST", "1", true);

  // create a new FTS instance
  zeitgeist_indexer_free (fix->indexer);
  GError *error = NULL;
  fix->indexer = zeitgeist_indexer_new (fix->db, &error);
  g_assert (error == NULL);

  // wait for it to rebuild the index
  process_pending (fix);

  results = search_simple (fix, "failme", NULL,
          ZEITGEIST_RESULT_TYPE_MOST_RECENT_EVENTS, &matches);

  g_assert_cmpuint (results->len, ==, 1); // we still don't want ubuntuone:uuid
}

G_BEGIN_DECLS

static void discard_message (const gchar *domain,
                             GLogLevelFlags level,
                             const gchar *msg,
                             gpointer userdata)
{
}

void test_indexer_create_suite (void)
{
  g_test_add ("/Zeitgeist/FTS/Indexer/Simple/Query", Fixture, 0,
              setup, test_simple_query, teardown);
  g_test_add ("/Zeitgeist/FTS/Indexer/Simple/QueryEmptyDatabase", Fixture, 0,
              setup, test_simple_query_empty_database, teardown);
  g_test_add ("/Zeitgeist/FTS/Indexer/Simple/QueryNoResults", Fixture, 0,
              setup, test_simple_query_no_results, teardown);
  g_test_add ("/Zeitgeist/FTS/Indexer/Simple/RecognizeSchemas", Fixture, 0,
              setup, test_simple_recognize_schemas, teardown);
  g_test_add ("/Zeitgeist/FTS/Indexer/Simple/WithFilter", Fixture, 0,
              setup, test_simple_with_filter, teardown);
  g_test_add ("/Zeitgeist/FTS/Indexer/Simple/WithValidFilter", Fixture, 0,
              setup, test_simple_with_valid_filter, teardown);
  g_test_add ("/Zeitgeist/FTS/Indexer/Simple/Negation", Fixture, 0,
              setup, test_simple_negation, teardown);
  g_test_add ("/Zeitgeist/FTS/Indexer/Simple/Noexpand", Fixture, 0,
              setup, test_simple_noexpand, teardown);
  g_test_add ("/Zeitgeist/FTS/Indexer/Simple/NoexpandValid", Fixture, 0,
              setup, test_simple_noexpand_valid, teardown);
  g_test_add ("/Zeitgeist/FTS/Indexer/Simple/Underscores", Fixture, 0,
              setup, test_simple_underscores, teardown);
  g_test_add ("/Zeitgeist/FTS/Indexer/Simple/EscapedString", Fixture, 0,
              setup, test_simple_escaped_string, teardown);
  g_test_add ("/Zeitgeist/FTS/Indexer/Simple/Camelcase", Fixture, 0,
              setup, test_simple_camelcase, teardown);
  g_test_add ("/Zeitgeist/FTS/Indexer/Simple/PrefixWithDashes", Fixture, 0,
              setup, test_simple_dashes_prefix, teardown);
  g_test_add ("/Zeitgeist/FTS/Indexer/Simple/PrefixWithDots", Fixture, 0,
              setup, test_simple_dots_prefix, teardown);
  g_test_add ("/Zeitgeist/FTS/Indexer/Simple/PrefixWithIntlChars", Fixture, 0,
              setup, test_simple_intl_prefix, teardown);
  g_test_add ("/Zeitgeist/FTS/Indexer/Simple/URLUnescape", Fixture, 0,
              setup, test_simple_url_unescape, teardown);
  g_test_add ("/Zeitgeist/FTS/Indexer/Simple/IDNSupport", Fixture, 0,
              setup, test_simple_idn_support, teardown);
  g_test_add ("/Zeitgeist/FTS/Indexer/Simple/CJK", Fixture, 0,
              setup, test_simple_cjk, teardown);
  g_test_add ("/Zeitgeist/FTS/Indexer/Simple/Relevancies", Fixture, 0,
              setup, test_simple_relevancies_query, teardown);
  g_test_add ("/Zeitgeist/FTS/Indexer/Simple/RelevanciesSubject", Fixture, 0,
              setup, test_simple_relevancies_subject_query, teardown);
  g_test_add ("/Zeitgeist/FTS/Indexer/Simple/MoveEvent", Fixture, 0,
              setup, test_simple_move_event, teardown);
  g_test_add ("/Zeitgeist/FTS/Indexer/Query/MostRecent", Fixture, 0,
              setup, test_query_most_recent, teardown);
  g_test_add ("/Zeitgeist/FTS/Indexer/Query/LeastRecent", Fixture, 0,
              setup, test_query_least_recent, teardown);
  g_test_add ("/Zeitgeist/FTS/Indexer/Query/SortOrder", Fixture, 0,
              setup, test_query_sort_order, teardown);
  g_test_add ("/Zeitgeist/FTS/Indexer/Query/Duplicates", Fixture, 0,
              setup, test_query_with_duplicates, teardown);
  // FIXME: this one doesn't work atm
  /*
  g_test_add ("/Zeitgeist/FTS/Indexer/Query/MostPopularSubjects", Fixture, 0,
              setup, test_query_most_popular_subjects, teardown);
  */
  g_test_add ("/Zeitgeist/FTS/Indexer/Index/IgnoreUbuntuOne", Fixture, 0,
              setup, test_index_ignore_ubuntu_one, teardown);

  // get rid of the "rebuilding index..." messages
  g_log_set_handler (NULL, G_LOG_LEVEL_MESSAGE, discard_message, NULL);

  // do not abort on warning()s, eg. when not finding actor information
  g_log_set_always_fatal (G_LOG_LEVEL_CRITICAL);
}

G_END_DECLS
