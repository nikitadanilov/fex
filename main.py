#!/usr/bin/env python

import fileinput
import getopt
import sys

import fex

def processinput(argv):
    kw = {
        "height"    :    1000,
        "width"     :    4000,
        "duration"  :     100,
    }
    xlate = {
        "-h" : ("height",    int, "Output image height in pixels."),
        "-w" : ("width",     int, "Output image width in pixels."),
        "-m" : ("minG",    float, "Minimum quote."),
        "-M" : ("maxG",    float, "Maximum quote."),
        "-v" : ("verbosity", int, "Verbosity level."),
        "-d" : ("duration",  int, "Candlestick duration."),
        "-S" : ("starttime", str, "Start time."),
        "-s" : ("stoptime",  str, "Stop time."),
        "-o" : ("outname",   str, "Output file name.")
    }
    try:
        opts, args = getopt.getopt(argv[1:], "h:w:s:S:d:o:v:m:M:")
    except getopt.GetoptError:
        print("{} [options]\n\nOptions:\n".format(argv[0]))
        for k in xlate:
            print("    {} : {}".format(k, xlate[k][2]))
        sys.exit(2)
    for opt, arg in opts:
        xl = xlate[opt]
        kw[xl[0]] = xl[1](arg)
   
    chart = fex.chart(**kw)
    for line in fileinput.input([]):
        if chart.add(line):
            break
    chart.done()

if __name__ == "__main__":
    processinput(sys.argv)

        
