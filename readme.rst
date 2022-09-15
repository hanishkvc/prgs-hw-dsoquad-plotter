#######################
DSOQuad/DS203 Plotter
#######################
Author: HanishKVC
Version: 20220914IST2253


Overview
##########

General
=========

Allow one to look at signal captured by the pocket oscilloscope, either
has a Dat file or Buf file.

This is tested for DSOQuad / DS203 wrt the Wildcat firmware.

Note that the sampled data is stored in these files similar to how it
would appear on the device screen, so to get enough resolution in the
captured data, ensure that the Volts/Div and Time/Div is fine enough
to capture what you are interested in.

Dat file doesnt contain meta data wrt the captured signal and also it
contains only one screen worth of data (ie around 400 samples). Other
than signal levels in terms of screen position, the only other info
it contains is the baseline wrt each channel.

In addition to the channel signal data, Buf file contains meta data like
volts/div, times/div, channel baseline levels, ...
Buf files are potentially more useful, if the oscilloscope is setup to
dump data when in the large buffer mode.


Additional
============

One can get the following additional info from / wrt buf files, when
interacting with the plot

* voltage and time wrt each position on the plot

* diff in voltage and time between the last two clicked positions.

* guess of freq wrt the data signal

* overlaying of user specified time divisions from a position specified
  by them. This also includes custom markers wrt each of these timedivs.

  It also shows a guessed binary digital data interpretation, wrt data
  signal in each of these overlaid user specified time divisions.

  Additionally 8bit hex values wrt guessed binary digital data can be
  printed.

The above correspond to signal data belonging to ytickschannel.


Decoding Digital bus
=======================

When looking at serial buses, you will have either synchronous or asynchronous
signalling. In synchronous signalling, there will normally be a clock line along
with data line like with i2c or spi or so, while asynchronous signalling will
have only data line normally like uart/rs232/rs485/...

For now to keep things minimal, simple yet flexible to try and allow both kind of
data to be decoded at a local level (ie byte or word level and not necessarily
beyond), this logic allows the user to define a virtual clock of their own using
the overlaytimedivs option. Inturn the logic allows one to specify markers to
identify the data bits and their bit positions, and the same will be used decode
/guess the binary bits and print their 8bit hex values, if so requested by the
user.

If i2c/spi/etal bus being monitored uses hardware for generating the bus signals,
then clock line will normally trigger at uniform interval wrt a single transaction
of byte(s), and the above simple yet flexible logic can be used to help decode the
same. However if the clock and data lines are implemented using software emulation
over gpio lines or so, then technically the bus standard does allow for variations
in clocking period even within a single transaction, but the above mentioned simple
logic based decoding currently implemented by this program wont be able to handle
such variations, if it goes beyond a small fraction.


Usage
########

Cmdline arguments
===================

The needed arguments

--file <path/dso_saved_buf_file>

  the saved buf file that should be plotted

Arguments that may be used if required

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

--overlaytimedivs <time[:StringOfCharMarkers]>

  Allows a overlay of timedivs, based on the time granularity
  specified, starting from position where mouse-right button is
  clicked.

  If a StringOfCharMarkers is specified, place one char at a time
  from this string into adjacent overlay time divs.

  Also show signal data interpreted as binary digital values, wrt
  each overlaid time division, as it appears at their centers.

  Additionally 8bit hex value wrt guessed binary digital data can be
  printed. For this

    If looking at serial bus data which follow start-bitpositions-stop
    template then use, S(tart),0-7(BitPositions),s(top) as the markers.
    s marker will trigger printing of accumulated hex value on plot.

    If looking at serial digital bus data, which contains only data bits
    and no start or stop bits, then use 0-7 as markers corresponding
    to bit positions and #print# to trigger printing of accumulated
    hex value on the plot.

    Printing will also reset the value accumulator variable.

    NOTE: The Bit position markers need not be in order.

  NOTE: This only works for buf files and not dat files, bcas dat
  files dont have time or voltage info in them.

  As the time/div supported by the oscilloscope need not directly
  align with the freq characteristic / bitrate of the signal being
  monitored, so one can use this option to overlay custom time/divs
  that matches what one is interested in wrt the signals.


Interactions
=============

Wrt Buf files
+++++++++++++++

* clicking a location on the plot will give its voltage and time info

* when two different locations have been clicked on the plot
  * show the difference in voltage and time btw those points
  * show the number of up/down waveform movements and a rough freq

* Clicking anywhere using right mouse button, will show a overlay of
  timedivs, with a time period specified using --overlaytimedivs.

  It will also show a set of markers wrt each time div, if user has
  specified the same as part of --overlaytimedivs.

  Additionally cummulated hex value from the guessed/infered individual
  digital bit values can/may be printed on the plot, as mentioned in
  the explanation wrt --overlaytimedivs argument.



Examples
==========

A example trying to look at Midi data capture, with its 32uSec bit time, 3 byte msgs of 1Start+8Data+0Parity+1Stop bits

./dso-plotter.py --file path/to/file.buf --overlaytimedivs 32e-6:S01234567sS01234567sS01234567s
./dso-plotter.py --file path/to/file.buf --overlaytimedivs 1/31250:S01234567sS01234567sS01234567s
./dso-plotter.py --file Data/UsbMidi/20220914S03/DATA023.BUF --overlaytimedivs 1/31250:001234567#print#0001234567#print#0001234567#print#

