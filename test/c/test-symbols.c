/*
 * Copyright © 2010 Canonical Ltd.
 *             By Michal Hruby <michal.mhr@gmail.com>
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
 */

#include <glib.h>
#include <glib-object.h>
#include <string.h>
#include "zeitgeist.h"

typedef struct
{
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
test_null_symbols (Fixture *fix, gconstpointer data)
{
  // shouldn't crash
  zeitgeist_symbol_is_a (NULL, NULL);
}

static void
test_null_first (Fixture *fix, gconstpointer data)
{
  gboolean res = zeitgeist_symbol_is_a (NULL, ZEITGEIST_NFO_MEDIA);

  g_assert_cmpint (res, ==, FALSE);
}

static void
test_null_second (Fixture *fix, gconstpointer data)
{
  gboolean res = zeitgeist_symbol_is_a (ZEITGEIST_NFO_MEDIA, NULL);

  g_assert_cmpint (res, ==, FALSE);
}

static void
test_not_uri (Fixture *fix, gconstpointer data)
{
  gboolean res = zeitgeist_symbol_is_a ("first", "second");

  g_assert_cmpint (res, ==, FALSE);
}

static void
test_not_uri_equal (Fixture *fix, gconstpointer data)
{
  gboolean res = zeitgeist_symbol_is_a ("something", "something");

  g_assert_cmpint (res, ==, FALSE);
}

static void
test_uris_equal (Fixture *fix, gconstpointer data)
{
  gboolean res = zeitgeist_symbol_is_a (ZEITGEIST_NFO_AUDIO,
                                        ZEITGEIST_NFO_AUDIO);

  g_assert_cmpint (res, ==, TRUE);
}

static void
test_vector_image_media (Fixture *fix, gconstpointer data)
{
  gboolean res = zeitgeist_symbol_is_a (ZEITGEIST_NFO_VECTOR_IMAGE,
                                        ZEITGEIST_NFO_MEDIA);

  g_assert_cmpint (res, ==, TRUE);
}

static void
test_media_vector_image (Fixture *fix, gconstpointer data)
{
  gboolean res = zeitgeist_symbol_is_a (ZEITGEIST_NFO_MEDIA,
                                        ZEITGEIST_NFO_VECTOR_IMAGE);

  g_assert_cmpint (res, ==, FALSE);
}

static void
test_media_software (Fixture *fix, gconstpointer data)
{
  gboolean res = zeitgeist_symbol_is_a (ZEITGEIST_NFO_MEDIA,
                                        ZEITGEIST_NFO_SOFTWARE);

  g_assert_cmpint (res, ==, FALSE);
}

static void
is_uri_valid (gpointer data, gpointer unused)
{
  const gchar SEM_D_URI[] = "http://www.semanticdesktop.org/ontologies";
  gchar *uri = (gchar*) data;
  g_assert (uri != NULL && g_str_has_prefix (uri, SEM_D_URI));
  gchar *str = g_strdup_printf ("%s", uri);

  g_free (str);
}

static void
test_media_children (Fixture *fix, gconstpointer data)
{
  GList* children = zeitgeist_symbol_get_children (ZEITGEIST_NFO_MEDIA);

  g_assert_cmpint (g_list_length (children), >, 0);
  g_list_foreach (children, is_uri_valid, NULL);

  g_list_free (children);
}

static void
test_media_all_children (Fixture *fix, gconstpointer data)
{
  GList* children = zeitgeist_symbol_get_all_children (ZEITGEIST_NFO_MEDIA);

  g_assert_cmpint (g_list_length (children), >, 0);
  g_list_foreach (children, is_uri_valid, NULL);

  g_list_free (children);
}

static void
test_vector_image_parents (Fixture *fix, gconstpointer data)
{
  GList* parents = zeitgeist_symbol_get_parents (ZEITGEIST_NFO_VECTOR_IMAGE);

  g_assert_cmpint (g_list_length (parents), >, 0);
  g_list_foreach (parents, is_uri_valid, NULL);

  g_list_free (parents);
}

static void
test_media_complex (Fixture *fix, gconstpointer data)
{
  GList* iter;
  GList* children = zeitgeist_symbol_get_children (ZEITGEIST_NFO_MEDIA);
  GList* all_ch = zeitgeist_symbol_get_all_children (ZEITGEIST_NFO_MEDIA);

  g_assert_cmpint (g_list_length (children), >, 0);
  g_assert_cmpint (g_list_length (all_ch), >, g_list_length (children));

  for (iter = children; iter; iter = iter->next)
  {
    // check that it's also in all_children
    g_assert (g_list_find_custom (all_ch, iter->data, (GCompareFunc) strcmp));
  }

  g_list_free (all_ch);
  g_list_free (children);
}

int
main (int   argc,
      char *argv[])
{
  g_type_init();
  g_test_init (&argc, &argv, NULL);

  g_test_add ("/Zeitgeist/Symbols/NullNull", Fixture, NULL,
              setup, test_null_symbols, teardown);
  g_test_add ("/Zeitgeist/Symbols/FirstNull", Fixture, NULL,
              setup, test_null_first, teardown);
  g_test_add ("/Zeitgeist/Symbols/SecondNull", Fixture, NULL,
              setup, test_null_second, teardown);
  g_test_add ("/Zeitgeist/Symbols/NotUris", Fixture, NULL,
              setup, test_not_uri, teardown);
  g_test_add ("/Zeitgeist/Symbols/NotUrisEqual", Fixture, NULL,
              setup, test_not_uri_equal, teardown);
  g_test_add ("/Zeitgeist/Symbols/EqualUris", Fixture, NULL,
              setup, test_uris_equal, teardown);
  g_test_add ("/Zeitgeist/Symbols/ValidParent", Fixture, NULL,
              setup, test_vector_image_media, teardown);
  g_test_add ("/Zeitgeist/Symbols/ValidChild", Fixture, NULL,
              setup, test_media_vector_image, teardown);
  g_test_add ("/Zeitgeist/Symbols/Unrelated", Fixture, NULL,
              setup, test_media_software, teardown);
  g_test_add ("/Zeitgeist/Symbols/GetChildren", Fixture, NULL,
              setup, test_media_children, teardown);
  g_test_add ("/Zeitgeist/Symbols/GetAllChildren", Fixture, NULL,
              setup, test_media_all_children, teardown);
  g_test_add ("/Zeitgeist/Symbols/GetParents", Fixture, NULL,
              setup, test_vector_image_parents, teardown);
  g_test_add ("/Zeitgeist/Symbols/SymbolInfo", Fixture, NULL,
              setup, test_media_complex, teardown);

  return g_test_run();
}
