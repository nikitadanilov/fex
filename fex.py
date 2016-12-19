#!/usr/bin/env python

import svgwrite
import datetime
import sys

class chart(object):
    def __init__(self, width, height, duration, starttime, stoptime, minG, maxG,
                 outname = "out.svg", outbar = "out.1m", outmt = "out.mt",
                 axes = 0, verbosity = 0):
        self.width     = width
        self.height    = height
        self.minG      = minG
        self.maxG      = maxG
        self.duration  = datetime.timedelta(milliseconds = duration)
        self.starttime = self.parsetime(starttime)
        self.stoptime  = self.parsetime(stoptime)
        self.outname   = outname
        self.outbar    = open(outbar, "w")
        self.outmt     = open(outmt,  "w")
        self.verbosity = verbosity
        self.area      = svgwrite.Drawing(outname, profile='full',
                                          size = (str(width)  + "px",
                                                  str(height) + "px"))
        self.cwidth    = 20 # candle width in pixels
        self.cnr       = 0
        self.cstart    = self.starttime
        self.cend      = self.starttime + self.duration
        if axes > 0:
            for nr in range(0, 50):
                y = self.px(nr * (self.maxG - self.minG) / 50 + self.minG)
                self.line(start = (0, y), end = (self.width, y),
                          stroke = svgwrite.rgb(0, 0, 0, '%'),
                          stroke_width = 1, stroke_dasharray = "1,1")
                nr = 0
                while self.starttime + nr * self.duration <= self.stoptime:
                    x = nr * self.cwidth
                    self.line(start = (x, 0), end = (x, self.height),
                              stroke = svgwrite.rgb(0, 0, 0, '%'),
                              stroke_width = 1, stroke_dasharray = "1,1")
                    self.text(str(self.starttime + nr * self.duration),
                              insert = (x + 1, self.height - 10))
                    for y in range(0, 50):
                        yy = y * (self.maxG - self.minG) / 50 + self.minG
                        self.text(str(yy), insert = (x + 1, self.px(yy)))
                        nr += 10
        self.candlestart()

    def add(self, line):
        (t, b, a, v) = self.parse(line)
        if t >= self.stoptime:
            return True
        if t < self.starttime:
            return False
        while t >= self.cend:
            self.candledone()
            self.candlenext()
        assert self.cstart <= t and t < self.cend
        self.candleadd(b)
        return False

    def done(self):
        self.candledone()
        self.area.save()
        self.outbar.close()
        self.outmt.close()

    def parse(self, stamp):
        # http://www.histdata.com/f-a-q/data-files-detailed-specification/
        #
        # 20151201 000049470,1.057440,1.057470,0
        # YYYYMMDD HHmmSSmmm BID Q    ASK Q    VOLUME
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
        left = self.cnr * self.cwidth
        if self.openQ != None:
            centre = left + self.cwidth/2
            openP  = self.px(self.openQ)
            lastP  = self.px(self.lastQ)
            minP   = self.px(self.minQ)
            maxP   = self.px(self.maxQ)
            if openP == lastP:
                lastP += 1

            self.line(start = (centre, minP), end = (centre, maxP),
                      stroke = svgwrite.rgb(0, 0, 0, '%'), stroke_width = 3)
            self.rect(insert = (left, min(openP, lastP)),
                      size = (self.cwidth, abs(openP - lastP)),
                      fill = svgwrite.rgb(100, 0, 0, '%') if lastP > openP else \
                      svgwrite.rgb(0, 100, 0, '%'))
            # 20120201 000100;1.306570;1.306570;1.306470;1.306560;0
            # YYYYmmdd HHmmSS;open Q  ; high Q ; low Q  ; close Q;volume
            self.outbar.write("{:%Y%m%d %H%M%S};{:f};{:f};{:f};{:f};0\n".format(
                self.cstart, self.openQ,self.maxQ, self.minQ, self.lastQ))
            # MetaTrader format
            # 2012.02.01,00:00,1.306600,1.306600,1.306560,1.306560,0
            # YYYY.mm.dd,HH:MM,open Q  ,hight Q ,low Q   ,close Q ,volume
            self.outmt.write("{:%Y.%m.%d,%H:%M},{:f},{:f},{:f},{:f},0\n".format(
                self.cstart, self.openQ,self.maxQ, self.minQ, self.lastQ))
            if self.verbosity > 0:
                print("Candle: {}/{}: [{}, {}): {} {} {} {}".
                      format(self.cnr, left, self.cstart, self.cend,
                             self.openQ, self.minQ, self.maxQ, self.lastQ))
        else: # gap
            self.rect(insert = (left, 0), size = (self.cwidth, self.height),
                      fill = svgwrite.rgb(50, 50, 50, '%'),
                      stroke = svgwrite.rgb(0, 0, 0, '%'), stroke_width = 3)

    def rect(self, **kw):
        self.area.add(self.area.rect(**kw))

    def line(self, **kw):
        self.area.add(self.area.line(**kw))

    def text(self, string, **kw):
        self.area.add(self.area.text(string, **kw))

    def px(self, quote):
        return self.height * (self.maxG - quote) / (self.maxG - self.minG)
