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
#include <string>

#include "stringutils.h"

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
  string s(orig);
  size_t pos = 0;
  while ((pos = s.find_first_of (": /", pos)) != string::npos)
  {
    s.replace (pos, 1, 1, '_');
  }

  return s;
}

} /* namespace StringUtils */

} /* namespace ZeitgeistFTS */
