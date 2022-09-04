#!/usr/bin/env python3
# Plot data captured from DSOQuad Oscilloscope
# HanishKVC, 2022
#

import numpy as np
import matplotlib.pyplot as plt
import sys


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


def plot_me(g):
    f = open(g['file'], "rb")
    d = f.read()
    meta = d[len(d)-512:]
    cd = np.zeros((4,4096))
    for i in range(0,4096*4,4):
        cd[0,i] = d[i]
        cd[1,i] = d[i+1]
        cd[2,i] = d[i+2]
        cd[3,i] = d[i+3]
    p = plt.subplots((4,1))
    for i in range(4):
        p[1][i].plot(cd[i])
    plt.show()


process_args(g, sys.argv)
print(g)
plot_me(g)
