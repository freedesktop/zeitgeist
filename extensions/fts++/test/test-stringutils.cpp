/*
 * Copyright (C) 2012 Mikkel Kamstrup Erlandsen
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
 * Authored by Mikkel Kamstrup Erlandsen <mikkel.kamstrup@gmail.com>
 *
 */

#include <glib-object.h>

#include "stringutils.h"

using namespace ZeitgeistFTS;

typedef struct
{
  int i;
} Fixture;

static void setup    (Fixture *fix, gconstpointer data);
static void teardown (Fixture *fix, gconstpointer data);

static void
setup (Fixture *fix, gconstpointer data)
{

}

static void
teardown (Fixture *fix, gconstpointer data)
{

}

static void
test_truncate (Fixture *fix, gconstpointer data)
{
  g_assert_cmpstr ("", ==, StringUtils::Truncate("").c_str ());

  g_assert_cmpstr ("", ==, StringUtils::Truncate("a", 0).c_str ());
  g_assert_cmpstr ("a", ==, StringUtils::Truncate("a", 1).c_str ());
  g_assert_cmpstr ("a", ==, StringUtils::Truncate("a").c_str ());

  g_assert_cmpstr ("", ==, StringUtils::Truncate("aa", 0).c_str ());
  g_assert_cmpstr ("a", ==, StringUtils::Truncate("aa", 1).c_str ());
  g_assert_cmpstr ("aa", ==, StringUtils::Truncate("aa", 2).c_str ());
  g_assert_cmpstr ("aa", ==, StringUtils::Truncate("aa").c_str ());


  g_assert_cmpstr ("", ==, StringUtils::Truncate("å", 0).c_str ());
  g_assert_cmpstr ("", ==, StringUtils::Truncate("å", 1).c_str ());
  g_assert_cmpstr ("å", ==, StringUtils::Truncate("å").c_str ());

  g_assert_cmpstr ("", ==, StringUtils::Truncate("åå", 0).c_str ());
  g_assert_cmpstr ("", ==, StringUtils::Truncate("åå", 1).c_str ());
  g_assert_cmpstr ("å", ==, StringUtils::Truncate("åå", 2).c_str ());
  g_assert_cmpstr ("å", ==, StringUtils::Truncate("åå", 3).c_str ());
  g_assert_cmpstr ("åå", ==, StringUtils::Truncate("åå", 4).c_str ());
  g_assert_cmpstr ("åå", ==, StringUtils::Truncate("åå").c_str ());
}

static void
test_mangle (Fixture *fix, gconstpointer data)
{
  g_assert_cmpstr ("", ==, StringUtils::MangleUri("").c_str ());

  g_assert_cmpstr ("file", ==, StringUtils::MangleUri("file").c_str ());
  g_assert_cmpstr ("file___", ==, StringUtils::MangleUri("file://").c_str ());
  g_assert_cmpstr ("http___www.zeitgeist-project.com", ==,
      StringUtils::MangleUri("http://www.zeitgeist-project.com").c_str ());

  g_assert_cmpstr ("scheme_no_spaces_in_uris", ==,
      StringUtils::MangleUri("scheme:no spaces in uris").c_str ());
}

G_BEGIN_DECLS

void test_stringutils_create_suite (void)
{
  g_test_add ("/Zeitgeist/FTS/StringUtils/Truncate", Fixture, 0,
              setup, test_truncate, teardown);
  g_test_add ("/Zeitgeist/FTS/StringUtils/MangleUri", Fixture, 0,
              setup, test_mangle, teardown);
}

G_END_DECLS
