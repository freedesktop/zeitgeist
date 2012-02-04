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

#ifndef _ZGFTS_H_
#define _ZGFTS_H_

#include <glib.h>
#include "zeitgeist-internal.h"

typedef struct _ZeitgeistIndexer ZeitgeistIndexer;

G_BEGIN_DECLS

ZeitgeistIndexer*     zeitgeist_indexer_new        (ZeitgeistDbReader* reader,
                                                    GError **error);

void                  zeitgeist_indexer_free       (ZeitgeistIndexer* indexer);

GPtrArray*            zeitgeist_indexer_search     (ZeitgeistIndexer *indexer,
                                                    const gchar *search_string,
                                                    ZeitgeistTimeRange *time_range,
                                                    GPtrArray *templates,
                                                    guint offset,
                                                    guint count,
                                                    ZeitgeistResultType result_type,
                                                    GError **error);

G_END_DECLS

#endif /* _ZGFTS_H_ */
