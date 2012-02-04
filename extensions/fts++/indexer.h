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

#ifndef _ZGFTS_INDEXER_H_
#define _ZGFTS_INDEXER_H_

#include <glib-object.h>
#include <xapian.h>

#include "zeitgeist-internal.h"

namespace ZeitgeistFTS {

class Indexer
{
public:
  Indexer (ZeitgeistDbReader *reader)
    : zg_reader (reader)
    , db (NULL)
    , query_parser (NULL)
    , enquire (NULL)
    , tokenizer (NULL)
  { }

  ~Indexer ()
  {
    if (tokenizer) delete tokenizer;
    if (enquire) delete enquire;
    if (query_parser) delete query_parser;
    if (db) delete db;
  }

  void Initialize (GError **error);
  bool CheckIndex ();
  void DropIndex ();

  std::string ExpandType (std::string const& prefix, const gchar* unparsed_uri);
  std::string CompileEventFilterQuery (GPtrArray *templates);
  std::string CompileTimeRangeFilterQuery (gint64 start, gint64 end);

  void IndexEvent (ZeitgeistEvent *event);
  void DeleteEvent (guint32 event_id);

  GPtrArray* Search (const gchar *search_string,
                     ZeitgeistTimeRange *time_range,
                     GPtrArray *templates,
                     guint offset,
                     guint count,
                     ZeitgeistResultType result_type,
                     GError **error);

private:
  ZeitgeistDbReader       *zg_reader;
  Xapian::Database        *db;
  Xapian::QueryParser     *query_parser;
  Xapian::Enquire         *enquire;
  Xapian::TermGenerator   *tokenizer;
};

}

#endif /* _ZGFTS_INDEXER_H_ */
