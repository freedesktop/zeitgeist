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

#ifndef _ZGFTS_TASK_H_
#define _ZGFTS_TASK_H_

#include <glib.h>

#include "indexer.h"

namespace ZeitgeistFTS {

/**
 * A task contains a chunk of work defined by the Controller.
 * A task should not be clever in scheduling on its own, the
 * Controller is responsible for breaking down tasks in suitable
 * chunks.
 */
class Task
{
public:
  virtual void Process (Indexer *indexer) = 0;
};

class IndexEventsTask : public Task
{
public:
  void Process (Indexer *indexer);

  IndexEventsTask (GPtrArray *event_arr)
    : events (event_arr) {}

  virtual ~IndexEventsTask ()
  {
    g_ptr_array_unref (events);
  }

private:
  GPtrArray *events;
};

}

#endif /* _ZGFTS_TASK_H_ */

