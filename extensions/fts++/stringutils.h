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

} /* namespace StringUtils */

} /* namespace ZeitgeistFTS */
