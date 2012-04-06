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

#include "controller.h"

namespace ZeitgeistFTS {

void Controller::Initialize (GError **error)
{
  indexer->Initialize (error);
}

void Controller::Run ()
{
  if (!indexer->CheckIndex ())
    {
      indexer->DropIndex ();
      RebuildIndex ();
    }
}

void Controller::RebuildIndex ()
{
  GError *error = NULL;
  guint32 *event_ids;
  gint event_ids_size;
  GPtrArray *templates = g_ptr_array_new_with_free_func (g_object_unref);
  ZeitgeistEvent *event;
  ZeitgeistTimeRange *time_range = zeitgeist_time_range_new_anytime ();

  if (g_getenv ("ZEITGEIST_FTS_DISABLE_EVENT_BLACKLIST") == NULL)
  {
    // Blacklist Ubuntu One events...

    event = zeitgeist_event_new ();
    zeitgeist_event_set_actor (event, "!dbus://com.ubuntuone.SyncDaemon.service");
    g_ptr_array_add (templates, event);

    event = zeitgeist_event_new ();
    zeitgeist_event_set_actor (event, "!dbus://org.desktopcouch.CouchDB.service");
    g_ptr_array_add (templates, event);
  }

  g_debug ("asking reader for all events");
  event_ids = zeitgeist_db_reader_find_event_ids (zg_reader,
                                                  time_range,
                                                  templates,
                                                  ZEITGEIST_STORAGE_STATE_ANY,
                                                  0,
                                                  ZEITGEIST_RESULT_TYPE_MOST_RECENT_EVENTS,
                                                  NULL,
                                                  &event_ids_size,
                                                  &error);

  if (error)
  {
    g_warning ("%s", error->message);
    g_error_free (error);
  }
  else
  {
    g_debug ("reader returned %d events", event_ids_size);

    IndexEvents (event_ids, event_ids_size);
    g_free (event_ids);

    // Set the db metadata key only once we're done
    PushTask (new MetadataTask ("fts_index_version", INDEX_VERSION));
    gint64 zg_creation_date = indexer->GetZeitgeistCreationDate ();
    gchar *creation = g_strdup_printf ("%" G_GINT64_FORMAT, zg_creation_date);
    std::string zg_creation_date_str (creation);
    PushTask (new MetadataTask ("zg_db_creation_date", zg_creation_date_str));
    g_free (creation);
  }

  g_object_unref (time_range);
  g_ptr_array_unref (templates);
}

void Controller::IndexEvents (GPtrArray *events)
{
  const int CHUNK_SIZE = 32;
  // Break down index tasks into suitable chunks
  for (unsigned i = 0; i < events->len; i += CHUNK_SIZE)
  {
    PushTask (new IndexEventsTask (g_ptr_array_ref (events), i, CHUNK_SIZE));
  }
}

void Controller::IndexEvents (guint *event_ids, int event_ids_size)
{
  const int CHUNK_SIZE = 64;
  // Break down index tasks into suitable chunks
  for (int i = 0; i < event_ids_size; i += CHUNK_SIZE)
  {
    int num_ids = i + CHUNK_SIZE > event_ids_size ? 
      event_ids_size - i : CHUNK_SIZE;
    PushTask (new IndexEventsTask (zg_reader,
        std::vector<guint> (&event_ids[i], &event_ids[i + num_ids])));
  }
}

void Controller::DeleteEvents (guint *event_ids, int event_ids_size)
{
  // FIXME: Should we break the task here as well?
  PushTask (new DeleteEventsTask (event_ids, event_ids_size));
}

void Controller::PushTask (Task* task)
{
  queued_tasks.push (task);

  if (processing_source_id == 0)
  {
    processing_source_id =
      g_idle_add ((GSourceFunc) &Controller::ProcessTask, this);
  }
}

gboolean Controller::ProcessTask ()
{
  if (!queued_tasks.empty ())
  {
    Task *task;

    task = queued_tasks.front ();
    queued_tasks.pop ();

    task->Process (indexer);
    delete task;
  }

  bool all_done = queued_tasks.empty ();
  if (all_done)
  {
    indexer->Commit ();
    if (processing_source_id != 0)
    {
      g_source_remove (processing_source_id);
      processing_source_id = 0;
    }
    return FALSE;
  }

  return TRUE;
}

bool Controller::HasPendingTasks ()
{
  return !queued_tasks.empty ();
}

}
