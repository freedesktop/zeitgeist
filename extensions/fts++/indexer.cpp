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

#include "indexer.h"
#include <xapian.h>

#define FILTER_PREFIX_EVENT_INTERPRETATION "ZGEI"
#define FILTER_PREFIX_EVENT_MANIFESTATION "ZGEM"
#define FILTER_PREFIX_ACTOR "ZGA"
#define FILTER_PREFIX_SUBJECT_URI "ZGSU"
#define FILTER_PREFIX_SUBJECT_INTERPRETATION "ZGSI"
#define FILTER_PREFIX_SUBJECT_MANIFESTATION "ZGSM"
#define FILTER_PREFIX_SUBJECT_ORIGIN "ZGSO"
#define FILTER_PREFIX_SUBJECT_MIMETYPE "ZGST"
#define FILTER_PREFIX_SUBJECT_STORAGE "ZGSS"
#define FILTER_PREFIX_XDG_CATEGORY "AC"

#define INDEX_VERSION 1

#define MAX_TERM_LENGTH 245

struct _ZeitgeistIndexer
{
  Xapian::Database      *db;

  void initialize (GError **error);
};

void ZeitgeistIndexer::initialize (GError **error)
{
  if (zeitgeist_utils_using_in_memory_database ())
  {
    this->db = new Xapian::WritableDatabase;
    this->db->add_database (Xapian::InMemory::open ());
  }
  else
  {
    gchar *path = g_build_filename (zeitgeist_utils_get_data_path (),
                                    "fts.index", NULL);
    try {
      this->db = new Xapian::WritableDatabase (path,
                                                  Xapian::DB_CREATE_OR_OPEN);
    } catch (const Xapian::Error &xp_error) {
      g_set_error_literal (error,
                           ZEITGEIST_ENGINE_ERROR,
                           ZEITGEIST_ENGINE_ERROR_DATABASE_ERROR,
                           xp_error.get_msg ().c_str ());
      this->db = NULL;
    }

    g_free (path);
  }
}

/* -------------------- Public methods -------------------- */
ZeitgeistIndexer*
zeitgeist_indexer_new (ZeitgeistDbReader *reader, GError **error)
{
  g_return_val_if_fail (ZEITGEIST_IS_DB_READER (reader), NULL);
  ZeitgeistIndexer *indexer;

  g_message ("Initializing Indexer...");
  g_setenv ("XAPIAN_CJK_NGRAM", "1", TRUE);
  indexer = new ZeitgeistIndexer;
  indexer->initialize (error);

  if (indexer->db == NULL)
  {
    // initialize() threw an error
    delete indexer;
    return NULL;
  }

  return indexer;
}

void
zeitgeist_indexer_free (ZeitgeistIndexer* indexer)
{
  g_return_if_fail (indexer != NULL);

  delete indexer;
}

