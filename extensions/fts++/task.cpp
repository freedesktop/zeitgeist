/*
 * Copyright (C) 2012 Canonical Ltd
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

}
