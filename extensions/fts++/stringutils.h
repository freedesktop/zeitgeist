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

#include <string>
#include <glib.h>

namespace ZeitgeistFTS {

namespace StringUtils {

const unsigned int MAX_TERM_LENGTH = 245;

std::string Truncate (std::string const& s,
                      unsigned int nbytes = MAX_TERM_LENGTH);

std::string MangleUri (std::string const& orig);

void SplitUri (std::string const& uri,
               std::string &host,
               std::string &path,
               std::string &basename);

std::string RemoveUnderscores (std::string const &input);

size_t CountDigits (std::string const &input);

std::string UnCamelcase (std::string const &input);

std::string AsciiFold (std::string const& input);

} /* namespace StringUtils */

} /* namespace ZeitgeistFTS */
