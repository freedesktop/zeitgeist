/*
 * Copyright © 2010 Canonical Ltd.
 *             By Mikkel Kamstrup Erlandsen <mikkel.kamstrup@canonical.com>
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
 */

#include <glib.h>
#include <glib-object.h>
#include "zeitgeist.h"

typedef struct
{
  ZeitgeistLog *log;
  GMainLoop    *mainloop;
} Fixture;

static void setup    (Fixture *fix, gconstpointer data);
static void teardown (Fixture *fix, gconstpointer data);

static void
setup (Fixture *fix, gconstpointer data)
{
  fix->log = zeitgeist_log_new ();
  fix->mainloop = g_main_loop_new (NULL, FALSE);
}

static void
teardown (Fixture *fix, gconstpointer data)
{
  g_object_unref (fix->log);
  g_main_loop_unref (fix->mainloop);
}

static gboolean
_quit_main_loop (GMainLoop *mainloop)
{
  g_main_loop_quit (mainloop);
  return FALSE;
}

static void
_on_events_deleted (ZeitgeistLog *log,
                    GAsyncResult *res,
                    GPtrArray    *expected_events)
{
  GError    *error;

  error = NULL;
  zeitgeist_log_delete_events_finish (log, res, &error);
  if (error)
    {
      g_critical ("Failed to get events: %s", error->message);
      g_error_free (error);
      return;
    }

  g_ptr_array_unref (expected_events);
}

static void
_on_events_received (ZeitgeistLog *log,
                     GAsyncResult *res,
                     GPtrArray    *expected_events)
{
  ZeitgeistResultSet *events;
  GArray             *event_ids;
  GError             *error;
  ZeitgeistEvent     *ev, *_ev;
  gint                i;
  guint32             event_id;

  error = NULL;
  events = zeitgeist_log_get_events_finish (log, res, &error);
  if (error)
    {
      g_critical ("Failed to get events: %s", error->message);
      g_error_free (error);
      return;
    }

  /* Assert that we got what we expected, and collect the event ids,
   * so we can delete the events */
  g_assert_cmpint (expected_events->len, ==, zeitgeist_result_set_size(events));
  event_ids = g_array_sized_new (FALSE, FALSE, sizeof (guint32),
                                    zeitgeist_result_set_size(events));
  for (i = 0; i < zeitgeist_result_set_size(events); ++i)
    {
      ev = zeitgeist_result_set_next_value(events);
      _ev = ZEITGEIST_EVENT (g_ptr_array_index (expected_events, i));
      g_assert_cmpstr (zeitgeist_event_get_interpretation (ev), ==,
                       zeitgeist_event_get_interpretation (_ev));
      g_assert_cmpstr (zeitgeist_event_get_manifestation (ev), ==,
                       zeitgeist_event_get_manifestation (_ev));
      g_assert_cmpstr (zeitgeist_event_get_actor (ev), ==,
                       zeitgeist_event_get_actor (_ev));
      g_assert_cmpint (zeitgeist_event_num_subjects (ev), ==,
                       zeitgeist_event_num_subjects (_ev));
      // TODO: compare subjects

      event_id = zeitgeist_event_get_id (ev);
      g_array_append_val (event_ids, event_id);
    }

  /* This method call now owns event_ids */
  zeitgeist_log_delete_events (log, event_ids, NULL,
                               (GAsyncReadyCallback) _on_events_deleted,
                               expected_events);

  g_array_unref (event_ids);
  g_object_unref (events);
}

static void
_on_events_inserted (ZeitgeistLog *log,
                     GAsyncResult *res,
                     GPtrArray    *expected_events)
{
  GArray *event_ids;
  GError *error;

  error = NULL;
  event_ids = zeitgeist_log_insert_events_finish (log, res, &error);
  if (error)
    {
      g_critical ("Failed to insert events: %s", error->message);
      g_error_free (error);
      return;
    }

  g_assert_cmpint (expected_events->len, ==, event_ids->len);

  zeitgeist_log_get_events (log, event_ids, NULL, 
                            (GAsyncReadyCallback) _on_events_received,
                            expected_events);

  g_array_unref (event_ids);
}

static void
test_insert_get_delete (Fixture *fix, gconstpointer data)
{
  ZeitgeistEvent   *ev;
  ZeitgeistSubject *su;
  GPtrArray        *expected_events;


  expected_events = g_ptr_array_new_with_free_func ((GDestroyNotify) g_object_unref);
  ev = zeitgeist_event_new ();
  su = zeitgeist_subject_new ();
  zeitgeist_event_add_subject (ev, su);
  g_ptr_array_add (expected_events, g_object_ref (ev));
  /* ^^ Regarding the extra ref on ev above, it's not normally
   * needed, but we need to keep them alive so we can compare the results
   * against the expected values */

  zeitgeist_event_set_interpretation (ev, "foo://Interp");
  zeitgeist_event_set_manifestation (ev, "foo://Manif");
  zeitgeist_event_set_actor (ev, "app://firefox.desktop");

  zeitgeist_subject_set_uri (su, "file:///tmp/bar.txt");
  zeitgeist_subject_set_interpretation (su, "foo://TextDoc");
  zeitgeist_subject_set_manifestation (su, "foo://File");
  zeitgeist_subject_set_mimetype (su, "text/plain");
  zeitgeist_subject_set_origin (su, "file:///tmp");
  zeitgeist_subject_set_text (su, "bar.txt");
  zeitgeist_subject_set_storage (su, "bfb486f6-f5f8-4296-8871-0cc749cf8ef7");

  /* This method call now owns all events, subjects, and the events array */
  // FIXME: this should be different:
  /* zeitgeist_log_insert_events (fix->log, NULL,
                               (GAsyncReadyCallback) _on_events_inserted,
                               expected_events,
                               ev);
  */
  zeitgeist_log_insert_events (fix->log, expected_events, NULL,
                               (GAsyncReadyCallback) _on_events_inserted,
                               expected_events);
  g_assert_cmpint (expected_events->len, ==, 1);

  g_timeout_add_seconds (1, (GSourceFunc) _quit_main_loop, fix->mainloop);
  g_main_loop_run (fix->mainloop);

}

static void
test_get_default (Fixture *fix, gconstpointer data) {
    ZeitgeistLog *zeitgeist_log1, *zeitgeist_log2;
    zeitgeist_log1 = zeitgeist_log_get_default ();
    zeitgeist_log2 = zeitgeist_log_get_default ();
    g_assert (zeitgeist_log1 == zeitgeist_log2);
}

int
main (int   argc,
      char *argv[])
{
  g_type_init();
  g_test_init (&argc, &argv, NULL);

  g_test_add ("/Zeitgeist/Log/InsertGetDelete", Fixture, NULL,
              setup, test_insert_get_delete, teardown);
  g_test_add ("/Zeitgeist/Log/GetDefault", Fixture, NULL,
              NULL, test_get_default, NULL);

  return g_test_run();
}
