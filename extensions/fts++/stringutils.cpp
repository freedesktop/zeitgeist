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

} /* namespace StringUtils */

} /* namespace ZeitgeistFTS */
