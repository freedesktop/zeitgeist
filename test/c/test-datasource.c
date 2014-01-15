/*
 * Copyright (C) 2010 Canonical Ltd
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
 * Authored by Mikkel Kamstrup Erlandsen <mikkel.kamstrup@canonical.com>
 *
 */

#include <glib.h>
#include <glib-object.h>

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
  ZeitgeistDataSource *src;

  src = zeitgeist_data_source_new ();

  g_assert_cmpstr (NULL, ==, zeitgeist_data_source_get_unique_id (src));
  g_assert_cmpstr (NULL, ==, zeitgeist_data_source_get_name (src));
  g_assert_cmpstr (NULL, ==, zeitgeist_data_source_get_description (src));
  g_assert (NULL == zeitgeist_data_source_get_event_templates (src));
  g_assert_cmpint (0, ==, zeitgeist_data_source_get_running (src));
  g_assert (0 == zeitgeist_data_source_get_timestamp (src));
  g_assert_cmpint (1, ==, zeitgeist_data_source_get_enabled (src));

  g_object_unref (src);
}

static void
test_create_full (Fixture *fix, gconstpointer data)
{
  ZeitgeistDataSource *src;
  GPtrArray           *event_templates;
  gint64               now;

  src = zeitgeist_data_source_new_full ("my-id", "my-name",
                                        "my description", NULL);

  g_assert_cmpstr ("my-id", ==, zeitgeist_data_source_get_unique_id (src));
  g_assert_cmpstr ("my-name", ==, zeitgeist_data_source_get_name (src));
  g_assert_cmpstr ("my description", ==, zeitgeist_data_source_get_description (src));
  g_assert (NULL == zeitgeist_data_source_get_event_templates (src));
  g_assert_cmpint (0, ==, zeitgeist_data_source_get_running (src));
  g_assert (0 == zeitgeist_data_source_get_timestamp (src));
  g_assert_cmpint (1, ==, zeitgeist_data_source_get_enabled (src));

  now = zeitgeist_timestamp_from_now ();
  zeitgeist_data_source_set_running (src, TRUE);
  zeitgeist_data_source_set_timestamp (src, now);
  zeitgeist_data_source_set_enabled (src, FALSE);

  g_assert_cmpint (1, ==, zeitgeist_data_source_get_running (src));
  g_assert (now == zeitgeist_data_source_get_timestamp (src));
  g_assert_cmpint (0, ==, zeitgeist_data_source_get_enabled (src));

  event_templates = g_ptr_array_new ();
  g_ptr_array_add (event_templates, zeitgeist_event_new ());
  zeitgeist_data_source_set_event_templates (src, event_templates); // own ref

  g_assert (event_templates == zeitgeist_data_source_get_event_templates (src));

  g_object_unref (src);
}

static void
test_to_from_variant (Fixture *fix, gconstpointer data)
{
  ZeitgeistDataSource *orig, *src;
  GPtrArray           *event_templates;
  gint64               now;
  GError**             error;

  error = NULL;
  /* Build the data source to serialize */
  orig = zeitgeist_data_source_new_full ("my-id", "my-name",
                                        "my description", NULL);

  now = zeitgeist_timestamp_from_now ();
  zeitgeist_data_source_set_timestamp (orig, now);

  event_templates = g_ptr_array_new ();
  g_ptr_array_add (event_templates, zeitgeist_event_new ());
  zeitgeist_data_source_set_event_templates (orig, event_templates); // own ref

  /* Serialize + unserialize */
  src = zeitgeist_data_source_new_from_variant (
                        zeitgeist_data_source_to_variant (orig), 0, error /* own ref */);

  g_assert_cmpstr ("my-id", ==, zeitgeist_data_source_get_unique_id (src));
  g_assert_cmpstr ("my-name", ==, zeitgeist_data_source_get_name (src));
  g_assert_cmpstr ("my description", ==, zeitgeist_data_source_get_description (src));
  g_assert (NULL != zeitgeist_data_source_get_event_templates (src));
  g_assert_cmpint (0, ==, zeitgeist_data_source_get_running (src));
  g_assert (now == zeitgeist_data_source_get_timestamp (src));
  g_assert_cmpint (1, ==, zeitgeist_data_source_get_enabled (src));

  event_templates = zeitgeist_data_source_get_event_templates (src);
  g_assert_cmpint (1, ==, event_templates->len);
  g_assert (ZEITGEIST_IS_EVENT (g_ptr_array_index (event_templates, 0)));

  g_object_unref (src);
}

int
main (int   argc,
      char *argv[])
{
  g_type_init();
  g_test_init (&argc, &argv, NULL);

  g_test_add ("/Zeitgeist/DataSource/CreateEmpty", Fixture, NULL,
              setup, test_create_empty, teardown);
  g_test_add ("/Zeitgeist/DataSource/CreateFull", Fixture, NULL,
                setup, test_create_full, teardown);
  g_test_add ("/Zeitgeist/DataSource/ToFromVariant", Fixture, NULL,
                  setup, test_to_from_variant, teardown);

  return g_test_run();
}
