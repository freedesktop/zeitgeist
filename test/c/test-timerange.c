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
} Fixture;

static void setup    (Fixture *fix, gconstpointer data);
static void teardown (Fixture *fix, gconstpointer data);

static void
setup (Fixture *fix, gconstpointer data)
{
}

static void
teardown (Fixture *fix, gconstpointer data)
{
}

static void
test_create (Fixture *fix, gconstpointer data)
{
  ZeitgeistTimeRange *tr;
  tr = zeitgeist_time_range_new (0, 1);

  g_assert_cmpint (0, ==, zeitgeist_time_range_get_start (tr));
  g_assert_cmpint (1, ==, zeitgeist_time_range_get_end (tr));

  g_object_unref (tr);
}

static void
test_anytime (Fixture *fix, gconstpointer data)
{
  ZeitgeistTimeRange *tr;

  tr = zeitgeist_time_range_new_anytime ();

  g_assert (0 == zeitgeist_time_range_get_start (tr));
  g_assert (G_MAXINT64 == zeitgeist_time_range_get_end (tr));

  g_object_unref (tr);
}

static void
test_to_now (Fixture *fix, gconstpointer data)
{
  ZeitgeistTimeRange *tr;

  tr = zeitgeist_time_range_new_to_now ();

  g_assert (0 == zeitgeist_time_range_get_start (tr));

  /* Since system time is unreliable we simply assert that the end timestamp
   * is after 2000. This assueres that we catch any uint/int32 overflow
   * at least */
  g_assert (30*ZEITGEIST_TIMESTAMP_YEAR < zeitgeist_time_range_get_end (tr));

  g_object_unref (tr);
}

static void
test_from_now (Fixture *fix, gconstpointer data)
{
  ZeitgeistTimeRange *tr;

  tr = zeitgeist_time_range_new_from_now ();  

  /* Since system time is unreliable we simply assert that the start timestamp
   * is after 2000. This assueres that we catch any uint/int32 overflow
   * at least */
  g_assert (30*ZEITGEIST_TIMESTAMP_YEAR < zeitgeist_time_range_get_start (tr));
  g_assert (G_MAXINT64 == zeitgeist_time_range_get_end (tr));

  g_object_unref (tr);
}

static void
test_from_variant (Fixture *fix, gconstpointer data)
{
  ZeitgeistTimeRange *tr;
  GVariant           *v;
  gint64              i,j;
  GError             **error;

  error = NULL;
  v = g_variant_new ("(xx)",
                     G_GINT64_CONSTANT(0), G_MAXINT64);
  g_variant_get (v, "(xx)", &i, &j);
  tr = zeitgeist_time_range_new_from_variant (v, error); // v freed

  g_assert (0 == zeitgeist_time_range_get_start (tr));
  g_assert (G_MAXINT64 == zeitgeist_time_range_get_end (tr));

  g_object_unref (tr);
}

static void
test_to_variant (Fixture *fix, gconstpointer data)
{
  ZeitgeistTimeRange *tr;
  GVariant           *v;
  gint64              i,j;

  tr = zeitgeist_time_range_new (0, G_MAXINT64);
  v = zeitgeist_time_range_to_variant (tr); // tr freed
  g_variant_get (v, "(xx)",
                 &i, &j);

  g_assert (0 == i);
  g_assert (G_MAXINT64 == j);

  g_variant_unref (v);
}

int
main (int   argc,
      char *argv[])
{
  g_type_init();
  g_test_init (&argc, &argv, NULL);

  g_test_add ("/Zeitgeist/TimeRange/Create", Fixture, NULL,
              setup, test_create, teardown);
  g_test_add ("/Zeitgeist/TimeRange/Anytime", Fixture, NULL,
              setup, test_anytime, teardown);
  g_test_add ("/Zeitgeist/TimeRange/ToNow", Fixture, NULL,
              setup, test_to_now, teardown);
  g_test_add ("/Zeitgeist/TimeRange/FromNow", Fixture, NULL,
              setup, test_from_now, teardown);
  g_test_add ("/Zeitgeist/TimeRange/FromVariant", Fixture, NULL,
                setup, test_from_variant, teardown);
  g_test_add ("/Zeitgeist/TimeRange/ToVariant", Fixture, NULL,
                  setup, test_to_variant, teardown);

  return g_test_run();
}
