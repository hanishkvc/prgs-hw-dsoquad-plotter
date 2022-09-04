#!/usr/bin/env python3
# Plot data captured from DSOQuad Oscilloscope
# HanishKVC, 2022
#

import numpy as np
import matplotlib.pyplot as plt
import sys
import array


g={}


def process_args(g, args):
    iArg = 0
    while iArg < len(args)-1:
        iArg += 1
        cArg = args[iArg]
        if cArg == "--file":
            iArg += 1
            g['file'] = args[iArg]
        elif cArg == "--format":
            iArg += 1
            g['format'] = args[iArg]


def parse_meta(g):
    meta = array.array('h')
    meta.frombytes(g['meta'])
    print("Channel Volts/Div:")
    g['vdiv'] = []
    for i in range(0,16,4):
        vd = meta[i+2]
        print("\t{}:{}".format(len(g['vdiv']), vd))
        g['vdiv'].append(vd)


def plot_me(g):
    f = open(g['file'], "rb")
    d = f.read()
    g['meta'] = d[len(d)-512:]
    parse_meta(g)
    cd = np.zeros((4,4096))
    for i in range(0,4096*4,4):
        j = int(i/4)
        cd[0,j] = d[i]
        cd[1,j] = d[i+1]
        cd[2,j] = d[i+2]
        cd[3,j] = d[i+3]
    p = plt.subplots(4,1)
    for i in range(4):
        ax = p[1][i]
        ax.plot(cd[i])
        ax.set_title("Channel:{}".format(i))
    plt.tight_layout()
    plt.show()


process_args(g, sys.argv)
print(g)
plot_me(g)
