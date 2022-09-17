#!/usr/bin/env python3
# Plot data captured from DSOQuad Oscilloscope
# For now
# * Supports Buf and Dat files
# * tested wrt the analog channels
# * guided digital decode of bus data
#   captured either has digital or analog signal
#   using a virtual clock and markers/hints mechanism
# HanishKVC, 2022
#

"""

DSOQuad DS203
###############

DSO Screen Res: 400x240

WildCat Buf format files
===========================

overview
-----------

doesnt contain raw adc samples, rather it only contains the values scaled
and inturn offset to help with direct plotting on the device screen, in a
easy/relatively straight forward manner.

So if you want maximum resolution/finer grained data then on DSO select

* a vertical scale/range/sensitivity (ie V/div) which makes the
  signal being monitored/captured occupy most of the screen vertical
  space.

* as always select a time base / horizontal sensitivity which captures the
  signal sufficiently clearly spread over the horizontal screen space.


Disk format
-------------

16K of data sample containing 4K data samples of Channel 0 to 3 intermixed
one after the other

* C0:D0 C1:D0 C2:D0 C3:D0 C0:D1 C1:D1 C2:D1 C3:D1 ...... C3:D4095

512 bytes of meta data which gives info about the way individual
channels were setup

Capture Buffer Mode
---------------------

Make short presses on the right toggle button till it shows a
small window within a very long/wide window at the bottom center,
this potentially corresponds to the large buffer mode (with a yellow
triangular waveform, even thou the doc seems to say orange???)

However even thou it is supposed to capture 4K samples, with the midi
test script, I seem to be seeing only NoteOff commands/messages and
not the NoteOn messages?????

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


Dat Files
===========

4 sets of 512 bytes each, corresponding to channel 0, 1, 2, 3. Each
consisting of

392 8bit dataSamplesOf Channel + 0000 0000 00BaseLine 0000 + 112 x 00 bytes


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

    --showfft <no|yes|samplingrate>
      no: dont show fft plot [the default].
      yes: infer the sampling rate from timebase and number of samples in it.
      samplingrate: allow user to override sampling rate assumed, which is
      currently used by the fft related logic.

    --overlaytimedivs <time[:StringOfCharMarkers]>
      Allows overlaying of a virtual clock signal | timedivs, based on the
      time granularity specified, starting from position where mouse-right
      button is clicked.
      Additionally allow hint to be passed to the guided digital data
      decode logic, in the form of a StringOfCharMarkers.

      This places one char at a time from this markers string into adjacent
      overlay time divs.
      Also shows channel (analog or digital doesnt matter) signal data
      interpreted as binary digital values, wrt each overlaid time division,
      as it appears at their centers, guided based on string of Markers/hints.

      Additionally 8bit hex value wrt guessed binary digital data can be
      printed.

      For this

        If looking at serial bus data which follow start-bitpositions-stop
        template then use S(tart), 0-7(BitPositions), s(top) as the markers.
        s marker will trigger printing of accumulated hex value on plot.

        If looking at serial digital bus data, which contains only data bits
        and no start or stop bits, then use 0-7 as markers corresponding
        to bit positions and P to trigger printing of accumulated hex value
        on the plot.

        Additionally one can use
          H to force a half time step|div.
          p to print the bit correponding to its time step|div
          without adding the bit to the 8bit value accumulator.

        Printing using s or P, will also reset the 8bit value accumulator
        variable.

        NOTE: The Bit position markers need not be in order. Thus giving
        the flexibility to interpret lsb first or msb first or if reqd
        even intermixed bit placement on the bus.

        All hint markers consume full or part of a time step | division,
        except for P.

      NOTE: This only works for buf files and not dat files, bcas dat
      files dont have time or voltage info in them.

Interactions:
    * clicking a location on the plot will give its voltage and time info
    * when two different locations have been clicked on the plot
      * show the difference in voltage and time btw those points
      * show the number of up/down waveform movements and a rough freq
    * Clicking anywhere using right mouse button, will show a overlay of
      timedivs, with a time period specified using --overlaytimedivs.
      It will also show a set of markers wrt each time div, if user has
      specified the same as part of --overlaytimedivs. And additionally
      the guessed/infered individual digital binary bit values and the
      cummulated 8bit hex values (from the guessed individual bits, if
      requested), as mentioned in the explanation wrt --overlaytimedivs
      argument.



Examples:
    A example trying to look at Midi data capture, with its 32uSec bit time, 3 byte msgs of 1Start+8Data+0Parity+1Stop bits
    ./dso-plotter.py --file Data/UsbMidi/20220914S01/DATA001.BUF --overlaytimedivs 32e-6:S01234567sS01234567sS01234567s
    ./dso-plotter.py --file Data/UsbMidi/20220914S03/DATA023.BUF --overlaytimedivs 1/31250:p01234567Ppp01234567Ppp01234567Pp

    A example where some data bits are in Left-to-Right and others in Right-to-Left order
    ./dso-plotter.py --file Path/To/File.BUF --overlaytimedivs 1/9600:S01234567sS76543210sS01234567s


"""
argsValid = [ "file", "format", "channels", "dtype", "ytickschannel", "filterdata", "overlaytimedivs", "showfft" ]
def process_args(g, args):
    g['channels'] = "0123"
    g['dtype'] = "B"
    g['ytickschannel'] = "?"
    g['filterdata'] = ""
    g['format'] = "auto"
    g['showfft'] = "no"
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
    g['sr'] = 1/g['tpixel']
    print("INFO:ParseMeta:SamplingRate:", g['sr'])


def adj_ydata(yin):
    return yin-56


gt = {}
gt['otdivlines'] = []
TIME_BEYONDMAX = 9999
TIME_BEYONDMIN = -9999
def show_info(ev):
    evaxY0 = ev.inaxes.get_subplotspec().get_position(g['fig']).y0
    axY0 = g['ax'].get_subplotspec().get_position(g['fig']).y0
    if (evaxY0 != axY0):
        return
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
        otdivMarkers = "01234567P01234567P"
    if (otdivStr != "") and (ev.button == 3):
        for i in range(len(gt['otdivlines'])):
            l = gt['otdivlines'].pop()
            l.remove()
        otdiv = eval(otdivTime)
        otdivPixels = otdiv/g['tpixel']
        otdivSigValPixels = otdivPixels/2
        tx = ev.xdata
        dy = ev.ydata - 4
        i = 0
        gt['val'] = 0
        txMin = TIME_BEYONDMAX
        txMax = TIME_BEYONDMIN
        while tx < HORI_ALLWINDOWS_SPACE:
            l = g['ax'].axvline(tx, color='r', alpha=0.1)
            gt['otdivlines'].append(l)
            timeAdjust = 1.0
            if i < len(otdivMarkers):
                marker = otdivMarkers[i]
                i += 1
                bPlotTD = False
                if marker == 'H':
                    timeAdjust = 0.5
                    bPlotTD = True
                dx = tx + (otdivSigValPixels*timeAdjust)
                cVal = g['ycFD'][round(dx)]
                if cVal > g['ycDMid']:
                    vtext = "1"
                else:
                    vtext = "0"
                if (marker == 's') or (marker == 'P'):
                    g['ax'].plot([txMin, txMax], [dy-5, dy-5], color='b', alpha=0.5)
                    print("DBUG:ShowInfo:8bitHex:", dy-5, txMin, txMax)
                    g['ax'].text((txMin+txMax)/2, dy-4, hex(gt['val']))
                    gt['val'] = 0
                    txMin = TIME_BEYONDMAX
                    txMax = TIME_BEYONDMIN
                    if marker == 's':
                        bPlotTD = True
                    else: # ie if P
                        timeAdjust = 0.0
                elif marker == 'S':
                    gt['val'] = 0
                    bPlotTD = True
                elif (marker >= '0') and (marker <= '7'):
                    ipos = int(marker)
                    ival = int(vtext)
                    gt['val'] &= ((1 << ipos) ^ 0xFF)
                    #gt['val'] &= (~np.uint8(1 << ipos))
                    gt['val'] |= (ival << ipos)
                    bPlotTD = True
                    if tx > txMax:
                        txMax = dx
                    if tx < txMin:
                        txMin = dx
                elif marker == 'p':
                    bPlotTD = True
                if bPlotTD:
                    g['ax'].text(tx, ev.ydata, marker)
                    g['ax'].text(dx, dy, vtext, color="r")
                #print(ipos, ival, bin(gt['val']))
            tx += (otdivPixels * timeAdjust)
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
        singleCycleTimeF1 = np.NaN
        singleCycleTimeF2 = np.NaN
    else:
        singleCycleTimeF1 = xvDelta/cntUpDown
        singleCycleTimeF2 = xvDelta/(cntUpDown/2)
    freq1 = 1/singleCycleTimeF1
    freq2 = 1/singleCycleTimeF2
    g['prevXYText'].set_text(" Prev: {}, {}".format(g['prevXVal'], g['prevYVal']))
    g['curXYText'].set_text("  Cur: {}, {}".format(xval, yval))
    g['deltaXYText'].set_text("Delta: {}, {}".format(xvDelta, yvDelta))
    g['freqText'].set_text(" Freq: UpDown[{}] FreqUD1[{}] FreqUD2[{}]".format(cntUpDown, freq1, freq2))
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


def show_fft(g):
    #print("AxFD", g['axFD'], dir(g['axFD']))
    try:
        sr = eval(g['showfft'])
    except:
        sr = g['sr']
    fd = np.fft.fft(g['ycFD'])
    fdLen = int(len(fd)/2)
    fd = fd[0:fdLen]
    fd[0] = 0 # clear the dc value
    fd = np.abs(fd)
    xd = np.arange(fdLen)*(sr*0.5/fdLen)
    g['axFD'].plot(xd,fd)


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

    if g['showfft'] != "no" :
        fig, ax = plt.subplots(2,1)
        g['axFD'] = ax[1]
        ax = ax[0]
    else:
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

    if g['showfft'] != "no" :
        show_fft(g)

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
