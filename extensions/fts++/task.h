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
  virtual ~Task () {}
  virtual void Process (Indexer *indexer) = 0;
};

class IndexEventsTask : public Task
{
public:
  void Process (Indexer *indexer);

  IndexEventsTask (GPtrArray *event_arr)
    : events (event_arr), start_index (0), event_count (event_arr->len) {}

  IndexEventsTask (GPtrArray *event_arr, unsigned index, unsigned count)
    : events (event_arr), start_index (index), event_count (count) {}
  
  IndexEventsTask (ZeitgeistDbReader *reader, std::vector<unsigned> const &ids)
    : events (NULL), zg_reader (reader), event_ids (ids) {}

  virtual ~IndexEventsTask ()
  {
    if (events) g_ptr_array_unref (events);
  }

private:
  GPtrArray *events;
  unsigned start_index;
  unsigned event_count;
  ZeitgeistDbReader *zg_reader;
  std::vector<unsigned> event_ids;
};

class DeleteEventsTask : public Task
{
public:
  void Process (Indexer *indexer);

  DeleteEventsTask (unsigned *event_ids_arr, int event_ids_arr_size)
    : event_ids (event_ids_arr, event_ids_arr + event_ids_arr_size) {}

  virtual ~DeleteEventsTask ()
  {
  }

private:
  std::vector<unsigned> event_ids;
};

class MetadataTask : public Task
{
public:
  void Process (Indexer *indexer);

  MetadataTask (std::string const& name, std::string const& val)
    : key_name (name), value (val) {}

  virtual ~MetadataTask ()
  {}

private:
  std::string key_name;
  std::string value;
};

}

#endif /* _ZGFTS_TASK_H_ */

