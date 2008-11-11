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

def time_delta(datetime1, datetime2):
    delta = datetime1 - datetime2
    if delta < datetime.timedelta():
        return -delta
    return delta


def same_day(date1, date2):
    return date1.timetuple()[:3] == date2.timetuple()[:3]


def end_of_day(date):
    start = datetime.datetime(*date.timetuple()[:3])
    return start + datetime.timedelta(1) - datetime.timedelta(0, 0, 0, 1)


def previous_day(date):
    return date - datetime.timedelta(1)


def next_day(date):
    return date + datetime.timedelta(1)


def previous_week(date):
    return date - datetime.timedelta(7)


def next_week(date):
    return date + datetime.timedelta(7)


def previous_month(cal, date):
    year, month, day = date.timetuple()[:3]
    if month == 1:
        year  -= 1
        month  = 12
    else:
        month -= 1
    prev_month_days = [d for d in cal.itermonthdays(year, month)]
    if day not in prev_month_days:
        day = max(prev_month_days)
    return datetime.datetime(year, month, day)


def next_month(cal, date):
    year, month, day = date.timetuple()[:3]
    if month == 12:
        year  += 1
        month  = 1
    else:
        month += 1
    next_month_days = [d for d in cal.itermonthdays(year, month)]
    if day not in next_month_days:
        day = max(next_month_days)
    return datetime.datetime(year, month, day)


def event_days(event1, event2):
    return time_delta(event1.start, event1.end).days \
         - time_delta(event2.start, event2.end).days


def event_intersects(event, start, end = None):
    if end is None:
        end = start
    return (event.start >= start and event.start < end) \
        or (event.end > start and event.end <= end) \
        or (event.start < start and event.end > end)


def get_intersection_list(list, start, end):
    intersections = []
    for event in list:
        if event_intersects(event, start, end):
            intersections.append(event)
    return intersections


def count_intersections(list, start, end):
    intersections = 0
    for event in list:
        if event_intersects(event, start, end):
            intersections += 1
    return intersections


def count_parallel_events(list, start, end):
    """
    Given a list of events, this function returns the maximum number of
    parallel events in the given timeframe.
    """
    parallel = 0
    i        = 0
    for i, event1 in enumerate(list):
        if not event_intersects(event1, start, end):
            continue
        parallel = max(parallel, 1)
        for f in range(i + 1, len(list)):
            event2    = list[f]
            new_start = max(event1.start, event2.start)
            new_end   = min(event1.end,   event2.end)
            if event_intersects(event2, start, end) \
                and event_intersects(event2, new_start, new_end):
                n = count_parallel_events(list[f:], new_start, new_end)
                parallel = max(parallel, n + 1)
    return parallel
