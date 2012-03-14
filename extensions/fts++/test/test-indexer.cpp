/*
 * Copyright © 2012 Mikkel Kamstrup Erlandsen <mikkel.kamstrup@gmail.com>
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
  zeitgeist_subject_set_text (subject, NULL);
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
  zeitgeist_subject_set_text (subject, NULL);
  zeitgeist_subject_set_mimetype (subject, "application/pdf");

  zeitgeist_event_set_interpretation (event, ZEITGEIST_ZG_MODIFY_EVENT);
  zeitgeist_event_set_manifestation (event, ZEITGEIST_ZG_USER_ACTIVITY);
  zeitgeist_event_set_actor (event, "application://libreoffice-impress.desktop");
  zeitgeist_event_add_subject (event, subject);

  g_object_unref (subject);
  return event;
}

// Steals the event, ref it if you want to keep it
static guint
index_event (Fixture *fix, ZeitgeistEvent *event)
{
  GPtrArray *events;
  guint event_id = 0;
  guint *event_ids;
  int num_events_inserted;

  zeitgeist_event_set_timestamp (event, zeitgeist_timestamp_now ());
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

  while (zeitgeist_indexer_has_pending_tasks (fix->indexer))
  {
    zeitgeist_indexer_process_task (fix->indexer);
  }

  return event_id;
}

static void
test_simple_query (Fixture *fix, gconstpointer data)
{
  guint matches;
  guint event_id;
  ZeitgeistEvent* event;
 
  // add test events to DBs
  event_id = index_event (fix, create_test_event1 ());
  index_event (fix, create_test_event2 ());
  index_event (fix, create_test_event3 ());
  index_event (fix, create_test_event4 ());

  GPtrArray *results =
    zeitgeist_indexer_search (fix->indexer,
                              "text",
                              zeitgeist_time_range_new_anytime (),
                              g_ptr_array_new (),
                              0,
                              10,
                              ZEITGEIST_RESULT_TYPE_MOST_RECENT_EVENTS,
                              &matches,
                              NULL);

  g_assert_cmpuint (matches, >, 0);
  g_assert_cmpuint (results->len, ==, 1);

  event = (ZeitgeistEvent*) results->pdata[0];
  g_assert_cmpuint (zeitgeist_event_get_id (event), ==, event_id);

  ZeitgeistSubject *subject = (ZeitgeistSubject*)
    g_ptr_array_index (zeitgeist_event_get_subjects (event), 0);
  g_assert_cmpstr (zeitgeist_subject_get_text (subject), ==, "text");
}

static void
test_simple_with_filter (Fixture *fix, gconstpointer data)
{
  guint matches;
  guint event_id;
  ZeitgeistEvent* event;

  // add test events to DBs
  index_event (fix, create_test_event1 ());
  index_event (fix, create_test_event2 ());

  GPtrArray *filters = g_ptr_array_new_with_free_func (g_object_unref);
  event = zeitgeist_event_new ();
  zeitgeist_event_set_interpretation (event, ZEITGEIST_NFO_DOCUMENT);
  g_ptr_array_add (filters, event); // steals ref

  GPtrArray *results =
    zeitgeist_indexer_search (fix->indexer,
                              "text",
                              zeitgeist_time_range_new_anytime (),
                              filters,
                              0,
                              10,
                              ZEITGEIST_RESULT_TYPE_MOST_RECENT_EVENTS,
                              &matches,
                              NULL);

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

  GPtrArray *results =
    zeitgeist_indexer_search (fix->indexer,
                              "text",
                              zeitgeist_time_range_new_anytime (),
                              filters,
                              0,
                              10,
                              ZEITGEIST_RESULT_TYPE_MOST_RECENT_EVENTS,
                              &matches,
                              NULL);

  g_assert_cmpuint (matches, >, 0);
  g_assert_cmpuint (results->len, ==, 1);

  event = (ZeitgeistEvent*) results->pdata[0];
  g_assert_cmpuint (zeitgeist_event_get_id (event), ==, event_id);

  subject = (ZeitgeistSubject*)
    g_ptr_array_index (zeitgeist_event_get_subjects (event), 0);
  g_assert_cmpstr (zeitgeist_subject_get_text (subject), ==, "text");
}

static void
test_simple_negation (Fixture *fix, gconstpointer data)
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
  zeitgeist_subject_set_interpretation (subject, "!" ZEITGEIST_NFO_IMAGE);
  zeitgeist_event_add_subject (event, subject);
  g_ptr_array_add (filters, event); // steals ref

  GPtrArray *results =
    zeitgeist_indexer_search (fix->indexer,
                              "text",
                              zeitgeist_time_range_new_anytime (),
                              filters,
                              0,
                              10,
                              ZEITGEIST_RESULT_TYPE_MOST_RECENT_EVENTS,
                              &matches,
                              NULL);

  g_assert_cmpuint (matches, ==, 0);
  g_assert_cmpuint (results->len, ==, 0);
}

static void
test_simple_noexpand (Fixture *fix, gconstpointer data)
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
  zeitgeist_subject_set_interpretation (subject, "+" ZEITGEIST_NFO_IMAGE);
  zeitgeist_event_add_subject (event, subject);
  g_ptr_array_add (filters, event); // steals ref

  GPtrArray *results =
    zeitgeist_indexer_search (fix->indexer,
                              "text",
                              zeitgeist_time_range_new_anytime (),
                              filters,
                              0,
                              10,
                              ZEITGEIST_RESULT_TYPE_MOST_RECENT_EVENTS,
                              &matches,
                              NULL);

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

  GPtrArray *results =
    zeitgeist_indexer_search (fix->indexer,
                              "text",
                              zeitgeist_time_range_new_anytime (),
                              filters,
                              0,
                              10,
                              ZEITGEIST_RESULT_TYPE_MOST_RECENT_EVENTS,
                              &matches,
                              NULL);

  g_assert_cmpuint (matches, >, 0);
  g_assert_cmpuint (results->len, ==, 1);

  event = (ZeitgeistEvent*) results->pdata[0];
  g_assert_cmpuint (zeitgeist_event_get_id (event), ==, event_id);

  subject = (ZeitgeistSubject*)
    g_ptr_array_index (zeitgeist_event_get_subjects (event), 0);
  g_assert_cmpstr (zeitgeist_subject_get_text (subject), ==, "text");
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

  GPtrArray *results =
    zeitgeist_indexer_search (fix->indexer,
                              "love",
                              zeitgeist_time_range_new_anytime (),
                              filters,
                              0,
                              10,
                              ZEITGEIST_RESULT_TYPE_MOST_RECENT_EVENTS,
                              &matches,
                              NULL);

  g_assert_cmpuint (matches, >, 0);
  g_assert_cmpuint (results->len, ==, 1);

  event = (ZeitgeistEvent*) results->pdata[0];
  g_assert_cmpuint (zeitgeist_event_get_id (event), ==, event_id);

  subject = (ZeitgeistSubject*)
    g_ptr_array_index (zeitgeist_event_get_subjects (event), 0);
  g_assert_cmpstr (zeitgeist_subject_get_text (subject), ==, "Example.com Wiki Page. Kanji is awesome 漢字");
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

  GPtrArray *results =
    zeitgeist_indexer_search (fix->indexer,
                              "fabulo*",
                              zeitgeist_time_range_new_anytime (),
                              g_ptr_array_new (),
                              0,
                              10,
                              ZEITGEIST_RESULT_TYPE_MOST_RECENT_EVENTS,
                              &matches,
                              NULL);

  g_assert_cmpuint (matches, >, 0);
  g_assert_cmpuint (results->len, ==, 1);

  event = (ZeitgeistEvent*) results->pdata[0];
  g_assert_cmpuint (zeitgeist_event_get_id (event), ==, event_id);
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

  GPtrArray *results =
    zeitgeist_indexer_search (fix->indexer,
                              "signal",
                              zeitgeist_time_range_new_anytime (),
                              g_ptr_array_new (),
                              0,
                              10,
                              ZEITGEIST_RESULT_TYPE_MOST_RECENT_EVENTS,
                              &matches,
                              NULL);

  g_assert_cmpuint (matches, >, 0);
  g_assert_cmpuint (results->len, ==, 1);

  event = (ZeitgeistEvent*) results->pdata[0];
  g_assert_cmpuint (zeitgeist_event_get_id (event), ==, event_id);
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

  GPtrArray *results =
    zeitgeist_indexer_search (fix->indexer,
                              "pdf",
                              zeitgeist_time_range_new_anytime (),
                              event_template,
                              0,
                              10,
                              ZEITGEIST_RESULT_TYPE_MOST_RECENT_EVENTS,
                              &matches,
                              NULL);

  g_assert_cmpuint (matches, >, 0);
  g_assert_cmpuint (results->len, ==, 1);

  event = (ZeitgeistEvent*) results->pdata[0];
  g_assert_cmpuint (zeitgeist_event_get_id (event), ==, event_id);
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

  GPtrArray *results =
    zeitgeist_indexer_search (fix->indexer,
                              "pdf",
                              zeitgeist_time_range_new_anytime (),
                              event_template,
                              0,
                              10,
                              ZEITGEIST_RESULT_TYPE_MOST_RECENT_EVENTS,
                              &matches,
                              NULL);

  g_assert_cmpuint (matches, >, 0);
  g_assert_cmpuint (results->len, ==, 1);

  event = (ZeitgeistEvent*) results->pdata[0];
  g_assert_cmpuint (zeitgeist_event_get_id (event), ==, event_id);
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

  GPtrArray *results =
    zeitgeist_indexer_search (fix->indexer,
                              "pdf",
                              zeitgeist_time_range_new_anytime (),
                              event_template,
                              0,
                              10,
                              ZEITGEIST_RESULT_TYPE_MOST_RECENT_EVENTS,
                              &matches,
                              NULL);

  g_assert_cmpuint (matches, >, 0);
  g_assert_cmpuint (results->len, ==, 1);

  event = (ZeitgeistEvent*) results->pdata[0];
  g_assert_cmpuint (zeitgeist_event_get_id (event), ==, event_id);
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

  GPtrArray *results =
    zeitgeist_indexer_search (fix->indexer,
                              "漢*",
                              zeitgeist_time_range_new_anytime (),
                              g_ptr_array_new (),
                              0,
                              10,
                              ZEITGEIST_RESULT_TYPE_MOST_RECENT_EVENTS,
                              &matches,
                              NULL);

  g_assert_cmpuint (matches, >, 0);
  g_assert_cmpuint (results->len, ==, 1);

  event = (ZeitgeistEvent*) results->pdata[0];
  g_assert_cmpuint (zeitgeist_event_get_id (event), ==, event_id);

  subject = (ZeitgeistSubject*)
    g_ptr_array_index (zeitgeist_event_get_subjects (event), 0);
  g_assert_cmpstr (zeitgeist_subject_get_text (subject), ==, "Example.com Wiki Page. Kanji is awesome 漢字");
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

  GPtrArray *results =
    zeitgeist_indexer_search (fix->indexer,
                              "παράδειγμα",
                              zeitgeist_time_range_new_anytime (),
                              g_ptr_array_new (),
                              0,
                              10,
                              ZEITGEIST_RESULT_TYPE_MOST_RECENT_EVENTS,
                              &matches,
                              NULL);

  g_assert_cmpuint (matches, >, 0);
  g_assert_cmpuint (results->len, ==, 1);

  event = (ZeitgeistEvent*) results->pdata[0];
  g_assert_cmpuint (zeitgeist_event_get_id (event), ==, event_id);

  subject = (ZeitgeistSubject*)
    g_ptr_array_index (zeitgeist_event_get_subjects (event), 0);
  g_assert_cmpstr (zeitgeist_subject_get_text (subject), ==, "IDNwiki");
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

  GPtrArray *results =
    zeitgeist_indexer_search_with_relevancies (fix->indexer,
                              "text",
                              zeitgeist_time_range_new_anytime (),
                              g_ptr_array_new (),
                              ZEITGEIST_STORAGE_STATE_ANY,
                              0,
                              10,
                              (ZeitgeistResultType) 100,
                              &relevancies, &relevancies_size,
                              &matches,
                              NULL);

  g_assert_cmpuint (matches, >, 0);
  g_assert_cmpuint (results->len, ==, 1);
  g_assert_cmpint (relevancies_size, ==, 1);
  g_assert_cmpfloat (relevancies[0], >=, 1.0);

  event = (ZeitgeistEvent*) results->pdata[0];
  g_assert_cmpuint (zeitgeist_event_get_id (event), ==, event_id);

  ZeitgeistSubject *subject = (ZeitgeistSubject*)
    g_ptr_array_index (zeitgeist_event_get_subjects (event), 0);
  g_assert_cmpstr (zeitgeist_subject_get_text (subject), ==, "text");
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

  GPtrArray *results =
    zeitgeist_indexer_search_with_relevancies (fix->indexer,
                              "user*",
                              zeitgeist_time_range_new_anytime (),
                              g_ptr_array_new (),
                              ZEITGEIST_STORAGE_STATE_ANY,
                              0,
                              10,
                              ZEITGEIST_RESULT_TYPE_MOST_RECENT_SUBJECTS,
                              &relevancies, &relevancies_size,
                              &matches,
                              NULL);

  g_assert_cmpuint (matches, >, 0);
  g_assert_cmpuint (results->len, ==, 3);
  g_assert_cmpint (relevancies_size, ==, 3);

  // we're creating event 6 after 5 and 4, so it has to be more recent (but it seems
  // that number of terms indexed matters as well, so careful with the relevancies)
  g_assert_cmpuint (event_id6, ==,
      zeitgeist_event_get_id ((ZeitgeistEvent*) results->pdata[0]));
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
  g_test_add ("/Zeitgeist/FTS/Indexer/SimpleQuery", Fixture, 0,
              setup, test_simple_query, teardown);
  g_test_add ("/Zeitgeist/FTS/Indexer/SimpleWithFilter", Fixture, 0,
              setup, test_simple_with_filter, teardown);
  g_test_add ("/Zeitgeist/FTS/Indexer/SimpleWithValidFilter", Fixture, 0,
              setup, test_simple_with_valid_filter, teardown);
  g_test_add ("/Zeitgeist/FTS/Indexer/SimpleNegation", Fixture, 0,
              setup, test_simple_negation, teardown);
  g_test_add ("/Zeitgeist/FTS/Indexer/SimpleNoexpand", Fixture, 0,
              setup, test_simple_noexpand, teardown);
  g_test_add ("/Zeitgeist/FTS/Indexer/SimpleNoexpandValid", Fixture, 0,
              setup, test_simple_noexpand_valid, teardown);
  g_test_add ("/Zeitgeist/FTS/Indexer/SimpleUnderscores", Fixture, 0,
              setup, test_simple_underscores, teardown);
  g_test_add ("/Zeitgeist/FTS/Indexer/SimpleCamelcase", Fixture, 0,
              setup, test_simple_camelcase, teardown);
  g_test_add ("/Zeitgeist/FTS/Indexer/PrefixWithDashes", Fixture, 0,
              setup, test_simple_dashes_prefix, teardown);
  g_test_add ("/Zeitgeist/FTS/Indexer/PrefixWithDots", Fixture, 0,
              setup, test_simple_dots_prefix, teardown);
  g_test_add ("/Zeitgeist/FTS/Indexer/PrefixWithIntlChars", Fixture, 0,
              setup, test_simple_intl_prefix, teardown);
  g_test_add ("/Zeitgeist/FTS/Indexer/URLUnescape", Fixture, 0,
              setup, test_simple_url_unescape, teardown);
  g_test_add ("/Zeitgeist/FTS/Indexer/IDNSupport", Fixture, 0,
              setup, test_simple_idn_support, teardown);
  g_test_add ("/Zeitgeist/FTS/Indexer/CJK", Fixture, 0,
              setup, test_simple_cjk, teardown);
  g_test_add ("/Zeitgeist/FTS/Indexer/Relevancies", Fixture, 0,
              setup, test_simple_relevancies_query, teardown);
  g_test_add ("/Zeitgeist/FTS/Indexer/RelevanciesSubject", Fixture, 0,
              setup, test_simple_relevancies_subject_query, teardown);

  // get rid of the "rebuilding index..." messages
  g_log_set_handler (NULL, G_LOG_LEVEL_MESSAGE, discard_message, NULL);
}

G_END_DECLS
