#!/usr/bin/env python3
# Plot data captured from DSOQuad Oscilloscope
# HanishKVC, 2022
#

"""

DSOQuad DS203
###############

DSO Screen Res: 400x240

WildCat Buf format files
===========================

doesnt contain raw adc samples, rather it only contains the values scaled
and inturn offset to help with direct plotting on the device screen, in a
easy/relatively straight forward manner.

So if you want maximum resolution/finer grained data then on DSO select

* a vertical scale/range/sensitivity (ie V/div) which makes the
  signal being monitored/captured occupy most of the screen vertical
  space.

* as always select a time base / horizontal sensitivity which captures the
  signal sufficiently clearly spread over the horizontal screen space.


Plot vertical
==============

It appears like around 200 pixels out of 240 pixels of device screen, is
used for plotting of the captured signals.

Inturn the signal data seems to be maintained as values in the range 0-199,
inturn mapping one-to-one to how it will appear on the 200 pixels set aside
for plotting on the screen, but inturn offset by 56.

Parallely the ypos wrt the channel(s) seems to be maintained without this
56 offset.

Plot horizontal
================

It appears like 30 data samples correspond to 1 time division. And the device
screen shows 13 time divisions in its full screen (ie no params) mode.


"""


import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import (MultipleLocator, AutoMinorLocator)
import sys
import array


DSCR_VIRT_VDIVS = 8
VIRT_VDIV_LEVELS = 25
VIRT_DATASPACE = 200 # VIRT_VDIV_LEVELS * DSCR_VIRT_VDIVS
HORI_SINGLEWINDOW_SPACE = 512
HIDDEN_WINDOWS = 8
HORI_ALLWINDOWS_SPACE = HORI_SINGLEWINDOW_SPACE * HIDDEN_WINDOWS
DSCR_HORI_TDIVS = 13
HORI_TDIV_DATASAMPLES = 30

NUM_CHANNELS = 4
BUFFILE_META_SIZE = 512

g={}
g['otdivlines'] = []



argsHelp = """
Usage:
    --file <path/dso_saved_buf_file>
      the saved buf file that should be plotted
    --format <buf|dat|auto>
      load either the dat or the buf signal/waveform dump/save file
    --channels <0|1|2|3|01|13|0123|...>
      specify which channels should be displayed as part of the plot
    --dtype <b|B>
      whether to treat the sample data as signed or unsigned(default)
    --ytickschannel <0|1|2|3>
      specify the channel that will be used for deciding the y ticks.
      Defaults to the 1st channel in the specified list of channels.
    --filterdata <convolve|fft|"">
      filter the signal data using the specified logic and plot the
      same additionally to the original signal data.
      convolve or convolve:[w1,w2,...wN]
      fft or fft:ratioOfDataTowardsEndToClearToZero
    --overlaytimedivs <time>
      Allows a overlay of timedivs, based on the time granularity
      specified, starting from position where mouse-right button is
      clicked.

Interactions:
    * clicking a location on the plot will give its voltage and time info
    * when two different locations have been clicked on the plot
      * show the difference in voltage and time btw those points
      * show the number of up/down waveform movements and a rough freq
"""
argsValid = [ "file", "format", "channels", "dtype", "ytickschannel", "filterdata", "overlaytimedivs" ]
def process_args(g, args):
    g['channels'] = "0123"
    g['dtype'] = "B"
    g['ytickschannel'] = "?"
    g['filterdata'] = ""
    g['format'] = "auto"
    if len(args) < 2:
        args.append("--help")
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
    if g['ytickschannel'] == "?":
        g['ytickschannel'] = g['channels'][0]
    g['ytickschannel'] = int(g['ytickschannel'])
    if g['format'] == "auto":
        theFile = g['file'].lower()
        if theFile.endswith(".buf"):
            g['format'] = "buf"
        elif theFile.endswith(".dat"):
            g['format'] = "dat"
        else:
            print("ERRR:ProcessArgs: File type of [{}] unknown, explicitly set --format".format(theFile))


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
    if (ind < 0) or (ind >= len(vdivList)):
        print("DBUG:ParseVDivIndex:{}: Corrupt or Unsupported/New Vdiv".format(ind))
        exit(50)
    return vdivList[ind][0], vdivList[ind][1]*vdivRefBase


def friendly_time(fval):
    # fval = fval[0]
    if fval < 1e-6:
        sval = "{}n".format(round(fval * 1e9, 2))
    elif fval < 1e-3:
        sval = "{}u".format(round(fval * 1e6, 2))
    elif fval < 1:
        sval = "{}m".format(round(fval * 1e3, 2))
    else:
        sval = "{}".format(round(fval, 2))
    print(fval, sval)
    return sval


def friendly_times(fa):
    #return np.apply_along_axis(friendly_time, 0, fa)
    sa = []
    for v in fa:
        sa.append(friendly_time(v))
    return sa


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


def parse_meta(g):
    meta = array.array('h') # Need to check if all entries that is needed here correspond to 16bit signed values only or are there some unsigned 16bit values.
    meta.frombytes(g['meta'])
    print("INFO:ParseMeta: Channel Volts/Div:")
    g['vdiv'] = []
    g['vpixel'] = []
    g['ypos'] = []
    for i in range(0, 16, 4): # Total entries, Entries/Channel
        vd = meta[i+2]
        vdText, vdVal = parse_vdiv_index(vd)
        vpixel = vdVal*DSCR_VIRT_VDIVS/VIRT_DATASPACE # 8 divisions on the screen, mapped to space set aside for plotting
        g['vdiv'].append(vdVal)
        g['vpixel'].append(vpixel)
        ypos = meta[i+3]
        g['ypos'].append(ypos)
        print("\tC{}:{} v/div, {} ypos(adjusted)".format(len(g['vdiv'])-1, vdText, ypos))
    g['timebase'] = parse_tdiv_index(meta[17])
    g['tpixel'] = g['timebase'][1]/HORI_TDIV_DATASAMPLES
    print("INFO:ParseMeta: time/div:{}".format(g['timebase']))


def adj_ydata(yin):
    return yin-56


def show_info(ev):
    xval = ev.xdata * g['tpixel']
    yval = g['yvB'] + (ev.ydata * g['yvPixel'])
    print(ev, xval, yval)
    g['prevX'] = g['curX']
    g['prevY'] = g['curY']
    g['curX'] = ev.xdata
    g['curY'] = ev.ydata
    # overlay tdiv
    otdivStr = g.get('overlaytimedivs', "")
    if ":" in otdivStr:
        otdivTime, otdivMarkers = otdivStr.split(":")
    else:
        otdivTime = otdivStr
        otdivMarkers = "0123456789ABCDEF"
    if (otdivStr != "") and (ev.button == 3):
        for i in range(len(g['otdivlines'])):
            l = g['otdivlines'].pop()
            l.remove()
        otdiv = float(otdivTime)
        otdivPixels = otdiv/g['tpixel']
        x = ev.xdata
        i = 0
        while x < HORI_ALLWINDOWS_SPACE:
            l = g['ax'].axvline(x, color='r', alpha=0.1)
            g['otdivlines'].append(l)
            if i < len(otdivMarkers):
                t = g['ax'].text(x, ev.ydata, otdivMarkers[i])
                i += 1
            x += otdivPixels
    # Calc Up/Down/Freq
    x0 = int(g['prevX'])
    x1 = int(g['curX'])
    pVal = g['ycFD'][x0]
    dValACC = 0
    if pVal < g['ycDMid']:
        bFindUp = True
    else:
        bFindUp = False
    cntUpDown = 0
    if x0 < x1:
        xD = 1
    else:
        xD = -1
    for x in range(x0, x1, xD):
        cVal = g['ycFD'][x]
        dVal = cVal - pVal
        dValACC += dVal
        pVal = cVal
        if dValACC > g['ycDThreshold']:
            dValACC = 0
            if bFindUp:
                cntUpDown += 1
                bFindUp = False
        if dValACC < -g['ycDThreshold']:
            dValACC = 0
            if not bFindUp:
                cntUpDown += 1
                bFindUp = True
    # All in
    xvDelta = xval-g['prevXVal']
    yvDelta = yval-g['prevYVal']
    if (cntUpDown == 0):
        singleCycleTime = np.NaN
    else:
        singleCycleTime = xvDelta/(cntUpDown/2)
    freq = 1/singleCycleTime
    g['prevXYText'].set_text(" Prev: {}, {}".format(g['prevXVal'], g['prevYVal']))
    g['curXYText'].set_text("  Cur: {}, {}".format(xval, yval))
    g['deltaXYText'].set_text("Delta: {}, {}".format(xvDelta, yvDelta))
    g['freqText'].set_text(" Freq: UpDown[{}] Freq[{}]".format(cntUpDown, freq))
    g['prevXVal'] = xval
    g['prevYVal'] = yval
    g['fig'].canvas.draw()


def filter_data(cd, stype):
    #np.convolve(cd[i], [0.1,0.2,0.4,0.2,0.1])
    #np.convolve(cd[i], [0.1,0.1,0.1,0.1,0.2,0.1,0.1,0.1,0.1])
    if stype.startswith('convolve'):
        if ":" in stype:
            convd = eval(stype.split(":")[1])
        else:
            convd = np.ones(10)*0.1
        fd = np.convolve(cd, convd)
    elif stype.startswith("fft"):
        sargs = stype.split(":")
        if len(sargs) == 2:
            ratio = eval(sargs[1])
        else:
            ratio = 0.02
        fd = np.fft.fft(cd)
        fd[int(len(fd)*ratio):] = 0
        fd = np.fft.ifft(fd)
    else:
        fd = cd
    return fd


def fixif_partialdata_window(din, cid):
    for ind in range(HORI_SINGLEWINDOW_SPACE - 4, HORI_ALLWINDOWS_SPACE):
        min = np.min(din[ind:])
        max = np.max(din[ind:])
        if min == max:
            print("WARN:FixIfPartialDataWindow:C{}: Extending single/partial data window starting from {}".format(cid, ind))
            din[ind:] = din[ind-1]
            break
    return din


DATFILE_TOTALSIZE = 2048
DATFILE_CHANNELSIZE = 512
def plot_datfile(g):
    f = open(g['file'], "rb")
    d = f.read()
    if (len(d) != DATFILE_TOTALSIZE):
        print("ERRR:PlotDatFile:FileSize doesnt match")
        exit(1)
    da = array.array(g['dtype']) # control whether to treat as signed or unsigned
    da.frombytes(d)
    cd = np.zeros((NUM_CHANNELS, DATFILE_CHANNELSIZE))
    g['ypos'] = np.zeros((NUM_CHANNELS, 1))
    for i in range(0, DATFILE_TOTALSIZE):
        cid = int(i/DATFILE_CHANNELSIZE)
        dind = i % DATFILE_CHANNELSIZE
        if dind >= 0x188:
            if dind == 0x18d:
                g['ypos'][cid] = da[i]
            continue
        cd[cid, dind] = da[i]
    fig, ax = plt.subplots()
    for i in range(NUM_CHANNELS):
        if not ("{}".format(i) in g['channels']):
            continue
        lines = ax.plot(cd[i])
        ax.annotate("C{}".format(i), (0,cd[i][0]))
        ax.axhline(g['ypos'][i], color=lines[0].get_color(), alpha=0.4)
        fd = filter_data(cd[i], g['filterdata'])
        if g['filterdata'] != "":
            ax.plot(fd)
    ax.xaxis.set_major_locator(MultipleLocator(HORI_TDIV_DATASAMPLES))
    ax.yaxis.set_major_locator(MultipleLocator(VIRT_VDIV_LEVELS))
    plt.grid()
    plt.title(g['file'])
    plt.tight_layout()
    plt.show()


def plot_buffile(g):
    f = open(g['file'], "rb")
    d = f.read()
    if (len(d) != HORI_ALLWINDOWS_SPACE*NUM_CHANNELS+BUFFILE_META_SIZE):
        print("ERRR:PlotBufFile:FileSize doesnt match")
        exit(1)
    da = array.array(g['dtype']) # control whether to treat as signed or unsigned
    da.frombytes(d)
    g['meta'] = d[len(d)-BUFFILE_META_SIZE:]
    parse_meta(g)
    cd = np.zeros((NUM_CHANNELS, HORI_ALLWINDOWS_SPACE))
    rd = np.zeros(HORI_ALLWINDOWS_SPACE)
    yc = g['ytickschannel']
    for i in range(0, HORI_ALLWINDOWS_SPACE*NUM_CHANNELS, NUM_CHANNELS):
        j = int(i/NUM_CHANNELS)
        rd[j] = da[i+yc]
        cd[0,j] = adj_ydata(da[i])
        cd[1,j] = adj_ydata(da[i+1])
        cd[2,j] = adj_ydata(da[i+2])
        cd[3,j] = adj_ydata(da[i+3])

    fig, ax = plt.subplots()
    g['fig'] = fig
    g['ax'] = ax
    fig.canvas.mpl_connect('button_press_event', show_info)
    for i in range(NUM_CHANNELS):
        if not ("{}".format(i) in g['channels']):
            continue
        cd[i] = fixif_partialdata_window(cd[i], i)
        lines = ax.plot(cd[i])
        fd = filter_data(cd[i], g['filterdata'])
        if g['filterdata'] != "":
            ax.plot(fd)
        ax.annotate("C{}:{}".format(i, g['vdiv'][i]), (0,cd[i][0]))
        ax.axhline(g['ypos'][i], color=lines[0].get_color(), alpha=0.4)
        if i == yc:
            yvB = - g['ypos'][i] * g['vpixel'][i]
            yvT = (VIRT_DATASPACE - g['ypos'][i]) * g['vpixel'][i]
            g['ycFD'] = fd

    g['ycDMin'] = np.min(cd[yc])
    g['ycDMax'] = np.max(cd[yc])
    g['ycDMid'] = (g['ycDMin'] + g['ycDMax'])/2
    g['ycDThreshold'] = (g['ycDMid'] - g['ycDMin'])*0.7
    print("INFO:PlotBufFile:C{}: Data Raw[{} to {}] Adjusted[{} to {}] Mid[{}] Threshold[{}]".format(yc, np.min(rd), np.max(rd), g['ycDMin'], g['ycDMax'], g['ycDMid'], g['ycDThreshold']))
    print("INFO:PlotBufFile:C{}:\n\tHistoRaw:{}\n\tHistoAdj:{}".format(yc, np.histogram(rd), np.histogram(cd[yc])))

    ax.grid(True)
    #plt.locator_params('both', tight=True)
    #plt.locator_params('y', nbins=8)
    if g['dtype'] == 'b':
        yB = -(VIRT_DATASPACE/2)
        yT = (VIRT_DATASPACE/2)-1
    else:
        yB = 0
        yT = VIRT_DATASPACE-1
    ax.set_ylim(yB, yT)
    labels = np.linspace(yvB, yvT, DSCR_VIRT_VDIVS+1)
    ax.set_yticks(np.linspace(yB, yT, DSCR_VIRT_VDIVS+1), labels)
    g['yvB'] = yvB
    g['yvT'] = yvT
    g['yvPixel'] = (yvT-yvB)/VIRT_DATASPACE
    xticks = np.arange(0, HORI_ALLWINDOWS_SPACE, HORI_TDIV_DATASAMPLES*10)
    xlabels = friendly_times(xticks*g['tpixel'])
    ax.set_xticks(xticks, xlabels)
    ax.xaxis.set_minor_locator(MultipleLocator(HORI_TDIV_DATASAMPLES))
    g['prevXYText'] = ax.text(0, 0.95, "", transform=ax.transAxes, fontfamily="monospace")
    g['curXYText'] = ax.text(0, 0.90, "", transform=ax.transAxes, fontfamily="monospace")
    g['deltaXYText'] = ax.text(0, 0.85, "", transform=ax.transAxes, fontfamily="monospace")
    g['freqText'] = ax.text(0, 0.80, "", transform=ax.transAxes, fontfamily="monospace")
    g['prevXVal'] = 0
    g['prevYVal'] = 0
    g['curX'] = 0
    g['curY'] = 0
    plt.title(g['file'])
    plt.tight_layout()
    plt.show()


process_args(g, sys.argv)
print(g)
if g['format'] == "dat":
    plot_datfile(g)
else:
    plot_buffile(g)
