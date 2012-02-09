/*
 * Copyright (C) 2012 Mikkel Kamstrup Erlandsen
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

static void
test_split (Fixture *fix, gconstpointer data)
{
  std::string authority, path, query;

  authority = path = query = "";
  StringUtils::SplitUri ("", authority, path, query); // doesn't crash

  g_assert_cmpstr ("", ==, authority.c_str ());
  g_assert_cmpstr ("", ==, path.c_str ());
  g_assert_cmpstr ("", ==, query.c_str ());

  authority = path = query = "";
  StringUtils::SplitUri ("scheme:", authority, path, query); // doesn't crash

  g_assert_cmpstr ("", ==, authority.c_str ());
  g_assert_cmpstr ("", ==, path.c_str ());
  g_assert_cmpstr ("", ==, query.c_str ());

  authority = path = query = "";
  StringUtils::SplitUri ("ldap://ldap1.example.net:6666/o=University%20"
                         "of%20Michigan,c=US??sub?(cn=Babs%20Jensen)",
                         authority, path, query);

  g_assert_cmpstr ("ldap1.example.net:6666", ==, authority.c_str ());
  g_assert_cmpstr ("/o=University%20of%20Michigan,c=US", ==, path.c_str ());
  g_assert_cmpstr ("?sub?(cn=Babs%20Jensen)", ==, query.c_str ());


  authority = path = query = "";
  StringUtils::SplitUri ("mailto:jsmith@example.com",
                         authority, path, query);

  g_assert_cmpstr ("jsmith@example.com", ==, authority.c_str ());
  g_assert_cmpstr ("", ==, path.c_str ());
  g_assert_cmpstr ("", ==, query.c_str ());

  authority = path = query = "";
  StringUtils::SplitUri ("mailto:jsmith@example.com?subject=A%20Test&body="
                         "My%20idea%20is%3A%20%0A", authority, path, query);

  g_assert_cmpstr ("jsmith@example.com", ==, authority.c_str ());
  g_assert_cmpstr ("", ==, path.c_str ());
  g_assert_cmpstr ("subject=A%20Test&body=My%20idea%20is%3A%20%0A", ==, query.c_str ());

  authority = path = query = "";
  StringUtils::SplitUri ("sip:alice@atlanta.com?subject=project%20x",
                         authority, path, query);

  g_assert_cmpstr ("alice@atlanta.com", ==, authority.c_str ());
  g_assert_cmpstr ("", ==, path.c_str ());
  g_assert_cmpstr ("subject=project%20x", ==, query.c_str ());

  authority = path = query = "";
  StringUtils::SplitUri ("file:///",
                         authority, path, query);

  g_assert_cmpstr ("", ==, authority.c_str ());
  g_assert_cmpstr ("/", ==, path.c_str ());
  g_assert_cmpstr ("", ==, query.c_str ());

  authority = path = query = "";
  StringUtils::SplitUri ("file:///home/username/file.ext",
                         authority, path, query);

  g_assert_cmpstr ("", ==, authority.c_str ());
  g_assert_cmpstr ("/home/username/file.ext", ==, path.c_str ());
  g_assert_cmpstr ("", ==, query.c_str ());

  authority = path = query = "";
  StringUtils::SplitUri ("dns://192.168.1.1/ftp.example.org?type=A",
                         authority, path, query);

  g_assert_cmpstr ("192.168.1.1", ==, authority.c_str ());
  g_assert_cmpstr ("/ftp.example.org", ==, path.c_str ());
  g_assert_cmpstr ("type=A", ==, query.c_str ());
}

G_BEGIN_DECLS

void test_stringutils_create_suite (void)
{
  g_test_add ("/Zeitgeist/FTS/StringUtils/Truncate", Fixture, 0,
              setup, test_truncate, teardown);
  g_test_add ("/Zeitgeist/FTS/StringUtils/MangleUri", Fixture, 0,
              setup, test_mangle, teardown);
  g_test_add ("/Zeitgeist/FTS/StringUtils/SplitUri", Fixture, 0,
              setup, test_split, teardown);
}

G_END_DECLS
