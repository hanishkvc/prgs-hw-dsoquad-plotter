#!/usr/bin/env python3
# Plot data captured from DSOQuad Oscilloscope
# HanishKVC, 2022
#

import numpy as np
import matplotlib.pyplot as plt
import sys
import array


VIRT_DIVS = 8
VIRT_DATASPACE = 256 # 8bits
HORI_DIVS = 13
HORI_DATASPACE = 512
HIDDEN_SCREENS = 8
HORI_TOTALSPACE = HORI_DATASPACE * HIDDEN_SCREENS
NUM_CHANNELS = 4
META_SIZE = 512

g={}


def process_args(g, args):
    g['channels'] = "0123"
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
        elif cArg == "--channels":
            iArg += 1
            g['channels'] = args[iArg]


def parse_meta(g):
    meta = array.array('h') # Need to check if all entries that is needed here correspond to 16bit signed values only or are there some unsigned 16bit values.
    meta.frombytes(g['meta'])
    print("Channel Volts/Div:")
    g['vdiv'] = []
    g['vdispres'] = []
    for i in range(0, 16, 4): # Total entries, Entries/Channel
        vd = meta[i+2]
        vdr = vd*VIRT_DIVS/VIRT_DATASPACE # 8 divisions on the screen, mapped to 8bit
        print("\t{}:{}".format(len(g['vdiv']), vd))
        g['vdiv'].append(vd)
        g['vdispres'].append(vdr)


def plot_me(g):
    f = open(g['file'], "rb")
    d = f.read()
    if (len(d) != HORI_TOTALSPACE*NUM_CHANNELS+META_SIZE):
        print("ERRR:PlotMe:FileSize doesnt match")
        exit(1)
    da = array.array("B") # control whether to treat as signed or unsigned
    da.frombytes(d)
    g['meta'] = d[len(d)-512:]
    parse_meta(g)
    cd = np.zeros((4,4096))
    for i in range(0,4096*4,4):
        j = int(i/4)
        cd[0,j] = da[i]
        cd[1,j] = da[i+1]
        cd[2,j] = da[i+2]
        cd[3,j] = da[i+3]
    #p = plt.subplots(4,1)
    for i in range(NUM_CHANNELS):
        if not ("{}".format(i) in g['channels']):
            continue
        plt.plot(cd[i])
        plt.annotate("C{}:{}".format(i, g['vdiv'][i]), (0,cd[i][0]))
    plt.grid(True)
    plt.ylim(VIRT_DATASPACE-1)
    plt.yticks(np.linspace(0, VIRT_DATASPACE-1, VIRT_DIVS+1))
    plt.tight_layout()
    plt.show()


process_args(g, sys.argv)
print(g)
plot_me(g)
