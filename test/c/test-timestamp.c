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
test_from_iso8601 (Fixture *fix, gconstpointer data)
{
  const gchar *orig = "2010-06-17T00:00:00Z";
  gint64 from_iso = zeitgeist_timestamp_from_iso8601 (orig);
  gchar *d = zeitgeist_timestamp_to_iso8601 (from_iso);

  g_assert_cmpstr (orig, ==, d);
  g_free (d);
}

static void
test_inc_year (Fixture *fix, gconstpointer data)
{
  gchar *d = zeitgeist_timestamp_to_iso8601 (ZEITGEIST_TIMESTAMP_YEAR);

  // Since ZEITGEIST_TIMESTAMP_YEAR accounts for leap years we wont exactly
  // match "1971-01-01T00:00:00Z" on the hour
  g_assert (g_str_has_prefix (d, "1971-01-01T"));
  g_free (d);
}

static void
test_from_date (Fixture *fix, gconstpointer data)
{
  GDate date = { 0 };

  g_date_set_dmy (&date, 25, G_DATE_JUNE, 2000);
  gint64 from_date = zeitgeist_timestamp_from_date (&date);

  gchar *d = zeitgeist_timestamp_to_iso8601 (from_date);

  /* API guarantees that the timestamp is rounded to midnight */
  g_assert_cmpstr ("2000-06-25T00:00:00Z", ==, d);
}

/* Assert that now() is after 2000. This will catch any overflow bugs
 * for uints of int32 */
static void
test_now (Fixture *fix, gconstpointer data)
{
  g_assert (30*ZEITGEIST_TIMESTAMP_YEAR < zeitgeist_timestamp_from_now ());
}

/* If a timestamp is divisible by 1000 we should have lossless conversion
 * to and from GTimeVals */
static void
test_timeval_conversion (Fixture *fix, gconstpointer data)
{
  GTimeVal tv = { 0 };
  gint64 ts, _ts;

  /* Check 0 */
  ts = 0;
  zeitgeist_timestamp_to_timeval (ts, &tv);
  _ts = zeitgeist_timestamp_from_timeval (&tv);
  g_assert (ts == _ts);

  /* Check a low number */
  ts = 10000;
  zeitgeist_timestamp_to_timeval (ts, &tv);
  _ts = zeitgeist_timestamp_from_timeval (&tv);
  g_assert (ts == _ts);

  /* Check 2010-06-18 */
  ts = G_GINT64_CONSTANT (1276849717119);
  zeitgeist_timestamp_to_timeval (ts, &tv);
  _ts = zeitgeist_timestamp_from_timeval (&tv);
  g_assert (ts == _ts);

  /* Note : G_MAXINT64 wont work because GTimeVal uses glongs internally
   * to track the numbers */
}

static void
test_prev_midnight (Fixture *fix, gconstpointer data)
{
  gint64 ts, midnight;
  gchar *iso;

  /* Check 2010-06-23T11:19:07Z */
  ts = G_GINT64_CONSTANT (1277284743659);

  /* Now the actual test */
  midnight = zeitgeist_timestamp_prev_midnight (ts);
  iso = zeitgeist_timestamp_to_iso8601(midnight);
  g_assert(g_str_has_prefix (iso, "2010-06-23T00:00:00"));
  g_free (iso);

  /* Pre midnight of 'midnight' should go one day back */
  midnight = zeitgeist_timestamp_prev_midnight (midnight);
  iso = zeitgeist_timestamp_to_iso8601(midnight);
  g_assert(g_str_has_prefix (iso, "2010-06-22T00:00:00"));
  g_free (iso);
}

static void
test_next_midnight (Fixture *fix, gconstpointer data)
{
  gint64 ts, midnight;
  gchar *iso;

  /* Check 2010-06-23T11:19:07Z */
  ts = G_GINT64_CONSTANT (1277284743659);

  /* Now the actual test */
  midnight = zeitgeist_timestamp_next_midnight (ts);
  iso = zeitgeist_timestamp_to_iso8601(midnight);
  g_assert(g_str_has_prefix (iso, "2010-06-24T00:00:00"));
  g_free (iso);

  /* Pre midnight of 'midnight' should go one day back */
  midnight = zeitgeist_timestamp_next_midnight (midnight);
  iso = zeitgeist_timestamp_to_iso8601(midnight);
  g_assert(g_str_has_prefix (iso, "2010-06-25T00:00:00"));
  g_free (iso);
}

int
main (int   argc,
      char *argv[])
{
  g_test_init (&argc, &argv, NULL);

  g_test_add ("/Zeitgeist/Timestamp/FromISO8601", Fixture, NULL,
              setup, test_from_iso8601, teardown);
  g_test_add ("/Zeitgeist/Timestamp/IncrementYear", Fixture, NULL,
              setup, test_inc_year, teardown);
  g_test_add ("/Zeitgeist/Timestamp/FromDate", Fixture, NULL,
              setup, test_from_date, teardown);
  g_test_add ("/Zeitgeist/Timestamp/Now", Fixture, NULL,
              setup, test_now, teardown);
  g_test_add ("/Zeitgeist/Timestamp/TimeValConversion", Fixture, NULL,
              setup, test_timeval_conversion, teardown);
  g_test_add ("/Zeitgeist/Timestamp/PrevMidnight", Fixture, NULL,
              setup, test_prev_midnight, teardown);
  g_test_add ("/Zeitgeist/Timestamp/NextMidnight", Fixture, NULL,
              setup, test_next_midnight, teardown);

  return g_test_run();
}
