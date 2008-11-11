# Copyright (C) 2008 Samuel Abels <http://debain.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2, as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
import datetime
import calendar


class MyCalendar(object):
    """
    A wrapper around Python's calendar.Calendar() that doesn't suck.
    """

    def __init__(self, week_start = calendar.SUNDAY):
        """
        Constructor.
        
        week_start -- the first day of the week, e.g. calendar.SUNDAY
        """
        assert week_start is not None
        self.calendar = calendar.Calendar(week_start)
        

    def get_week(self, date):
        """
        Returns a tuple (start, end), where "start" points to the first day 
        of the given week, and "end" points to the last day of given week.
        """
        month_tuple = date.timetuple()[:2]
        week_tuple  = date.timetuple()[:3]
        weeks       = self.calendar.monthdatescalendar(*month_tuple)
        for week in weeks:
            if week_tuple not in [d.timetuple()[:3] for d in week]:
                continue
            return week[0], week[-1]
        raise Exception('No such week')


    def get_month(self, date):
        """
        Returns a tuple (start, end), where "start points to the first day 
        of the given month and "end" points to the last day of the given 
        month.
        """
        date_tuple = date.timetuple()
        year       = date_tuple[0]
        month      = date_tuple[1]
        last_day   = calendar.monthrange(year, month)[1]
        start      = datetime.date(year, month, 1)
        end        = datetime.date(year, month, last_day)
        return start, end


    def get_month_weeks(self, date, fill = True):
        """
        Returns a tuple (start, end), where "start" points to the first day 
        of the first week of given month, and "end" points to the last day of 
        the last week of the same month.

        If "fill" is True, this function always returns 6 weeks per month by 
        appending another week if the time span is shorter.
        """
        weeks = self.calendar.monthdatescalendar(*date.timetuple()[:2])
        start = weeks[0][0]
        end   = weeks[-1][-1]
        if fill:
            end += datetime.timedelta(7) * (6 - len(weeks))
        return start, end


    def get_day_name(self, date):
        day = calendar.weekday(*date.timetuple()[:3])
        return calendar.day_name[day]


    def get_month_name(self, date):
        return calendar.month_name[date.timetuple()[1]]
