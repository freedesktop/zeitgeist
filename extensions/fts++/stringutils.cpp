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

#include "stringutils.h"
#include <string>
#include <algorithm>

#ifdef HAVE_DEE_ICU
#include <dee-icu.h>
#endif

using namespace std;

namespace ZeitgeistFTS {

namespace StringUtils {

/**
 * Make sure s has equal or less than 'nbytes' bytes making sure the returned
 * string is still valid UTF-8.
 *
 * NOTE: It is assumed the input string is valid UTF-8. Untrusted text
 * should be validated with g_utf8_validate().
 *
 * This function useful for working with Xapian terms because Xapian has
 * a max term length of 245 (which is not very well documented, but see
 * http://xapian.org/docs/omega/termprefixes.html).
 */
string Truncate (string const& s, unsigned int nbytes)
{
  const gchar *str = s.c_str();
  const gchar *iter = str;

  nbytes = MIN(nbytes, s.length());

  while (iter - str < nbytes)
  {
    const gchar *tmp = g_utf8_next_char (iter);
    if (tmp - str > nbytes) break;
    iter = tmp;
  }


  return s.substr(0, iter - str);
}

/**
 * Converts a URI into an index- and query friendly string. The problem
 * is that Xapian doesn't handle CAPITAL letters or most non-alphanumeric
 * symbols in a boolean term when it does prefix matching. The mangled
 * URIs returned from this function are suitable for boolean prefix searches.
 *                 
 * IMPORTANT: This is a 1-way function! You can not convert back.
 */
string MangleUri (string const& orig)
{
  // the input is supposed to be a uri, so no utf8 characters
  gchar *casefolded = g_ascii_strdown (orig.c_str (), orig.size ());

  string s(casefolded);
  g_free (casefolded);
  size_t pos = 0;
  while ((pos = s.find_first_of (": /-.%", pos)) != string::npos)
  {
    s.replace (pos, 1, 1, '_');
    pos++;
  }

  return s;
}

/**
 * This method expects a valid uri and tries to split it into authority,
 * path and query.
 *
 * Note that any and all parts may be left untouched.
 */
void SplitUri (string const& uri, string &authority,
               string &path, string &query)
{
  size_t colon_pos = uri.find (':');
  if (colon_pos == string::npos) return; // not an uri?
  bool has_double_slash = uri.length () > colon_pos + 2 && 
    uri.compare (colon_pos + 1, 2, "//") == 0;

  size_t start_pos = has_double_slash ? colon_pos + 3 : colon_pos + 1;

  size_t first_slash = uri.find ('/', start_pos);
  size_t question_mark_pos = uri.find ('?', first_slash == string::npos ?
      start_pos : first_slash + 1);

  authority = uri.substr (start_pos);
  if (first_slash != string::npos)
  {
    authority.resize (first_slash - start_pos);
  }
  else if (question_mark_pos != string::npos)
  {
    authority.resize (question_mark_pos - start_pos);
  }

  if (first_slash == string::npos)
  {
    first_slash = start_pos + authority.length ();
  }

  if (question_mark_pos != string::npos)
  {
    path = uri.substr (first_slash, question_mark_pos - first_slash);
    query = uri.substr (question_mark_pos + 1);
  }
  else
  {
    path = uri.substr (first_slash);
  }
}

string RemoveUnderscores (string const &input)
{
  string result (input);
  std::replace (result.begin (), result.end (), '_', ' ');

  return result;
}

static bool is_digit (char c) { return c >= '0' && c <= '9'; }

size_t CountDigits (string const &input)
{
  return std::count_if (input.begin (), input.end (), is_digit);
}

static GRegex *camelcase_matcher = NULL;

static gboolean
matcher_cb (const GMatchInfo *match_info, GString *result, gpointer user_data)
{
  gint start_pos;
  g_match_info_fetch_pos (match_info, 0, &start_pos, NULL);
  if (start_pos != 0) g_string_append_c (result, ' ');
  gchar *word = g_match_info_fetch (match_info, 0);
  g_string_append (result, word);
  g_free (word);

  return FALSE;
}

string UnCamelcase (string const &input)
{
  if (camelcase_matcher == NULL)
  {
    camelcase_matcher = g_regex_new ("(?<=^|[[:lower:]])[[:upper:]]+[^[:upper:]]+", G_REGEX_OPTIMIZE, (GRegexMatchFlags) 0, NULL);
    if (camelcase_matcher == NULL) g_critical ("Unable to create matcher!");
  }

  gchar *result = g_regex_replace_eval (camelcase_matcher, input.c_str (),
                                        input.length (), 0,
                                        (GRegexMatchFlags) 0,
                                        matcher_cb, NULL, NULL);

  string ret (result);
  g_free (result);
  return ret;
}

#ifdef HAVE_DEE_ICU
static DeeICUTermFilter *icu_filter = NULL;

/**
 * Use ascii folding filter on the input text and return folded version
 * of the original string.
 *
 * Note that if the folded version is exactly the same as the original
 * empty string will be returned.
 */
string AsciiFold (string const& input)
{
  if (icu_filter == NULL)
  {
    icu_filter = dee_icu_term_filter_new_ascii_folder ();
    if (icu_filter == NULL) return "";
  }

  // FIXME: check first if the input contains any non-ascii chars?

  gchar *folded = dee_icu_term_filter_apply (icu_filter, input.c_str ());
  string result (folded);
  g_free (folded);

  return result == input ? "" : result;
}
#else
string AsciiFold (string const& input)
{
  return "";
}
#endif

} /* namespace StringUtils */

} /* namespace ZeitgeistFTS */
