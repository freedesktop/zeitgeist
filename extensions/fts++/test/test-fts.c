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

void test_stringutils_create_suite (void);
void test_indexer_create_suite (void);

gint
main (gint argc, gchar *argv[])
{
  g_type_init ();

  g_test_init (&argc, &argv, NULL);

  test_stringutils_create_suite ();
  test_indexer_create_suite ();

  return g_test_run ();
}
