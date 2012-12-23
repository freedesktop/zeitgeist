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
  ZeitgeistMonitor   *mon;
  ZeitgeistTimeRange *tr;
  GPtrArray          *event_templates, *event_templates_;

  event_templates = g_ptr_array_new ();
  mon = zeitgeist_monitor_new (zeitgeist_time_range_new (27, 68),
                               event_templates);

  g_object_get (mon,
                "time-range", &tr,
                "event-templates", &event_templates_,
                NULL);

  g_assert_cmpint (27, ==, zeitgeist_time_range_get_start (tr));
  g_assert_cmpint (68, ==, zeitgeist_time_range_get_end (tr));

  g_assert (event_templates == event_templates_);

  g_object_unref (tr);
  g_ptr_array_unref (event_templates_);
  g_object_unref (mon);
}

int
main (int   argc,
      char *argv[])
{
  g_type_init();
  g_test_init (&argc, &argv, NULL);

  g_test_add ("/Zeitgeist/Monitor/Create", Fixture, NULL,
              setup, test_create, teardown);

  return g_test_run();
}
