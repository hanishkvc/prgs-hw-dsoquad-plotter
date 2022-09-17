#################################################
DSOQuad/DS203 Plotter and Guided Digital Decoder
#################################################
Author: HanishKVC
Version: 20220917IST1045
License: GPL-3.0-or-later


Overview
##########

General
=========

Allow one to look at signal captured by the pocket oscilloscope, either
has a Dat file or Buf file.

This is tested for DSOQuad / DS203 wrt the Wildcat firmware.

Inturn as currently I am using its analog channels, that is what I have
tested while developing this logic.

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

* guided digital decoding of bus signals (captured either over digital
  or analog channel ie either as digital or analog signal)

  Allow user to overlay a custom virtual clock of user specified time
  period | division, over the captured signal data, from a position
  specified by the user interactively. Along with passing of digital
  data decoding hint in the form of custom markers string wrt each of
  the adjacent time divs which are of interest to the user.

  The same is used by the program to show guessed binary digital data
  bit interpretation, wrt data signal in each of these overlaid user
  specified time divisions | steps.

  Additionally 8bit hex values wrt guessed binary digital data can be
  printed.

The above corresponds to signal data belonging to ytickschannel, something
to keep in mind if multiple channels are being looked at, at the same time.

FUTURE: The freq detection uses counting of up/down within the specified
time duration. May also add a fft plot in future.

Guided Decoding of Digital bus
================================

When looking at data (serial/parallel) buses, you will have either synchronous or
asynchronous signalling. In synchronous signalling, there will normally be a clock
line along with data line like with i2c or spi or general purpose memory interface
or so, while asynchronous signalling will have only data line normally like uart
/ rs232 / rs485 / ...

For now to keep things minimal, simple yet flexible to try and allow both kind of
data to be decoded at a local level (ie byte or word level and not necessarily
beyond), this logic, using its overlaytimedivs mechanism, allows the user to guide
the decoding of the digital bus data captured either over a digital channel or
even the analog channel (as long as the voltage crosses a internally infered
threshold it will be treated as logic 1, else logic 0).

As part of this, one is required to

* define a virtual clock of their own, which can be overlaid on the plot, starting
  from any position chosen by the user. This should be configured to match the
  data related clocking setup of the bus being analysed.

  * ex: for 1 KHz specify 1e-3 or 1/1e3 or so

  * ex: for 9600 buad rate, simply specify 1/9600

* Inturn the logic also allows one to specify a markers string to help guide the
  identification of the data bits and their bit positions, as well as non data bits
  (control/sync/...) bits like start, stop, any others (just print those bit, if
  needed). And the same will be used to decode / guess the significance of binary
  bits wrt each of the time steps|divisions starting from the position selected by
  the user and inturn print the same (ie individual binary bits) and additionally
  the cummulated 8bit hex values, if so requested by the user.

  * ex: for midi specify S01234567sS01234567sS01234567s

  * ex: for 16bits of serial data without any start-stop-etal and assuming lsb
    first use 01234567P01234567P

  * ex: for 16bits of serial data without any start-stop-etal and assuming msb
    first use 76543210P76543210P

* look at the example usage specified further down wrt --overlaytimedivs arg
  for more examples.

  * ex: for midi use --overlaytimedivs 1/31250:S01234567sS01234567sS01234567s

If i2c/spi/etal bus being monitored uses hardware for generating the bus signals,
then the bus (clock and data lines) will operate with a uniform time period/interval
wrt a single transaction of byte(s), and the above mentioned guided decoding of
digital bus will be able to decode the bus data. However if the clock and data lines
are implemented using software emulation over gpio lines or so, then technically the
bus standard does allow for variations in clocking period even within a single
transaction, and depending on how the software logic is implemented the clock period
may or may not be uniform over the duration of a single transaction of byte(s). Then
the above mentioned guided decoding logic (virtual clock time divs + hint markers)
currently implemented by this program wont be able to handle such variations in timing,
if it goes beyond a small fraction.

Some Synchronous buses especially the parallel ones, may use wait state insertion
to allow for stretching of the bus transaction cycle. So one may have to insert
extra(one or more) p or 0 or 7 or so to account for same.

FUTURE: May add support for a check string in addition to markers string. This can
allow automatic cross check of start/stop/... bits and the value expected wrt them.
It could use chars like 0,1,?|* or so


Usage
########

Cmdline arguments
===================

The needed arguments

--file <path/dso_saved_buf_or_dat_file>

  the saved buf or dat file that should be plotted

Arguments that may be used if required

--format <buf|dat|auto>

  load either the dat or the buf signal/waveform dump/save file

  default is auto and based on file extension the file format is selected.

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

  no: dont show fft plot [the default]

  yes: picks a hardcoded sampling rate, this is supported for only
  few timebases and may be wrong wrt the actual sampling rate used
  with different firmware versions.

  samplingrate: the sampling rate to assume wrt fft related logic

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

      p to print the bit corresponding to its time step|div,
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
  specified the same as part of --overlaytimedivs. And additionally
  the guessed/infered individual digital binary bit values and the
  cummulated 8bit hex values (from the guessed individual bits, if
  requested), as mentioned in the explanation wrt --overlaytimedivs
  argument.



Examples
==========

A example trying to look at Midi data capture, with its 32uSec bit time, 3 byte msgs of 1Start+8Data+0Parity+1Stop bits

./dso-plotter.py --file path/to/file.buf --overlaytimedivs 32e-6:S01234567sS01234567sS01234567s

./dso-plotter.py --file path/to/file.buf --overlaytimedivs 1/31250:S01234567sS01234567sS01234567s

./dso-plotter.py --file Data/UsbMidi/20220914S03/DATA023.BUF --overlaytimedivs 1/31250:p01234567Ppp01234567Ppp01234567Pp

