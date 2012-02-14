/*
 * Copyright © 2012 Canonical Ltd.
 *             By Michal Hruby <michal.hruby@canonical.com>
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

#include "fts.h"
#include "indexer.h"
#include "controller.h"

ZeitgeistIndexer*
zeitgeist_indexer_new (ZeitgeistDbReader *reader, GError **error)
{
  ZeitgeistFTS::Controller *ctrl;
  GError                   *local_error;

  g_return_val_if_fail (ZEITGEIST_IS_DB_READER (reader), NULL);
  g_return_val_if_fail (error == NULL || *error == NULL, NULL);

  g_setenv ("XAPIAN_CJK_NGRAM", "1", TRUE);
  ctrl = new ZeitgeistFTS::Controller (reader);

  local_error = NULL;
  ctrl->Initialize (&local_error);
  if (local_error)
  {
    delete ctrl;
    g_propagate_error (error, local_error);
    return NULL;
  }


  ctrl->Run ();

  return (ZeitgeistIndexer*) ctrl;
}

void
zeitgeist_indexer_free (ZeitgeistIndexer* indexer)
{
  g_return_if_fail (indexer != NULL);

  delete (ZeitgeistFTS::Controller*) indexer;
}

GPtrArray* zeitgeist_indexer_search (ZeitgeistIndexer *indexer,
                                     const gchar *search_string,
                                     ZeitgeistTimeRange *time_range,
                                     GPtrArray *templates,
                                     guint offset,
                                     guint count,
                                     ZeitgeistResultType result_type,
                                     guint *matches,
                                     GError **error)
{
  GPtrArray *results;
  ZeitgeistFTS::Controller *_indexer;

  g_return_val_if_fail (indexer != NULL, NULL);
  g_return_val_if_fail (search_string != NULL, NULL);
  g_return_val_if_fail (ZEITGEIST_IS_TIME_RANGE (time_range), NULL);
  g_return_val_if_fail (error == NULL || *error == NULL, NULL);

  _indexer = (ZeitgeistFTS::Controller*) indexer;

  results = _indexer->indexer->Search (search_string, time_range,
                                       templates, offset, count, result_type,
                                       matches, error);

  return results;
}

GPtrArray*
zeitgeist_indexer_search_with_relevancies (ZeitgeistIndexer *indexer,
                                           const gchar *search_string,
                                           ZeitgeistTimeRange *time_range,
                                           GPtrArray *templates,
                                           ZeitgeistStorageState storage_state,
                                           guint offset,
                                           guint count,
                                           ZeitgeistResultType result_type,
                                           gdouble **relevancies,
                                           gint *relevancies_size,
                                           guint *matches,
                                           GError **error)
{
  GPtrArray *results;
  ZeitgeistFTS::Controller *_indexer;

  g_return_val_if_fail (indexer != NULL, NULL);
  g_return_val_if_fail (search_string != NULL, NULL);
  g_return_val_if_fail (ZEITGEIST_IS_TIME_RANGE (time_range), NULL);
  g_return_val_if_fail (error == NULL || *error == NULL, NULL);

  _indexer = (ZeitgeistFTS::Controller*) indexer;

  results = _indexer->indexer->SearchWithRelevancies (
      search_string, time_range, templates, storage_state, offset, count,
      result_type, relevancies, relevancies_size, matches, error);

  return results;
}

void zeitgeist_indexer_index_events (ZeitgeistIndexer *indexer,
                                     GPtrArray *events)
{
  ZeitgeistFTS::Controller *_indexer;

  g_return_if_fail (indexer != NULL);
  g_return_if_fail (events != NULL);

  _indexer = (ZeitgeistFTS::Controller*) indexer;

  _indexer->IndexEvents (events);
}

void zeitgeist_indexer_delete_events (ZeitgeistIndexer *indexer,
                                      guint *event_ids,
                                      int event_ids_size)
{
  ZeitgeistFTS::Controller *_indexer;

  g_return_if_fail (indexer != NULL);

  if (event_ids_size <= 0) return;

  _indexer = (ZeitgeistFTS::Controller*) indexer;

  _indexer->DeleteEvents (event_ids, event_ids_size);
}

gboolean zeitgeist_indexer_has_pending_tasks (ZeitgeistIndexer *indexer)
{
  ZeitgeistFTS::Controller *_indexer;

  g_return_val_if_fail (indexer != NULL, FALSE);

  _indexer = (ZeitgeistFTS::Controller*) indexer;

  return _indexer->HasPendingTasks () ? TRUE : FALSE;
}

void zeitgeist_indexer_process_task (ZeitgeistIndexer *indexer)
{
  ZeitgeistFTS::Controller *_indexer;

  g_return_if_fail (indexer != NULL);

  _indexer = (ZeitgeistFTS::Controller*) indexer;

  _indexer->ProcessTask ();
}

