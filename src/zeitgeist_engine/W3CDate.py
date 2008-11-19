import re
import time

__author__ = "Andrew Shearer, ashearerw@shearersoftware.com"
__version__ = "1.1.1"

# URL: http://www.shearersoftware.com/software/developers/w3cdate/
# Python-licensed.

class W3CDate:
    """Date parsing and formatting according to RFC 8601, RFC 822, and XML-RPC.
    Formats from <http://www.w3.org/TR/NOTE-datetime> are preferred.
    Also see <http://www.cs.tut.fi/~jkorpela/iso8601.html>.
    But XML-RPC omits date punctuation and timezones, and clients rely on
    this. (For example, w.bloggar refuses to recognize dates with dashes.)
    And RSS's postDate element is completely different, an RFC 822-style date.
    So this class converts between all three styles.
    ISO8601 (W3C Date subset):
    2003-01-15
    2003-01-15T02:30:45         (secs optional)
    2003-01-15T02:30:45Z        (secs optional)
    2003-01-15T02:30:45-05:00   (secs optional)
    XML-RPC:
    20030115
    20030115T02:30:45           (secs optional)
    RFC822:
    Sun, 02 Feb 2003, 02:30:45 -0500
    
    >>> d = W3CDate()
    >>> d.parseRFC822("Fri, 15 Nov 2002, 15:44 -0500")
    >>> d.getRFC822()
    'Fri, 15 Nov 2002 15:44:00 -0500'
    >>> d.getISO8601()
    '2002-11-15T15:44:00-05:00'
    >>> d.parseRFC822("Fri, 15 Nov 2002, 15:44 GMT")
    >>> d.getISO8601()
    '2002-11-15T15:44:00Z'
    >>> d.getRFC822()
    'Fri, 15 Nov 2002 15:44:00 GMT'
    >>> d.getXMLRPC()
    '20021115T15:44:00'
    >>> d.parse('2003/01/10T08:45:12-05:00')
    >>> d.getISO8601()
    '2003-01-10T08:45:12-05:00'
    >>> d.getRFC822()
    'Fri, 10 Jan 2003 08:45:12 -0500'

    """
    datePunctLen = 10
    datePunctRE = re.compile(r"^\d\d\d\d\D\d\d\D\d\d")
    dateNoPunctLen = 8
    dateNoPunctRE = re.compile(r"^\d\d\d\d\d\d\d\d")
    timeNoMinutesPunctLen = 6
    timeNoMinutesPunctRE = re.compile(r"^[Tt]\d\d\D\d\d")
    minutesPunctLen = 3
    minutesPunctRE = re.compile(r"^[^0-9+-]\d\d")
    timezoneGMTLen = 1
    timezoneGMTRE = re.compile(r"^[Zz]")
    timezoneOffsetLen = 6
    timezoneOffsetRE = re.compile(r"^[+-]\d\d\D\d\d")
    
    def __init__(self, text = None):
        self.dateSecs = None        # in GMT
        self.dateMiniTuple = None   # missing weekday, Julian day, DST
        self.dateFullTuple = None
        self.timezone = None        # None means we don't know; assume local timezone
        if text: self.parse(text)
        
    def parse(self, datestring, ceiling = 0):
        """Parse an RFC8601 (W3C) or XML-RPC date.
        """
        t = datestring  # t holds remaining suffix of datestring, still to be parsed
        timezone = parseddate = None 
        if ceiling:
            parsedtime = [23, 59, 59]               # +++ doesn't handle leap seconds
        else:
            parsedtime = [0, 0, 0]
         
        if self.datePunctRE.search(t):          # extract year-month-day
            parseddate = (int(t[0:4]),int(t[5:7]),int(t[8:10]))
            t = t[self.datePunctLen:]
        elif self.dateNoPunctRE.search(t):      # extract yearmonthday
            parseddate = (int(t[0:4]),int(t[4:6]),int(t[6:8]))
            t = t[self.dateNoPunctLen:]
        else:
            raise TypeError, ('invalid date "%s"' % datestring)
        if len(t) > 0:                                  # more?
            if self.timeNoMinutesPunctRE.search(t):     # extract hours:minutes
                parsedtime[0] = int(t[1:3])
                parsedtime[1] = int(t[4:6])
                t = t[self.timeNoMinutesPunctLen:]
                if self.minutesPunctRE.search(t):       # extract :seconds
                    parsedtime[2] = int(t[1:3])
                    t = t[self.minutesPunctLen:]
            if self.timezoneOffsetRE.search(t):         # extract [+-]time:zone
                timezone = int(t[1:3]) * 3600 + int(t[4:6]) * 60
                if t[0] != '-': timezone = -timezone
                t = t[self.timezoneOffsetLen:]
            elif self.timezoneGMTRE.search(t):          # extract Z (meaning GMT)
                timezone = 0
                t = t[self.timezoneGMTLen:]
            
        if len(t) > 0:
            raise TypeError, ('invalid date "%s", at "%s"' % (datestring, t))
        
        if timezone is not None:
            dst = 0     # no dst correction desired
        else:
            dst = -1    # unknown dst; use current local interp.
        self.dateMiniTuple = (parseddate[0], parseddate[1], parseddate[2],
            parsedtime[0], parsedtime[1], parsedtime[2], 0, 0, dst)
        # our tuple isn't complete; it's missing weekday, Julian day, DST
        self.dateFullTuple = None
        self.dateSecs = None
        self.timezone = timezone    # for auto timezone, could use time.timezone
    
    def parseRFC822(self, datestring):
        try:
            from email.Utils import parsedate_tz as parseDateRFC822Tuple
        except ImportError:
            from rfc822 import parsedate_tz as parseDateRFC822Tuple
        
        miniTupleWithTZ = parseDateRFC822Tuple(datestring)
        if miniTupleWithTZ is None:
            raise TypeError, ('invalid date "%s"' % datestring)
        if miniTupleWithTZ[9] is not None:
            self.timezone = -miniTupleWithTZ[9]
        else:
            self.timezone = None
        self.dateMiniTuple = miniTupleWithTZ[:9]
        self.dateFullTuple = None
        self.dateSecs = None
    
    def getISO8601(self):
        if self.dateMiniTuple is None:
            self._cacheTuples()
        result = time.strftime('%Y-%m-%dT%H:%M:%S', self.dateMiniTuple)
        if self.timezone is None:
            pass
        elif self.timezone == 0:
            result = result + 'Z'
        elif self.timezone < 0:
            result = result + ('+%02d:%02d' % divmod(-self.timezone / 60, 60))
        else:
            result = result + ('-%02d:%02d' % divmod(self.timezone / 60, 60))
        return result
        
    __str__ = __repr__ = getISO8601
    
    
    def getXMLRPC(self):
        if self.dateMiniTuple is None:
            self._cacheTuples()
        return time.strftime('%Y%m%dT%H:%M:%S', self.dateMiniTuple)
    
    def getRFC822(self):
        if self.dateFullTuple is None:
            self._cacheTuples()
        # not strictly intl-compliant, since English should always be used but this will localize
        # rfc822 module could help here, but it always uses GMT
        result = time.strftime("%a, %d %b %Y %H:%M:%S", self.dateFullTuple)
        if self.timezone is None:   # add timezone only if we know it
            pass
        elif self.timezone == 0:    # GMT
            result = result + (' GMT')
        elif self.timezone < 0:     # offset
            result = result + (' +%02d%02d' % divmod(-self.timezone / 60, 60))
        else:                       # offset the other way
            result = result + (' -%02d%02d' % divmod(self.timezone / 60, 60))
        return result
    
    def getSeconds(self):
        if self.dateSecs is None:
            self._cacheSeconds()
        return self.dateSecs
    
    def getDateTuple(self):
        if self.dateFullTuple is None:  
            self._cacheTuples()
        return self.dateFullTuple
    
    def setCurrentDate(self):
        self.dateSecs = time.time() # dateSecs is in GMT
        self.dateMiniTuple = self.dateFullTuple = time.localtime(self.dateSecs)
        if self.dateFullTuple[8] == 1 and time.daylight:    # in DST, and know DST's offset?
            self.timezone = time.altzone
        else:
            self.timezone = time.timezone
    
    def translateToGMT(self):
        if self.timezone != 0:
            if self.dateSecs is None: self._cacheSeconds()
            self.timezone = 0
            self.dateMiniTuple = self.dateFullTuple = None
    
    def _cacheTuples(self):
        if self.dateSecs is None:
            self._cacheSeconds()
        if self.timezone is None:
            self.dateFullTuple = self.dateMiniTuple = time.localtime(self.dateSecs)
        else:
            self.dateFullTuple = self.dateMiniTuple = time.gmtime(self.dateSecs - self.timezone)
    
    def _cacheSeconds(self):
        if self.dateMiniTuple is None:
            raise TypeError, "date has not been specified"
        self.dateSecs = time.mktime(self.dateMiniTuple)
        # time.mktime's conversion is affected by the local timezone, which we
        # don't necessarily want (because we may be representing any timezone).
        # So, correct for the difference between the local timezone and desired
        # timezone. If no specific timezone is set, we leave things at the local
        # timezone.
        if self.timezone is not None:
            if self.dateMiniTuple[8] != 0 and time.localtime(self.dateSecs)[8] == 1 and time.daylight:
                self.dateSecs = self.dateSecs - time.altzone
            else:
                self.dateSecs = self.dateSecs - time.timezone
            self.dateSecs = self.dateSecs + self.timezone
    
    def _check(self):
        if self.dateSecs is None: self._cacheSeconds()
        if self.dateMiniTuple is None: self._cacheTuples()
        origSecs = self.dateSecs
        self.dateSecs = None
        self._cacheSeconds()
        if int(self.dateSecs) != int(origSecs): print "Error: dateSecs don't match (%f became %f)" % (origSecs, self.dateSecs)
        origMiniTuple = self.dateMiniTuple
        self.dateMiniTuple = self.dateFullTuple = None
        self._cacheTuples()
        if self.dateMiniTuple != origMiniTuple: print "Error: dateMiniTuples don't match (%s became %s)" % (repr(origMiniTuple), repr(self.dateMiniTuple))
    
