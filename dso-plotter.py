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
    g['dtype'] = "b"
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
        elif cArg == "--dtype":
            iArg += 1
            g['dtype'] = args[iArg]


vdivRefBase=25e-6
vdivList = [
    [ "50mV", 2000],
    [ "0.1V", 4000],
    [ "0.2V", 8000],
    [ "0.5V", 20000],
    [ " 1V ", 40000],
    [ " 2V ", 80000],
    [ " 5V ", 200000],
    [ "10V ", 400000]
]

def parse_vdiv_index(ind):
    return vdivList[ind][0], vdivList[ind][1]*vdivRefBase


YPOS_ADJ = 1.28
def parse_meta(g):
    meta = array.array('h') # Need to check if all entries that is needed here correspond to 16bit signed values only or are there some unsigned 16bit values.
    meta.frombytes(g['meta'])
    print("Channel Volts/Div:")
    g['vdiv'] = []
    g['vdispres'] = []
    g['ypos'] = []
    for i in range(0, 16, 4): # Total entries, Entries/Channel
        vd = meta[i+2]
        vdText, vdVal = parse_vdiv_index(vd)
        vdr = vdVal*VIRT_DIVS/VIRT_DATASPACE # 8 divisions on the screen, mapped to 8bit
        g['vdiv'].append(vdVal)
        g['vdispres'].append(vdr)
        ypos = meta[i+3]*YPOS_ADJ
        g['ypos'].append(ypos)
        print("\tC{}:{} v/div, {} ypos(adjusted)".format(len(g['vdiv']), vdText, ypos))


def adj_ydata(yin):
    """
    A very imperfect ydata adjustment for now.
    Need to look at the underlying reasons and implications and then
    update this to be more accurate.
    """
    y = 256-yin
    y = y * YPOS_ADJ
    y = 256-y
    return y


def plot_me(g):
    f = open(g['file'], "rb")
    d = f.read()
    if (len(d) != HORI_TOTALSPACE*NUM_CHANNELS+META_SIZE):
        print("ERRR:PlotMe:FileSize doesnt match")
        exit(1)
    da = array.array(g['dtype']) # control whether to treat as signed or unsigned
    da.frombytes(d)
    g['meta'] = d[len(d)-512:]
    parse_meta(g)
    cd = np.zeros((4,4096))
    for i in range(0,4096*4,4):
        j = int(i/4)
        cd[0,j] = adj_ydata(da[i])
        cd[1,j] = adj_ydata(da[i+1])
        cd[2,j] = adj_ydata(da[i+2])
        cd[3,j] = adj_ydata(da[i+3])
    #p = plt.subplots(4,1)
    for i in range(NUM_CHANNELS):
        if not ("{}".format(i) in g['channels']):
            continue
        plt.plot(cd[i])
        plt.annotate("C{}:{}".format(i, g['vdiv'][i]), (0,cd[i][0]))
        plt.axhline(g['ypos'][i], 0, 4096, color='r')
    plt.grid(True)
    #plt.locator_params('both', tight=True)
    #plt.locator_params('y', nbins=8)
    if g['dtype'] == 'b':
        yB = -(VIRT_DATASPACE/2)
        yT = (VIRT_DATASPACE/2)-1
    else:
        yB = 0
        yT = VIRT_DATASPACE-1
        plt.ylim(0, VIRT_DATASPACE-1)
    plt.ylim(yB, yT)
    plt.yticks(np.linspace(yB, yT, VIRT_DIVS+1))
    plt.title(g['file'])
    plt.tight_layout()
    plt.show()


process_args(g, sys.argv)
print(g)
plot_me(g)
