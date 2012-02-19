/* logging.vala
 *
 * Copyright © 2012 Canonical Ltd.
 *             By Siegfried-A. Gevatter <siegfried.gevatter@collabora.co.uk>
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

namespace Zeitgeist
{
    namespace Logging
    {

        private const string BLUE = "\x1b[34m";
        private const string GREEN = "\x1b[32m";
        private const string RED = "\x1b[31m";
        private const string YELLOW = "\x1b[33m";
        private const string RESET = "\x1b[0m";

        private string get_log_level_string (LogLevelFlags log_levels,
            out string color)
        {
            string log_level;

            if ((log_levels & LogLevelFlags.LEVEL_ERROR) != 0)
            {
                log_level = "ERROR";
                color = RED;
            }
            else if ((log_levels & LogLevelFlags.LEVEL_CRITICAL) != 0)
            {
                log_level = "CRITICAL";
                color = RED;
            }
            else if ((log_levels & LogLevelFlags.LEVEL_WARNING) != 0)
            {
                log_level = "WARNING";
                color = RED;
            }
            else if ((log_levels & LogLevelFlags.LEVEL_MESSAGE) != 0)
            {
                log_level = "MESSAGE";
                color = BLUE;
            }
            else if ((log_levels & LogLevelFlags.LEVEL_INFO) != 0)
            {
                log_level = "INFO";
                color = BLUE;
            }
            else if ((log_levels & LogLevelFlags.LEVEL_DEBUG) != 0)
            {
                log_level = "DEBUG";
                color = GREEN;
            }
            else
            {
                log_level = "UNKNOWN";
                color = BLUE;
            }

            return log_level;
        }

        private void log_handler (string? log_domain, LogLevelFlags log_levels,
            string message)
        {
            string color;
            string log_level = get_log_level_string (log_levels, out color);
            string timestamp = TimeVal ().to_iso8601 ().substring (11, 15);
            //string datestamp = new DateTime.now_local ().format (
            //    "%Y-%m-%d %H:%M:%S");
            // FIXME: get PID

            unowned FileStream output;
            if (log_levels >= LogLevelFlags.LEVEL_MESSAGE)
                output = stdout; // MESSAGE, INFO or DEBUG
            else
                output = stderr;

            // Print to console
            output.printf ("%s[%s %s]%s %s\n", color, timestamp,
                log_level, RESET, message);

            // Log to file
            // FIXME:
            //printf ("[%s] - %s - %s\n", datestamp, log_level, message);
        }

        public void setup_logging (string? log_level)
        {
            LogLevelFlags discarded = LogLevelFlags.LEVEL_DEBUG;
            if (log_level != null)
            {
                var ld = LogLevelFlags.LEVEL_DEBUG;
                var li = LogLevelFlags.LEVEL_INFO;
                var lm = LogLevelFlags.LEVEL_MESSAGE;
                var lw = LogLevelFlags.LEVEL_WARNING;
                var lc = LogLevelFlags.LEVEL_CRITICAL;
                switch (log_level.up ())
                {
                    case "DEBUG":
                        discarded = 0;
                        break;
                    case "INFO":
                        discarded = ld;
                        break;
                    case "WARNING":
                        discarded = ld | li | lm;
                        break;
                    case "CRITICAL":
                        discarded = ld | li | lm | lw;
                        break;
                    case "ERROR":
                        discarded = ld | li | lm | lw | lc;
                        break;
                }
            }
            if (discarded != 0)
                Log.set_handler (null, discarded, () => {});

            LogLevelFlags logged = ~discarded & ~LogLevelFlags.FLAG_RECURSION;
            Log.set_handler (null, logged, log_handler);
        }

    }
}

// vim:expandtab:ts=4:sw=4
