/* where-clause.vala
 *
 * Copyright © 2011 Collabora Ltd.
 *             By Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
 *
 * Based upon a Python implementation (2009-2011) by:
 *  Markus Korn <thekorn@gmx.net>
 *  Mikkel Kamstrup Erlandsen <mikkel.kamstrup@gmail.com>
 *  Seif Lotfy <seif@lotfy.com>
 *  Siegfried-Angel Gevatter Pujals <siegfried@gevatter.com>
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Lesser General Public License as published by
 * the Free Software Foundation, either version 2.1 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 */

using Zeitgeist;

namespace Zeitgeist
{

    /**
     * This class provides a convenient representation a SQL `WHERE' clause,
     * composed of a set of conditions joined together.
     *
     * The relation between conditions can be either of type *AND* or *OR*, but
     * not both. To create more complex clauses, use several `WhereClause`
     * instances and joining them together using `extend`.
     *
     * Instances of this class can then be used to obtain a line of SQL code and
     * a list of arguments, for use with SQLite 3.
     */
    public class WhereClause : Object
    {

        private static string AND = " AND ";
        private static string OR  = " OR ";
        private static string NOT = " NOT ";

        private GenericArray<string> conditions;

        public WhereClause ()
        {
            
        }

        /*public void add_text (string condition, string? argument=null)
        {
            if (condition == "") // FIXME: why do we have this?
                return;
            conditions.add (condition);
            if (argument != null)
            {
                
            }
        }*/

        // optimize_glob

    }

}
