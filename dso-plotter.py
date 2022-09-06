#!/usr/bin/env python3
# Plot data captured from DSOQuad Oscilloscope
# HanishKVC, 2022
#

"""


Buf format
============

doesnt contain raw adc samples, rather it only contains the values scaled
and inturn offset for direct plotting on the device screen.

So if you want maximum resolution/finer grained data then on DSO select

* a vertical scale/range/sensitivity (ie V/div) which makes the
  signal being monitored/captured occupy most of the screen vertical
  space.

* as always select a time base / horizontal sensitivity which captures the
  signal sufficiently clearly spread over the horizontal screen space.


Plot vertical
==============

The DSO seems to map the plot value vertically in a bit of a odd way.

Rather initially as I had assumed buf files will contain raw adc samples,
and then morphed the logic to assume that it is a raw mapping of the plot
on screen, however I had forgotten about the actual screen resolution of
the DSO. Not sure if that is what has lead to the strangeness I noticied,
need to look into it yet.


"""


import numpy as np
import matplotlib.pyplot as plt
import sys
import array


VIRT_DIVS = 8
VIRT_DATASPACE = 200 # 240 vertical space divided into 8 units of data, ~0.5 unit of bottom menu space, 1 unit of top menu space
HORI_DIVS = 13
HORI_DATASPACE = 512
HIDDEN_SCREENS = 8
HORI_TOTALSPACE = HORI_DATASPACE * HIDDEN_SCREENS
NUM_CHANNELS = 4
META_SIZE = 512

g={}


argsHelp = """
Usage:
    --file <path/dso_saved_buf_file>
    --format buf
    --channels <0|1|2|3|01|13|0123|...>
    --dtype <b|B>
"""
argsValid = [ "file", "format", "channels", "dtype" ]
def process_args(g, args):
    g['channels'] = "0123"
    g['dtype'] = "B"
    iArg = 0
    while iArg < len(args)-1:
        iArg += 1
        cArg = args[iArg]
        if cArg.startswith("--"):
            cKey = cArg[2:]
            if not (cKey in argsValid):
                if cKey == "help":
                    print(argsHelp)
                else:
                    print("ERRR:ProcessArgs: Unknown argument ", cKey)
                exit(1)
            iArg += 1
            cVal = args[iArg]
            g[cKey] = cVal


vdivRefBase=25e-6
#
# Values picked from Sys::Bios.c::Y_Attr
#
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


tdivRefBase = 3.3333e-6
#
# Values picked from Sys::Bios.c::X_Attr and App::Process.c::TbaseOS
#
tdivList = [
    [ "1S", 200-1, 1500-1 ],
    [ "500mS", 100-1, 1500-1 ],
    [ "200mS", 40-1, 1500-1 ],
    [ "100mS", 40-1, 750-1 ],
    [ "50mS", 40-1, 375-1 ],
    [ "20mS", 16-1, 375-1 ],
    [ "10mS", 8-1, 375-1 ],
    [ "5mS", 4-1, 375-1 ],
    [ "2mS", 4-1, 150-1 ],
    [ "1mS", 2-1, 150-1 ],
    [ "500uS", 1-1, 150-1 ],
    [ "200uS", 1-1, 60-1 ],
    [ "100uS", 1-1, 30-1 ],
    [ "50uS", 1-1, 15-1 ],
    [ "20uS", 1-1, 6-1 ],
    [ "10uS", 1-1, 3-1 ],
    [ "5uS", 1-1, 2-1 ]
]

def parse_tdiv_index(ind):
    val = (tdivList[ind][1]+1)*(tdivList[ind][2]+1)*tdivRefBase
    return tdivList[ind][0], val


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
        vdr = vdVal*VIRT_DIVS/VIRT_DATASPACE # 8 divisions on the screen, mapped to space set aside for plotting
        g['vdiv'].append(vdVal)
        g['vdispres'].append(vdr)
        ypos = meta[i+3]
        g['ypos'].append(ypos)
        print("\tC{}:{} v/div, {} ypos(adjusted)".format(len(g['vdiv']), vdText, ypos))
    g['timebase'] = parse_tdiv_index(meta[17])
    print("\tt/div:{}".format(g['timebase']))


def adj_ydata(yin):
    return yin-56


def adj_ydata_c3(yin):
    """
    A very imperfect ydata adjustment for now.
    Need to look at the underlying reasons and implications and then
    update this to be more accurate.
    """
    y = 256-yin
    y = y * YPOS_ADJ
    y = 256-y
    y = y - y*0.04
    return y


def adj_ydata_c2(yin):
    """
    A very imperfect ydata adjustment for now.
    Need to look at the underlying reasons and implications and then
    update this to be more accurate.
    """
    y = yin*0.82
    y = y + 14
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
    td = np.zeros(4096)
    for i in range(0,4096*4,4):
        j = int(i/4)
        td[j] = da[i]
        cd[0,j] = adj_ydata(da[i])
        cd[1,j] = adj_ydata(da[i+1])
        cd[2,j] = adj_ydata(da[i+2])
        cd[3,j] = adj_ydata(da[i+3])
    print("Data Min,Max:", np.min(td), np.max(td))
    #p = plt.subplots(4,1)
    for i in range(NUM_CHANNELS):
        if not ("{}".format(i) in g['channels']):
            continue
        plt.plot(cd[i])
        plt.annotate("C{}:{}".format(i, g['vdiv'][i]), (0,cd[i][0]))
        plt.axhline(g['ypos'][i], 0, 4096, color='r')
        yvB = - g['ypos'][i] * g['vdispres'][i]
        yvT = (VIRT_DATASPACE - g['ypos'][i]) * g['vdispres'][i]
    plt.grid(True)
    #plt.locator_params('both', tight=True)
    #plt.locator_params('y', nbins=8)
    if g['dtype'] == 'b':
        yB = -(VIRT_DATASPACE/2)
        yT = (VIRT_DATASPACE/2)-1
    else:
        yB = 0
        yT = VIRT_DATASPACE-1
    plt.ylim(yB, yT)
    labels = np.linspace(yvB, yvT, VIRT_DIVS+1)
    plt.yticks(np.linspace(yB, yT, VIRT_DIVS+1), labels)
    plt.xticks(np.linspace(0, HORI_TOTALSPACE, 18*8))
    plt.title(g['file'])
    plt.tight_layout()
    plt.show()


process_args(g, sys.argv)
print(g)
plot_me(g)
