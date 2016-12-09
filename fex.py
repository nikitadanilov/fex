#!/usr/bin/env python

import svgwrite
import datetime
import sys

class chart(object):
    def __init__(self, width, height, duration, starttime, stoptime, minG, maxG,
                 outname = "out.svg", verbosity = 0):
        self.width     = width
        self.height    = height
        self.minG      = minG
        self.maxG      = maxG
        self.duration  = datetime.timedelta(milliseconds = duration)
        self.starttime = self.parsetime(starttime)
        self.stoptime  = self.parsetime(stoptime)
        self.outname   = outname
        self.verbosity = verbosity
        self.area      = svgwrite.Drawing(outname, profile='full',
                                          size = (str(width)  + "px",
                                                  str(height) + "px"))
        self.cwidth    = 20 # candle width in pixels
        self.cnr       = 0
        self.cstart    = self.starttime
        self.cend      = self.starttime + self.duration
        self.candlestart()

    def add(self, line):
        (t, b, a, v) = self.parse(line)
        if t >= self.stoptime:
            return True
        if t >= self.cend:
            self.candledone()
            self.candlenext()
        if self.cstart <= t and t < self.cend:
            self.candleadd(b)
        return False

    def done(self):
        self.candledone()
        self.area.save()

    def parse(self, stamp):
        # http://www.histdata.com/f-a-q/data-files-detailed-specification/
        #
        # 20151201 000049470,1.057440,1.057470,0
        # YYYYMMDD HHMMSSmmm BID Q    ASK Q    VOLUME
        # 01234567890123456789012345678901234567
        t = self.parsetime(stamp)
        b = float(stamp[19 : 27])
        a = float(stamp[28 : 36])
        return (t, b, a, 0)

    def parsetime(self, stamp):
        return datetime.datetime(year        = int(stamp[ 0 :  4]),
                                 month       = int(stamp[ 4 :  6]),
                                 day         = int(stamp[ 6 :  8]),
                                 hour        = int(stamp[ 9 : 11]),
                                 minute      = int(stamp[11 : 13]),
                                 second      = int(stamp[13 : 15]),
                                 microsecond = int(stamp[15 : 18]))
    def candlestart(self):
        self.minQ = sys.maxsize
        self.maxQ = 0
        self.openQ = None
        self.lastQ = None

    def candleadd(self, q):
        if self.openQ == None:
            self.openQ = q
        self.lastQ = q
        self.minQ  = min(self.minQ, q)
        self.maxQ  = max(self.maxQ, q)

    def candlenext(self):
        self.cstart = self.cend
        self.cend   = self.cend + self.duration
        self.cnr   += 1
        self.candlestart()

    def candledone(self):
        if self.openQ != None:
            left   = self.cnr * self.cwidth
            centre = left + self.cwidth/2
            openP  = self.px(self.openQ)
            lastP  = self.px(self.lastQ)
            minP   = self.px(self.minQ)
            maxP   = self.px(self.maxQ)
            if openP == lastP:
                lastP += 1

            self.line(start = (centre, minP), end = (centre, maxP),
                      stroke = svgwrite.rgb(0, 0, 10, '%'), stroke_width = 3)
            self.rect(insert = (left, min(openP, lastP)),
                      size = (self.cwidth, abs(openP - lastP)),
                      fill = svgwrite.rgb(100, 0, 0, '%') if lastP > openP else \
                      svgwrite.rgb(0, 100, 0, '%'))
            if self.verbosity > 0:
                print("Candle: [{}, {}): {} {} {} {}\n".
                      format(self.cstart, self.cend,
                             self.openQ, self.minQ, self.maxQ, self.lastQ))

    def rect(self, **kw):
        self.area.add(self.area.rect(**kw))

    def line(self, **kw):
        self.area.add(self.area.line(**kw))

    def px(self, quote):
        return self.height * (self.maxG - quote) / (self.maxG - self.minG)
