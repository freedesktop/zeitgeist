/*
 * Copyright © 2010 Canonical Ltd.
 *             By Mikkel Kamstrup Erlandsen <mikkel.kamstrup@canonical.com>
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
test_mime_textplain (Fixture *fix, gconstpointer data)
{
  g_assert_cmpstr (ZEITGEIST_NFO_TEXT_DOCUMENT, ==,
                   zeitgeist_interpretation_for_mimetype ("text/plain"));
}

static void
test_mime_none (Fixture *fix, gconstpointer data)
{
  g_assert (zeitgeist_interpretation_for_mimetype ("asdfasdf") == NULL);
}

static void
test_mime_regex (Fixture *fix, gconstpointer data)
{
  /* We should have a fallback for application/x-applix-* */
  g_assert_cmpstr (ZEITGEIST_NFO_DOCUMENT, ==,
                   zeitgeist_interpretation_for_mimetype ("application/x-applix-FOOOOBAR!"));

  /* Still application/x-applix-spreadsheet should be a spreadsheet */
  g_assert_cmpstr (ZEITGEIST_NFO_SPREADSHEET, ==,
                   zeitgeist_interpretation_for_mimetype ("application/x-applix-spreadsheet"));
}

static void
test_scheme_file (Fixture *fix, gconstpointer data)
{
  g_assert_cmpstr (ZEITGEIST_NFO_FILE_DATA_OBJECT, ==,
                   zeitgeist_manifestation_for_uri ("file:///tmp/foo.txt"));
}

static void
test_scheme_none (Fixture *fix, gconstpointer data)
{
  g_assert (zeitgeist_manifestation_for_uri ("asdf://asdfasdf") == NULL);
}

int
main (int   argc,
      char *argv[])
{
  g_test_init (&argc, &argv, NULL);

  g_test_add ("/Zeitgeist/Mime/TextPlain", Fixture, NULL,
              setup, test_mime_textplain, teardown);
  g_test_add ("/Zeitgeist/Mime/None", Fixture, NULL,
              setup, test_mime_none, teardown);
  g_test_add ("/Zeitgeist/Mime/Regex", Fixture, NULL,
              setup, test_mime_regex, teardown);
  g_test_add ("/Zeitgeist/UriScheme/File", Fixture, NULL,
              setup, test_scheme_file, teardown);
  g_test_add ("/Zeitgeist/UriScheme/None", Fixture, NULL,
              setup, test_scheme_none, teardown);

  return g_test_run();
}
