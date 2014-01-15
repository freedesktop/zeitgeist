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
#include <gio/gdesktopappinfo.h>

#include "zeitgeist.h"


typedef struct
{
} Fixture;

static void setup    (Fixture *fix, gconstpointer data);
static void teardown (Fixture *fix, gconstpointer data);

static const gchar *old_xdg_data_dirs = NULL;

static void
setup (Fixture *fix, gconstpointer data)
{
  old_xdg_data_dirs = g_getenv ("XDG_DATA_DIRS");
  g_setenv ("XDG_DATA_DIRS", TEST_DIR, TRUE);
}

static void
teardown (Fixture *fix, gconstpointer data)
{
  if (old_xdg_data_dirs != NULL)
    g_setenv ("XDG_DATA_DIRS", old_xdg_data_dirs, TRUE);
}

static void
test_create_empty (Fixture *fix, gconstpointer data)
{
  ZeitgeistEvent *ev;

  ev = zeitgeist_event_new ();

  g_assert_cmpint (0, ==, zeitgeist_event_get_id (ev));
  g_assert_cmpint (0, ==, zeitgeist_event_get_timestamp (ev));
  g_assert_cmpstr (NULL, ==, zeitgeist_event_get_interpretation (ev));
  g_assert_cmpstr (NULL, ==, zeitgeist_event_get_manifestation (ev));
  g_assert_cmpstr (NULL, ==, zeitgeist_event_get_actor (ev));
  g_assert_cmpstr (NULL, ==, zeitgeist_event_get_origin (ev));
  g_assert_cmpint (0, ==, zeitgeist_event_num_subjects (ev));
  g_assert (zeitgeist_event_get_payload (ev) == NULL);

  g_object_unref (ev);
}

static void
test_create_full (Fixture *fix, gconstpointer data)
{
  ZeitgeistEvent *ev;
  ZeitgeistSubject *su;

  /* Test with two subjects, one of them empty */
  ev = zeitgeist_event_new_full (
                   ZEITGEIST_ZG_ACCESS_EVENT,
                   ZEITGEIST_ZG_USER_ACTIVITY,
                   "application://firefox.desktop",
                   NULL,
                   zeitgeist_subject_new_full ("http://example.com",
                                               ZEITGEIST_NFO_WEBSITE,
                                               ZEITGEIST_NFO_REMOTE_DATA_OBJECT,
                                               "text/html",
                                               "http://example.com",
                                               "example.com",
                                               "net"),
                   zeitgeist_subject_new (),
                   NULL);

  g_assert_cmpint (0, ==, zeitgeist_event_get_id (ev));
  g_assert_cmpint (0, ==, zeitgeist_event_get_timestamp (ev));
  g_assert_cmpstr (ZEITGEIST_ZG_ACCESS_EVENT,==, zeitgeist_event_get_interpretation (ev));
  g_assert_cmpstr (ZEITGEIST_ZG_USER_ACTIVITY, ==, zeitgeist_event_get_manifestation (ev));
  g_assert_cmpstr ("application://firefox.desktop", ==, zeitgeist_event_get_actor (ev));
  g_assert (zeitgeist_event_get_origin (ev) == NULL);
  g_assert_cmpint (2, ==, zeitgeist_event_num_subjects (ev));
  g_assert (zeitgeist_event_get_payload (ev) == NULL);

  su = zeitgeist_event_get_subject (ev, 0);
  g_assert_cmpstr ("http://example.com", ==, zeitgeist_subject_get_uri(su));
  g_assert_cmpstr (ZEITGEIST_NFO_WEBSITE, ==, zeitgeist_subject_get_interpretation (su));
  g_assert_cmpstr (ZEITGEIST_NFO_REMOTE_DATA_OBJECT, ==, zeitgeist_subject_get_manifestation (su));
  g_assert_cmpstr ("text/html", ==, zeitgeist_subject_get_mimetype (su));
  g_assert_cmpstr ("http://example.com", ==, zeitgeist_subject_get_origin (su));
  g_assert_cmpstr ("example.com", ==, zeitgeist_subject_get_text (su));
  g_assert_cmpstr ("net", ==, zeitgeist_subject_get_storage (su));
  g_assert (NULL == zeitgeist_subject_get_current_uri (su));

  su = zeitgeist_event_get_subject (ev, 1);
  g_assert (zeitgeist_subject_get_uri(su) == NULL);
  g_assert (zeitgeist_subject_get_interpretation (su) == NULL);
  g_assert (zeitgeist_subject_get_manifestation (su) == NULL);
  g_assert (zeitgeist_subject_get_mimetype (su) == NULL);
  g_assert (zeitgeist_subject_get_origin (su) == NULL);
  g_assert (zeitgeist_subject_get_text (su) == NULL);
  g_assert (zeitgeist_subject_get_storage (su) == NULL);
  g_assert (zeitgeist_subject_get_current_uri (su) == NULL);

  g_object_unref (ev);
}

static void
test_actor_from_app_info (Fixture *fix, gconstpointer data)
{
  ZeitgeistEvent *ev;
  GAppInfo       *appinfo;

  appinfo = G_APP_INFO (g_desktop_app_info_new_from_filename (TEST_DIR"/test.desktop"));
  g_assert (G_IS_APP_INFO (appinfo));

  ev = zeitgeist_event_new ();
  zeitgeist_event_set_actor_from_app_info (ev, appinfo);

  g_assert_cmpstr ("application://test.desktop", ==, zeitgeist_event_get_actor (ev));
}

static void
test_from_variant (Fixture *fix, gconstpointer data)
{
  GVariant *var;
  GVariantBuilder b;
  ZeitgeistEvent *ev;
  ZeitgeistSubject *su;
  GByteArray *payload;
  GError **error;

  error = NULL;
  g_variant_builder_init (&b, G_VARIANT_TYPE ("(" ZEITGEIST_EVENT_SIGNATURE ")"));

  /* Build event data */
  g_variant_builder_open (&b, G_VARIANT_TYPE ("as"));
  g_variant_builder_add (&b, "s", "27");
  g_variant_builder_add (&b, "s", "68");
  g_variant_builder_add (&b, "s", ZEITGEIST_ZG_ACCESS_EVENT);
  g_variant_builder_add (&b, "s", ZEITGEIST_ZG_USER_ACTIVITY);
  g_variant_builder_add (&b, "s", "application://foo.desktop");
  g_variant_builder_close (&b);

  /* Build subjects */
  g_variant_builder_open (&b, G_VARIANT_TYPE ("aas"));
    {
      g_variant_builder_open (&b, G_VARIANT_TYPE ("as"));
      g_variant_builder_add (&b, "s", "file:///tmp/foo.txt");
      g_variant_builder_add (&b, "s", ZEITGEIST_NFO_DOCUMENT);
      g_variant_builder_add (&b, "s", ZEITGEIST_NFO_FILE_DATA_OBJECT);
      g_variant_builder_add (&b, "s", "file:///tmp");
      g_variant_builder_add (&b, "s", "text/plain");
      g_variant_builder_add (&b, "s", "foo.txt");
      g_variant_builder_add (&b, "s", "36e5604e-7e1b-4ebd-bb6a-184c6ea99627");
      g_variant_builder_close (&b);
    }
  g_variant_builder_close (&b);

  /* Build payload */
  g_variant_builder_open (&b, G_VARIANT_TYPE ("ay"));
  g_variant_builder_add (&b, "y", 1);
  g_variant_builder_add (&b, "y", 2);
  g_variant_builder_add (&b, "y", 3);
  g_variant_builder_close (&b);

  var = g_variant_builder_end (&b);
  error = NULL;
  ev = zeitgeist_event_new_from_variant (var, error); // var freed

  g_assert_cmpint (27, ==, zeitgeist_event_get_id (ev));
  g_assert_cmpint (68, ==, zeitgeist_event_get_timestamp (ev));
  g_assert_cmpstr (ZEITGEIST_ZG_ACCESS_EVENT,==, zeitgeist_event_get_interpretation (ev));
  g_assert_cmpstr (ZEITGEIST_ZG_USER_ACTIVITY, ==, zeitgeist_event_get_manifestation (ev));
  g_assert_cmpstr ("application://foo.desktop", ==, zeitgeist_event_get_actor (ev));
  g_assert (zeitgeist_event_get_origin (ev) == NULL);
  g_assert_cmpint (1, ==, zeitgeist_event_num_subjects (ev));

  su = zeitgeist_event_get_subject (ev, 0);
  g_assert_cmpstr ("file:///tmp/foo.txt", ==, zeitgeist_subject_get_uri(su));
  g_assert_cmpstr (ZEITGEIST_NFO_DOCUMENT, ==, zeitgeist_subject_get_interpretation (su));
  g_assert_cmpstr (ZEITGEIST_NFO_FILE_DATA_OBJECT, ==, zeitgeist_subject_get_manifestation (su));
  g_assert_cmpstr ("text/plain", ==, zeitgeist_subject_get_mimetype (su));
  g_assert_cmpstr ("file:///tmp", ==, zeitgeist_subject_get_origin (su));
  g_assert_cmpstr ("foo.txt", ==, zeitgeist_subject_get_text (su));
  g_assert_cmpstr ("36e5604e-7e1b-4ebd-bb6a-184c6ea99627", ==, zeitgeist_subject_get_storage (su));
  g_assert (zeitgeist_subject_get_current_uri (su) == NULL);

  payload = zeitgeist_event_get_payload (ev);
  g_assert (payload != NULL);
  g_assert_cmpint (3, ==, payload->len);
  g_assert_cmpint (1, ==, payload->data[0]);
  g_assert_cmpint (2, ==, payload->data[1]);
  g_assert_cmpint (3, ==, payload->data[2]);

  g_object_unref (ev);
}

static void
test_from_variant_with_new_fields (Fixture *fix, gconstpointer data)
{
  GVariant *var;
  GVariantBuilder b;
  ZeitgeistEvent *ev;
  ZeitgeistSubject *su;
  GByteArray *payload;
  GError *error;

  g_variant_builder_init (&b, G_VARIANT_TYPE ("(" ZEITGEIST_EVENT_SIGNATURE ")"));

  /* Build event data */
  g_variant_builder_open (&b, G_VARIANT_TYPE ("as"));
  g_variant_builder_add (&b, "s", "27");
  g_variant_builder_add (&b, "s", "68");
  g_variant_builder_add (&b, "s", ZEITGEIST_ZG_ACCESS_EVENT);
  g_variant_builder_add (&b, "s", ZEITGEIST_ZG_USER_ACTIVITY);
  g_variant_builder_add (&b, "s", "application://foo.desktop");
  g_variant_builder_add (&b, "s", "origin");
  g_variant_builder_close (&b);

  /* Build subjects */
  g_variant_builder_open (&b, G_VARIANT_TYPE ("aas"));
    {
      g_variant_builder_open (&b, G_VARIANT_TYPE ("as"));
      g_variant_builder_add (&b, "s", "file:///tmp/foo.txt");
      g_variant_builder_add (&b, "s", ZEITGEIST_NFO_DOCUMENT);
      g_variant_builder_add (&b, "s", ZEITGEIST_NFO_FILE_DATA_OBJECT);
      g_variant_builder_add (&b, "s", "file:///tmp");
      g_variant_builder_add (&b, "s", "text/plain");
      g_variant_builder_add (&b, "s", "foo.txt");
      g_variant_builder_add (&b, "s", "36e5604e-7e1b-4ebd-bb6a-184c6ea99627");
      g_variant_builder_add (&b, "s", "file:///tmp/current.txt");
      g_variant_builder_close (&b);
    }
  g_variant_builder_close (&b);

  /* Build payload */
  g_variant_builder_open (&b, G_VARIANT_TYPE ("ay"));
  g_variant_builder_add (&b, "y", 1);
  g_variant_builder_add (&b, "y", 2);
  g_variant_builder_add (&b, "y", 3);
  g_variant_builder_close (&b);

  var = g_variant_builder_end (&b);
  error = NULL;
  ev = zeitgeist_event_new_from_variant (var, &error); // var freed

  g_assert_cmpint (27, ==, zeitgeist_event_get_id (ev));
  g_assert_cmpint (68, ==, zeitgeist_event_get_timestamp (ev));
  g_assert_cmpstr (ZEITGEIST_ZG_ACCESS_EVENT,==, zeitgeist_event_get_interpretation (ev));
  g_assert_cmpstr (ZEITGEIST_ZG_USER_ACTIVITY, ==, zeitgeist_event_get_manifestation (ev));
  g_assert_cmpstr ("application://foo.desktop", ==, zeitgeist_event_get_actor (ev));
  g_assert_cmpstr ("origin", ==, zeitgeist_event_get_origin (ev));
  g_assert_cmpint (1, ==, zeitgeist_event_num_subjects (ev));

  su = zeitgeist_event_get_subject (ev, 0);
  g_assert_cmpstr ("file:///tmp/foo.txt", ==, zeitgeist_subject_get_uri(su));
  g_assert_cmpstr (ZEITGEIST_NFO_DOCUMENT, ==, zeitgeist_subject_get_interpretation (su));
  g_assert_cmpstr (ZEITGEIST_NFO_FILE_DATA_OBJECT, ==, zeitgeist_subject_get_manifestation (su));
  g_assert_cmpstr ("text/plain", ==, zeitgeist_subject_get_mimetype (su));
  g_assert_cmpstr ("file:///tmp", ==, zeitgeist_subject_get_origin (su));
  g_assert_cmpstr ("foo.txt", ==, zeitgeist_subject_get_text (su));
  g_assert_cmpstr ("36e5604e-7e1b-4ebd-bb6a-184c6ea99627", ==, zeitgeist_subject_get_storage (su));
  g_assert_cmpstr ("file:///tmp/current.txt", ==, zeitgeist_subject_get_current_uri (su));

  payload = zeitgeist_event_get_payload (ev);
  g_assert (payload != NULL);
  g_assert_cmpint (3, ==, payload->len);
  g_assert_cmpint (1, ==, payload->data[0]);
  g_assert_cmpint (2, ==, payload->data[1]);
  g_assert_cmpint (3, ==, payload->data[2]);

  g_object_unref (ev);
}

static void
test_empty_to_from_variant (Fixture *fix, gconstpointer data)
{
  ZeitgeistEvent *orig, *marshalled;
  GError *error;

  orig = zeitgeist_event_new ();
  error = NULL;
  marshalled = zeitgeist_event_new_from_variant (zeitgeist_event_to_variant (orig), &error);

  g_assert_cmpint (0, ==, zeitgeist_event_get_id (marshalled));
  // FIXME g_assert_cmpint (zeitgeist_event_get_timestamp (orig), ==, zeitgeist_event_get_timestamp (marshalled));
  g_assert (zeitgeist_event_get_interpretation (marshalled) == NULL);
  g_assert (zeitgeist_event_get_manifestation (marshalled) == NULL);
  g_assert (zeitgeist_event_get_actor (marshalled) == NULL);
  g_assert (zeitgeist_event_get_origin (marshalled) == NULL);
  g_assert_cmpint (0, ==, zeitgeist_event_num_subjects (marshalled));
  g_assert (zeitgeist_event_get_payload (marshalled) == NULL);

  g_object_unref (orig);
  g_object_unref (marshalled);
}

static void
test_with_one_subject_to_from_variant (Fixture *fix, gconstpointer data)
{
  ZeitgeistEvent   *orig, *marshalled;
  ZeitgeistSubject *su;
  GByteArray       *payload;
  guint8            byte;
  GError           *error;

  orig = zeitgeist_event_new_full (
                   ZEITGEIST_ZG_ACCESS_EVENT,
                   ZEITGEIST_ZG_USER_ACTIVITY,
                   "application://firefox.desktop",
                   "origin",
                   zeitgeist_subject_new_full ("http://example.com",
                                               ZEITGEIST_NFO_WEBSITE,
                                               ZEITGEIST_NFO_REMOTE_DATA_OBJECT,
                                               "text/html",
                                               "http://example.com",
                                               "example.com",
                                               "net"),
                   NULL);
  // FIXME: this line should be removed. We need to fix the setting the timestamp
  zeitgeist_event_set_timestamp(orig, 123);

  // Set current_uri
  zeitgeist_subject_set_current_uri (
      zeitgeist_event_get_subject (orig, 0), "http://current-example.com");

  payload = g_byte_array_new ();
  byte = 255;
  g_byte_array_append (payload, &byte, 1);
  zeitgeist_event_set_payload (orig, payload); // steals payload

  error = NULL;
  marshalled = zeitgeist_event_new_from_variant (zeitgeist_event_to_variant (orig), &error);

  g_assert_cmpint (0, ==, zeitgeist_event_get_id (marshalled));
  g_assert_cmpint (123, ==, zeitgeist_event_get_timestamp (marshalled));
  g_assert_cmpstr (ZEITGEIST_ZG_ACCESS_EVENT,==, zeitgeist_event_get_interpretation (marshalled));
  g_assert_cmpstr (ZEITGEIST_ZG_USER_ACTIVITY, ==, zeitgeist_event_get_manifestation (marshalled));
  g_assert_cmpstr ("application://firefox.desktop", ==, zeitgeist_event_get_actor (marshalled));
  g_assert_cmpstr ("origin", ==, zeitgeist_event_get_origin (marshalled));
  g_assert_cmpint (1, ==, zeitgeist_event_num_subjects (marshalled));

  payload = zeitgeist_event_get_payload (marshalled);
  g_assert (payload != NULL);
  g_assert_cmpint (1, ==, payload->len);
  g_assert_cmpint (255, ==, payload->data[0]);

  su = zeitgeist_event_get_subject (marshalled, 0);
  g_assert_cmpstr ("http://example.com", ==, zeitgeist_subject_get_uri(su));
  g_assert_cmpstr (ZEITGEIST_NFO_WEBSITE, ==, zeitgeist_subject_get_interpretation (su));
  g_assert_cmpstr (ZEITGEIST_NFO_REMOTE_DATA_OBJECT, ==, zeitgeist_subject_get_manifestation (su));
  g_assert_cmpstr ("text/html", ==, zeitgeist_subject_get_mimetype (su));
  g_assert_cmpstr ("http://example.com", ==, zeitgeist_subject_get_origin (su));
  g_assert_cmpstr ("example.com", ==, zeitgeist_subject_get_text (su));
  g_assert_cmpstr ("net", ==, zeitgeist_subject_get_storage (su));
  g_assert_cmpstr ("http://current-example.com", ==, zeitgeist_subject_get_current_uri (su));

  g_object_unref (orig);
  g_object_unref (marshalled);
}

static void
test_3_events_to_from_variant (Fixture *fix, gconstpointer data)
{
  GPtrArray      *events;
  GVariant       *vevents;
  GError         *error;

  events = g_ptr_array_sized_new (3);

  g_ptr_array_add (events, zeitgeist_event_new ());
  g_ptr_array_add (events, zeitgeist_event_new ());
  g_ptr_array_add (events, zeitgeist_event_new ());

  vevents = zeitgeist_events_to_variant (events); // events ref stolen
  g_assert_cmpint (3, ==, g_variant_n_children (vevents));

  error = NULL;
  events = zeitgeist_events_from_variant (vevents, &error); // vevents ref stolen
  g_assert_cmpint (3, ==, events->len);
  g_assert (ZEITGEIST_IS_EVENT (g_ptr_array_index (events, 0)));
  g_assert (ZEITGEIST_IS_EVENT (g_ptr_array_index (events, 1)));
  g_assert (ZEITGEIST_IS_EVENT (g_ptr_array_index (events, 2)));

  g_ptr_array_unref (events);
}

static void
test_0_events_to_from_variant (Fixture *fix, gconstpointer data)
{
  GPtrArray      *events;
  GVariant       *vevents;
  GError         *error;

  events = g_ptr_array_new ();

  vevents = zeitgeist_events_to_variant (events); // events ref stolen
  g_assert_cmpint (0, ==, g_variant_n_children (vevents));

  error = NULL;
  events = zeitgeist_events_from_variant (vevents, &error); // vevents ref stolen
  g_assert_cmpint (0, ==, events->len);

  g_ptr_array_unref (events);
}

int
main (int   argc,
      char *argv[])
{
  g_type_init();
  g_test_init (&argc, &argv, NULL);

  g_test_add ("/Zeitgeist/Event/CreateEmpty", Fixture, NULL,
              setup, test_create_empty, teardown);
  g_test_add ("/Zeitgeist/Event/CreateFull", Fixture, NULL,
              setup, test_create_full, teardown);
  g_test_add ("/Zeitgeist/Event/ActorFromInfo", Fixture, NULL,
              setup, test_actor_from_app_info, teardown);
  g_test_add ("/Zeitgeist/Event/FromVariant", Fixture, NULL,
                setup, test_from_variant, teardown);
  g_test_add ("/Zeitgeist/Event/FromVariantWithNewFields", Fixture, NULL,
                setup, test_from_variant_with_new_fields, teardown);
  g_test_add ("/Zeitgeist/Event/EmptyToFromVariant", Fixture, NULL,
              setup, test_empty_to_from_variant, teardown);
  g_test_add ("/Zeitgeist/Event/WithOneSubjectToFromVariant", Fixture, NULL,
                setup, test_with_one_subject_to_from_variant, teardown);
  g_test_add ("/Zeitgeist/Event/3EventsToFromVariant", Fixture, NULL,
                  setup, test_3_events_to_from_variant, teardown);
  g_test_add ("/Zeitgeist/Event/0EventsToFromVariant", Fixture, NULL,
                  setup, test_0_events_to_from_variant, teardown);

  return g_test_run();
}
