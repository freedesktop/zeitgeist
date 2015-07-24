/*
 * Copyright © 2012 Mikkel Kamstrup Erlandsen <mikkel.kamstrup@gmail.com>
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
  std::string truncated;

  truncated = StringUtils::Truncate("");
  g_assert_cmpstr ("", ==, truncated.c_str ());

  truncated = StringUtils::Truncate("a", 0);
  g_assert_cmpstr ("", ==, truncated.c_str ());
  truncated = StringUtils::Truncate("a", 1);
  g_assert_cmpstr ("a", ==, truncated.c_str ());
  truncated = StringUtils::Truncate("a");
  g_assert_cmpstr ("a", ==, truncated.c_str ());

  truncated = StringUtils::Truncate("aa", 0);
  g_assert_cmpstr ("", ==, truncated.c_str ());
  truncated = StringUtils::Truncate("aa", 1);
  g_assert_cmpstr ("a", ==, truncated.c_str ());
  truncated = StringUtils::Truncate("aa", 2);
  g_assert_cmpstr ("aa", ==, truncated.c_str ());
  truncated = StringUtils::Truncate("aa");
  g_assert_cmpstr ("aa", ==, truncated.c_str ());


  truncated = StringUtils::Truncate("å", 0);
  g_assert_cmpstr ("", ==, truncated.c_str ());
  truncated = StringUtils::Truncate("å", 1);
  g_assert_cmpstr ("", ==, truncated.c_str ());
  truncated = StringUtils::Truncate("å");
  g_assert_cmpstr ("å", ==, truncated.c_str ());

  truncated = StringUtils::Truncate("åå", 0);
  g_assert_cmpstr ("", ==, truncated.c_str ());
  truncated = StringUtils::Truncate("åå", 1);
  g_assert_cmpstr ("", ==, truncated.c_str ());
  truncated = StringUtils::Truncate("åå", 2);
  g_assert_cmpstr ("å", ==, truncated.c_str ());
  truncated = StringUtils::Truncate("åå", 3);
  g_assert_cmpstr ("å", ==, truncated.c_str ());
  truncated = StringUtils::Truncate("åå", 4);
  g_assert_cmpstr ("åå", ==, truncated.c_str ());
  truncated = StringUtils::Truncate("åå");
  g_assert_cmpstr ("åå", ==, truncated.c_str ());
}

static void
test_mangle (Fixture *fix, gconstpointer data)
{
  std::string mangled;

  mangled = StringUtils::MangleUri("");
  g_assert_cmpstr ("", ==, mangled.c_str ());

  mangled = StringUtils::MangleUri("file");
  g_assert_cmpstr ("file", ==, mangled.c_str ());
  mangled = StringUtils::MangleUri("file://");
  g_assert_cmpstr ("file___", ==, mangled.c_str ());
  mangled = StringUtils::MangleUri("http://www.zeitgeist-project.com");
  g_assert_cmpstr ("http___www_zeitgeist_project_com", ==, mangled.c_str ());

  mangled = StringUtils::MangleUri("scheme:no spaces in uris");
  g_assert_cmpstr ("scheme_no_spaces_in_uris", ==, mangled.c_str ());
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

static void
test_ascii_fold (Fixture *fix, gconstpointer data)
{
  std::string folded;

  folded = StringUtils::AsciiFold ("");
  g_assert_cmpstr ("", ==, folded.c_str ());

  // if the original matches the folded version, AsciiFold returns ""
  folded = StringUtils::AsciiFold ("a");
  g_assert_cmpstr ("", ==, folded.c_str ());

  folded = StringUtils::AsciiFold ("abcdef");
  g_assert_cmpstr ("", ==, folded.c_str ());

  folded = StringUtils::AsciiFold ("å");
  g_assert_cmpstr ("a", ==, folded.c_str ());

  folded = StringUtils::AsciiFold ("åå");
  g_assert_cmpstr ("aa", ==, folded.c_str ());

  folded = StringUtils::AsciiFold ("aåaåa");
  g_assert_cmpstr ("aaaaa", ==, folded.c_str ());
}

static void
test_underscores (Fixture *fix, gconstpointer data)
{
  std::string s;

  s = StringUtils::RemoveUnderscores ("");
  g_assert_cmpstr ("", ==, s.c_str ());

  s = StringUtils::RemoveUnderscores ("_");
  g_assert_cmpstr (" ", ==, s.c_str ());

  s = StringUtils::RemoveUnderscores ("___");
  g_assert_cmpstr ("   ", ==, s.c_str ());

  s = StringUtils::RemoveUnderscores ("abcd");
  g_assert_cmpstr ("abcd", ==, s.c_str ());

  s = StringUtils::RemoveUnderscores ("_abcd_");
  g_assert_cmpstr (" abcd ", ==, s.c_str ());

  s = StringUtils::RemoveUnderscores ("a_b_c_d");
  g_assert_cmpstr ("a b c d", ==, s.c_str ());
}

static void
test_uncamelcase (Fixture *fix, gconstpointer data)
{
  std::string s;

  s = StringUtils::UnCamelcase ("");
  g_assert_cmpstr ("", ==, s.c_str ());

  s = StringUtils::UnCamelcase ("abcd");
  g_assert_cmpstr ("abcd", ==, s.c_str ());

  s = StringUtils::UnCamelcase ("Abcd");
  g_assert_cmpstr ("Abcd", ==, s.c_str ());

  s = StringUtils::UnCamelcase ("ABCD");
  g_assert_cmpstr ("ABCD", ==, s.c_str ());

  s = StringUtils::UnCamelcase ("ABcd");
  g_assert_cmpstr ("ABcd", ==, s.c_str ());

  s = StringUtils::UnCamelcase ("AbcdEf");
  g_assert_cmpstr ("Abcd Ef", ==, s.c_str ());

  s = StringUtils::UnCamelcase ("Text Editor");
  g_assert_cmpstr ("Text Editor", ==, s.c_str ());

  s = StringUtils::UnCamelcase ("pyKaraoke");
  g_assert_cmpstr ("py Karaoke", ==, s.c_str ());

  s = StringUtils::UnCamelcase ("ZeitgeistProject");
  g_assert_cmpstr ("Zeitgeist Project", ==, s.c_str ());

  s = StringUtils::UnCamelcase ("VeryNiceCamelCaseText");
  g_assert_cmpstr ("Very Nice Camel Case Text", ==, s.c_str ());

  s = StringUtils::UnCamelcase ("ŇeedšŤoWórkÓńÚtfČhářactersAsWelL");
  g_assert_cmpstr ("Ňeedš Ťo Wórk Óń Útf Čhářacters As WelL", ==, s.c_str ());
}

static void
test_count_digits (Fixture *fix, gconstpointer data)
{
  g_assert_cmpuint (0, ==, StringUtils::CountDigits (""));

  g_assert_cmpuint (0, ==, StringUtils::CountDigits ("abcdefghijklmnopqrstuvwxyz"));

  g_assert_cmpuint (10, ==, StringUtils::CountDigits ("0123456789"));

  g_assert_cmpuint (1, ==, StringUtils::CountDigits ("abc3"));

  g_assert_cmpuint (3, ==, StringUtils::CountDigits ("::123__poa//weee"));

  g_assert_cmpuint (5, ==, StringUtils::CountDigits ("PCN30129.JPG"));

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
  g_test_add ("/Zeitgeist/FTS/StringUtils/RemoveUnderscores", Fixture, 0,
              setup, test_underscores, teardown);
  g_test_add ("/Zeitgeist/FTS/StringUtils/UnCamelcase", Fixture, 0,
              setup, test_uncamelcase, teardown);
  g_test_add ("/Zeitgeist/FTS/StringUtils/CountDigits", Fixture, 0,
              setup, test_count_digits, teardown);
#ifdef HAVE_DEE_ICU
  g_test_add ("/Zeitgeist/FTS/StringUtils/AsciiFold", Fixture, 0,
              setup, test_ascii_fold, teardown);
#endif
}

G_END_DECLS
