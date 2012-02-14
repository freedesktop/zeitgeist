/*
 * Copyright © 2012 Canonical Ltd.
 *           By Michal Hruby <michal.hruby@canonical.com>
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

#ifndef _ZGFTS_H_
#define _ZGFTS_H_

#include <glib.h>
#include "zeitgeist-internal.h"

typedef struct _ZeitgeistIndexer ZeitgeistIndexer;

G_BEGIN_DECLS

ZeitgeistIndexer*  zeitgeist_indexer_new           (ZeitgeistDbReader* reader,
                                                    GError **error);

void               zeitgeist_indexer_free          (ZeitgeistIndexer* indexer);

GPtrArray*         zeitgeist_indexer_search        (ZeitgeistIndexer *indexer,
                                                    const gchar *search_string,
                                                    ZeitgeistTimeRange *time_range,
                                                    GPtrArray *templates,
                                                    guint offset,
                                                    guint count,
                                                    ZeitgeistResultType result_type,
                                                    guint *matches,
                                                    GError **error);

GPtrArray*         zeitgeist_indexer_search_with_relevancies
                                                   (ZeitgeistIndexer *indexer,
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
                                                    GError **error);

void               zeitgeist_indexer_index_events  (ZeitgeistIndexer *indexer,
                                                    GPtrArray *events);

void               zeitgeist_indexer_delete_events (ZeitgeistIndexer *indexer,
                                                    guint *event_ids,
                                                    int event_ids_size);

gboolean           zeitgeist_indexer_has_pending_tasks (ZeitgeistIndexer *indexer);

void               zeitgeist_indexer_process_task  (ZeitgeistIndexer *indexer);

G_END_DECLS

#endif /* _ZGFTS_H_ */
