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

        private string get_log_level_string (LogLevelFlags log_levels)
        {
            string log_level;

            if ((log_levels & LogLevelFlags.LEVEL_ERROR) != 0)
                log_level = "ERROR";
            else if ((log_levels & LogLevelFlags.LEVEL_CRITICAL) != 0)
                log_level = "CRITICAL";
            else if ((log_levels & LogLevelFlags.LEVEL_WARNING) != 0)
                log_level = "WARNING";
            else if ((log_levels & LogLevelFlags.LEVEL_MESSAGE) != 0)
                log_level = "MESSAGE";
            else if ((log_levels & LogLevelFlags.LEVEL_INFO) != 0)
                log_level = "INFO";
            else if ((log_levels & LogLevelFlags.LEVEL_DEBUG) != 0)
                log_level = "DEBUG";
            else
                log_level = "UNKNOWN";

            return log_level;
        }

        private void log_handler (string? log_domain, LogLevelFlags log_levels,
            string message)
        {
            string log_level = get_log_level_string (log_levels);
            //string timestamp = new DateTime.now_local ().format (
            //    "%Y-%m-%d %H:%M:%S");
            // FIXME: get PID

            unowned FileStream output;
            if ((log_levels & LogLevelFlags.LEVEL_DEBUG) != 0)
                output = stdout;
            else
                output = stderr;
            output.printf ("** %s: %s\n", log_level, message);
            
            // FIXME: log to file
            //printf ("[%s] - %s - %s\n", timestamp, log_level, message);
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
