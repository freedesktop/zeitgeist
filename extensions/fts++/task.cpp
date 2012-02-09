/*
 * Copyright (C) 2012 Canonical Ltd
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
 * Authored by Michal Hruby <michal.hruby@canonical.com>
 *
 */

#include "task.h"

namespace ZeitgeistFTS {

void IndexEventsTask::Process (Indexer *indexer)
{
  unsigned end_index = MIN (start_index + event_count, events->len);
  for (unsigned i = start_index; i < end_index; i++)
  {
    indexer->IndexEvent ((ZeitgeistEvent*) g_ptr_array_index (events, i));
  }
}

void DeleteEventsTask::Process (Indexer *indexer)
{
  for (unsigned i = 0; i < event_ids.size (); i++)
  {
    indexer->DeleteEvent (event_ids[i]);
  }
}

void MetadataTask::Process (Indexer *indexer)
{
  indexer->SetDbMetadata (key_name, value);
}

}
