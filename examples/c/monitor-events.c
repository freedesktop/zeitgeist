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
#include <glib/gprintf.h>
#include <glib-object.h>
#include <zeitgeist.h>

static void
on_events_inserted (ZeitgeistMonitor   *mon,
                    ZeitgeistTimeRange *time_range,
                    ZeitgeistResultSet *events,
                    gpointer            user_data)
{
  ZeitgeistEvent   *event;
  ZeitgeistSubject *subject;
  gint              j;
  
  g_message ("%i events inserted", zeitgeist_result_set_size (events));

  while (zeitgeist_result_set_has_next (events))
    {
      event = zeitgeist_result_set_next_value (events);
      for (j = 0; j < zeitgeist_event_num_subjects (event); j++)
        {
          subject = zeitgeist_event_get_subject (event, j);
          g_message (" * %s", zeitgeist_subject_get_uri (subject));
        }
    }
}

static void
on_events_deleted (ZeitgeistMonitor   *mon,
                   ZeitgeistTimeRange *time_range,
                   GArray             *event_ids,
                   gpointer            user_data)
{
  g_message ("%i events deleted", event_ids->len);
}

gint
main (gint   argc,
      gchar *argv[])
{
  GMainLoop          *mainloop;
  ZeitgeistLog       *log;
  ZeitgeistMonitor   *monitor;
  GPtrArray          *templates;
  GError**           error;
  
  error = NULL;
  mainloop = g_main_loop_new (NULL, FALSE);
  log = g_object_new (ZEITGEIST_TYPE_LOG, NULL);

  /* Templates matching anything */
  templates = g_ptr_array_new ();
  g_ptr_array_add (templates, zeitgeist_event_new ());

  monitor = zeitgeist_monitor_new (zeitgeist_time_range_new_anytime (),
                                   templates);

  g_signal_connect (monitor, "events-inserted",
                    G_CALLBACK (on_events_inserted), NULL);
  g_signal_connect (monitor, "events-deleted",
                    G_CALLBACK (on_events_deleted), NULL);

  zeitgeist_log_install_monitor (log, monitor, error);
  
  g_main_loop_run (mainloop);
  
  return 0;
}
